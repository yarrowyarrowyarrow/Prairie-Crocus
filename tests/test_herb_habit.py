"""
tests/test_herb_habit.py — a wildflower is drawn from its own numbers once
somebody has read them, and from the shared figure until then (V3.48, F268).

Three things can go wrong quietly, and each has a test here:

  * a plant whose numbers are the seeder's estimate is drawn at life size from
    them, stating a guess as a measurement (P9);
  * the Python rule and the viewer chunk disagree about a form or about how
    many flower clusters a stem carries, so flowers stack on one tip or tips
    stand bare;
  * a reading is written without saying where it came from, or with a word the
    data gate will refuse a month later.
"""

import json
import os
import re
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from src import data_quality, herb_habit  # noqa: E402

_JS = os.path.join(_ROOT, "html", "scene3d")


def _js(name: str) -> str:
    with open(os.path.join(_JS, name), encoding="utf-8") as fh:
        return fh.read()


def _plant(**over) -> dict:
    p = {"plant_type": "wildflower", "growth_form": "erect",
         "leaf_shape": "lanceolate", "leaf_size_cm": 8.0,
         "leaf_arrangement": "alternate", "stem_branching": "branched_above",
         "basal_rosette": 0, "flowering_stems": 24, "stem_leaf_nodes": 20,
         "leaf_data_source": "photo", "x": 1.0, "y": 2.0,
         "height_m": 0.8, "canopy_m": 0.4,
         "mature_height_m": 1.0, "mature_canopy_m": 0.45}
    p.update(over)
    return p


class TheGate(unittest.TestCase):
    """Only a plant whose leaves were read is drawn from them."""

    def test_an_estimate_keeps_the_baked_figure(self):
        for source in ("", "estimated", None):
            self.assertIsNone(herb_habit.form_for(_plant(leaf_data_source=source)),
                              f"leaf_data_source={source!r} was drawn as read")

    def test_a_reading_of_any_kind_counts(self):
        for source in herb_habit.READ:
            self.assertEqual(herb_habit.form_for(_plant(leaf_data_source=source)), "stems")
        self.assertEqual(set(herb_habit.READ), {"photo", "flora", "measured"})

    def test_only_wildflowers_herbs_and_groundcovers(self):
        for kind in ("wildflower", "herb", "groundcover"):
            self.assertIsNotNone(herb_habit.form_for(_plant(plant_type=kind)))
        for kind in ("grass", "sedge", "rush", "shrub", "tree", "vine"):
            self.assertIsNone(herb_habit.form_for(_plant(plant_type=kind)), kind)

    def test_a_fern_and_a_herb_like_water_plant_are_drawn_too(self):
        """V3.67b: an ostrich fern's fronds, and a water parsnip's leafy stems;
        a floating, submerged or emergent water plant keeps the pond's body."""
        self.assertEqual(herb_habit.form_for(_plant(plant_type="fern", growth_form="fern")),
                         "fronds")
        self.assertEqual(herb_habit.form_for(_plant(plant_type="aquatic")), "stems")
        for habit in ("emergent", "floating", "submerged"):
            self.assertIsNone(herb_habit.form_for(_plant(plant_type="aquatic",
                                                         growth_form=habit)), habit)

    def test_a_one_leaf_shoot_of_a_divided_leaf_is_an_umbrella(self):
        """V3.67b: wild sarsaparilla's shoots are each one ternate leaf."""
        p = _plant(growth_form="colony", stem_leaf_nodes=1, leaf_shape="ternate")
        self.assertEqual(herb_habit.form_for(p), "umbrella")
        p = _plant(growth_form="colony", stem_leaf_nodes=1, leaf_shape="ovate")
        self.assertEqual(herb_habit.form_for(p), "colony")

    def test_a_woody_mat_is_the_shrub_bodys(self):
        """V3.67b: creeping juniper, its stems counted, is drawn as a shrub."""
        p = _plant(plant_type="groundcover", growth_form="mat", branching="prostrate",
                   woody_stems=14)
        self.assertIsNone(herb_habit.form_for(p))

    def test_no_leaf_recorded_draws_nothing_new(self):
        self.assertIsNone(herb_habit.form_for(_plant(leaf_shape="")))
        self.assertIsNone(herb_habit.form_for(_plant(leaf_size_cm=None)))

    def test_a_habit_these_forms_do_not_draw_is_left_alone(self):
        # "fern" is drawn since V3.67b (the fronds form), on a fern.
        for habit in ("tussock", "emergent", "floating", "jointed", "pads",
                      "globose", "succulent", "vining", ""):
            self.assertIsNone(herb_habit.form_for(_plant(growth_form=habit)), habit)

    def test_another_modules_body_is_not_overwritten(self):
        vine = _plant(drawn={"habit": "climbing"})
        herb_habit.apply_herb_habits([vine])
        self.assertEqual(vine["drawn"], {"habit": "climbing"})


