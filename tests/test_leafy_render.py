"""
tests/test_leafy_render.py — a wildflower built from its own numbers, read
back from the real viewer (V3.48, F268).

``src/herb_habit.py`` decides which plants are drawn from what was read of
them and ``html/scene3d/03c-leafy.js`` builds the body. Every part of that can
be right while the picture is wrong, which is what the reference sheets showed
of the baked figures for years: leaves stretched with the plant, flowers with
nothing under them. So this pushes scenes built by the real ``build_scene``
into the real viewer in headless Chromium and reads back what was built
(``html/leafy_probe.html``):

* a read plant is the new body and an estimated one is the baked figure;
* it is placed at one scale up and across, so a leaf recorded 8 cm is 8 cm;
* it spends no more than its budget;
* there is a stem tip for every flower cluster, and the flower layer is handed
  those tips;
* every form builds with every leaf outline in the vocabulary.

Skips with no Chromium binary or no WebGL, as the other render gates do; a
viewer that THROWS fails.
"""

import html as _html
import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import render_yard                                            # noqa: E402
from src import data_quality, herb_habit                      # noqa: E402
from src import sprite_gallery as sg                          # noqa: E402
from tests.test_scene3d_render import fail_on_viewer_errors   # noqa: E402

_ROW = {"common_name": "Test Aster", "scientific_name": "Testus asterus",
        "plant_type": "wildflower", "mature_height_m": "1", "spacing_m": "0.3",
        "bloom_period": "July–August", "deciduous_evergreen": "herbaceous",
        "growth_form": "erect", "leaf_shape": "lanceolate", "leaf_size_cm": 8.0,
        "leaf_arrangement": "alternate", "stem_branching": "branched_above",
        "basal_rosette": 0, "flowering_stems": 24, "flower_form": "daisy",
        "flower_arch": "head", "flower_diameter_cm": 2.5, "petal_count": 21,
        "petal_shape": "narrow", "flower_symmetry": "radial",
        "flower_color": "#8e6fc4", "flower_center_color": "#e8b93a"}


def _scene(name="Test Aster", **over):
    import datetime
    row = dict(_ROW, common_name=name, **over)
    return sg._scene_for(sg._species_specimen(row), 1, name, 1,
                         when=datetime.datetime(2024, 7, 15, 12, 0))


SCENES = {
    "read": _scene(leaf_data_source="photo", stem_leaf_nodes=18),
    "estimated": _scene(),
    "mat": _scene("Test Mat", plant_type="groundcover", growth_form="mat",
                  mature_height_m="0.15", leaf_shape="obovate", leaf_size_cm=2.0,
                  flowering_stems=8, stem_branching="unbranched",
                  leaf_data_source="photo"),
    "rosette": _scene("Test Rosette", growth_form="rosette", mature_height_m="0.3",
                      leaf_shape="spatulate", leaf_size_cm=6.0, leaf_arrangement="basal",
                      basal_rosette=1, flowering_stems=5, stem_branching="unbranched",
                      leaf_data_source="photo"),
    "many": _scene("Test Many", leaf_shape="bipinnate", flowering_stems=120,
                   stem_leaf_nodes=60, basal_rosette=1, leaf_data_source="photo"),
}


