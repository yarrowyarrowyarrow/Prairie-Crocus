"""
tests/test_shrub_habit.py — a shrub is drawn from its own stems and leaves once
somebody has read them, and from the shared figure until then (V3.49, F268).

What can go wrong quietly, each with a test here:

  * a shrub whose numbers are the seeder's estimate is drawn in a body of its
    own, stating a guess as a reading (P9);
  * the Python rule and the viewer chunk disagree about a form, so a shrub the
    scene calls a thicket is drawn as nothing;
  * the shrub layer, moved out of a chunk at its ceiling, is lost on the way,
    or the new body is routed to the pond layer with every other body the
    plant list does not know;
  * a reading is written with no stem count, or a count with no reading.
"""

import json
import os
import re
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from src import data_quality, herb_habit, native_here, shrub_habit  # noqa: E402

_JS = os.path.join(_ROOT, "html", "scene3d")


def _js(name: str) -> str:
    with open(os.path.join(_JS, name), encoding="utf-8") as fh:
        return fh.read()


def _shrub(**over) -> dict:
    p = {"plant_type": "shrub", "branching": "multi_stem", "woody_stems": 25,
         "leaf_shape": "ovate", "leaf_size_cm": 8.0, "leaf_arrangement": "opposite",
         "leaf_data_source": "photo", "x": 1.0, "y": 2.0,
         "height_m": 2.4, "canopy_m": 2.4,
         "mature_height_m": 3.0, "mature_canopy_m": 3.0}
    p.update(over)
    return p


class TheGate(unittest.TestCase):
    """Only a shrub whose leaves were read and stems counted gets the body."""

    def test_an_estimate_keeps_the_baked_figure(self):
        for source in ("", "estimated", None):
            self.assertIsNone(shrub_habit.form_for(_shrub(leaf_data_source=source)),
                              f"leaf_data_source={source!r} was drawn as read")

    def test_a_reading_of_any_kind_counts(self):
        for source in herb_habit.READ:
            self.assertEqual(shrub_habit.form_for(_shrub(leaf_data_source=source)), "clump")

    def test_only_shrubs(self):
        """A tree keeps its crown; a wildflower has a body of its own."""
        for kind in ("tree", "vine", "wildflower", "herb", "groundcover", "grass"):
            self.assertIsNone(shrub_habit.form_for(_shrub(plant_type=kind)), kind)

    def test_no_stem_count_draws_nothing_new(self):
        for stems in (None, 0, ""):
            self.assertIsNone(shrub_habit.form_for(_shrub(woody_stems=stems)))

    def test_no_leaf_recorded_draws_nothing_new(self):
        self.assertIsNone(shrub_habit.form_for(_shrub(leaf_shape="")))
        self.assertIsNone(shrub_habit.form_for(_shrub(leaf_size_cm=None)))

    def test_a_habit_these_forms_do_not_draw_is_left_alone(self):
        for habit in ("decurrent", "excurrent", "rosette", ""):
            self.assertIsNone(shrub_habit.form_for(_shrub(branching=habit)), habit)

    def test_another_modules_body_is_not_overwritten(self):
        """The yucca is recorded a shrub and drawn as a succulent."""
        yucca = _shrub(drawn={"body": "swords"})
        shrub_habit.apply_shrub_habits([yucca])
        self.assertEqual(yucca["drawn"], {"body": "swords"})


class TheBlock(unittest.TestCase):

    def test_every_habit_it_maps_is_in_the_vocabulary(self):
        for habit, form in shrub_habit.FORM_OF.items():
            self.assertIn(habit, data_quality.BRANCHING_HABITS)
            self.assertIn(form, shrub_habit.FORMS)
        self.assertEqual(set(shrub_habit.FORM_OF.values()), set(shrub_habit.FORMS))

    def test_the_block_carries_the_recorded_numbers_in_metres(self):
        p = _shrub()
        shrub_habit.apply_shrub_habits([p])
        d = p["drawn"]
        self.assertEqual((d["body"], d["form"], d["stems"]), ("woody", "clump", 25))
        self.assertAlmostEqual(d["leaf_m"], 0.08)
        self.assertEqual((d["leaf_shape"], d["arrangement"]), ("ovate", "opposite"))
        self.assertEqual((d["mature_h"], d["mature_w"]), (3.0, 3.0))
        # What the wildlife, the vines and the cameras read off any drawn block.
        self.assertEqual((d["x"], d["y"], d["height_m"], d["canopy_m"]), (1.0, 2.0, 2.4, 2.4))
        json.dumps(d)

    def test_each_habit_has_its_form(self):
        want = {"multi_stem": "clump", "suckering": "thicket", "arching": "arching",
                "prostrate": "mat"}
        for habit, form in want.items():
            self.assertEqual(shrub_habit.form_for(_shrub(branching=habit)), form)


