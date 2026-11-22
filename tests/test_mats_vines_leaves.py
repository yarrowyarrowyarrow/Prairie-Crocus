"""
tests/test_mats_vines_leaves.py — mats, vines, big compound leaves and flower
clusters at their read size (V3.65, F268).

What can go wrong quietly, each with a test here:

  * a dense wildflower's cluster goes back to a size guessed from its flower
    count (tall meadow rue's plume drawn 5 cm where it is 30);
  * a cluster's size read alone is written as if the plant's habit or its
    flowers' numbers had been read (P9);
  * a mat is drawn as a solid plate again;
  * a big ternate leaf is one flat plate of nine leaflets again;
  * a shrub's opposite leaves are painted as two even rows, which read as a
    pinnate leaf, so a dogwood cannot be told from the peavine on it;
  * a herbaceous vine is put on the 3 m dogwood in the review's stage again.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from src import herb_habit  # noqa: E402

_JS = os.path.join(_ROOT, "html", "scene3d")


def _js(name):
    with open(os.path.join(_JS, name), encoding="utf-8") as fh:
        return fh.read()


def _fn(src, name):
    s = src[src.index("function " + name):]
    return s[:s.index("\n}\n") + 2]


def _rows():
    with open(os.path.join(_ROOT, "data", "plants_master.json"), encoding="utf-8") as fh:
        return {r["common_name"]: r for r in json.load(fh)}


class TheClustersWereRead(unittest.TestCase):

    def test_forty_wildflowers_carry_a_cluster_size(self):
        rows = _rows()
        read = [r for r in rows.values() if r.get("head_length_cm")
                and r["plant_type"] in herb_habit.TYPES]
        self.assertGreaterEqual(len(read), 40)
        for r in read:
            self.assertTrue(r.get("head_width_cm"), r["common_name"])
            # A cluster is part of its plant: never longer than it is tall.
            self.assertLess(r["head_length_cm"] / 100, float(r["mature_height_m"]),
                            r["common_name"])

    def test_the_meadow_rue_plume_is_its_size(self):
        r = _rows()["Tall Meadow Rue"]
        self.assertEqual((r["head_length_cm"], r["head_width_cm"]), (30.0, 20.0))

    def test_a_wildflower_with_a_size_is_not_drawn_as_a_grass(self):
        """grass_habit draws a tuft from head_length_cm: only on a graminoid."""
        from src import grass_habit
        for r in _rows().values():
            if r["plant_type"] in herb_habit.TYPES and r.get("head_length_cm"):
                self.assertIsNone(grass_habit.form_for(r), r["common_name"])


class TheReadingTool(unittest.TestCase):

    def setUp(self):
        import leaf_readings
        self.lr = leaf_readings
        self.rows = [{"scientific_name": "Testus flos", "common_name": "Test Flower",
                      "plant_type": "wildflower", "flower_data_source": "estimated",
                      "flower_data_citation": ""},
                     {"scientific_name": "Testus gramen", "common_name": "Test Grass",
                      "plant_type": "grass"}]
        self.review = {"Testus flos": {"refs": {"flower": ["9"]}},
                       "Testus gramen": {"refs": {"flower": ["8"]}}}

    def test_a_cluster_alone_needs_no_habit(self):
        batch = {"Testus flos": {"head_length_cm": 12, "head_width_cm": 4}}
        self.assertEqual(self.lr.problems(batch, {r["scientific_name"]: r for r in self.rows},
                                          self.review), [])

    def test_a_cluster_alone_leaves_both_pairs(self):
        """The flowers' other numbers were not read: saying so would be false."""
        self.lr.apply({"Testus flos": {"head_length_cm": 12, "head_width_cm": 4}},
                      self.rows, self.review)
        row = self.rows[0]
        self.assertEqual((row["head_length_cm"], row["head_width_cm"]), (12.0, 4.0))
        self.assertEqual(row["flower_data_source"], "estimated")
        self.assertNotIn("leaf_data_source", row)

    def test_a_grass_head_is_read_with_its_blades(self):
        batch = {"Testus gramen": {"head_length_cm": 12}}
        got = self.lr.problems(batch, {r["scientific_name"]: r for r in self.rows}, self.review)
        self.assertTrue(any("cluster" in g for g in got), got)


class TheViewer(unittest.TestCase):

    def test_a_mat_has_no_plate(self):
        leafy = _js("03c-leafy.js")
        mat = _fn(leafy, "_leafyMat")
        self.assertNotIn("_leafyUnderlay", mat)
        self.assertIn("_wdSpray", mat)
        for word in ("MAT_COVER", "MAT_GAIN_MAX", "TERNATE_TWICE_M", "TERNATE_DROOP"):
            self.assertRegex(leafy, r"\b%s = [\d.]+" % word)

    def test_the_herb_layer_places_a_mats_shoots(self):
        self.assertIn("leafyCardsMesh(arch, total, surf)", _js("04-quality.js"))

    def test_opposite_leaves_turn_a_quarter(self):
        spray = _fn(_js("03d-woody.js"), "_wdSpray(shape")
        self.assertIn("per === 2 && j % 2 === 1", spray)

    def test_a_read_vine_clothes_its_side(self):
        m = re.search(r"const VINE_SHOOT_GAP = ([\d.]+);", _js("22b-vineleaves.js"))
        self.assertLessEqual(float(m.group(1)), 0.3)


@unittest.skipUnless(shutil.which("node") or shutil.which("nodejs"), "needs node")
class TheCardInNode(unittest.TestCase):

    def _run(self, expr):
        src = _js("15c-woodybloom.js")
        prog = "\n".join([_fn(src, "_wbFill"), _fn(src, "_wbShare"),
                          f"console.log(JSON.stringify({expr}));"])
        node = shutil.which("node") or shutil.which("nodejs")
        out = subprocess.run([node, "-e", prog], capture_output=True, text=True,
                             encoding="utf-8", check=True)
        return json.loads(out.stdout)

    def test_the_painted_cluster_fills_a_share_of_its_card(self):
        for arch in ("raceme", "spike", "panicle", "corymb", "umbel", "cyme", "whorl"):
            for petals in (0, 5):
                for share in (0.06, 0.3, 1):
                    w, h = self._run(f"_wbFill('{arch}', {petals}, {share})")
                    self.assertGreater(w, 0.05, arch)
                    self.assertLessEqual(w, 1, arch)
                    self.assertGreater(h, 0.4, arch)
                    self.assertLessEqual(h, 1, arch)

    def test_a_flat_top_is_wider_than_it_is_tall(self):
        w, h = self._run("_wbFill('corymb', 5, 0.06)")
        self.assertGreater(w, h)


class TheReviewStage(unittest.TestCase):

    def test_a_herbaceous_vine_scrambles_over_a_low_shrub(self):
        from src import sprite_gallery as sg
        rows = _rows()
        for name, host in (("Purple Peavine", sg.VINE_HOST_LOW), ("Wild Vetch", sg.VINE_HOST_LOW),
                           ("Blue Clematis", sg.VINE_HOST)):
            sc = sg._vine_scene(sg._species_specimen(rows[name]), 1, name, 1)
            names = {p.get("common_name") for p in sc["plants"]}
            want = next(r["common_name"] for r in rows.values() if r["scientific_name"] == host)
            self.assertIn(want, names, name)


if __name__ == "__main__":
    unittest.main()
