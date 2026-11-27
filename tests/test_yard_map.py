"""
tests/test_yard_map.py — the Yard palette on the real map (V3.72, F280).

Boots ``html/map.html`` in headless Chromium through ``html/yard_map_probe.html``
(the harness ``tests/test_boundary_press.py`` uses) and checks:

* **a saved line is drawn without telling Python it was drawn.** Until V3.72
  ``loadHedgerow`` went through ``finishHedgerow``, which sent
  ``onHedgerowComplete``: every open added a copy of each hedge and fence to the
  design and marked it changed. Measured on V3.71's map, before the fix: one
  call for one saved fence. The line keeps its stored id, so a right-click on it
  after a reopen removes it, not a copy;
* a line drawn by hand is still told to Python, once;
* a placed object is dragged (its move reported with where it was), turned 45°
  from its right-click menu (which no longer removes at once) and by R with the
  pointer over it, and a turned rectangle is drawn turned, including one loaded
  from a design;
* an existing building mark still removes on a right-click.

Self-skips with no Chromium.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_boundary_press import _run_probe                # noqa: E402
from tests.test_scene3d_render import _find_chromium            # noqa: E402


@unittest.skipIf(_find_chromium() is None,
                 "no Chromium binary (set CHROME= to run this gate)")
class TheYardOnTheMap(unittest.TestCase):
    m = None

    @classmethod
    def setUpClass(cls):
        cls.m = _run_probe("yard_map_probe.html")
        if "error" in cls.m:
            raise AssertionError(cls.m["error"])

    def test_a_saved_line_is_not_sent_back(self):
        self.assertEqual(self.m["load_line"]["complete_sent"], 0)
        self.assertTrue(self.m["load_line"]["kept_id"])
        self.assertEqual(self.m["load_line"]["layers"], 1)

    def test_a_drawn_line_is_sent_once(self):
        self.assertEqual(self.m["draw_line"], {"sent": 1, "style": "wall"})

    def test_an_object_is_dragged(self):
        self.assertEqual(self.m["placed"]["bearing"], 0)
        drag = self.m["drag"]
        self.assertEqual(drag["sent"], 1)
        self.assertAlmostEqual(drag["from_lat"], 53.5461, places=5)
        self.assertAlmostEqual(drag["east_m"], 2.0, delta=0.2)

    def test_its_menu_turns_it(self):
        self.assertTrue(self.m["menu"]["turn"])
        self.assertTrue(self.m["menu"]["remove"])
        self.assertEqual(self.m["menu"]["removed_at_once"], 0)
        self.assertEqual(self.m["turn_menu"],
                         {"sent": 1, "bearing": 45, "drawn": 45})

    def test_r_turns_the_one_under_the_pointer(self):
        key = self.m["turn_key"]
        self.assertTrue(key["turned"])
        self.assertEqual((key["bearing"], key["drawn"]), (90, 90))
        self.assertFalse(key["away"])

    def test_a_turned_one_is_drawn_turned_on_open(self):
        self.assertEqual(self.m["loaded_turned"]["bearing"], 90)

    def test_an_existing_building_still_removes(self):
        self.assertEqual(self.m["existing"]["removed"], 1)


class TheTurnIsStored(unittest.TestCase):
    """The Python side of a turn and a move (no browser)."""

    def _main(self):
        from unittest import mock
        main = mock.MagicMock()
        main._persistence = None
        main._project = {"features": [{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-113.5, 53.5]},
            "properties": {"element_type": "structure",
                           "struct_id": "bee_hotel",
                           "struct_def": {"id": "bee_hotel", "size_m": 0.6,
                                          "width_m": 0.3,
                                          "shape": "rectangle"}}}]}
        return main

    def test_a_turn_is_stored_and_read_everywhere(self):
        from src import tree_edit_flow, yard_kinds
        from src.project import project_to_map_data
        from src.scene_structures import footprint
        main = self._main()
        tree_edit_flow.on_structure_turned(main, "m1", "bee_hotel", 53.5,
                                           -113.5, 405.0)
        props = main._project["features"][0]["properties"]
        self.assertEqual(props["bearing_deg"], 45.0)
        main._mark_modified.assert_called_once()
        self.assertEqual(footprint(props)["bearing_deg"], 45.0)
        sd = project_to_map_data(main._project)["structures"][0]["struct_def"]
        self.assertEqual(sd["bearing_deg"], 45.0)
        ring = yard_kinds.footprint_ring(main._project["features"][0])
        self.assertEqual(len(ring), 5)

    def test_an_object_moves(self):
        from src import tree_edit_flow
        main = self._main()
        tree_edit_flow.on_existing_feature_moved(main, "m1", "bee_hotel",
                                                 53.5, -113.5, 53.5001,
                                                 -113.4999)
        self.assertEqual(
            main._project["features"][0]["geometry"]["coordinates"],
            [-113.4999, 53.5001])

    def test_the_scene_turns_the_model(self):
        from src.scene_structures import record
        props = self._main()._project["features"][0]["properties"]
        props["bearing_deg"] = 90.0
        self.assertEqual(record(props, 0, 0)["bearing_deg"], 90.0)


if __name__ == "__main__":
    unittest.main()
