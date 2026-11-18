"""
tests/test_plant_page_sections.py — the plant page (PR-4, WD-3, WD-8; V3.26;
one page in both modes since V3.56; docs/homeowner/05-plants-that-lead.md §7).

The page is what a person can act on, with the details a design needs on it
(V3.56, the owner); the animal list and where it grows wild wait in two folds
that start closed. Never the notes (L8, P12).
"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TMP = tempfile.mkdtemp(prefix="page_sections_")
import src.db.plants as _plants  # noqa: E402
_plants._DATA_DIR = _TMP
_plants._DB_PATH = os.path.join(_TMP, "permadesign_test.db")

from src import plant_page_sections as pps  # noqa: E402

try:
    from PyQt6.QtWidgets import QApplication, QLabel, QPushButton
    _HAVE_QT = True
except Exception:                                          # noqa: BLE001
    _HAVE_QT = False

#: What the page never says with its folds closed (§8, PR-4's acceptance;
#: V3.56 added the long page's repeats and internals).
_FORBIDDEN = ("VASCAN", "records, high confidence", "Estimate (",
              "Where these relationships came from", "Roles", "AB retail",
              "Why it matters", "Toxicity not assessed", "(read V",
              "Where these numbers came from", "iNaturalist photographs")
#: The words a page may run to (V3.56: the design details came onto it;
#: the median plant is about 100, the longest about 170).
_MOST_WORDS = 180


def tearDownModule():
    shutil.rmtree(_TMP, ignore_errors=True)


def _db():
    _plants._DATA_DIR = _TMP
    _plants._DB_PATH = os.path.join(_TMP, "permadesign_test.db")
    _plants.init_db()


def _named(name):
    return next(r for r in _plants.get_all_plants()
                if r["common_name"] == name)


def _entry(name):
    from src.plant_directory import species_entry
    return species_entry(_named(name)["id"])


class TheWords(unittest.TestCase):

    def test_growing_in_words(self):
        self.assertEqual(pps.growing_words(
            {"sun": "full sun,partial shade", "water": "medium,low"}),
            "Full sun to part shade. Dry to average soil.")
        self.assertEqual(pps.growing_words({}), "")

    def test_size_in_words_with_the_one_spacing(self):
        self.assertEqual(pps.size_words(
            {"mature_height_m": 5, "mature_canopy_m": 4.5,
             "years_to_maturity": 1, "spacing_m": 0.33}),
            "Grows to 5 m tall and 4.5 m wide in about 1 year. "
            "Plant 0.35 m apart.")
        self.assertEqual(pps.size_words({}), "")


class TheSimplePage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _db()

    def test_chokecherry_exactly(self):
        sections = pps.simple(_entry("Chokecherry"), place="edmonton")
        self.assertEqual([h for h, _b in sections],
                         ["Why this plant", "Good to know",
                          "Growing it", pps.SEASON, "Buying it",
                          "Native around Edmonton."])
        self.assertLessEqual(pps.word_count(sections), _MOST_WORDS)
        good = dict(sections)["Good to know"]
        self.assertIn("Poisonous to pets if eaten", good)
        self.assertNotIn("Not checked for poison", good)   # said once
        self.assertIn("Hardy to zone", dict(sections)["Growing it"])
        self.assertIn("White to cream flowers", dict(sections)[pps.SEASON])

    def test_animals_are_named_two_or_three_by_the_overview_rule(self):
        why = dict(pps.simple(_entry("Saskatoon Berry"),
                              place="edmonton"))["Why this plant"]
        self.assertIn("Berries for 5 kinds of bird, among them", why)
        self.assertNotIn("Berries or seed", why)

    def test_the_naming_shares_three_and_never_says_and_one_more(self):
        from src.plant_priority import Assessment
        a = Assessment(impact=5, band="Top pick",
                       reasons=["Caterpillar food for 4 kinds", "Seed for 2",
                                "Visited by 9 kinds"],
                       who={"Caterpillar food for 4 kinds": {1, 2, 3, 4},
                            "Seed for 2": {5, 6}, "Visited by 9 kinds": {7}})
        names = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "F", 7: "G"}
        got = pps.named_reasons(a, names_fn=lambda ids: sorted(
            names[i] for i in ids))
        self.assertEqual(got, ["Caterpillar food for 4 kinds, among them A "
                               "and B", "Seed for 2: E and F",
                               "Visited by 9 kinds"])

    def test_a_wind_pollinated_tree_feeds_no_early_bee(self):
        """V3.56: a birch's April catkins were said to feed early bees, and
        scored a point for it. A willow's still do."""
        for name in ("Water Birch", "Paper Birch", "Trembling Aspen",
                     "White Spruce", "Thinleaf Alder"):
            why = dict(pps.simple(_entry(name), place="edmonton")).get(
                "Why this plant", "")
            self.assertNotIn("early bees", why, name)
        from src import plant_priority
        willows = [r for r in _plants.get_all_plants()
                   if (r["scientific_name"] or "").startswith("Salix")
                   and plant_priority.assess(r).parts["season"]]
        self.assertTrue(willows)

    def test_no_page_says_what_the_simple_page_keeps_out(self):
        for row in _plants.get_all_plants():
            entry = {"id": row["id"], "scientific_name": row["scientific_name"],
                     "sun": (row.get("sun_requirement") or "").replace("_", " "),
                     "water": row.get("water_needs") or "",
                     "sourcing": {}}
            sections = pps.simple(entry, row, place="edmonton")
            text = " ".join(f"{h} {b}" for h, b in sections)
            for word in _FORBIDDEN + ("Everything about this plant",):
                self.assertNotIn(word, text, row["common_name"])
            notes = (row.get("notes") or "").strip()
            if len(notes) > 20:
                self.assertNotIn(notes[:20], text, row["common_name"])
            self.assertNotIn("_", text, row["common_name"])
            self.assertLessEqual(pps.word_count(sections), _MOST_WORDS,
                                 row["common_name"])

    def test_an_off_list_plant_says_so_once(self):
        from src import native_here
        names = native_here.native_names("edmonton")
        row = next(r for r in _plants.get_all_plants()
                   if r["scientific_name"] not in names
                   and r.get("native_provinces"))
        heads = [h for h, _b in pps.simple({"id": row["id"]}, row,
                                           place="edmonton")]
        self.assertNotIn("Not native here", heads)
        self.assertIn("Not native around Edmonton.", heads)


