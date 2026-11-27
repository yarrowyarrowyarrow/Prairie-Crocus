"""
tests/test_yard_palette.py — Placement › Yard (V3.72, F280; replaces
tests/test_shape_tool.py and tests/test_structures_grouped.py, whose tools it
replaces).

One list under six headings; each kind's options as the owner answered them
(Q6); one verb a kind; what each verb hands the map, which the map's tools and
``map_events`` already take; and fences and hedges in the simple app (Q2).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src import yard_kinds as Y                                # noqa: E402

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication
    _HAVE_QT = True
except ImportError:                                        # pragma: no cover
    _HAVE_QT = False


class ThePaletteTable(unittest.TestCase):
    """Qt-free: the table the tab reads."""

    def test_every_kind_is_under_one_heading(self):
        listed = [k for _h, keys in Y.PALETTE for k in keys]
        self.assertEqual(len(listed), len(set(listed)))
        self.assertEqual(sorted(listed), sorted(k.key for k in Y.KINDS))
        self.assertEqual([h for h, _k in Y.PALETTE],
                         ["Beds and ground", "Water", "For wildlife",
                          "Fences and hedges", "Buildings",
                          "Around the yard"])

    def test_the_owners_surfaces(self):
        """Q6, answered "those surfaces are fine"."""
        path = Y.option(Y.BY_KEY["path"], "surface")
        patio = Y.option(Y.BY_KEY["patio"], "surface")
        self.assertEqual([w for _v, w in path.choices],
                         ["Flagstone", "Pavers", "Gravel", "Wood chips",
                          "Stepping stones"])
        self.assertEqual([w for _v, w in patio.choices],
                         ["Pavers", "Flagstone", "Concrete"])
        self.assertEqual(Y.BY_KEY["deck"].options, ())      # a deck is wood

    def test_the_height_box_is_only_on_a_building(self):
        """The V3.69 trap: a Garden Bed given a height drew as a building."""
        with_height = [k.key for k in Y.KINDS
                       if Y.option(k, "height_m") is not None]
        self.assertEqual(with_height, ["building"])
        raised = Y.option(Y.BY_KEY["bed"], "raised_cm")
        self.assertEqual([v for v, _w in raised.choices], [0, 30, 45, 60, 90])

    def test_only_custom_is_advanced(self):
        self.assertEqual([k.key for k in Y.KINDS if k.advanced], ["custom"])

    def test_every_drawn_kind_has_its_map_colours(self):
        for k in Y.KINDS:
            if k.verb == Y.AREA:
                self.assertEqual(len(k.colours), 4, k.key)
                self.assertTrue(k.legacy_shape, k.key)
            elif k.verb == Y.LINE:
                self.assertEqual(len(k.colours), 1, k.key)

    def test_a_drawn_kind_is_stored_once_one_way(self):
        props = Y.drawn_props("deck")
        self.assertEqual((props["kind"], props["shape_type"],
                          props["element_type"]),
                         ("deck", "Patio / Deck", "custom_shape"))
        house = Y.drawn_props("building", building="house")
        self.assertEqual((house["element_type"], house["height_m"],
                          house["shape_type"]),
                         ("canopy_footprint", 6.0, "Building"))
        self.assertTrue(Y.is_building_footprint(house))
        wall = Y.drawn_props("wall")
        self.assertEqual((wall["element_type"], wall["style"]),
                         ("hedgerow", "wall"))
        # The stored kind wins over the older copy's shape type.
        feature = {"properties": Y.drawn_props("native_lawn")}
        self.assertEqual(Y.kind_of(feature).key, "native_lawn")
        self.assertEqual(Y.look_of(feature), "young_meadow")


@unittest.skipUnless(_HAVE_QT, "PyQt6 not installed in this env")
class TheYardTab(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication(["yard-palette"])

    def setUp(self):
        from src.yard_palette import YardPalette
        self.p = YardPalette()
        self.addCleanup(self.p.deleteLater)
        self.sent = []
        self.p.draw_area_requested.connect(lambda d: self.sent.append(
            ("area", d)))
        self.p.draw_line_requested.connect(lambda d: self.sent.append(
            ("line", d)))
        self.p.place_object_requested.connect(lambda d: self.sent.append(
            ("object", d)))

    def _rows(self):
        return [self.p._list.item(i) for i in range(self.p._list.count())]

    def test_six_headings_that_cannot_be_chosen(self):
        heads = [r for r in self._rows()
                 if r.data(Qt.ItemDataRole.UserRole) is None]
        self.assertEqual([h.text() for h in heads],
                         [h for h, _k in Y.PALETTE])
        for h in heads:
            self.assertEqual(h.flags(), Qt.ItemFlag.NoItemFlags)

    def test_fences_and_hedges_are_in_the_simple_app(self):
        keys = {r.data(Qt.ItemDataRole.UserRole) for r in self._rows()}
        for key in ("fence", "wall", "hedge", "living_fence", "windbreak"):
            self.assertIn(key, keys)
        self.assertNotIn("custom", keys)
        self.p.set_advanced_tools(True)
        keys = {r.data(Qt.ItemDataRole.UserRole) for r in self._rows()}
        self.assertIn("custom", keys)

    def test_each_kind_says_its_verb(self):
        for key, verb in (("path", "Draw on the map"),
                          ("fence", "Draw on the map"),
                          ("bee_hotel", "Place on the map")):
            self.assertTrue(self.p.choose(key))
            self.assertEqual(self.p._verb.text(), verb, key)
            self.assertTrue(self.p._verb.isEnabled())

    def test_a_path_draws_with_its_surface(self):
        self.p.choose("path")
        self.p._inputs["surface"].setCurrentIndex(2)          # gravel
        self.p._verb.click()
        what, d = self.sent[-1]
        self.assertEqual(what, "area")
        self.assertEqual((d["kind"], d["surface"], d["shape_type"]),
                         ("path", "gravel", "Pathway"))
        self.assertEqual(d["height_m"], 0.0)

    def test_a_building_follows_what_it_is_until_changed(self):
        self.p.choose("building")
        what = self.p._inputs["building"]
        height = self.p._inputs["height_m"]
        what.setCurrentIndex(what.findData("house"))
        self.assertEqual(height.value(), 6.0)
        height.setValue(7.5)
        self.p._verb.click()
        _what, d = self.sent[-1]
        self.assertEqual((d["kind"], d["building"], d["height_m"]),
                         ("building", "house", 7.5))

    def test_a_fence_draws_a_line_of_its_kind(self):
        self.p.choose("fence")
        box = self.p._inputs["fence_kind"]
        box.setCurrentIndex(box.findData("board"))
        self.p._verb.click()
        what, d = self.sent[-1]
        self.assertEqual(what, "line")
        self.assertEqual((d["kind"], d["style"], d["fence_kind"]),
                         ("fence", "fence", "board"))

    def test_an_object_is_placed_at_its_size(self):
        self.p.choose("bee_hotel")
        size = self.p._inputs["size_m"]
        size.setValue(0.9)
        self.p._verb.click()
        what, d = self.sent[-1]
        self.assertEqual((what, d["id"], d["size_m"]),
                         ("object", "bee_hotel", 0.9))

    def test_a_raised_bed(self):
        self.p.choose("bed")
        raised = self.p._inputs["raised_cm"]
        raised.setCurrentIndex(raised.findData(60))
        self.p._verb.click()
        _what, d = self.sent[-1]
        self.assertEqual((d["kind"], d["raised_cm"], d["shape_type"]),
                         ("bed", 60, "Garden Bed"))

    def test_every_control_has_a_name(self):
        for key in [k.key for k in Y.KINDS if not k.advanced]:
            self.p.choose(key)
            for w in self.p._inputs.values():
                self.assertTrue(w.accessibleName(), key)


@unittest.skipUnless(_HAVE_QT, "PyQt6 not installed in this env")
class WhatTheMapHandlersStore(unittest.TestCase):
    """The palette's payload, through the mode stash and the map's finished
    callbacks, to the stored feature (no window: the controllers alone)."""

    def _main(self):
        from unittest import mock
        main = mock.MagicMock()
        main._project = {"features": []}
        return main

    def test_an_area_is_stored_with_its_kind(self):
        from src.controllers.map_events import MapEventRouter
        from src.controllers.mode import ModeController
        main = self._main()
        payload = {**Y.drawn_props("deck"), "label": "", "height_m": 0.0}
        payload.pop("element_type")
        ModeController(main)._enter_shape_mode(payload)
        MapEventRouter(main)._on_shape_complete(
            "s1", "[[53.5,-113.5],[53.5,-113.4999],[53.5001,-113.4999]]", "",
            "Patio / Deck", "#a1887f", "#6d4c41", 0.4, "", 6.0, 0.0)
        props = main._project["features"][-1]["properties"]
        self.assertEqual((props["element_type"], props["kind"]),
                         ("custom_shape", "deck"))

    def test_a_building_is_stored_as_a_shade_caster(self):
        from src.controllers.map_events import MapEventRouter
        from src.controllers.mode import ModeController
        main = self._main()
        payload = Y.drawn_props("building", building="garage")
        payload.pop("element_type")
        ModeController(main)._enter_shape_mode(payload)
        MapEventRouter(main)._on_shape_complete(
            "s1", "[[53.5,-113.5],[53.5,-113.4999],[53.5001,-113.4999]]", "",
            "Building", "#8d6e63", "#5d4037", 0.3, "", 6.0, 4.0)
        props = main._project["features"][-1]["properties"]
        self.assertEqual((props["element_type"], props["kind"],
                          props["building"], props["height_m"]),
                         ("canopy_footprint", "building", "garage", 4.0))
        self.assertTrue(props["cast_shade"])
        self.assertGreater(props["canopy_radius_m"], 0)

    def test_an_area_from_site_features_is_not_given_a_kind(self):
        """Site › Features' building outline arms the same tool."""
        from src.controllers.map_events import MapEventRouter
        from src.controllers.mode import ModeController
        main = self._main()
        ModeController(main)._enter_shape_mode(
            {"shape_type": "Building footprint", "height_m": 5.0})
        MapEventRouter(main)._on_shape_complete(
            "s1", "[[53.5,-113.5],[53.5,-113.4999],[53.5001,-113.4999]]", "",
            "Building footprint", "#8d6e63", "#5d4037", 0.3, "", 6.0, 5.0)
        props = main._project["features"][-1]["properties"]
        self.assertNotIn("kind", props)
        self.assertEqual(props["element_type"], "canopy_footprint")

    def test_a_line_is_stored_with_its_kind(self):
        from src.controllers.map_events import MapEventRouter
        from src.controllers.mode import ModeController
        main = self._main()
        ModeController(main)._enter_hedgerow_mode(
            {**Y.drawn_props("fence", fence_kind="chain_link"),
             "width_m": 0.3})
        MapEventRouter(main)._on_hedgerow_complete(
            "h1", "[[53.5,-113.5],[53.5,-113.4999]]", "", "fence", 7.0, 0)
        props = main._project["features"][-1]["properties"]
        self.assertEqual((props["kind"], props["fence_kind"]),
                         ("fence", "chain_link"))


if __name__ == "__main__":
    unittest.main()
