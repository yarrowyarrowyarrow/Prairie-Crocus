"""
tests/test_tree_habit.py — a tree is drawn from its own crown, and a vine
with its own leaves, once somebody has read them (V3.50, F268).

What can go wrong quietly, each with a test here:

  * a tree whose crown is the seeder's estimate is drawn in a body of its
    own, stating a guess as a reading (P9);
  * Python and the viewer disagree about a crown outline or limb habit, so a
    tree the scene calls conical is drawn with no outline;
  * the new body is filed under the pond layer, which takes every body the
    plant list does not name, and nothing is drawn;
  * a needle tree is given a broad leaf's spray, or a willow's catkins hang;
  * a catkin, recorded flower_form 'none' so the pollinator logic reads it as
    wind-pollinated, is changed to reach the picture.
"""

import json
import os
import re
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from src import data_quality, herb_habit, native_here, tree_habit  # noqa: E402

_JS = os.path.join(_ROOT, "html", "scene3d")


def _js(name: str) -> str:
    with open(os.path.join(_JS, name), encoding="utf-8") as fh:
        return fh.read()


def _tree(**over) -> dict:
    p = {"plant_type": "tree", "scientific_name": "Populus tremuloides",
         "woody_stems": 1, "crown_shape": "oval", "crown_clear": 0.55,
         "limb_habit": "ascending", "leaf_shape": "orbicular", "leaf_size_cm": 5.0,
         "leaf_arrangement": "alternate", "leaf_data_source": "photo",
         "x": 1.0, "y": 2.0, "height_m": 16.0, "canopy_m": 6.0,
         "mature_height_m": 20.0, "mature_canopy_m": 7.5}
    p.update(over)
    return p


class TheGate(unittest.TestCase):

    def test_an_estimate_keeps_the_baked_crown(self):
        for source in ("", "estimated", None):
            self.assertIsNone(tree_habit.form_for(_tree(leaf_data_source=source)))

    def test_a_reading_of_any_kind_counts(self):
        for source in herb_habit.READ:
            self.assertEqual(tree_habit.form_for(_tree(leaf_data_source=source)), "oval")

    def test_every_crown_number_is_needed(self):
        for field, empty in (("crown_shape", ""), ("limb_habit", ""), ("crown_clear", None),
                             ("woody_stems", None), ("leaf_shape", ""), ("leaf_size_cm", 0)):
            self.assertIsNone(tree_habit.form_for(_tree(**{field: empty})), field)

    def test_a_bare_bole_of_nothing_is_a_reading(self):
        """A spruce has branches to the ground: 0 is read, not missing."""
        self.assertEqual(tree_habit.form_for(_tree(crown_clear=0.0)), "oval")

    def test_only_trees_get_a_crown_and_a_read_vine_says_so(self):
        self.assertIsNone(tree_habit.form_for(_tree(plant_type="shrub")))
        self.assertEqual(tree_habit.form_for(_tree(plant_type="vine")), "vine")
        vine = _tree(plant_type="vine", drawn={"habit": "climbing"})
        tree_habit.apply_tree_habits([vine])
        self.assertEqual(vine["drawn"], {"habit": "climbing"})


class TheBlock(unittest.TestCase):

    def test_the_block_carries_the_crown(self):
        p = _tree()
        tree_habit.apply_tree_habits([p])
        d = p["drawn"]
        self.assertEqual((d["body"], d["form"], d["trunks"], d["clear"], d["limbs"]),
                         ("crown", "oval", 1, 0.55, "ascending"))
        self.assertEqual((d["mature_h"], d["mature_w"]), (20.0, 7.5))
        self.assertEqual((d["x"], d["y"], d["height_m"], d["canopy_m"]), (1.0, 2.0, 16.0, 6.0))
        self.assertAlmostEqual(d["leaf_m"], 0.05)
        json.dumps(d)

    def test_how_needles_are_carried(self):
        self.assertEqual(tree_habit.spray_for(_tree()), "leaf")
        self.assertEqual(tree_habit.spray_for(_tree(leaf_shape="needle", leaf_size_cm=1.8)), "frond")
        self.assertEqual(tree_habit.spray_for(_tree(leaf_shape="needle", leaf_size_cm=3.0,
                                                    leaf_arrangement="fascicled")), "tuft")
        self.assertEqual(tree_habit.spray_for(_tree(leaf_shape="needle", leaf_size_cm=2.5,
                                                    leaf_arrangement="fascicled")), "rosette")

    def test_which_catkins_hang(self):
        for sci in ("Populus balsamifera", "Betula occidentalis", "Alnus incana"):
            self.assertTrue(tree_habit.drawn_block(_tree(scientific_name=sci), "oval")["catkins_hang"])
        self.assertFalse(tree_habit.drawn_block(_tree(scientific_name="Salix bebbiana"),
                                                "rounded")["catkins_hang"])

    def test_the_vocabularies_are_the_gates(self):
        self.assertEqual(tree_habit.SHAPES, data_quality.CROWN_SHAPES)
        self.assertEqual(tree_habit.LIMBS, data_quality.LIMB_HABITS)


