"""
tests/test_hedge_planting.py — a hedge you can plant (V3.74, F280's fourth
increment; ``docs/plans/V3.74-hedges-you-can-plant.md``).

Until V3.74 a hedge, a living fence and a windbreak were a green line with a
species typed into a box: nothing bought, scored, fed or shaded by it. Holds:

* the rules (``src/hedge_planting.py``): which of the region's plants fill
  each role, which comes first, where they stand along the line (the plant's
  own spacing, half a step in from each end; a living fence repeating its
  shrubs; a windbreak two rows, the back row on one side, the more northern);
* planting through ``project_store``, grouped under the line, replacing what
  it had, and whether a line is planted read from its plants;
* an old hedge's words matched, and the Overview's offer (never planted on
  its own, the owner's Q5);
* a wall and a board fence cast shade, a rail and a chain link fence do not
  (the owner's Q3), on the shade map and as the timeline's fixed casters;
* a planted line draws nothing in 3D;
* the window's side (``src/hedge_flow.py``): a line drawn with plants chosen
  is planted in the handler's one undo step, and removing it takes them.
"""

import json
import math
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_TMP = tempfile.mkdtemp(prefix="hedge_planting_")
import src.db.plants as _plants  # noqa: E402
_plants._DATA_DIR = _TMP
_plants._DB_PATH = os.path.join(_TMP, "permadesign_test.db")

from src import hedge_planting as hp  # noqa: E402
from src import yard_kinds  # noqa: E402
from src.projection import Projector  # noqa: E402

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


def _xy(lat, lng):
    return _P.to_xy(lat, lng)


def _line(kind, pts, hid="h1", **props):
    p = yard_kinds.drawn_props(kind)
    p.update({"hedge_id": hid}, **props)
    return {"type": "Feature",
            "geometry": {"type": "LineString",
                         "coordinates": [_ll(x, y) for x, y in pts]},
            "properties": p}


def _by_name(name):
    for r in hp._region_rows("shrub") + hp._region_rows("tree"):
        if r["common_name"] == name:
            return r
    raise AssertionError(f"{name} is not on the region's list")


class WhichPlants(unittest.TestCase):

    def test_every_choice_is_a_region_native_that_stands(self):
        from src import native_here, region, zoning
        names = native_here.native_names(region.default().key)
        for role in (hp.SHRUB, hp.TALL, hp.FRONT):
            rows = hp.candidates(role)
            self.assertGreater(len(rows), 5, role)
            for r in rows:
                self.assertIn(r["scientific_name"], names)
                self.assertNotEqual(r.get("branching"), "prostrate")
                self.assertFalse(zoning.needs_standing_water(r))

    def test_the_roles_by_height(self):
        for r in hp.candidates(hp.SHRUB):
            self.assertEqual(r["plant_type"], "shrub")
            self.assertGreaterEqual(r["mature_height_meters"], hp.HEDGE_MIN_M)
        for r in hp.candidates(hp.FRONT):
            self.assertGreaterEqual(r["mature_height_meters"], hp.FRONT_MIN_M)
        tall = hp.candidates(hp.TALL)
        self.assertTrue(any(r["plant_type"] == "tree" for r in tall))
        for r in tall:
            if r["plant_type"] == "shrub":
                self.assertGreaterEqual(r["mature_height_meters"],
                                        hp.TALL_MIN_M)

    def test_a_windbreak_back_row_puts_an_evergreen_first(self):
        first = hp.candidates(hp.TALL)[0]
        self.assertEqual(first["deciduous_evergreen"], "evergreen")

    def test_the_lists_are_by_name(self):
        names = [n for _pid, n in hp.choices(hp.SHRUB)]
        self.assertEqual(names, sorted(names, key=str.lower))

    def test_defaults_never_repeat_a_plant_and_the_third_is_none(self):
        d = hp.default_choices("living_fence")
        self.assertIsNone(d["shrub_3"])
        self.assertNotEqual(d["shrub"], d["shrub_2"])
        w = hp.default_choices("windbreak")
        self.assertNotEqual(w["tree"], w["shrub"])

    def test_chosen_ids_in_the_kinds_order(self):
        self.assertEqual(hp.chosen_ids("living_fence",
                                       {"shrub": 3, "shrub_2": 1,
                                        "shrub_3": None}), [3, 1])
        self.assertEqual(hp.chosen_ids("windbreak",
                                       {"shrub": 7, "tree": 9}), [9, 7])
        self.assertEqual(hp.chosen_ids("fence", {"fence_kind": "board"}), [])