class TheBodyInTheRealViewer(unittest.TestCase):
    got = None

    @classmethod
    def setUpClass(cls):
        job = {"scenes": SCENES, "forms": list(herb_habit.FORMS),
               "shapes": sorted(data_quality.LEAF_SHAPES)}
        try:
            server = render_yard.Server({"/__yard/job.json": job})
        except OSError as exc:
            raise unittest.SkipTest(f"cannot bind a local port: {exc}")
        try:
            dom = render_yard.run_probe(
                server.url("leafy_probe.html?job=/__yard/job.json"),
                budget_ms=90000, timeout=420)
        except (OSError, RuntimeError, Exception) as exc:    # noqa: BLE001
            server.stop()
            raise unittest.SkipTest(f"Chromium would not run headlessly: {exc}")
        server.stop()
        fail_on_viewer_errors(dom)
        match = re.search(r"<title>MEASURED (\{.*\})</title>", dom, re.S)
        if not match:
            raise unittest.SkipTest("the probe never reported: no WebGL in "
                                    "this environment")
        cls.got = json.loads(_html.unescape(match.group(1)))

    def _body(self, name):
        bodies = [b for b in self.got["scenes"][name]["bodies"]]
        self.assertTrue(bodies, f"{name}: nothing was drawn")
        return bodies[0]

    # ── which body ───────────────────────────────────────────────────────────

    def test_the_fixtures_are_what_the_gate_needs(self):
        self.assertEqual(SCENES["read"]["plants"][0]["drawn"]["body"], "leafy")
        self.assertIsNone(SCENES["estimated"]["plants"][0].get("drawn"))
        self.assertEqual(SCENES["mat"]["plants"][0]["drawn"]["form"], "mat")
        self.assertEqual(SCENES["rosette"]["plants"][0]["drawn"]["form"], "rosette")

    def test_a_read_plant_is_drawn_from_its_own_numbers(self):
        self.assertTrue(self._body("read")["leafy"])

    def test_an_estimated_plant_keeps_the_baked_figure(self):
        """Drawing a genus guess at life size would state it as a measurement."""
        self.assertFalse(self._body("estimated")["leafy"])

    def test_a_groundcover_with_its_own_body_is_drawn_once(self):
        """It goes to the herb layer, not to the capped mat as well."""
        bodies = self.got["scenes"]["mat"]["bodies"]
        self.assertEqual(len(bodies), 1)
        self.assertTrue(bodies[0]["leafy"])

    # ── at its size ──────────────────────────────────────────────────────────

    def test_it_is_placed_at_one_scale_up_and_across(self):
        """The baked figures are stretched to the plant's width. This body is
        not: a leaf recorded 8 cm long is 8 cm long whichever way it points."""
        for name in ("read", "mat", "rosette"):
            sx, sy, sz = self._body(name)["scale"]
            self.assertAlmostEqual(sx / sy, 1.0, delta=0.03, msg=name)
            self.assertAlmostEqual(sz / sy, 1.0, delta=0.03, msg=name)

    def test_it_stands_as_tall_as_the_plant(self):
        for name in ("read", "mat", "rosette"):
            b, p = self._body(name), SCENES[name]["plants"][0]
            self.assertAlmostEqual(b["bottom"], 0.0, delta=0.02, msg=name)
            self.assertLessEqual(b["top"], 1.001, msg=name)
            self.assertAlmostEqual(b["scale"][1], p["height_m"], delta=0.01, msg=name)

    def test_the_leaf_is_the_length_that_was_read(self):
        plan = self._body("read")["plan"]
        self.assertAlmostEqual(plan["L"], 0.08, places=4)
        self.assertEqual(plan["nodes"], 18, "the counted leaves were not used")

    def test_the_body_stays_about_the_ground_it_was_spaced_for(self):
        """Not stretched to it, and not far outside it either."""
        for name in ("read", "mat", "rosette"):
            b = self._body(name)
            self.assertLess(b["body_half_width"], 1.6 * b["unit_half_width"], name)

    # ── within its budget ────────────────────────────────────────────────────

    def test_no_plant_spends_more_than_its_budget(self):
        for name in SCENES:
            b = self._body(name)
            if not b["leafy"]:
                continue
            budget = self.got["scenes"][name]["budget"][1]
            self.assertLessEqual(b["triangles"], budget * 1.12,
                                 f"{name}: {b['triangles']} triangles")

    def test_a_plant_with_more_than_the_budget_holds_is_cut_not_dropped(self):
        b = self._body("many")
        self.assertTrue(b["leafy"])
        self.assertGreaterEqual(b["plan"]["stems"], 5)
        self.assertGreaterEqual(b["plan"]["nodes"], 4)
        self.assertEqual(b["plan"]["lod"], 0, "the leaves were not made plainer first")

    def test_it_carries_shade_and_no_bad_number(self):
        for name in SCENES:
            b = self._body(name)
            self.assertEqual(b["bad"], 0, name)
            if b["leafy"]:
                self.assertTrue(b["colours"], f"{name}: no vertex colours, so the "
                                              f"leaf material draws it black or flat")

    # ── flowers on its tips ──────────────────────────────────────────────────

    def test_there_is_a_tip_for_every_flower_cluster(self):
        """24 clusters on stems that fork above: six stems of four tips. With
        fewer tips than clusters the flowers stack on one another."""
        b = self._body("read")
        self.assertEqual(b["plan"]["stems"], 6)
        self.assertEqual(b["tips"], 24)

    def test_the_flower_layer_is_handed_those_tips(self):
        sc = self.got["scenes"]["read"]
        p = SCENES["read"]["plants"][0]
        self.assertEqual(len(sc["anchors"]), 24)
        tops = [a[1] for a in sc["anchors"]]
        self.assertAlmostEqual(max(tops), p["height_m"], delta=0.03)
        self.assertGreater(min(tops), 0.45 * p["height_m"])
        self.assertTrue(all(a[3] == 1 for a in sc["anchors"]),
                        "a stem tip is where a cluster's top goes")

    # ── every form, every outline ────────────────────────────────────────────

    def test_every_form_builds_with_every_leaf_outline(self):
        rows = self.got["matrix"]
        self.assertEqual(len(rows), len(herb_habit.FORMS) * len(data_quality.LEAF_SHAPES) * 4)
        for r in rows:
            where = f"{r['form']} / {r['shape']} / {r['arrangement']}"
            self.assertNotIn("error", r, f"{where}: {r.get('error')}")
            self.assertEqual(r["bad"], 0, where)
            self.assertGreater(r["triangles"], 20, where)
            self.assertLessEqual(r["triangles"], 1800 * 1.12, where)
            self.assertGreater(r["tips"], 0, where)
            self.assertAlmostEqual(r["top"], 1.0, delta=0.02, msg=where)

    def test_a_mat_is_leafy_shoots_and_not_a_plate(self):
        """V3.65: until then a solid mound stood in for a mat's leaves, and
        every mat read as a green plate with sprigs round its edge."""
        cards = self.got["scenes"]["mat"]["cards"]
        self.assertEqual(len(cards), 1, "the mat's leafy shoots were not drawn")
        self.assertTrue(cards[0]["cut"], "a card not cut to its leaves is a plate again")
        self.assertGreater(cards[0]["triangles"], 120)
        self.assertEqual(len(self.got["mats"]), len(data_quality.LEAF_SHAPES) * 3)
        for r in self.got["mats"]:
            where = f"mat / {r['shape']} / {r['arrangement']}"
            self.assertNotIn("error", r, f"{where}: {r.get('error')}")
            self.assertEqual(r["bad"], 0, where)
            self.assertTrue(r["uv"], where)
            self.assertGreaterEqual(r["cards"], 60, where)
            self.assertLessEqual(r["triangles"], 1800 * 1.12, where)
            self.assertLess(r["card_top"], 0.75, f"{where}: the leaves stand, not lie")

    def test_two_species_do_not_share_a_body_they_should_not(self):
        keys = {(r["form"], r["shape"], r["arrangement"]): r["key"] for r in self.got["matrix"]}
        self.assertEqual(len(set(keys.values())), len(keys))


class TheProbeIsADevPage(unittest.TestCase):

    def test_the_viewer_knows_nothing_of_it(self):
        with open(os.path.join(render_yard.HTML, "scene3d", "chunks.js"),
                  encoding="utf-8") as fh:
            self.assertNotIn("leafy_probe", fh.read())

    def test_it_loads_the_error_watcher(self):
        with open(os.path.join(render_yard.HTML, "leafy_probe.html"),
                  encoding="utf-8") as fh:
            self.assertIn('src="probe_watch.js"', fh.read())


if __name__ == "__main__":
    unittest.main()