class TheBlock(unittest.TestCase):

    def test_every_recorded_habit_it_maps_is_in_the_vocabulary(self):
        for habit, form in herb_habit.FORM_OF.items():
            self.assertIn(habit, data_quality.GROWTH_FORMS)
            self.assertIn(form, herb_habit.FORMS)

    def test_the_block_carries_the_recorded_numbers_in_metres(self):
        p = _plant()
        herb_habit.apply_herb_habits([p])
        d = p["drawn"]
        self.assertEqual(d["body"], "leafy")
        self.assertEqual(d["form"], "stems")
        self.assertAlmostEqual(d["leaf_m"], 0.08)
        self.assertEqual((d["leaf_shape"], d["arrangement"]), ("lanceolate", "alternate"))
        self.assertEqual(d["nodes"], 20)
        self.assertEqual((d["mature_h"], d["mature_w"]), (1.0, 0.45))
        # What the wildlife and the cameras read off any drawn block.
        for key in ("x", "y", "height_m", "canopy_m"):
            self.assertIn(key, d)
        self.assertEqual((d["height_m"], d["canopy_m"]), (0.8, 0.4))
        json.dumps(d)

    def test_stems_are_the_clusters_over_what_a_stem_carries(self):
        self.assertEqual(herb_habit.stems_for(_plant(stem_branching="unbranched",
                                                     flowering_stems=6), "stems"), 6)
        self.assertEqual(herb_habit.stems_for(_plant(stem_branching="branched_above",
                                                     flowering_stems=24), "stems"), 6)
        self.assertEqual(herb_habit.stems_for(_plant(stem_branching="branched_throughout",
                                                     flowering_stems=40), "stems"), 5)
        # A rosette's stalks do not fork, whatever the branching says.
        self.assertEqual(herb_habit.stems_for(_plant(flowering_stems=8), "rosette"), 8)
        # Nothing recorded: a stated default, never zero stems.
        self.assertGreaterEqual(herb_habit.stems_for(_plant(flowering_stems=None), "stems"), 1)

    def test_leaves_at_the_ground(self):
        self.assertFalse(herb_habit.drawn_block(_plant(), "stems")["basal"])
        self.assertTrue(herb_habit.drawn_block(_plant(basal_rosette=1), "stems")["basal"])
        self.assertTrue(herb_habit.drawn_block(_plant(leaf_arrangement="basal"), "mat")["basal"])
        self.assertTrue(herb_habit.drawn_block(_plant(growth_form="rosette"), "rosette")["basal"])

    def test_no_count_leaves_the_spacing_to_the_viewer(self):
        self.assertEqual(herb_habit.drawn_block(_plant(stem_leaf_nodes=None), "stems")["nodes"], 0)


class TheScene(unittest.TestCase):
    """build_scene gives a read plant its block and leaves an estimate alone."""

    def _scene(self, **over):
        from src import sprite_gallery as sg
        row = {"common_name": "Test Aster", "scientific_name": "Testus asterus",
               "plant_type": "wildflower", "mature_height_m": "1", "spacing_m": "0.3",
               "bloom_period": "July–August", "deciduous_evergreen": "herbaceous",
               "growth_form": "erect", "leaf_shape": "lanceolate", "leaf_size_cm": 8.0,
               "leaf_arrangement": "alternate", "stem_branching": "branched_above",
               "basal_rosette": 0, "flowering_stems": 24, "flower_form": "daisy"}
        row.update(over)
        return sg._scene_for(sg._species_specimen(row), 1, "Test Aster", 1)

    def test_a_read_plant_is_drawn_from_its_numbers(self):
        scene = self._scene(leaf_data_source="photo", stem_leaf_nodes=18)
        d = scene["plants"][0].get("drawn")
        self.assertIsNotNone(d, "a read wildflower got no drawn block")
        self.assertEqual((d["body"], d["form"], d["nodes"]), ("leafy", "stems", 18))
        self.assertEqual(d["stems"], 6)

    def test_an_estimated_plant_is_not(self):
        self.assertIsNone(self._scene().get("plants")[0].get("drawn"))


