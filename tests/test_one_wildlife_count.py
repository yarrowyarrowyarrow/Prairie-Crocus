"""
tests/test_one_wildlife_count.py — one wildlife count, worded as records
(V3.20, OV-5).

The Report card counted every animal with any record on the design's plants,
food or shelter, as "wildlife species supported"; Design › Food counted food
edges and said "Your plants feed N animals". One design read 263 on one and 271
on the other (OVF-4), and "supported" or "feed" claims more than a record of an
animal eating a plant somewhere in two provinces can (R15). All three pages now
count food edges and say "recorded as food for".
"""

import os
import re
import sys
import tempfile
import unittest
import unittest.mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TMP = tempfile.mkdtemp(prefix="sp_one_count_")
import src.db.plants as _plants_mod  # noqa: E402
_plants_mod._DATA_DIR = _TMP
_plants_mod._DB_PATH = os.path.join(_TMP, "one_count.db")

try:
    from PyQt6.QtWidgets import QApplication
    _HAVE_QT = True
except ImportError:                                        # pragma: no cover
    _HAVE_QT = False

_COUNT = re.compile(r"recorded as food for (\d+) kinds", re.I)


class TheCount(unittest.TestCase):

    def test_shelter_alone_does_not_count(self):
        from src import what_it_feeds as feeds
        fed = [{"taxon": "bird", "food": True}, {"taxon": "bee", "food": True},
               {"taxon": "bird", "food": False}]
        with unittest.mock.patch.object(feeds, "animals_fed",
                                        return_value=fed):
            counts = feeds.food_counts([1])
        self.assertEqual(list(counts.items()), [("bee", 1), ("bird", 1)])
        self.assertEqual(feeds.food_words(counts),
                         "recorded as food for 2 kinds of wildlife")
        self.assertEqual(feeds.food_words({}), "")


@unittest.skipUnless(_HAVE_QT, "PyQt6 not installed in this env")
class ThreePagesOneNumber(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication(["sp-one-count"])
        _plants_mod.init_db()
        from src.onboarding import resolve_example_planting
        placements, missing = resolve_example_planting()
        assert not missing, missing
        cls.placed = [{"plant_id": p["plant_id"]} for p in placements]

    def _number(self, text):
        found = _COUNT.search(re.sub(r"<[^>]+>", "", text))
        self.assertIsNotNone(found, text[:300])
        return int(found.group(1))

    def test_the_year_habitat_and_the_overview_agree(self):
        """The Report card was the third page until V3.55 (F270); the
        Overview says the number now."""
        from src.analysis_panel import AnalysisPanel
        from src.food_page import FoodPage
        from src.what_it_feeds import food_counts, food_words

        food = FoodPage()
        self.addCleanup(food.close)
        food.set_placed_plants(self.placed)
        food.refresh()
        on_food = self._number(food._summary_line.text())

        on_overview = self._number(food_words(food_counts(
            {p["plant_id"] for p in self.placed})))

        habitat = AnalysisPanel()
        self.addCleanup(habitat.close)
        habitat.set_placed_plants(self.placed)
        habitat._calc_habitat_score()
        on_habitat = self._number(habitat._habitat_breakdown.text())

        self.assertEqual((on_overview, on_habitat), (on_food, on_food))
        self.assertGreater(on_food, 0)


class NoPageSaysSupported(unittest.TestCase):

    def test_no_visible_wildlife_species_supported(self):
        root = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "src")
        for name in sorted(os.listdir(root)):
            if not name.endswith(".py"):
                continue
            with open(os.path.join(root, name), encoding="utf-8") as fh:
                text = fh.read()
            self.assertNotIn("wildlife species supported", text, name)
            self.assertNotIn("Wildlife supported", text, name)


if __name__ == "__main__":
    unittest.main()