class TheScene(unittest.TestCase):
    """build_scene gives a read shrub its block and leaves an estimate alone."""

    def _scene(self, **over):
        from src import sprite_gallery as sg
        row = {"common_name": "Test Dogwood", "scientific_name": "Testus cornus",
               "plant_type": "shrub", "mature_height_m": "3", "spacing_m": "2",
               "bloom_period": "June–July", "deciduous_evergreen": "deciduous",
               "branching": "multi_stem", "leaf_shape": "ovate", "leaf_size_cm": 8.0,
               "leaf_arrangement": "opposite", "bark_color": "#b5402e"}
        row.update(over)
        return sg._scene_for(sg._species_specimen(row), 1, "Test Dogwood", 1)

    def test_a_read_shrub_is_drawn_from_its_numbers(self):
        p = self._scene(leaf_data_source="photo", woody_stems=25)["plants"][0]
        d = p.get("drawn")
        self.assertIsNotNone(d, "a read shrub got no drawn block")
        self.assertEqual((d["body"], d["form"], d["stems"]), ("woody", "clump", 25))
        self.assertEqual(p["woody_stems"], 25, "the scene does not carry the count")

    def test_an_estimated_shrub_is_not(self):
        self.assertIsNone(self._scene().get("plants")[0].get("drawn"))
        self.assertIsNone(self._scene(woody_stems=25).get("plants")[0].get("drawn"))

    def test_it_still_drops_its_leaves(self):
        """A body of its own must not take a deciduous shrub out of the season."""
        import datetime
        from src import sprite_gallery as sg
        row = {"common_name": "Test Dogwood", "scientific_name": "Testus cornus",
               "plant_type": "shrub", "mature_height_m": "3", "spacing_m": "2",
               "deciduous_evergreen": "deciduous", "branching": "multi_stem",
               "leaf_shape": "ovate", "leaf_size_cm": 8.0, "leaf_arrangement": "opposite",
               "leaf_data_source": "photo", "woody_stems": 25}
        scene = sg._scene_for(sg._species_specimen(row), 1, "Test Dogwood", 1,
                              when=datetime.datetime(2024, 1, 15, 12, 0))
        p = scene["plants"][0]
        self.assertEqual(p["drawn"]["body"], "woody")
        self.assertEqual((p.get("season") or {}).get("look"), "bare")

    def test_a_vine_can_still_climb_it(self):
        from src import vine_habit
        self.assertTrue(vine_habit.holds_vines(_shrub()))


