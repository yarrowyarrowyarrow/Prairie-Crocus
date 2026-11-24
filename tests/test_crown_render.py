"""
tests/test_crown_render.py — a tree built from its own crown, and a vine with
its own leaves, read back from the real viewer (V3.50, F268).

``src/tree_habit.py`` decides which trees are drawn from what was read of them
and ``html/scene3d/03e-crowns.js`` builds them; ``22b-vineleaves.js`` gives a
read vine its leafy shoots. This pushes scenes built by the real
``build_scene`` from the catalogue's own rows into the real viewer in headless
Chromium (``html/woody_probe.html``) and reads back what was built:

* every native tree is its own crown, within its budget, as tall and as wide
  as it is recorded, its leaves cut to their outline and casting that shadow;
* the bare bole is as high as was read, and a spruce's branches reach the
  ground;
* a deciduous tree is bare in winter and a spruce is not;
* a poplar's catkins are drawn in April;
* a read vine carries its own leafy shoots on what it climbs;
* an estimated tree keeps the baked crown, and Stylised draws none of this.

Skips with no Chromium binary or no WebGL, as the other render gates do; a
viewer that THROWS fails.
"""

import copy
import datetime
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
from src import native_here, tree_habit                       # noqa: E402
from src import sprite_gallery as sg                          # noqa: E402
from tests.test_scene3d_render import fail_on_viewer_errors   # noqa: E402

with open(os.path.join(ROOT, "data", "plants_master.json"), encoding="utf-8") as _fh:
    _ROWS = {r["scientific_name"]: r for r in json.load(_fh)}
_NATIVE = native_here.native_names()
TREES = sorted(s for s, r in _ROWS.items() if s in _NATIVE and r["plant_type"] == "tree")


def _scene(sci, month=7, quality=1, **over):
    row = dict(_ROWS[sci], **over)
    sc = sg._scene_for(sg._species_specimen(row), 1, row["common_name"], 1,
                       when=datetime.datetime(2024, month, 15, 12, 0))
    sc["quality"] = quality
    return sc


SCENES = {sci: _scene(sci) for sci in TREES}
SCENES.update({
    "estimated": _scene("Populus tremuloides", leaf_data_source="estimated"),
    "stylised": _scene("Populus tremuloides", quality=0),
    "aspen_winter": _scene("Populus tremuloides", month=1),
    "spruce_winter": _scene("Picea glauca", month=1),
    "poplar_april": _scene("Populus balsamifera", month=4),
    "vine": _scene("Clematis occidentalis", month=6),
})
_young = copy.deepcopy(SCENES["Populus tremuloides"])
for _k in ("height_m", "canopy_m"):
    _young["plants"][0][_k] *= 0.3
    _young["plants"][0]["drawn"][_k] *= 0.3
SCENES["young"] = _young