class TheViewerAgrees(unittest.TestCase):

    def test_the_forms_are_the_same_words(self):
        m = re.search(r"const LEAFY_FORMS = \[(.*?)\];", _js("03c-leafy.js"))
        self.assertEqual(tuple(re.findall(r"'(\w+)'", m.group(1))), herb_habit.FORMS)

    def test_a_stem_carries_as_many_clusters_as_python_divides_by(self):
        """One more than its forks: the stem's own tip. If the two disagree,
        flowers stack on one tip or tips stand with nothing on them."""
        src = _js("03c-leafy.js")
        block = re.search(r"const FORKS = \{(.*?)\};", src, re.S).group(1)
        forks = {k: len(re.findall(r"[\d.]+", v))
                 for k, v in re.findall(r"(\w+): \[(.*?)\]", block, re.S)}
        self.assertEqual({k: n + 1 for k, n in forks.items()},
                         {k: v for k, v in herb_habit.TIPS_PER_STEM.items() if v > 1})
        self.assertEqual(herb_habit.TIPS_PER_STEM["unbranched"], 1)

    def test_the_chunk_loads_after_the_leaf_outlines_and_before_the_layers(self):
        order = re.findall(r"'scene3d/([\w-]+\.js)'", _js("chunks.js"))
        self.assertLess(order.index("03-herbs.js"), order.index("03c-leafy.js"))
        self.assertLess(order.index("03c-leafy.js"), order.index("04-quality.js"))

    def test_the_herb_layer_asks_for_the_plants_own_body_first(self):
        quality = _js("04-quality.js")
        self.assertIn("leafyKeyFor(p)", quality)
        self.assertIn("formName === 'leafy' && buildLeafyGeo(morph, v)", quality)
        # A groundcover with its own body is placed by the herb layer, not as
        # a capped mat and not as a pond plant.
        self.assertRegex(quality, r"if \(pb && \[[^\]]*'leafy'[^\]]*\]\.indexOf\(pb\) < 0\)")
        self.assertIn("pb === 'herb' || pb === 'leafy' ? 'herb'", quality)

    def test_stylised_keeps_its_faceted_forms(self):
        """Detail level 0 is a style: it draws none of these bodies."""
        body = _js("03c-leafy.js")
        key = body[body.index("function leafyKeyFor"):body.index("function buildLeafyGeo")]
        self.assertIn("STYLISED ||", key)

    def test_the_flowers_go_on_the_tips_the_body_names(self):
        self.assertIn("geo.userData.tips", _js("15b-anchors.js"))
        self.assertIn("g.userData.tips =", _js("03c-leafy.js"))

    def test_every_leaf_outline_in_the_vocabulary_has_a_width(self):
        """A leaf with no width ratio is drawn at the default 0.3, silently."""
        m = re.search(r"const LEAF_WIDTH_RATIO = \{(.*?)\};", _js("03-herbs.js"), re.S)
        have = set(re.findall(r"(\w+):", m.group(1)))
        self.assertEqual(data_quality.LEAF_SHAPES - have, set())

    def test_what_is_estimated_is_named_as_an_estimate(self):
        head = _js("03c-leafy.js")[:2500]
        for word in ("INTERNODE", "WHORL", "estimate"):
            self.assertIn(word, head)

    def test_no_month_is_compared_in_the_chunk(self):
        self.assertIsNone(re.search(r"month\s*[<>=!]=?\s*\d", _js("03c-leafy.js")))


class TheVocabulary(unittest.TestCase):

    def test_the_new_words(self):
        self.assertIn("palmately_lobed", data_quality.LEAF_SHAPES)
        self.assertIn("ternate", data_quality.LEAF_SHAPES)
        self.assertIn("colony", data_quality.GROWTH_FORMS)

    def test_the_baked_models_still_resolve_them(self):
        """A shrub or an unread plant carrying a new outline is drawn by a
        baked model, which knows four blade classes."""
        sys.path.insert(0, os.path.join(_ROOT, "scripts", "blender"))
        from assetlib import conventions as C
        self.assertEqual(C.blade_class("palmately_lobed"), "cut")
        self.assertEqual(C.blade_class("ternate"), "compound")
        plants = _js("02-plants.js")
        self.assertIn("'palmately_lobed'", plants)
        self.assertIn("'ternate'", plants)


