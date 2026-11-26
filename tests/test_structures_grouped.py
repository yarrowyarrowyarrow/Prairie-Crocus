"""
tests/test_structures_grouped.py — Placement › Structures under three
headings (V3.21, RM-9; docs/homeowner/03-what-goes.md §6).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication
    _HAVE_QT = True
except ImportError:                                        # pragma: no cover
    _HAVE_QT = False


@unittest.skipUnless(_HAVE_QT, "PyQt6 not installed in this env")
class ThreeHeadings(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication(["sp-structures"])

    def test_every_structure_is_in_one_group(self):
        from src.db.structures import STRUCTURES
        from src.structure_panel import STRUCTURE_GROUPS
        grouped = [i for _h, ids in STRUCTURE_GROUPS for i in ids]
        self.assertEqual(len(grouped), len(set(grouped)))
        self.assertEqual(sorted(grouped), sorted(s["id"] for s in STRUCTURES))

    def test_the_list_shows_three_headings_and_the_same_fifteen(self):
        from src.structure_panel import StructurePanel
        panel = StructurePanel()
        self.addCleanup(panel.close)
        rows = [panel._struct_list.item(i)
                for i in range(panel._struct_list.count())]
        heads = [r.text() for r in rows
                 if r.data(Qt.ItemDataRole.UserRole) is None]
        self.assertEqual(heads, ["For wildlife", "For water",
                                 "Around the yard"])
        for r in rows:
            if r.data(Qt.ItemDataRole.UserRole) is None:
                self.assertEqual(r.flags(), Qt.ItemFlag.NoItemFlags)
        self.assertEqual(len(rows) - len(heads), 15)

    def test_a_search_keeps_only_the_headings_with_a_match(self):
        from src.structure_panel import StructurePanel
        panel = StructurePanel()
        self.addCleanup(panel.close)
        panel._search.setText("barrel")
        panel._filter_structures()
        texts = [panel._struct_list.item(i).text()
                 for i in range(panel._struct_list.count())]
        self.assertEqual(texts[0], "For water")
        self.assertEqual(len(texts), 2)
        self.assertIn("Rain Barrel", texts[1])


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(_HAVE_QT, "PyQt6 not installed in this env")
class TheSizeBoxFollowsTheKind(unittest.TestCase):
    """V3.70 (F288): the Size box ran 0.5 to 50 m for every structure and was
    always called Size; a rectangle's Size is its length on the map."""

    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication(["sp-structures"])

    def _choose(self, panel, sid):
        for i in range(panel._struct_list.count()):
            item = panel._struct_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == sid:
                panel._struct_list.setCurrentItem(item)
                return
        self.fail(f"{sid} is not in the list")

    def test_a_raised_bed_asks_its_length_within_its_range(self):
        from src.structure_panel import StructurePanel
        panel = StructurePanel()
        self.addCleanup(panel.close)
        self._choose(panel, "raised_bed")
        self.assertEqual(panel._size_label.text(), "Length (m):")
        self.assertEqual((panel._size_spin.minimum(),
                          panel._size_spin.maximum()), (1.0, 8.0))
        self.assertEqual(panel._size_spin.value(), 3.0)
        placed = []
        panel.place_structure_requested.connect(placed.append)
        panel._size_spin.setValue(50.0)              # held to the range
        panel._on_place_clicked()
        self.assertEqual(placed[0]["size_m"], 8.0)

    def test_a_pond_asks_its_width_across(self):
        from src.structure_panel import StructurePanel
        panel = StructurePanel()
        self.addCleanup(panel.close)
        self._choose(panel, "pond")
        self.assertEqual(panel._size_label.text(), "Across (m):")
        self.assertEqual((panel._size_spin.minimum(),
                          panel._size_spin.maximum()), (1.5, 12.0))