class TheCrownInTheRealViewer(unittest.TestCase):
    got = None

    @classmethod
    def setUpClass(cls):
        try:
            server = render_yard.Server({"/__yard/job.json": {"scenes": SCENES, "forms": [],
                                                             "shapes": []}})
        except OSError as exc:
            raise unittest.SkipTest(f"cannot bind a local port: {exc}")
        try:
            dom = render_yard.run_probe(server.url("woody_probe.html?job=/__yard/job.json"),
                                        budget_ms=150000, timeout=600)
        except (OSError, RuntimeError, Exception) as exc:    # noqa: BLE001
            server.stop()
            raise unittest.SkipTest(f"Chromium would not run headlessly: {exc}")
        server.stop()
        fail_on_viewer_errors(dom)
        match = re.search(r"<title>MEASURED (\{.*\})</title>", dom, re.S)
        if not match:
            raise unittest.SkipTest("the probe never reported: no WebGL in this environment")
        cls.got = json.loads(_html.unescape(match.group(1)))

    def _crown(self, name):
        leaves = [b for b in self.got["scenes"][name]["bodies"] if b["leaves"]]
        self.assertEqual(len(leaves), 1, f"{name}: not one crown of its own")
        self.assertTrue(leaves[0]["plan"].get("trunks"), f"{name}: a shrub's body, not a crown")
        return leaves[0]

    def _branches(self, name):
        st = [b for b in self.got["scenes"][name]["bodies"] if b["woody"] and not b["leaves"]]
        self.assertEqual(len(st), 1, name)
        return st[0]

    def test_every_native_tree_is_its_own_crown(self):
        self.assertEqual(len(TREES), 10)
        for sci in TREES:
            plan = self._crown(sci)["plan"]
            d = SCENES[sci]["plants"][0]["drawn"]
            self.assertEqual((plan["form"], plan["limbs"], plan["trunks"]),
                             (d["form"], d["limbs"], d["trunks"]), sci)

    def test_within_its_budget_and_its_leaves_at_most_three_times_their_size(self):
        for sci in TREES + ["young"]:
            b = self._crown(sci)
            self.assertLessEqual(b["whole"], b["plan"]["budget"] + 2, sci)
            self.assertTrue(1.0 <= b["plan"]["gain"] <= 3.0, sci)
            self.assertGreater(b["plan"]["cards"], 1000 if sci != "young" else 300, sci)

    def test_as_tall_and_as_wide_as_the_tree(self):
        for sci in TREES:
            b, p = self._crown(sci), SCENES[sci]["plants"][0]
            self.assertAlmostEqual(self._branches(sci)["bottom"], 0.0, delta=0.01, msg=sci)
            self.assertAlmostEqual(b["scale"][1], p["height_m"], delta=0.05, msg=sci)
            wide = 2 * b["half"] * b["scale"][0]
            self.assertAlmostEqual(wide, p["canopy_m"], delta=0.2 * p["canopy_m"], msg=sci)
            sx, sy, _ = b["scale"]
            self.assertLess(abs(sx / sy - 1.0), 0.3, sci)

    def test_the_bare_bole_is_as_high_as_was_read(self):
        """No leaf below the crown's base: the aspen's lower half is white trunk."""
        for sci in TREES:
            b = self._crown(sci)
            clear = SCENES[sci]["plants"][0]["drawn"]["clear"]
            self.assertGreater(b["bottom"], clear - 0.12, sci)
        self.assertLess(self._crown("Picea glauca")["bottom"], 0.08,
                        "a white spruce's branches reach the ground")

    def test_its_leaves_wear_their_outline_and_cast_its_shadow(self):
        for sci in TREES:
            b = self._crown(sci)
            self.assertTrue(b["cut"] and b["shadow_cut"] and b["uv"], sci)
            self.assertGreaterEqual(b["mips"], 8, sci)

    def test_needles_are_carried_as_the_species_carries_them(self):
        spray = {sci: self._crown(sci)["plan"]["spray"]["key"] for sci in TREES}
        self.assertIn("needle-frond", spray["Picea glauca"])
        self.assertIn("needle-tuft", spray["Pinus banksiana"])
        self.assertIn("needle-rosette", spray["Larix laricina"])
        self.assertIn("branchlet", spray["Populus tremuloides"])

    def test_a_deciduous_tree_is_bare_in_winter_and_a_spruce_is_not(self):
        self.assertLess(self._crown("aspen_winter")["scale"][1], 0.01)
        self.assertGreater(self._branches("aspen_winter")["scale"][1], 5)
        self.assertGreater(self._crown("spruce_winter")["scale"][1], 5)

    def test_a_poplars_catkins_are_drawn_in_april(self):
        cards = self.got["scenes"]["poplar_april"]["blooms"]["cards"]
        self.assertTrue(cards, "no catkins on a poplar in April")
        self.assertGreater(sum(c["count"] for c in cards), 100)

    def test_a_young_tree_is_a_smaller_tree(self):
        young, grown = self._crown("young")["plan"], self._crown("Populus tremuloides")["plan"]
        self.assertLess(young["H"], grown["H"])
        self.assertLess(young["tier"], 1)

    def test_an_estimated_tree_keeps_the_baked_crown(self):
        self.assertFalse(any(b["woody"] for b in self.got["scenes"]["estimated"]["bodies"]))
        self.assertFalse(any(b["woody"] for b in self.got["scenes"]["stylised"]["bodies"]))

    def test_a_read_vine_carries_its_own_leaves(self):
        """The scene holds two: one climbing a shrub, one in the open on the ground."""
        vines = self.got["scenes"]["vine"]["vines"]
        self.assertEqual(len(vines), 2, "the clematis drew no leaves of its own")
        for v in vines:
            self.assertGreater(v["cards"], 20)
            self.assertTrue(v["cut"] and v["shadow_cut"])
            self.assertEqual(v["triangles"], 2 * v["cards"])
        self.assertGreater(max(v["cards"] for v in vines), 100, "the climbing one is a wisp")


if __name__ == "__main__":
    unittest.main()