class WhereTheyStand(unittest.TestCase):

    def test_a_hedge_at_its_shrubs_own_spacing_half_a_step_in(self):
        row = _by_name("Red Osier Dogwood")
        s = hp.spacing_of(row)
        line = [_ll(0, 0), _ll(20, 0)]
        spots = hp.layout(line, "hedge", [row])
        self.assertEqual(len(spots), round(20 / s))
        xs = sorted(_xy(lat, lng)[0] for _r, lat, lng in spots)
        step = 20 / len(spots)
        self.assertAlmostEqual(xs[0], step / 2, delta=0.05)
        self.assertAlmostEqual(20 - xs[-1], step / 2, delta=0.05)
        for a, b in zip(xs, xs[1:]):
            self.assertAlmostEqual(b - a, step, delta=0.05)
        for _r, lat, lng in spots:
            self.assertAlmostEqual(_xy(lat, lng)[1], 0.0, delta=0.05)

    def test_the_crowns_meet_once_grown(self):
        """The catalogue's crown is 1.5 times its spacing: neighbours
        overlap, so the hedge closes as it grows."""
        for name in ("Red Osier Dogwood", "Saskatoon Berry",
                     "Common Snowberry"):
            row = _by_name(name)
            self.assertGreater(float(row["mature_canopy_m"]),
                               hp.spacing_of(row))

    def test_a_short_line_still_gets_one(self):
        spots = hp.layout([_ll(0, 0), _ll(0.4, 0)], "hedge",
                          [_by_name("Saskatoon Berry")])
        self.assertEqual(len(spots), 1)

    def test_a_living_fence_repeats_its_shrubs_in_order(self):
        rows = [_by_name(n) for n in ("Red Osier Dogwood", "Common Snowberry",
                                      "Shrubby Cinquefoil")]
        spots = hp.layout([_ll(0, 0), _ll(16, 0)], "living_fence", rows)
        names = [r["common_name"] for r, _lat, _lng in
                 sorted(spots, key=lambda s: _xy(s[1], s[2])[0])]
        self.assertGreaterEqual(len(names), 9)
        for i, name in enumerate(names):
            self.assertEqual(name, rows[i % 3]["common_name"])

    def test_a_windbreak_is_two_rows_the_back_row_north(self):
        back, front = _by_name("White Spruce"), _by_name("Chokecherry")
        spots = hp.layout([_ll(0, 0), _ll(30, 0)], "windbreak", [back, front])
        gap = max(hp.ROW_GAP_MIN_M, hp.ROW_GAP_SHARE * hp.spacing_of(back))
        for r, lat, lng in spots:
            y = _xy(lat, lng)[1]
            want = gap / 2 if r is back else -gap / 2
            self.assertAlmostEqual(y, want, delta=0.05, msg=r["common_name"])
        # Drawn the other way, the back row is still on the north side.
        spots = hp.layout([_ll(30, 0), _ll(0, 0)], "windbreak", [back, front])
        self.assertTrue(all(_xy(lat, lng)[1] > 0
                            for r, lat, lng in spots if r is back))

    def test_a_bent_windbreak_keeps_one_side(self):
        """An L drawn north then east: the back row stays on the outside, so
        the rows never swap at the corner."""
        back, front = _by_name("White Spruce"), _by_name("Chokecherry")
        spots = hp.layout([_ll(0, 0), _ll(0, 20), _ll(20, 20)], "windbreak",
                          [back, front])
        for r, lat, lng in spots:
            x, y = _xy(lat, lng)
            outside = x < 0 or y > 20
            self.assertEqual(outside, r is back, (r["common_name"], x, y))


def _project(*features):
    return {"type": "FeatureCollection", "features": list(features),
            "properties": {}}


