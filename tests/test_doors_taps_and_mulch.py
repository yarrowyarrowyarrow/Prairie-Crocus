"""
tests/test_doors_taps_and_mulch.py — doors, downspouts, spigots and mulch
rings (V3.76; ``docs/plans/V3.76-doors-taps-and-mulch-rings.md``).

The owner: doors, downspouts and mulch rings (the V3.71 plan's last
increment), "mulch rings off by default but available not only in the plan my
yard mode but in planting you do yourself", and "spigots to the water work as
many will be using city water". Holds:

* a wall object goes onto the nearest building's wall (``src/wall_objects.py``),
  on the outside, along it, slid in from a corner, and stands where it was
  clicked far from every wall; the map handler stores it so;
* a door keeps its doorstep clear and is where *From the house* stands;
* the Water page's spigot line: the reach of a garden hose and the minutes at
  the tap;
* mulch rings: off unless asked for, the plan's box, the placing box and the
  right-click menu each setting a plant's own ``mulch_ring``; none drawn in a
  bed; their mulch in every mulch figure, counted once; kept through a swap.
"""

import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_TMP = tempfile.mkdtemp(prefix="doors_taps_mulch_")
import src.db.plants as _plants  # noqa: E402
_plants._DATA_DIR = _TMP
_plants._DB_PATH = os.path.join(_TMP, "permadesign_test.db")

from src import mulch_rings as M  # noqa: E402
from src import wall_objects as W  # noqa: E402
from src import water_budget as WB  # noqa: E402
from src import yard_kinds as Y  # noqa: E402
from src.db.structures import get_structure  # noqa: E402
from src.project_store import ProjectStore  # noqa: E402
from src.projection import Projector  # noqa: E402

_P = Projector(53.5461, -113.4938)


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


def _house():
    """A 10 x 8 m house, its south wall on y = 0."""
    return {"type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[
                _ll(0, 0), _ll(10, 0), _ll(10, 8), _ll(0, 8), _ll(0, 0)]]},
            "properties": Y.drawn_props("building", building="house")}


def _project(*features):
    return {"type": "FeatureCollection", "features": list(features),
            "properties": {}}


def _placed(project, sid, x, y):
    sd = dict(get_structure(sid))
    props = {"element_type": "structure", "struct_id": sid,
             "name": sd["name"], "size_m": sd["size_m"], "struct_def": sd}
    lat, lng = W.place(project, props, *_P.to_latlng(x, y))
    f = {"type": "Feature",
         "geometry": {"type": "Point", "coordinates": [lng, lat]},
         "properties": props}
    project["features"].append(f)
    return f