class TheViewerAgrees(unittest.TestCase):

    def test_the_forms_are_the_same_words(self):
        m = re.search(r"const WOODY_FORMS = \[(.*?)\];", _js("03d-woody.js"))
        self.assertEqual(tuple(re.findall(r"'(\w+)'", m.group(1))), shrub_habit.FORMS)

    def test_every_form_has_its_numbers(self):
        """A form with no base or bias row is NaN in every coordinate."""
        src = _js("03d-woody.js")
        for table in ("_WD_BASE", "_WD_BIAS"):
            block = re.search(r"const %s = \{(.*?)\};" % table, src, re.S).group(1)
            self.assertEqual(set(re.findall(r"(\w+):", block)), set(shrub_habit.FORMS), table)

    def test_the_chunk_loads_after_the_leaf_outlines_and_before_the_layers(self):
        order = re.findall(r"'scene3d/([\w-]+\.js)'", _js("chunks.js"))
        self.assertLess(order.index("03c-leafy.js"), order.index("03d-woody.js"))
        self.assertLess(order.index("03d-woody.js"), order.index("04-quality.js"))

    def test_the_shrub_layer_moved_whole(self):
        """04-quality.js was at its ceiling, so the layer went to the new
        chunk. Defined twice, the later definition would silently win."""
        quality, woody = _js("04-quality.js"), _js("03d-woody.js")
        for name in ("function buildShrubLayer(", "function getShrubArch(",
                     "const SHRUB_CACHE", "const SHRUB_VARIANTS"):
            self.assertNotIn(name, quality)
            self.assertEqual(woody.count(name), 1, name)
        self.assertIn("buildShrubLayer(byKind.shrub", quality)

    def test_a_shrub_with_its_own_body_is_not_sent_to_the_pond(self):
        """buildPlants files any body it does not name under the pond layer."""
        quality = _js("04-quality.js")
        m = re.search(r"if \(pb && \[(.*?)\]\.indexOf\(pb\) < 0\) \{ byKind\.pond", quality)
        self.assertIsNotNone(m, "the routing line changed shape")
        self.assertIn("'woody'", m.group(1))
        self.assertIn("'leafy'", m.group(1))

    def test_the_layer_asks_for_the_shrubs_own_body_first(self):
        woody = _js("03d-woody.js")
        self.assertIn("const own = woodyKeyFor(p);", woody)
        self.assertIn("(own && buildWoodyGeo(morph, v)) ||", woody)

    def test_stylised_keeps_its_faceted_forms(self):
        """Detail level 0 is a style: it draws none of these bodies."""
        body = _js("03d-woody.js")
        key = body[body.index("function woodyKeyFor"):body.index("function _wdGeometry")]
        self.assertIn("STYLISED ||", key)

    def test_the_leaves_wear_their_outline_and_cast_its_shadow(self):
        woody, surface = _js("03d-woody.js"), _js("01b-surface.js")
        self.assertIn("surfaceMaterial(MAT_PRESETS.shrubLeaf, surf, true, cut)", woody)
        self.assertIn("foliage.customDepthMaterial = cut.depth", woody)
        self.assertIn("mat.alphaMap = opts.cut.map", surface)
        # The material cache must tell a cut-out from a plain leaf.
        self.assertIn("(cut ? '|' + cut.key : '')", surface)

    def test_the_mask_keeps_its_cover_as_it_shrinks(self):
        """With mipmaps the machine makes, a leaf's pixels average under the
        cut and the shrub goes bare with distance."""
        woody = _js("03d-woody.js")
        self.assertIn("map.mipmaps = mips; map.generateMipmaps = false;", woody)
        self.assertIn("function _wdMip(", woody)

    def test_the_flowers_go_where_the_shoots_end(self):
        self.assertIn("geos[0].userData.crown", _js("15b-anchors.js"))
        woody = _js("03d-woody.js")
        self.assertIn("foliageGeo.userData.crown =", woody)
        self.assertIn("stemGeo.userData.crown =", woody)

    def test_what_is_estimated_is_named_as_an_estimate(self):
        head = _js("03d-woody.js")[:3200]
        for word in ("WOODY_PIPE", "WOODY_PER_SHOOT", "WOODY_GAIN_MAX", "estimate"):
            self.assertIn(word, head)

    def test_a_leaf_is_never_drawn_more_than_three_times_its_size(self):
        m = re.search(r"const WOODY_GAIN_MAX = ([\d.]+);", _js("03d-woody.js"))
        self.assertLessEqual(float(m.group(1)), 3.0)

    def test_no_month_is_compared_in_the_chunk(self):
        self.assertIsNone(re.search(r"month\s*[<>=!]=?\s*\d", _js("03d-woody.js")))