class InTheDesign(unittest.TestCase):

    def test_planted_through_the_store_grouped_under_the_line(self):
        from src.project_store import ProjectStore
        line = _line("hedge", [(0, 0), (12, 0)])
        project = _project(line)
        store = ProjectStore(project)
        row = _by_name("Saskatoon Berry")
        added = hp.plant(project, line, [row], store=store)
        self.assertEqual(len(added), round(12 / hp.spacing_of(row)))
        plants = hp.plants_of(project, "h1")
        self.assertEqual(len(plants), len(added))
        for f in plants:
            props = f["properties"]
            self.assertEqual(props["placement_group_id"], "h1")
            self.assertEqual(props["pattern_kind"], hp.PATTERN_KIND)
            self.assertIn("hedge you drew", props["why_here"][0])
        self.assertEqual(line["properties"]["plant_ids"], [row["id"]])
        self.assertEqual(line["properties"]["num_plants"], len(added))
        self.assertEqual(store.check_consistency(), [])
        self.assertEqual(hp.planted(project), {"h1"})
        self.assertEqual(hp.unplanted(project), [])

    def test_planting_again_replaces_its_plants(self):
        from src.project_store import ProjectStore
        line = _line("hedge", [(0, 0), (12, 0)])
        project = _project(line)
        store = ProjectStore(project)
        hp.plant(project, line, [_by_name("Saskatoon Berry")], store=store)
        hp.plant(project, line, [_by_name("Common Snowberry")], store=store)
        names = {f["properties"]["common_name"]
                 for f in hp.plants_of(project, "h1")}
        self.assertEqual(names, {"Common Snowberry"})
        self.assertEqual(len(store.placed_plants),
                         len(hp.plants_of(project, "h1")))
        self.assertEqual(store.check_consistency(), [])

    def test_removing_the_line_takes_its_plants_and_nothing_else(self):
        from src.project_store import ProjectStore
        a = _line("hedge", [(0, 0), (12, 0)], hid="a")
        b = _line("windbreak", [(0, 10), (20, 10)], hid="b")
        project = _project(a, b)
        store = ProjectStore(project)
        hp.plant(project, a, [_by_name("Saskatoon Berry")], store=store)
        hp.plant(project, b, [_by_name("White Spruce"),
                              _by_name("Chokecherry")], store=store)
        kept = len(hp.plants_of(project, "b"))
        removed = hp.remove(project, "a", store=store)
        self.assertGreater(len(removed), 0)
        self.assertIsNone(hp.line_by_id(project, "a"))
        self.assertEqual(hp.plants_of(project, "a"), [])
        self.assertEqual(len(hp.plants_of(project, "b")), kept)
        self.assertEqual(store.check_consistency(), [])

    def test_planted_is_read_from_its_plants(self):
        """Delete every plant by hand and the line is unplanted again."""
        from src.project_store import ProjectStore
        line = _line("hedge", [(0, 0), (6, 0)])
        project = _project(line)
        store = ProjectStore(project)
        hp.plant(project, line, [_by_name("Saskatoon Berry")], store=store)
        store.remove_plants_batch(
            (f["properties"]["plant_id"], f["geometry"]["coordinates"][1],
             f["geometry"]["coordinates"][0])
            for f in hp.plants_of(project, "h1"))
        self.assertEqual(hp.planted(project), set())
        self.assertEqual([f["properties"]["hedge_id"]
                          for f in hp.unplanted(project)], ["h1"])

    def test_a_fence_is_never_a_line_to_plant(self):
        project = _project(_line("fence", [(0, 0), (10, 0)], hid="f"))
        self.assertEqual(hp.unplanted(project), [])


class AnOldHedge(unittest.TestCase):
    """The owner's Q5: an old hedge is never planted on its own; its words
    are read against the region's list for the offer."""

    def _old(self, words, style="hedge"):
        f = _line(style, [(0, 0), (10, 0)])
        f["properties"].pop("kind", None)        # as a V3.71 design stored it
        f["properties"]["species"] = words
        return f

    def test_its_words_are_matched(self):
        for words, want in (("saskatoon", "Saskatoon Berry"),
                            ("Red osier dogwood", "Red Osier Dogwood"),
                            ("Amelanchier alnifolia", "Saskatoon Berry")):
            self.assertEqual(hp.match(self._old(words))["common_name"], want)
        self.assertIsNone(hp.match(self._old("lilac")))
        self.assertIsNone(hp.match(self._old("")))

    def test_the_match_goes_in_the_row_it_fits(self):
        f = self._old("spruce", "windbreak")
        got = hp.offer_choices(f)
        self.assertEqual(_plants.get_plant(got["tree"])["common_name"],
                         "White Spruce")
        f = self._old("dogwood", "windbreak")
        got = hp.offer_choices(f)
        self.assertEqual(_plants.get_plant(got["shrub"])["common_name"],
                         "Red Osier Dogwood")
        self.assertNotEqual(got["tree"], got["shrub"])

    def test_a_planted_line_reopens_with_its_own_plants(self):
        f = _line("living_fence", [(0, 0), (10, 0)], plant_ids=[249, 71])
        got = hp.offer_choices(f)
        self.assertEqual((got["shrub"], got["shrub_2"]), (249, 71))

    def test_the_overview_offers_it_and_plants_nothing(self):
        from src import yard_overview_items as yi
        from src.project_store import ProjectStore
        old = self._old("saskatoon")
        old["properties"]["hedge_id"] = "old1"
        project = _project(old)
        store = ProjectStore(project)
        store.add_plant(_by_name("Common Snowberry")["id"], "Common Snowberry",
                        *_P.to_latlng(5, 8))
        before = json.dumps(project, sort_keys=True)
        cover = next(it for it in yi.overview(project) if it.key == "cover")
        self.assertEqual(json.dumps(project, sort_keys=True), before)
        self.assertEqual((cover.action, cover.target),
                         ("Plant this hedge", "hedge:old1"))
        self.assertTrue(any("Saskatoon Berry matches" in line
                            for line in cover.lines), cover.lines)
        # With the yard outlined, the same offer beside the cover.
        ring = [_ll(-5, -5), _ll(15, -5), _ll(15, 15), _ll(-5, 15),
                _ll(-5, -5)]
        project["features"].append({
            "type": "Feature", "geometry": {"type": "Polygon",
                                            "coordinates": [ring]},
            "properties": {"element_type": "property_boundary"}})
        cover = next(it for it in yi.overview(project) if it.key == "cover")
        self.assertEqual(cover.target, "hedge:old1")
        self.assertTrue(cover.lines[0].startswith("Once grown"), cover.lines)
        # Planted, it is offered no more.
        hp.plant(project, old, [_by_name("Saskatoon Berry")], store=store)
        cover = next(it for it in yi.overview(project) if it.key == "cover")
        self.assertNotEqual(cover.target, "hedge:old1")