class TheWallObjects(unittest.TestCase):

    def test_in_the_table_and_the_palette(self):
        self.assertIn("door", dict(Y.PALETTE)["Buildings"])
        for key in ("downspout", "spigot"):
            self.assertIn(key, dict(Y.PALETTE)["Water"])
        for sid in ("door", "downspout", "spigot"):
            self.assertTrue(get_structure(sid)["on_wall"], sid)
        self.assertTrue(Y.is_door("door"))
        self.assertFalse(Y.is_door("spigot"))
        self.assertEqual(Y.BY_KEY["door"].planting, Y.KEEP_OUT)

    def test_onto_the_nearest_wall_outside_along_it(self):
        project = _project(_house())
        door = get_structure("door")
        out_m = door["width_m"] / 2 + W.WALL_GAP_M
        for click in ((5, -1.5), (5, 1.0)):             # outside, inside
            got = W.snap(project, *_P.to_latlng(*click), door)
            x, y = _xy(got["lat"], got["lng"])
            self.assertAlmostEqual(x, 5.0, delta=0.01)
            self.assertAlmostEqual(y, -out_m, delta=0.01)
            self.assertEqual((got["bearing_deg"], got["facing_deg"]),
                             (90.0, 180.0))
            self.assertEqual(got["wall_h_m"], Y.BUILDING_HEIGHT_M["house"])

    def test_slid_in_from_a_corner_and_free_far_from_a_wall(self):
        project = _project(_house())
        door = get_structure("door")
        got = W.snap(project, *_P.to_latlng(-0.5, 9.0), door)
        x, _y = _xy(got["lat"], got["lng"])
        self.assertAlmostEqual(x, door["size_m"] / 2, delta=0.01)
        self.assertIsNone(W.snap(project, *_P.to_latlng(20, 20), door))
        self.assertIsNone(W.snap(_project(), *_P.to_latlng(0, 0), door))

    def test_the_doorstep_is_kept_clear(self):
        from src import exclusion
        project = _project(_house())
        _placed(project, "door", 5, -1)
        door_f = project["features"][-1]
        self.assertTrue(Y.is_keep_out(door_f))
        ring = Y.footprint_ring(door_f)
        ys = [_xy(p[1], p[0])[1] for p in ring]
        gap = W.WALL_GAP_M
        self.assertAlmostEqual(max(ys), -gap, delta=0.02)   # at the wall
        self.assertAlmostEqual(min(ys), -1.2 - gap, delta=0.02)  # 1.2 m out
        self.assertTrue(exclusion.keepout_areas(project))

    def test_the_map_handler_puts_it_on_the_wall(self):
        from src.controllers.map_events import MapEventRouter
        main = mock.MagicMock()
        main._project = _project(_house())
        lat, lng = _P.to_latlng(11.5, 4.0)               # off the east wall
        MapEventRouter(main)._on_structure_placed("spigot", "Spigot", lat,
                                                  lng, 0.3)
        f = main._project["features"][-1]
        x, y = _xy(f["geometry"]["coordinates"][1],
                   f["geometry"]["coordinates"][0])
        self.assertAlmostEqual(x, 10 + 0.15 + W.WALL_GAP_M, delta=0.01)
        self.assertAlmostEqual(y, 4.0, delta=0.01)
        self.assertEqual(f["properties"]["facing_deg"], 90.0)
        # The map is told to draw it where it stands.
        main.map_widget.load_structure.assert_called_once()

    def test_the_house_view_stands_at_the_door(self):
        from src import scene_views
        project = _project(_house())
        door = _placed(project, "door", 5, -1)
        from src.scene_structures import record
        lat, lng = door["geometry"]["coordinates"][1], \
            door["geometry"]["coordinates"][0]
        rec = record(door["properties"], *_xy(lat, lng))
        house = [_xy(p[1], p[0]) for p in
                 project["features"][0]["geometry"]["coordinates"][0][:-1]]
        plants = [{"x": 5.0, "y": -8.0, "plant_id": 1}]
        view = scene_views.house_view(None, plants, [
            {"ring": [list(p) for p in house], "kind": "building",
             "height_m": 6.0}], pin=(5.0, 4.0), doors=[rec])
        self.assertTrue(view and view.get("at_door"), view)
        self.assertAlmostEqual(view["eye"][0], 5.0, delta=0.02)
        self.assertLess(view["eye"][1], 0.0)            # out of the door
        self.assertLess(view["look"][1], view["eye"][1])  # at the planting


class TheSpigot(unittest.TestCase):

    def test_reach_from_the_nearest_tap(self):
        project = _project(_house())
        _placed(project, "spigot", 5, -1)
        store = ProjectStore(project)
        for x, y in ((5, -5), (5, -20), (5, -30)):
            store.add_plant(1, "A", *_P.to_latlng(x, y))
        reach = WB.tap_reach(project)
        self.assertEqual(reach["taps"], 1)
        self.assertEqual([round(m) for m in sorted(reach["metres"])],
                         [5, 20, 30])

    def test_the_words(self):
        plants = [{"plant_type": "shrub", "water_needs": "medium"}] * 4
        words = WB.tap_words({"taps": 1, "metres": [5, 20, 30]}, plants)
        self.assertIn("farthest plant is 30 m away in a straight line", words)
        self.assertIn("reaches 1 of 3 plants", words)
        self.assertIn("one 2.", words)
        self.assertIn("minutes at the tap", words)
        self.assertIn("No spigot is on the map",
                      WB.tap_words({"taps": 0, "metres": []}, plants))
        self.assertEqual(WB.tap_words({"taps": 0, "metres": []}, []), "")