class TheCatalogue(unittest.TestCase):
    """Every row that says it was read can be drawn from what it carries."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(_ROOT, "data", "plants_master.json"), encoding="utf-8") as fh:
            cls.rows = json.load(fh)

    def test_a_read_row_names_its_photographs(self):
        for r in self.rows:
            if herb_habit.is_read(r):
                self.assertTrue((r.get("leaf_data_citation") or "").strip(),
                                f"{r['scientific_name']}: read, with no citation")

    def test_a_read_wildflower_has_what_the_body_needs(self):
        for r in self.rows:
            if not herb_habit.is_read(r) or r.get("plant_type") not in herb_habit.TYPES:
                continue
            for field in ("growth_form", "leaf_shape", "leaf_size_cm", "leaf_arrangement"):
                self.assertTrue(r.get(field), f"{r['scientific_name']}: read, no {field}")

    def test_a_leaf_is_not_longer_than_the_plant_can_carry(self):
        """A unit slip (mm for cm) or a leaf read off the wrong plant: no
        stem leaf is longer than the plant is tall, and a leaf at the ground
        is at most three times it (a strawberry's is)."""
        for r in self.rows:
            if not herb_habit.is_read(r) or r.get("plant_type") not in herb_habit.TYPES:
                continue
            h = float(r.get("mature_height_m") or 0) * 100
            leaf = float(r.get("leaf_size_cm") or 0)
            self.assertLessEqual(leaf, 3.0 * h, f"{r['scientific_name']}: leaf {leaf} cm "
                                                f"on a {h:g} cm plant")


class TheReadingTool(unittest.TestCase):

    def setUp(self):
        import leaf_readings
        self.lr = leaf_readings
        self.rows = {"Testus asterus": {"scientific_name": "Testus asterus",
                                        "common_name": "Test Aster",
                                        "growth_form": "erect", "leaf_shape": "ovate",
                                        "leaf_size_cm": 8.0, "leaf_arrangement": "alternate",
                                        "mature_height_m": "1"}}
        self.review = {"Testus asterus": {"refs": {"habit": ["111"], "leaf": ["222", "111"]}}}

    def _bad(self, reading):
        return self.lr.problems({"Testus asterus": reading}, self.rows, self.review)

    def test_a_good_reading_passes(self):
        self.assertEqual(self._bad({"leaf_shape": "lanceolate", "leaf_size_cm": 6,
                                    "stem_leaf_nodes": 20, "basal_rosette": 1}), [])

    def test_it_refuses_what_the_gate_would(self):
        self.assertTrue(self._bad({"leaf_shape": "maple"}))
        self.assertTrue(self._bad({"growth_form": "bushy"}))
        self.assertTrue(self._bad({"leaf_size_cm": 800}))
        self.assertTrue(self._bad({"stem_leaf_nodes": 2.5}))
        self.assertTrue(self._bad({"basal_rosette": 2}))
        self.assertTrue(self.lr.problems({"Nobody here": {"leaf_size_cm": 3}},
                                         self.rows, self.review))

    def test_it_does_not_take_a_colour_or_a_note(self):
        """Flower colours are the owner's answers (V3.34); free text is where a
        plant's uses would come in (P12)."""
        for field in ("flower_color", "flower_colours", "notes", "permaculture_uses",
                      "edible_parts"):
            self.assertTrue(self._bad({field: "x"}), field)
            self.assertNotIn(field, self.lr.FIELDS)

    def test_no_photographs_no_reading(self):
        self.assertTrue(self.lr.problems({"Testus asterus": {"leaf_size_cm": 6}},
                                         self.rows, {}))

    def test_a_reading_says_where_it_came_from(self):
        rows = [dict(self.rows["Testus asterus"])]
        n = self.lr.apply({"Testus asterus": {"leaf_size_cm": 6, "mature_height_m": 0.8,
                                              "flowering_stems": 12}}, rows, self.review)
        self.assertEqual(n, 1)
        row = rows[0]
        self.assertEqual(row["leaf_data_source"], "photo")
        self.assertIn("111", row["leaf_data_citation"])
        self.assertIn("222", row["leaf_data_citation"])
        self.assertEqual(row["leaf_size_cm"], 6.0)
        self.assertEqual(row["mature_height_m"], "0.8", "a height is kept as text")
        # Stems alone are not a reading of the flower.
        self.assertNotIn("flower_data_source", row)

    def test_flower_numbers_mark_the_flower_pair_too(self):
        rows = [dict(self.rows["Testus asterus"])]
        self.lr.apply({"Testus asterus": {"flower_diameter_cm": 3}}, rows, self.review)
        self.assertEqual(rows[0]["flower_data_source"], "photo")
        self.assertTrue(rows[0]["flower_data_citation"])


if __name__ == "__main__":
    unittest.main()