class SolidLinesCastShade(unittest.TestCase):
    """The owner's Q3: a wall and a board fence cast shade; a rail and a
    chain link fence let the light through."""

    def _fence(self, fence_kind):
        return _line("fence", [(-10, 0), (10, 0)], fence_kind=fence_kind)

    def test_which_lines_cast(self):
        from src import shade
        self.assertEqual(len(shade.casters_from_project(
            _project(self._fence("board")))), 1)
        for kind in ("rail", "chain_link"):
            self.assertEqual(shade.casters_from_project(
                _project(self._fence(kind))), [], kind)
        wall = shade.casters_from_project(
            _project(_line("wall", [(0, 0), (5, 0), (5, 5)])))
        self.assertEqual(len(wall), 2)                     # one a segment
        self.assertEqual({c["height_m"] for c in wall},
                         {yard_kinds.WALL_HEIGHT_M})
        hedge = _line("hedge", [(0, 0), (5, 0)])
        self.assertEqual(shade.casters_from_project(_project(hedge)), [])

    def test_the_ground_north_of_a_board_fence_is_shaded(self):
        from src import shade
        s, w = _P.to_latlng(-10, -10)
        n, e = _P.to_latlng(10, 10)
        elev = {"grid": [[0.0] * 20 for _ in range(20)], "rows": 20,
                "cols": 20, "bbox": {"south": s, "west": w, "north": n,
                                     "east": e}}
        board = shade.shade_grid_for_design(_project(self._fence("board")),
                                            elev, terrain=False)
        rail = shade.shade_grid_for_design(_project(self._fence("rail")),
                                           elev, terrain=False)
        north_of = [row[10] for row in board[:10]]      # row 0 is the north
        south_of = [row[10] for row in board[10:]]
        self.assertGreater(max(north_of), 0.5)
        self.assertEqual(max(south_of), 0.0)
        self.assertEqual(max(max(r) for r in rail), 0.0)

    def test_the_timeline_counts_it_as_a_fixed_caster(self):
        from src.succession_engine import static_casters_from_project
        self.assertEqual(len(static_casters_from_project(
            _project(self._fence("board")))), 1)

    def test_the_timeline_calls_it_a_fence(self):
        """Not "a building": the notes name what shades a plant."""
        from src import scene_timeline
        from src.succession_engine import (SuccessionEngine,
                                           static_casters_from_project)
        row = next(r for r in _plants.search_plants(plant_type="wildflower")
                   if r.get("sun_requirement") == "full_sun")
        lat, lng = _P.to_latlng(0, 1.0)              # a metre north of it
        engine = SuccessionEngine(
            [{"plant_id": row["id"], "lat": lat, "lng": lng}],
            static_casters=static_casters_from_project(
                _project(self._fence("board"))), origin=(_LAT, _LNG))
        shader = engine.main_shader(0, 3)
        self.assertEqual(shader["what"], "fence")
        self.assertEqual(scene_timeline.shader_words(shader, [], [], None,
                                                     None), "the fence")

    def test_the_3d_and_the_shade_read_one_height(self):
        from src import scene_kinds, scene_site
        self.assertIs(scene_kinds.FENCE_HEIGHT_M, yard_kinds.FENCE_HEIGHT_M)
        self.assertEqual(scene_site.LINE_HEIGHT_M["wall"],
                         yard_kinds.WALL_HEIGHT_M)
        self.assertEqual(yard_kinds.shade_height(self._fence("board")),
                         yard_kinds.FENCE_HEIGHT_M["board"])