def _yard_with_bed():
    bed = {"type": "Feature",
           "geometry": {"type": "Polygon", "coordinates": [[
               _ll(1, 1), _ll(5, 1), _ll(5, 4), _ll(1, 4), _ll(1, 1)]]},
           "properties": Y.drawn_props("bed")}
    outline = {"type": "Feature",
               "geometry": {"type": "Polygon", "coordinates": [[
                   _ll(0, 0), _ll(20, 0), _ll(20, 20), _ll(0, 20),
                   _ll(0, 0)]]},
               "properties": {"element_type": "property_boundary"}}
    return _project(outline, bed)


def _row(kind, wide):
    for r in _plants.search_plants(plant_type=kind):
        s = float(r.get("spacing_meters") or 0)
        if (s >= 2.0) if wide else (0 < s < 0.4):
            return r
    raise AssertionError(kind)


class MulchRings(unittest.TestCase):

    def test_off_unless_asked(self):
        store = ProjectStore(_project())
        store.add_plant(1, "A", 53.5, -113.5)
        self.assertNotIn("mulch_ring", store.features[0]["properties"])
        store.mulch_new_plants = True                  # the placing box
        store.add_plant(1, "B", 53.6, -113.5)
        store.add_plant(1, "C", 53.7, -113.5, mulch_ring=False)  # a walk
        self.assertEqual([p.get("mulch_ring") for p in store.placed_plants],
                         [None, True, None])
        self.assertEqual(store.check_consistency(), [])

    def test_a_ring_is_about_the_plants_spacing(self):
        self.assertEqual(M.ring_diameter_m({"spacing_meters": 0.2}),
                         M.RING_M[0])
        self.assertEqual(M.ring_diameter_m({"spacing_meters": 1.0}), 1.0)
        self.assertEqual(M.ring_diameter_m({"spacing_meters": 5.0}),
                         M.RING_M[1])
        self.assertEqual(M.ring_diameter_m({}), M.RING_M[0])

    def test_none_drawn_in_a_bed_and_its_mulch_counted_once(self):
        from src.yard_overview import bed_area_m2
        project = _yard_with_bed()
        store = ProjectStore(project)
        store.mulch_new_plants = True
        shrub, herb = _row("shrub", True), _row("wildflower", False)
        store.add_plant(shrub["id"], "S", *_P.to_latlng(10, 10))
        store.add_plant(shrub["id"], "S", *_P.to_latlng(10.5, 10))  # overlap
        store.add_plant(herb["id"], "H", *_P.to_latlng(3, 2))       # in bed
        rings = M.rings(project)
        self.assertEqual([r["shown"] for r in rings], [True, True, False])
        area = M.ring_area_m2(project)
        one = 3.14159 * (M.RING_M[1] / 2) ** 2
        self.assertGreater(area, one)
        self.assertLess(area, 2 * one)                   # overlap counted once
        self.assertAlmostEqual(M.mulch_area_m2(project),
                               bed_area_m2(project) + area, places=6)

    def test_the_overview_buys_mulch_for_rings_alone(self):
        from src import yard_overview_items as yi
        project = _project(
            {"type": "Feature",
             "geometry": {"type": "Polygon", "coordinates": [[
                 _ll(0, 0), _ll(20, 0), _ll(20, 20), _ll(0, 20), _ll(0, 0)]]},
             "properties": {"element_type": "property_boundary"}},
            {"type": "Feature",
             "geometry": {"type": "Polygon", "coordinates": [[
                 _ll(0, 0), _ll(20, 0), _ll(20, 20), _ll(0, 20), _ll(0, 0)]]},
             "properties": Y.drawn_props("lawn")})
        store = ProjectStore(project)
        shrub = _row("shrub", True)
        store.add_plant(shrub["id"], "S", *_P.to_latlng(10, 10))
        line = lambda: next(it for it in yi.overview(project)  # noqa: E731
                            if it.key == "cost").lines[0]
        self.assertNotIn("Mulch", line())
        store.set_mulch_rings([(shrub["id"], *_P.to_latlng(10, 10))], True)
        self.assertIn("Mulch", line())

    def test_the_3d_gets_the_drawn_rings(self):
        from src import scene_site
        project = _yard_with_bed()
        store = ProjectStore(project)
        store.mulch_new_plants = True
        store.add_plant(_row("shrub", True)["id"], "S", *_P.to_latlng(10, 10))
        store.add_plant(_row("wildflower", False)["id"], "H",
                        *_P.to_latlng(3, 2))
        rings = scene_site.site_fields(project, _P, None, [])["mulch_rings"]
        self.assertEqual(len(rings), 1)
        x, y, r = rings[0]
        self.assertAlmostEqual(x, 10.0, delta=0.01)
        self.assertAlmostEqual(r, M.RING_M[1] / 2)


