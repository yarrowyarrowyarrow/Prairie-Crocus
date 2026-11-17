"""
tests/test_tuft_render.py — a grass, sedge or rush built from its own blades
and seed head, read back from the real viewer (V3.51, F268).

``src/grass_habit.py`` decides which are drawn from what was read and
``html/scene3d/03f-tufts.js`` builds them. This pushes scenes built by the
real ``build_scene`` from the catalogue's rows into the real viewer in headless
Chromium (``html/tuft_probe.html``) and reads back what was built:

* every read native is its own body, blades, stems and head, and nothing else
  is drawn for it (no billboard, no baked tuft);
* within its budget, as tall as it is recorded and its heads inside that;
* the blades in the species' read colour, the heads in theirs;
* the heads come with flowering and stand on the dry stems in winter, except
  the cotton, which is gone;
* a leafless rush or bulrush has no blades;
* an estimated row keeps the baked tuft, and Stylised draws none of this;
* every head form at every attitude builds, leafy and leafless, with every
  coordinate a number.

Skips with no Chromium binary or no WebGL, as the other render gates do; a
viewer that THROWS fails.
"""

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
from src import grass_habit, native_here                      # noqa: E402
from src import sprite_gallery as sg                          # noqa: E402
from tests.test_scene3d_render import fail_on_viewer_errors   # noqa: E402

with open(os.path.join(ROOT, "data", "plants_master.json"), encoding="utf-8") as _fh:
    _ROWS = {r["scientific_name"]: r for r in json.load(_fh)}
_NATIVE = native_here.native_names()
READ = sorted(s for s, r in _ROWS.items() if s in _NATIVE and grass_habit.form_for(r))
BY_NAME = {r["common_name"]: s for s, r in _ROWS.items()}


def _scene(sci, month=7, quality=1, **over):
    row = dict(_ROWS[sci], **over)
    sc = sg._scene_for(sg._species_specimen(row), 1, row["common_name"], 1,
                       when=datetime.datetime(2024, month, 15, 12, 0))
    sc["quality"] = quality
    return sc


SCENES = {sci: _scene(sci) for sci in READ}
SCENES.update({
    "estimated": _scene(BY_NAME["Blue Grama Grass"], leaf_data_source="estimated"),
    "stylised": _scene(BY_NAME["Blue Grama Grass"], quality=0),
    "grama_may": _scene(BY_NAME["Blue Grama Grass"], month=5),
    "grama_january": _scene(BY_NAME["Blue Grama Grass"], month=1),
    "cotton_january": _scene(BY_NAME["Narrowleaf Cotton-grass"], month=1),
})
HEADS = list(grass_habit.HEADS)


class TheTuftInTheRealViewer(unittest.TestCase):
    got = None

    @classmethod
    def setUpClass(cls):
        try:
            server = render_yard.Server({"/__yard/job.json": {"scenes": SCENES, "heads": HEADS}})
        except OSError as exc:
            raise unittest.SkipTest(f"cannot bind a local port: {exc}")
        try:
            dom = render_yard.run_probe(server.url("tuft_probe.html?job=/__yard/job.json"),
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

    def _parts(self, name):
        return self.got["scenes"][name]["meshes"]

    def test_every_read_native_is_its_own_body_and_nothing_else(self):
        self.assertEqual(len(READ), 47)
        for sci in READ:
            s = self.got["scenes"][sci]
            self.assertTrue(s["key"], sci)
            self.assertIn(len(s["meshes"]), (2, 3), sci)
            self.assertEqual(s["billboards"], 0, f"{sci}: something else drawn too")

    def test_within_budget_and_as_tall_as_recorded(self):
        for sci in READ:
            parts = self._parts(sci)
            whole = sum(m["triangles"] for m in parts)
            self.assertLess(whole, 9000, sci)
            p = SCENES[sci]["plants"][0]
            for m in parts:
                self.assertAlmostEqual(m["scale"][1], p["height_m"], delta=0.02 * p["height_m"] + 0.01,
                                       msg=sci)
                self.assertLess(m["top"], 1.12, f"{sci}: a part stands above the plant")

    def test_the_blades_and_heads_wear_their_read_colours(self):
        for sci in READ:
            row, parts = _ROWS[sci], self._parts(sci)
            self.assertEqual(parts[0]["colour"], row["leaf_color"], sci)
            d = SCENES[sci]["plants"][0]["drawn"]
            if d["head_from"] <= 7 <= d["ripe"] - 2 or d["head"] == "cotton":   # as read
                self.assertEqual(parts[-1]["colour"], row["head_color"], sci)
            else:                                         # ripening toward straw
                self.assertNotEqual(parts[-1]["colour"], row["head_color"], sci)

    def test_a_leafless_plant_has_no_blades(self):
        for name in ("Wire Rush", "Great Bulrush", "Creeping Spikerush"):
            parts = self._parts(BY_NAME[name])
            self.assertEqual(len(parts), 2, name)
            self.assertEqual(parts[0]["tuft"]["plan"]["blades"], 0, name)

    def test_the_heads_come_with_flowering_and_stand_the_winter(self):
        may = self._parts("grama_may")
        self.assertLess(may[-1]["scale"][1], 0.01, "a grama head in May")
        jan = self._parts("grama_january")
        self.assertGreater(jan[-1]["scale"][1], 0.05, "a grama's head gone in January")
        cotton = self._parts("cotton_january")
        self.assertLess(cotton[-1]["scale"][1], 0.01, "cotton in January")

    def test_an_estimated_row_and_stylised_keep_the_baked_tuft(self):
        for name in ("estimated", "stylised"):
            s = self.got["scenes"][name]
            self.assertEqual(s["meshes"], [], name)
            self.assertIsNone(s["key"], name)

    def test_every_head_builds_at_every_attitude(self):
        rows = self.got["matrix"]
        self.assertEqual(len(rows), len(HEADS) * 4 * 2)
        for r in rows:
            self.assertNotIn("error", r, r)
            self.assertEqual(r["bad"], 0, r)
            self.assertGreater(r["heads"], 0, r)
            self.assertLess(r["triangles"], 9000, r)


if __name__ == "__main__":
    unittest.main()