class TheScene(unittest.TestCase):

    def test_a_read_native_tree_is_drawn_from_its_crown(self):
        from src import sprite_gallery as sg
        with open(os.path.join(_ROOT, "data", "plants_master.json"), encoding="utf-8") as fh:
            row = next(r for r in json.load(fh) if r["scientific_name"] == "Picea glauca")
        p = sg._scene_for(sg._species_specimen(row), 1, row["common_name"], 1)["plants"][0]
        self.assertEqual((p["drawn"]["body"], p["drawn"]["form"], p["drawn"]["spray"]),
                         ("crown", "conical", "frond"))
        self.assertEqual(p["crown_shape"], "conical")


class TheViewerAgrees(unittest.TestCase):

    def test_the_words_are_the_same(self):
        src = _js("03e-crowns.js")
        for const, words in (("CROWN_SHAPES", tree_habit.SHAPES), ("LIMB_HABITS", tree_habit.LIMBS)):
            m = re.search(r"const %s = \[(.*?)\];" % const, src)
            self.assertEqual(tuple(re.findall(r"'(\w+)'", m.group(1))), words, const)
        for table in ("LIMB_RISE", "LIMB_BIAS", "LIMB_DROOP"):
            block = re.search(r"const %s = \{(.*?)\};" % table, src, re.S).group(1)
            self.assertEqual(set(re.findall(r"(\w+):", block)), set(tree_habit.LIMBS), table)
        unit = re.search(r"const SPRAY_UNIT = \{(.*?)\};", src).group(1)
        self.assertEqual(set(re.findall(r"(\w+):", unit)) | {"leaf"}, set(tree_habit.SPRAYS))

    def test_the_crown_body_is_not_sent_to_the_pond(self):
        m = re.search(r"if \(pb && \[(.*?)\]\.indexOf\(pb\) < 0\) \{ byKind\.pond", _js("04-quality.js"))
        self.assertIn("'crown'", m.group(1))

    def test_the_tree_layer_asks_for_its_own_crown_first(self):
        quality = _js("04-quality.js")
        self.assertIn("crownKeyFor(p)", quality)
        self.assertIn("own ? getCrownArch(items[0], sub)", quality)
        self.assertIn("foliage.customDepthMaterial = cut.depth", quality)

    def test_the_chunks_load_in_order(self):
        order = re.findall(r"'scene3d/([\w-]+\.js)'", _js("chunks.js"))
        self.assertLess(order.index("03d-woody.js"), order.index("03e-crowns.js"))
        self.assertLess(order.index("03e-crowns.js"), order.index("04-quality.js"))
        self.assertLess(order.index("22-vines.js"), order.index("22b-vineleaves.js"))

    def test_stylised_keeps_its_faceted_trees(self):
        crown = _js("03e-crowns.js")
        self.assertIn("STYLISED ||", crown[crown.index("function crownKeyFor"):])
        self.assertIn("!STYLISED &&", _js("22b-vineleaves.js"))

    def test_a_catkin_reaches_the_picture_without_its_flower_form_changing(self):
        """flower_form 'none' is what the pollinator logic reads for a
        wind-pollinated tree; the flower layer lets a card body through on its
        colour instead."""
        flowers = _js("05-flowers.js")
        self.assertIn("(!byForm[form] && !carries)", flowers)
        with open(os.path.join(_ROOT, "data", "plants_master.json"), encoding="utf-8") as fh:
            rows = {r["scientific_name"]: r for r in json.load(fh)}
        self.assertEqual(rows["Populus tremuloides"]["flower_form"], "none")
        self.assertEqual(rows["Populus tremuloides"]["flower_arch"], "spike")

    def test_the_estimates_are_named(self):
        head = _js("03e-crowns.js")[:3200]
        for word in ("TRUNK_PIPE", "limbCount", "LIMB_RISE", "SPRAY_UNIT", "estimate"):
            self.assertIn(word, head)
        self.assertIn("VINE_SHOOT_GAP", _js("22b-vineleaves.js")[:1800])
        for name in ("03e-crowns.js", "22b-vineleaves.js"):
            self.assertIsNone(re.search(r"month\s*[<>=!]=?\s*\d", _js(name)), name)