class TheWindowsSide(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PyQt6.QtWidgets import QApplication
        except ImportError:                              # pragma: no cover
            raise unittest.SkipTest("no PyQt6")
        cls.app = QApplication.instance() or QApplication(["mulch-tests"])

    def _main(self):
        project = _yard_with_bed()
        main = mock.MagicMock()
        main._project = project
        main._store = ProjectStore(project)
        return main

    def test_the_menu_rings_one_plant_or_its_group_in_one_step(self):
        from src import mulch_rings_flow
        main = self._main()
        for x in (8, 9, 10):
            main._store.add_plant(5, "S", *_P.to_latlng(x, 10),
                                  placement_group_id="g1")
        lat, lng = _P.to_latlng(8, 10)
        self.assertEqual(mulch_rings_flow.toggle(main, 5, lat, lng, "", True),
                         1)
        self.assertEqual(mulch_rings_flow.toggle(main, 5, lat, lng, "g1",
                                                 True), 2)
        self.assertEqual(sum(bool(p.get("mulch_ring"))
                             for p in main._store.placed_plants), 3)
        self.assertEqual(main._persistence.checkpoint.call_count, 2)
        main.map_widget.set_mulch_rings.assert_called()

    def test_the_placing_box_is_off_and_sets_the_store(self):
        from PyQt6.QtCore import QSettings
        from src import mulch_rings_flow
        QSettings().remove(mulch_rings_flow.SETTINGS_KEY)
        main = self._main()
        main.placement_bar = None
        box = mulch_rings_flow.install(main)
        self.addCleanup(box.deleteLater)
        self.addCleanup(lambda: QSettings().remove(
            mulch_rings_flow.SETTINGS_KEY))
        self.assertFalse(box.isChecked())
        self.assertFalse(main._store.mulch_new_plants)
        box.setChecked(True)
        self.assertTrue(main._store.mulch_new_plants)
        self.assertTrue(mulch_rings_flow.placing_on())

    def test_a_swap_keeps_the_ring(self):
        from src import yard_overview_dialogs
        main = self._main()
        main._store.add_plant(5, "S", *_P.to_latlng(10, 10), mulch_ring=True)
        main._store.add_plant(5, "S", *_P.to_latlng(12, 10))
        yard_overview_dialogs.replace(main, 5, 6)
        self.assertEqual(sorted((p["plant_id"], bool(p.get("mulch_ring")))
                                for p in main._store.placed_plants),
                         [(6, False), (6, True)])

    def test_the_plan_asks_and_remembers(self):
        from src.generate_design_dialog import GenerateDesignDialog
        dlg = GenerateDesignDialog(has_boundary=True, has_pin=True,
                                   mulch_rings=True)
        self.addCleanup(dlg.deleteLater)
        self.assertTrue(dlg.mulch_rings())
        dlg2 = GenerateDesignDialog(has_boundary=True, has_pin=True)
        self.addCleanup(dlg2.deleteLater)
        self.assertFalse(dlg2.mulch_rings())


if __name__ == "__main__":
    unittest.main()
