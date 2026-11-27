"""
tests/test_yard_palette.py — Placement › Yard (V3.72, F280; replaces
tests/test_shape_tool.py and tests/test_structures_grouped.py, whose tools it
replaces).

One list under six headings; each kind's options as the owner answered them
(Q6); one verb a kind; what each verb hands the map, which the map's tools and
``map_events`` already take; and fences and hedges in the simple app (Q2).
"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# A hedge's plant lists read the catalogue (V3.74): never the person's own.
_TMP = tempfile.mkdtemp(prefix="yard_palette_")
import src.db.plants as _plants                                # noqa: E402
_plants._DATA_DIR = _TMP
_plants._DB_PATH = os.path.join(_TMP, "permadesign_test.db")

from src import yard_kinds as Y                                # noqa: E402


def setUpModule():
    _plants._DATA_DIR = _TMP
    _plants._DB_PATH = os.path.join(_TMP, "permadesign_test.db")
    _plants.init_db()


def tearDownModule():
    shutil.rmtree(_TMP, ignore_errors=True)

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QColor
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
        # V3.75: the lawn's conversion stages are their own group.
        self.assertEqual([h for h, _k in Y.PALETTE],
                         ["Beds and ground", "Lawn conversion", "Water",
                          "For wildlife", "Fences and hedges", "Buildings",
                          "Around the yard"])

    def test_a_hedge_is_one_already_growing(self):
        """V3.75, the owner: the living fence and the windbreak planted rows,
        which the Plants tab's Row does; a hedge is one already there."""
        self.assertEqual(dict(Y.PALETTE)["Fences and hedges"],
                         ("fence", "wall", "hedge"))
        self.assertNotIn("living_fence", Y.BY_KEY)
        self.assertNotIn("windbreak", Y.BY_KEY)
        self.assertEqual([v for v, _w in Y.HEDGE_KINDS],
                         ["cotoneaster", "caragana", "lilac", "cedar",
                          "other"])

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

    def test_the_height_box_is_only_on_a_building_and_a_hedge(self):
        """The V3.69 trap: a Garden Bed given a height drew as a building. A
        hedge's height is what it shades from (V3.75)."""
        with_height = [k.key for k in Y.KINDS
                       if Y.option(k, "height_m") is not None]
        self.assertEqual(with_height, ["building", "hedge"])
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

    def _kinds(self):
        return [head.child(i).data(0, Qt.ItemDataRole.UserRole)
                for head in self.p.groups() for i in range(head.childCount())]

    def test_seven_groups_closed_that_cannot_be_chosen(self):
        """V3.75, the owner: "a bit messy ... some collapsing groupings"."""
        heads = self.p.groups()
        self.assertEqual([h.data(0, Qt.ItemDataRole.AccessibleTextRole)
                          for h in heads], [h for h, _k in Y.PALETTE])
        for h, (_words, keys) in zip(heads, Y.PALETTE):
            self.assertFalse(h.isExpanded())
            self.assertFalse(h.flags() & Qt.ItemFlag.ItemIsSelectable)
            shown = [k for k in keys if not Y.BY_KEY[k].advanced]
            self.assertTrue(h.text(0).endswith(f"({len(shown)})"), h.text(0))

    def test_a_click_opens_a_group_and_choosing_a_kind_opens_its_own(self):
        head = self.p.groups()[2]                       # Water
        self.p._on_clicked(head)
        self.assertTrue(head.isExpanded())
        self.p._on_clicked(head)
        self.assertFalse(head.isExpanded())
        self.assertTrue(self.p.choose("rain_garden"))
        self.assertTrue(head.isExpanded())
        self.assertEqual(self.p.kind().key, "rain_garden")

    def test_fences_and_hedges_are_in_the_simple_app(self):
        keys = set(self._kinds())
        for key in ("fence", "wall", "hedge"):
            self.assertIn(key, keys)
        self.assertNotIn("custom", keys)
        self.p.set_advanced_tools(True)
        self.assertIn("custom", set(self._kinds()))

    def test_every_row_highlights_alike(self):
        """The owner: "only every 2nd item on the yard list highlights". The
        alternate rows' colour had been declared after the chosen one's."""
        from src.yard_palette import LIST_STYLE
        self.assertNotIn("alternate", LIST_STYLE)
        self.assertFalse(self.p._list.alternatingRowColors())
        self.p.resize(320, 700)
        self.p.show()
        self.addCleanup(self.p.hide)
        colours = []
        for key in ("bed", "mulch", "lawn", "path"):     # rows 1 to 4
            self.p.choose(key)
            QApplication.processEvents()
            rect = self.p._list.visualItemRect(self.p._list.currentItem())
            image = self.p._list.viewport().grab().toImage()
            colours.append(image.pixelColor(rect.right() - 6,
                                            rect.center().y()).name())
        self.assertEqual(len(set(colours)), 1, colours)
        got, want = QColor(colours[0]), QColor("#2e6a36")
        for a, b in ((got.red(), want.red()), (got.green(), want.green()),
                     (got.blue(), want.blue())):
            self.assertLessEqual(abs(a - b), 3, colours[0])

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

    def test_a_hedge_is_what_it_is_at_its_size(self):
        """V3.75: what an existing hedge is, its height and width, which
        follow what it is until changed; no plants are chosen."""
        from PyQt6.QtWidgets import QComboBox
        self.p.choose("hedge")
        self.assertEqual(list(self.p._inputs),
                         ["hedge_kind", "height_m", "width_m"])
        what = self.p._inputs["hedge_kind"]
        self.assertIsInstance(what, QComboBox)
        what.setCurrentIndex(what.findData("caragana"))
        self.assertEqual((self.p._inputs["height_m"].value(),
                          self.p._inputs["width_m"].value()),
                         Y.HEDGE_SIZE_M["caragana"])
        self.p._inputs["height_m"].setValue(3.2)
        self.p._verb.click()
        what_, d = self.sent[-1]
        self.assertEqual(what_, "line")
        self.assertEqual((d["kind"], d["hedge_kind"], d["height_m"],
                          d["color"]),
                         ("hedge", "caragana", 3.2,
                          Y.HEDGE_COLOURS["caragana"]))
        self.assertNotIn("plant_ids", d)

    def test_an_area_is_placed_as_its_outline_a_rectangle_or_a_circle(self):
        """V3.75, the owner: "a few options, like circle, rectangle (where you
        put the dimensions), in addition to the fill area manner"."""
        self.p.choose("bed")
        place = self.p._shape["place"]
        self.assertEqual([place.itemData(i) for i in range(place.count())],
                         ["outline", "rectangle", "circle"])
        self.p._verb.click()
        self.assertEqual(self.sent[-1][1]["place"], "outline")
        form = self.p._form
        place.setCurrentIndex(place.findData("rectangle"))
        self.assertTrue(form.isRowVisible(self.p._shape["length"]))
        self.assertFalse(form.isRowVisible(self.p._shape["across"]))
        self.p._shape["length"].setValue(4.0)
        self.p._verb.click()
        d = self.sent[-1][1]
        self.assertEqual((d["place"], d["place_length_m"], d["place_width_m"]),
                         ("rectangle", 4.0, Y.SHAPE_SIZE_M["bed"][1]))
        # The choice carries to the next area; a circle needs only its width
        # across.
        self.p.choose("pond")
        place = self.p._shape["place"]
        self.assertEqual(place.currentData(), "rectangle")
        place.setCurrentIndex(place.findData("circle"))
        self.assertFalse(form.isRowVisible(self.p._shape["length"]))
        self.p._verb.click()
        d = self.sent[-1][1]
        self.assertEqual((d["place"], d["place_across_m"]),
                         ("circle", Y.SHAPE_ACROSS_M["pond"]))
        # A line and an object have no such choice.
        for key in ("fence", "bee_hotel"):
            self.p.choose(key)
            self.assertEqual(self.p._shape, {})

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
            for w in list(self.p._inputs.values()) + list(
                    self.p._shape.values()):
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

    def test_a_hedge_is_stored_as_what_it_is(self):
        from src.controllers.map_events import MapEventRouter
        from src.controllers.mode import ModeController
        main = self._main()
        ModeController(main)._enter_hedgerow_mode(
            Y.drawn_props("hedge", hedge_kind="cedar", height_m=2.2))
        MapEventRouter(main)._on_hedgerow_complete(
            "h1", "[[53.5,-113.5],[53.5,-113.4999]]", "", "hedge", 7.0, 0)
        props = main._project["features"][-1]["properties"]
        self.assertEqual((props["kind"], props["hedge_kind"], props["height_m"],
                          props["width_m"]), ("hedge", "cedar", 2.2,
                                              Y.HEDGE_SIZE_M["cedar"][1]))


if __name__ == "__main__":
    unittest.main()