class TheCatalogue(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(_ROOT, "data", "plants_master.json"), encoding="utf-8") as fh:
            cls.rows = json.load(fh)
        cls.names = native_here.native_names()

    def test_every_native_tree_and_vine_is_read(self):
        native = [r for r in self.rows if r["scientific_name"] in self.names
                  and r["plant_type"] in ("tree", "vine")]
        self.assertGreaterEqual(len(native), 15)
        self.assertEqual([r["common_name"] for r in native if not tree_habit.form_for(r)], [])

    def test_crown_numbers_are_a_reading_of_a_tree_or_a_shrub(self):
        # A tree's crown since V3.50; a shrub's outline since V3.63, in its own
        # words. Either way it is read off photographs, never a guess, and a
        # limb habit is a tree's alone.
        from src import data_quality
        for r in self.rows:
            if r.get("crown_shape") or r.get("limb_habit") or r.get("crown_clear") is not None:
                self.assertIn(r["plant_type"], ("tree", "shrub"), r["scientific_name"])
                self.assertTrue(herb_habit.is_read(r), r["scientific_name"])
                words = (data_quality.SHRUB_CROWN_SHAPES if r["plant_type"] == "shrub"
                         else data_quality.CROWN_SHAPES)
                self.assertIn(r.get("crown_shape"), words, r["scientific_name"])
                if r["plant_type"] == "shrub":
                    self.assertFalse(r.get("limb_habit"), r["scientific_name"])


class TheReadingTool(unittest.TestCase):

    def setUp(self):
        import leaf_readings
        self.lr = leaf_readings
        self.rows = {"Testus arbor": {"scientific_name": "Testus arbor", "common_name": "Test Tree",
                                      "plant_type": "tree", "leaf_shape": "ovate",
                                      "leaf_size_cm": 8.0, "leaf_arrangement": "alternate"}}
        self.review = {"Testus arbor": {"refs": {"habit": ["111"], "winter": ["333"]}}}

    def _bad(self, reading):
        return self.lr.problems({"Testus arbor": reading}, self.rows, self.review)

    def test_a_tree_needs_its_crown(self):
        self.assertTrue(self._bad({"woody_stems": 1}))
        self.assertEqual(self._bad({"woody_stems": 1, "crown_shape": "oval", "crown_clear": 0.4,
                                    "limb_habit": "ascending"}), [])

    def test_it_refuses_a_crown_the_gate_would(self):
        full = {"woody_stems": 1, "crown_shape": "oval", "crown_clear": 0.4, "limb_habit": "ascending"}
        self.assertTrue(self._bad(dict(full, crown_shape="lollipop")))
        self.assertTrue(self._bad(dict(full, limb_habit="weeping")))
        self.assertTrue(self._bad(dict(full, crown_clear=0.95)))


class TheDataGate(unittest.TestCase):

    def _errors(self, **over):
        with open(os.path.join(_ROOT, "data", "plants_master.json"), encoding="utf-8") as fh:
            row = next(r for r in json.load(fh) if r["scientific_name"] == "Picea glauca")
        errors, _w = data_quality.validate_plant(
            dict(row, **over), source_label="test.json", idx=0,
            use_keys=data_quality._load_use_keys(),
            ecoregion_keys=data_quality._load_ecoregion_keys())
        return [e for e in errors if "crown" in e or "limb" in e]

    def test_the_read_row_passes(self):
        self.assertEqual(self._errors(), [])

    def test_anything_else_is_refused(self):
        for over in ({"crown_shape": "lollipop"}, {"limb_habit": "up"}, {"crown_clear": 1.2},
                     {"crown_clear": "half"}):
            self.assertTrue(self._errors(**over), over)


if __name__ == "__main__":
    unittest.main()