class In3D(unittest.TestCase):

    def test_a_planted_line_draws_nothing_an_old_one_still_does(self):
        from src import scene_site
        from src.project_store import ProjectStore
        planted = _line("hedge", [(0, 0), (10, 0)], hid="p")
        old = _line("hedge", [(0, 5), (10, 5)], hid="o")
        fence = _line("fence", [(0, 9), (10, 9)], hid="f")
        project = _project(planted, old, fence)
        hp.plant(project, planted, [_by_name("Saskatoon Berry")],
                 store=ProjectStore(project))
        kinds = [row["kind"] for row in scene_site.lines(project, _P)]
        self.assertEqual(sorted(kinds), ["fence", "hedge"])


def _fake_main(project):
    """A window with a real store over ``project`` and nothing else real."""
    from src.project_store import ProjectStore
    main = mock.MagicMock()
    main._project = project
    main._store = ProjectStore(project)
    main._plant_info.return_value = (1.0, "shrub", None)
    return main


class TheWindow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PyQt6.QtWidgets import QApplication
        except ImportError:                              # pragma: no cover
            raise unittest.SkipTest("no PyQt6")
        cls.app = QApplication.instance() or QApplication(["hedge-tests"])

    def test_a_line_drawn_with_plants_is_planted_in_one_step(self):
        from src.controllers.map_events import MapEventRouter
        main = _fake_main(_project())
        row = _by_name("Saskatoon Berry")
        main._hedge_config = {"kind": "hedge", "style": "hedge",
                              "plant_ids": [row["id"]], "color": "#4caf50"}
        pts = [_P.to_latlng(0, 0), _P.to_latlng(10, 0)]
        MapEventRouter(main)._on_hedgerow_complete(
            "h9", json.dumps([list(p) for p in pts]), "", "hedge", 10.0, 0)
        # One checkpoint around the line and its plants.
        main._persistence.checkpoint.assert_called_once()
        plants = hp.plants_of(main._project, "h9")
        self.assertEqual(len(plants), round(10 / hp.spacing_of(row)))
        self.assertEqual(main.map_widget.place_plant_marker.call_count,
                         len(plants))
        line = main.map_widget.load_hedgerow.call_args[0][0]
        self.assertEqual((line["hedge_id"], line["plants"], line["living"]),
                         ("h9", len(plants), True))

    def test_removing_the_line_takes_its_plants(self):
        from src.controllers.map_events import MapEventRouter
        line = _line("hedge", [(0, 0), (10, 0)], hid="h7")
        main = _fake_main(_project(line))
        hp.plant(main._project, line, [_by_name("Saskatoon Berry")],
                 store=main._store)
        MapEventRouter(main)._on_hedgerow_removed("h7", "[]")
        self.assertEqual(main._project["features"], [])
        self.assertEqual(main._store.placed_plants, [])
        main._persistence.redraw.assert_called_once()

    def test_plant_this_hedge_asks_and_plants_the_answer(self):
        from src import hedge_flow
        line = _line("hedge", [(0, 0), (10, 0)], hid="h5")
        line["properties"].update({"species": "saskatoon"})
        main = _fake_main(_project(line))
        seen = {}

        def _answer(dialog):
            seen["first"] = dialog.lists["shrub"].currentText()
            dialog._accept()
            return 1

        with mock.patch.object(hedge_flow, "_exec", _answer):
            n = hedge_flow.offer(main, "h5")
        self.assertEqual(seen["first"], "Saskatoon Berry")
        self.assertGreater(n, 0)
        self.assertEqual({f["properties"]["common_name"]
                          for f in hp.plants_of(main._project, "h5")},
                         {"Saskatoon Berry"})
        main._persistence.checkpoint.assert_called_once()

    def test_cancel_plants_nothing(self):
        from src import hedge_flow
        line = _line("hedge", [(0, 0), (10, 0)], hid="h6")
        main = _fake_main(_project(line))
        with mock.patch.object(hedge_flow, "_exec", lambda d: 0):
            self.assertEqual(hedge_flow.offer(main, "h6"), 0)
        self.assertEqual(hp.plants_of(main._project, "h6"), [])


if __name__ == "__main__":
    unittest.main()
