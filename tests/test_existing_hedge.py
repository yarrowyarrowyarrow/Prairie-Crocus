"""
tests/test_existing_hedge.py — a hedge already growing, and the lines that
cast shade (V3.75; ``docs/plans/V3.75-the-yard-tab-tidied.md``).

V3.74 planted a hedge, a living fence and a windbreak with the region's
shrubs. The owner found that a second way to plant a row ("you can plant a row
of plants") and asked for the hedge that is already there, "most likely
cotoneaster or sometimes caragana" around Edmonton. Holds:

* what a hedge is (the owner's five), sized and coloured by it unless the
  person said, and read from the words typed on an old one;
* an old hedge, living fence or windbreak converted at the height the 3D drew
  it, and a line V3.74 planted taken off with its plants kept;
* a hedge casts shade at its height and width, a deciduous one with the
  leaf-off break, is kept out of by the planner, is named in the timeline's
  notes, and is drawn in 3D in its own green (the cedar green in winter);
* a wall and a board fence cast shade, a rail and a chain link fence do not
  (the owner's Q3, V3.74), on the shade map and as the timeline's fixed
  casters, which call it "the fence".
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_TMP = tempfile.mkdtemp(prefix="existing_hedge_")
import src.db.plants as _plants  # noqa: E402
_plants._DATA_DIR = _TMP
_plants._DB_PATH = os.path.join(_TMP, "permadesign_test.db")

from src import yard_kinds as Y  # noqa: E402
from src import yard_upgrade as U  # noqa: E402
from src.projection import Projector  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LAT, _LNG = 53.5461, -113.4938
_P = Projector(_LAT, _LNG)


def setUpModule():
    _plants._DATA_DIR = _TMP
    _plants._DB_PATH = os.path.join(_TMP, "permadesign_test.db")
    _plants.init_db()


def tearDownModule():
    shutil.rmtree(_TMP, ignore_errors=True)


def _ll(x, y):
    lat, lng = _P.to_latlng(x, y)
    return [lng, lat]


def _line(pts, hid="h1", **props):
    p = {"element_type": "hedgerow", "hedge_id": hid}
    p.update(props)
    return {"type": "Feature",
            "geometry": {"type": "LineString",
                         "coordinates": [_ll(x, y) for x, y in pts]},
            "properties": p}


def _kind_line(key, pts, hid="h1", **options):
    f = _line(pts, hid)
    f["properties"].update(Y.drawn_props(key, **options))
    return f


def _project(*features):
    return {"type": "FeatureCollection", "features": list(features),
            "properties": {}}


class WhatAHedgeIs(unittest.TestCase):

    def test_sized_and_coloured_by_what_it_is_unless_said(self):
        for what, (h, w) in Y.HEDGE_SIZE_M.items():
            props = Y.drawn_props("hedge", hedge_kind=what)
            self.assertEqual((props["height_m"], props["width_m"]), (h, w))
            self.assertEqual(props["color"], Y.HEDGE_COLOURS[what])
        props = Y.drawn_props("hedge", hedge_kind="lilac", height_m=3.4)
        self.assertEqual(props["height_m"], 3.4)

    def test_an_old_hedge_is_read_by_its_words(self):
        for words, want in (("Peking cotoneaster", "cotoneaster"),
                            ("caragana", "caragana"),
                            ("Siberian peashrub", "caragana"),
                            ("lilacs", "lilac"), ("Syringa", "lilac"),
                            ("Brandon cedar", "cedar"), ("thuja", "cedar"),
                            ("dogwood", "other"), ("", "other")):
            f = _line([(0, 0), (5, 0)], style="hedge", species=words)
            self.assertEqual(Y.hedge_kind(f), want, words)

    def test_the_cedar_keeps_its_leaves(self):
        f = _kind_line("hedge", [(0, 0), (5, 0)], hedge_kind="cedar")
        self.assertEqual(Y.hedge_foliage(f), "evergreen")
        f = _kind_line("hedge", [(0, 0), (5, 0)], hedge_kind="caragana")
        self.assertEqual(Y.hedge_foliage(f), "deciduous")
        self.assertEqual(Y.hedge_foliage(_kind_line("fence", [(0, 0), (5, 0)])),
                         "")

    def test_kept_out_of_by_the_planner(self):
        from src import exclusion
        f = _kind_line("hedge", [(0, 0), (10, 0)], hedge_kind="cotoneaster")
        self.assertTrue(Y.is_keep_out(f))
        areas = exclusion.keepout_areas(_project(f))
        self.assertTrue(areas, "a hedge is not kept out of")


class OldDesigns(unittest.TestCase):

    def test_a_hedge_living_fence_or_windbreak_becomes_an_existing_hedge(self):
        for style, height in U.OLD_LINE_HEIGHT_M.items():
            f = _line([(0, 0), (8, 0)], style=style, species="caragana",
                      width_m=2.0)
            project = _project(f)
            self.assertEqual(U.upgrade(project), 1, style)
            props = project["features"][0]["properties"]
            self.assertEqual((props["kind"], props["style"], props["hedge_kind"],
                              props["height_m"], props["width_m"],
                              props["species"]),
                             ("hedge", "hedge", "caragana", height, 2.0,
                              "caragana"), style)
            self.assertEqual(U.upgrade(project), 0, style)

    def test_a_line_v3_74_planted_comes_off_and_its_plants_stay(self):
        planted = _line([(0, 0), (8, 0)], hid="p", kind="living_fence",
                        style="living_fence", plant_ids=[1, 2])
        bare = _line([(0, 4), (8, 4)], hid="b", kind="hedge", style="hedge",
                     plant_ids=[3])
        plant = {"type": "Feature",
                 "geometry": {"type": "Point", "coordinates": _ll(1, 0)},
                 "properties": {"element_type": "plant", "plant_id": 1,
                                "placement_group_id": "p"}}
        project = _project(planted, bare, plant)
        self.assertEqual(U.upgrade(project), 2)
        kinds = [(f["properties"].get("hedge_id"),
                  f["properties"]["element_type"])
                 for f in project["features"]]
        self.assertEqual(kinds, [("b", "hedgerow"), (None, "plant")])
        self.assertNotIn("plant_ids", project["features"][0]["properties"])


def _grid():
    s, w = _P.to_latlng(-10, -10)
    n, e = _P.to_latlng(10, 10)
    return {"grid": [[0.0] * 20 for _ in range(20)], "rows": 20, "cols": 20,
            "bbox": {"south": s, "west": w, "north": n, "east": e}}


class Shade(unittest.TestCase):

    def _fence(self, fence_kind):
        return _kind_line("fence", [(-10, 0), (10, 0)], fence_kind=fence_kind)

    def test_which_lines_cast(self):
        from src import shade
        self.assertEqual(len(shade.casters_from_project(
            _project(self._fence("board")))), 1)
        for kind in ("rail", "chain_link"):
            self.assertEqual(shade.casters_from_project(
                _project(self._fence(kind))), [], kind)
        wall = shade.casters_from_project(
            _project(_kind_line("wall", [(0, 0), (5, 0), (5, 5)])))
        self.assertEqual(len(wall), 2)                     # one a segment
        self.assertEqual({c["height_m"] for c in wall}, {Y.WALL_HEIGHT_M})
        hedge = shade.casters_from_project(_project(_kind_line(
            "hedge", [(0, 0), (5, 0)], hedge_kind="caragana")))
        self.assertEqual([(c["height_m"], c["radius_m"], c["kind"],
                           c["foliage"], c["what"]) for c in hedge],
                         [(2.5, 0.75, "hedge", "deciduous", "caragana hedge")])

    def test_the_ground_north_of_a_board_fence_is_shaded(self):
        from src import shade
        board = shade.shade_grid_for_design(_project(self._fence("board")),
                                            _grid(), terrain=False)
        rail = shade.shade_grid_for_design(_project(self._fence("rail")),
                                           _grid(), terrain=False)
        north_of = [row[10] for row in board[:10]]      # row 0 is the north
        south_of = [row[10] for row in board[10:]]
        self.assertGreater(max(north_of), 0.5)
        self.assertEqual(max(south_of), 0.0)
        self.assertEqual(max(max(r) for r in rail), 0.0)

    def test_a_deciduous_hedge_lets_the_winter_sun_through(self):
        from src import shade
        winter = [(12, 21)]
        grids = {}
        for what in ("cedar", "caragana"):
            casters = shade.casters_from_project(_project(_kind_line(
                "hedge", [(-10, 0), (10, 0)], hedge_kind=what, height_m=2.5,
                width_m=1.0)))
            grids[what] = shade.shade_grid(casters, _grid(), dates=winter,
                                           terrain=False)
        just_north = lambda g: max(row[10] for row in g[5:9])   # noqa: E731
        self.assertGreater(just_north(grids["cedar"]),
                           just_north(grids["caragana"]))
        self.assertGreater(just_north(grids["caragana"]), 0.0)

    def test_the_timeline_names_the_fence_and_the_hedge(self):
        from src import scene_timeline
        from src.succession_engine import (SuccessionEngine,
                                           static_casters_from_project)
        row = next(r for r in _plants.search_plants(plant_type="wildflower")
                   if r.get("sun_requirement") == "full_sun")
        lat, lng = _P.to_latlng(0, 1.0)              # a metre north of it
        for line, words in (
                (self._fence("board"), "the fence"),
                (_kind_line("hedge", [(-10, 0), (10, 0)],
                            hedge_kind="cotoneaster"),
                 "the cotoneaster hedge")):
            engine = SuccessionEngine(
                [{"plant_id": row["id"], "lat": lat, "lng": lng}],
                static_casters=static_casters_from_project(_project(line)),
                origin=(_LAT, _LNG))
            shader = engine.main_shader(0, 3)
            self.assertEqual(scene_timeline.shader_words(
                shader, [], [], None, None), words)

    def test_the_3d_and_the_shade_read_one_height(self):
        from src import scene_kinds, scene_site
        self.assertIs(scene_kinds.FENCE_HEIGHT_M, Y.FENCE_HEIGHT_M)
        self.assertEqual(scene_site.LINE_HEIGHT_M["wall"], Y.WALL_HEIGHT_M)
        self.assertEqual(Y.shade_height(self._fence("board")),
                         Y.FENCE_HEIGHT_M["board"])


class In3D(unittest.TestCase):

    def test_a_hedge_at_its_height_and_width_in_its_kind(self):
        from src import scene_site
        f = _kind_line("hedge", [(0, 0), (10, 0)], hedge_kind="cedar",
                       height_m=2.2, width_m=0.8)
        row = scene_site.lines(_project(f), _P)[0]
        self.assertEqual((row["kind"], row["hedge_kind"], row["height_m"],
                          row["width_m"]), ("hedge", "cedar", 2.2, 0.8))

    def test_its_green_by_kind_and_bare_in_winter_but_the_cedar(self):
        """The viewer's ``hedgeColour`` (``02d-kinds.js``), run in node."""
        try:
            subprocess.run(["node", "--version"], capture_output=True,
                           check=True)
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("no node")
        with open(os.path.join(_ROOT, "html", "scene3d", "02d-kinds.js"),
                  encoding="utf-8") as fh:
            js = fh.read()
        block = js[js.index("const HEDGE_LOOK"):]
        script = ("function seasonLeavesDown(m) { return m === 1; }\n" + block +
                  "\nconst out = {};\nfor (const k of " +
                  json.dumps([v for v, _w in Y.HEDGE_KINDS]) +
                  ") out[k] = [hedgeColour(k, 7), hedgeColour(k, 1)];\n"
                  "console.log(JSON.stringify(out));")
        got = json.loads(subprocess.run(["node", "-e", script],
                                        capture_output=True, text=True,
                                        encoding="utf-8", check=True).stdout)
        summer = {k: v[0] for k, v in got.items()}
        self.assertEqual(len(set(summer.values())), len(summer), summer)
        for k, (july, january) in got.items():
            if k in Y.EVERGREEN_HEDGES:
                self.assertEqual(january, july, k)
            else:
                self.assertNotEqual(january, july, k)


if __name__ == "__main__":
    unittest.main()
