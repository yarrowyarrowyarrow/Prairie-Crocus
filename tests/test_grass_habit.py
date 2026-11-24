"""
tests/test_grass_habit.py — which grasses, sedges and rushes are drawn from
their own blades and seed head, and what the viewer is told (V3.51, F268).

``src/grass_habit.py`` decides it once, in ``build_scene``; the viewer's
``html/scene3d/03f-tufts.js`` builds it. These hold the decision and the
vocabularies the two sides share.
"""

import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from src import data_quality as dq                              # noqa: E402
from src import grass_habit as GH, native_here, pond_habit     # noqa: E402

with open(os.path.join(ROOT, "data", "plants_master.json"), encoding="utf-8") as _fh:
    ROWS = json.load(_fh)
NATIVE = native_here.native_names()
JS = open(os.path.join(ROOT, "html", "scene3d", "03f-tufts.js"), encoding="utf-8").read()
QUALITY = open(os.path.join(ROOT, "html", "scene3d", "04-quality.js"), encoding="utf-8").read()


def _js_list(name):
    m = re.search(r"const %s = \[([^\]]*)\]" % name, JS)
    return tuple(re.findall(r"'([a-z_]+)'", m.group(1)))


class TheDecision(unittest.TestCase):

    def test_every_native_graminoid_is_read_and_drawn(self):
        """All the region's grasses, sedges and rushes but the horsetails, and
        the five grass-like water plants."""
        drawn = [r for r in ROWS if r["scientific_name"] in NATIVE and GH.form_for(r)]
        self.assertEqual(len(drawn), 47)
        left = [r["common_name"] for r in ROWS if r["scientific_name"] in NATIVE
                and r["plant_type"] in GH.GRAMINOIDS and not GH.form_for(r)
                and r.get("growth_form") != "jointed"]
        self.assertEqual(left, [])

    def test_a_horsetail_keeps_its_own_builder(self):
        for r in ROWS:
            if r.get("growth_form") == "jointed":
                self.assertIsNone(GH.form_for(r), r["common_name"])

    def test_an_estimated_row_keeps_the_baked_tuft(self):
        row = next(r for r in ROWS if r["common_name"] == "Blue Grama Grass")
        self.assertEqual(GH.form_for(row), "bunch")
        self.assertIsNone(GH.form_for(dict(row, leaf_data_source="estimated")))
        self.assertIsNone(GH.form_for(dict(row, head_length_cm=None)))

    def test_a_creeping_plant_is_a_sod_and_a_rush_has_no_blades(self):
        by = {r["common_name"]: r for r in ROWS}
        self.assertEqual(GH.form_for(by["Wire Rush"]), "sod")
        d = GH.drawn_block(by["Wire Rush"], "sod")
        self.assertEqual((d["blades"], d["blade_m"], d["attitude"]), ("none", 0.0, "side"))

    def test_the_pond_leaves_a_read_water_plant_to_this_body(self):
        by = {r["common_name"]: r for r in ROWS}
        for name in ("Cattail", "Great Bulrush", "Giant Bur-reed", "Rat Root",
                     "Small Bottle Sedge"):
            self.assertIsNone(pond_habit.body_for(by[name]), name)
            self.assertIsNotNone(GH.form_for(by[name]), name)

    def test_when_the_heads_stand(self):
        by = {r["common_name"]: r for r in ROWS}
        grama = GH.drawn_block(dict(by["Blue Grama Grass"], bloom_start=7, bloom_end=8), "bunch")
        self.assertEqual((grama["head_from"], grama["ripe"], grama["holds"]), (7, 10, True))
        cotton = GH.drawn_block(by["Narrowleaf Cotton-grass"], "sod")
        self.assertFalse(cotton["holds"], "the cotton blows away; it does not stand the winter")

    def test_the_head_colour_is_never_the_flower_colour_field(self):
        """A seed head's colour is read into its own column; flower colours
        are the owner's answers and were not touched."""
        spike = next(r for r in ROWS if r["common_name"] == "Creeping Spikerush")
        self.assertEqual(spike["flower_color"], "#d6453a")
        self.assertEqual(spike["head_color"], "#7a5a3a")


class TheTwoSidesAgree(unittest.TestCase):

    def test_forms_and_heads(self):
        self.assertEqual(_js_list("TUFT_FORMS"), GH.FORMS)
        self.assertEqual(_js_list("HEAD_FORMS"), GH.HEADS)
        self.assertLessEqual(set(GH.HEADS), dq.INFLORESCENCE_FORMS)

    def test_the_blade_habits(self):
        held = set(re.findall(r"(\w+):\s*\{ rise:", JS))
        self.assertEqual(held | {"none"}, set(dq.BLADE_HABITS))

    def test_buildPlants_names_the_body(self):
        """A body buildPlants does not name is filed under the pond layer."""
        self.assertIn("pb === 'tuft'", QUALITY)
        self.assertIn("buildTuftLayer(byKind.tuft", QUALITY)

    def test_the_seeder_agrees_with_the_readings(self):
        import seed_inflorescence_morphology as seeder
        for r in ROWS:
            if r.get("plant_type") in ("grass", "sedge", "rush") and seeder.form_for(r):
                self.assertEqual(seeder.form_for(r), r.get("inflorescence_form"),
                                 r["common_name"])


if __name__ == "__main__":
    unittest.main()