class TheCatalogue(unittest.TestCase):
    """Every shrub that says it was read can be drawn from what it carries."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(_ROOT, "data", "plants_master.json"), encoding="utf-8") as fh:
            cls.rows = json.load(fh)
        cls.shrubs = [r for r in cls.rows if r.get("plant_type") in shrub_habit.TYPES]

    def test_a_read_shrub_has_what_the_body_needs(self):
        for r in self.shrubs:
            if not herb_habit.is_read(r):
                continue
            for field in ("branching", "woody_stems", "leaf_shape", "leaf_size_cm",
                          "leaf_arrangement", "leaf_data_citation"):
                self.assertTrue(r.get(field), f"{r['scientific_name']}: read, no {field}")

    def test_a_stem_count_is_a_reading(self):
        """A count on a row nobody read would be an estimate drawn as one."""
        for r in self.rows:
            if r.get("woody_stems"):
                self.assertTrue(herb_habit.is_read(r),
                                f"{r['scientific_name']}: a stem count with no reading")
                self.assertIn(r.get("plant_type"), shrub_habit.TYPES, r["scientific_name"])

    def test_every_native_shrub_is_drawn_from_its_own_numbers(self):
        names = native_here.native_names()
        native = [r for r in self.shrubs if r["scientific_name"] in names]
        self.assertGreaterEqual(len(native), 30)
        left = [r["common_name"] for r in native if not shrub_habit.form_for(r)]
        self.assertEqual(left, [], "native shrubs still on the shared baked figure")

    def test_a_leaf_is_a_leaf_of_a_shrub(self):
        """A unit slip (mm for cm): no shrub leaf here is under 1 cm or over 20."""
        for r in self.shrubs:
            if herb_habit.is_read(r):
                self.assertTrue(1.0 <= float(r["leaf_size_cm"]) <= 20.0, r["scientific_name"])


class TheReadingTool(unittest.TestCase):

    def setUp(self):
        import leaf_readings
        self.lr = leaf_readings
        self.rows = {"Testus cornus": {"scientific_name": "Testus cornus",
                                       "common_name": "Test Dogwood", "plant_type": "shrub",
                                       "branching": "multi_stem", "leaf_shape": "ovate",
                                       "leaf_size_cm": 9.0, "leaf_arrangement": "opposite",
                                       "mature_height_m": "3"}}
        self.review = {"Testus cornus": {"refs": {"habit": ["111"], "winter": ["333"],
                                                  "leaf": ["222"]}}}

    def _bad(self, reading):
        return self.lr.problems({"Testus cornus": reading}, self.rows, self.review)

    def test_a_shrub_needs_its_stems_counted(self):
        self.assertTrue(self._bad({"leaf_size_cm": 8}), "read with no stem count")
        self.assertEqual(self._bad({"leaf_size_cm": 8, "woody_stems": 25}), [])

    def test_it_refuses_a_habit_or_a_count_the_gate_would(self):
        self.assertTrue(self._bad({"woody_stems": 25, "branching": "bushy"}))
        self.assertTrue(self._bad({"woody_stems": 400}))
        self.assertTrue(self._bad({"woody_stems": 2.5}))

    def test_the_winter_photograph_is_cited(self):
        """It is the one the stems were counted on."""
        rows = [dict(self.rows["Testus cornus"])]
        self.lr.apply({"Testus cornus": {"woody_stems": 25}}, rows, self.review)
        self.assertEqual(rows[0]["woody_stems"], 25)
        self.assertEqual(rows[0]["leaf_data_source"], "photo")
        self.assertIn("333", rows[0]["leaf_data_citation"])

    def test_the_groups_name_real_modules(self):
        self.assertEqual(self.lr.GROUPS["shrubs"]["habit"], shrub_habit)
        self.assertEqual(self.lr.GROUPS["herbs"]["habit"], herb_habit)
        self.assertIn(("winter", 1), self.lr.GROUPS["shrubs"]["kinds"])


class TheDataGate(unittest.TestCase):

    def _errors(self, **over):
        with open(os.path.join(_ROOT, "data", "plants_master.json"), encoding="utf-8") as fh:
            row = next(r for r in json.load(fh) if r["scientific_name"] == "Cornus sericea")
        errors, _warnings = data_quality.validate_plant(
            dict(row, **over), source_label="test.json", idx=0,
            use_keys=data_quality._load_use_keys(),
            ecoregion_keys=data_quality._load_ecoregion_keys())
        return [e for e in errors if "woody_stems" in e]

    def test_a_whole_number_in_range_passes(self):
        self.assertEqual(self._errors(woody_stems=25), [])
        self.assertEqual(self._errors(woody_stems=None), [])

    def test_anything_else_is_refused(self):
        for bad in (0, 61, 2.5, "many", True):
            self.assertTrue(self._errors(woody_stems=bad), repr(bad))


if __name__ == "__main__":
    unittest.main()