@unittest.skipUnless(_HAVE_QT, "PyQt6 not installed in this env")
class ThePage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication(["permadesign-tests"])
        _db()

    def setUp(self):
        from src.species_page import SpeciesPage
        self.page = SpeciesPage(actions=True, closable=True)
        self.addCleanup(self.page.deleteLater)
        self.page.resize(410, 600)
        self.page.show_plant(_named("Wild Bergamot"))

    def _texts(self):
        return " ".join(l.text() for l in self.page.findChildren(QLabel))

    def test_short_with_the_folds_closed(self):
        texts = self._texts()
        self.assertIn("Why this plant", texts)
        for word in _FORBIDDEN + ("Notes", pps.ID_LINE, "Caterpillar host for",
                                  "Native to"):
            self.assertNotIn(word, texts)
        for key in ("animals", "wild"):
            fold = self.page.findChild(QPushButton, f"speciesPageFold_{key}")
            self.assertIsNotNone(fold, key)
            self.assertFalse(fold.isChecked())

    def test_the_folds_open_stay_open_and_never_show_the_notes(self):
        self.page.findChild(QPushButton, "speciesPageFold_animals").click()
        self.page.findChild(QPushButton, "speciesPageFold_wild").click()
        texts = self._texts()
        self.assertIn("Nectar for</b>", texts)
        self.assertIn("Sources: ", texts)
        self.assertIn("Native to", texts)
        self.assertIn("records", texts)
        notes = _named("Wild Bergamot").get("notes") or ""
        self.assertTrue(notes)
        self.assertNotIn(notes[:20], texts)
        # The next plant opens with the same folds open, to compare.
        self.page.show_plant(_named("Chokecherry"))
        self.assertTrue(self.page.findChild(
            QPushButton, "speciesPageFold_wild").isChecked())
        self.page.findChild(QPushButton, "speciesPageFold_wild").click()
        self.assertNotIn("Native to", self._texts())

    def test_the_switch_changes_only_the_id_line(self):
        before = self._texts()
        self.page.set_advanced_tools(True)
        after = self._texts()
        self.assertIn(pps.ID_LINE, after)
        self.assertEqual(after.replace(pps.ID_LINE + " ", ""), before)


if __name__ == "__main__":
    unittest.main()
