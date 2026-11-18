"""
tests/test_through_the_year.py — Design › Through the year's arithmetic
(F270, V3.55; docs/plans/V3.55-the-year-and-who-it-feeds.md).

The owner: the month by month "is far and away the most useful information",
and "most people do not know or aim to create a yard for a specific creature".
So the animals come to the person: who is eating here each month, the
chickadee nest in plain words, and the animals recorded as depending on a few
plants. Each rule below is one the plan states.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_TMP = tempfile.mkdtemp(prefix="sp_through_the_year_")
import src.db.plants as _plants  # noqa: E402
_plants._DATA_DIR = _TMP
_plants._DB_PATH = os.path.join(_TMP, "through_the_year.db")

from src import through_the_year as ty  # noqa: E402
from src import what_it_feeds as feeds  # noqa: E402


class _Records:
    """A stand-in for ``fauna_fit.Records``: every animal *here* unless named
    otherwise, none familiar."""

    def __init__(self, bands=None, familiar=()):
        self._bands, self._familiar = dict(bands or {}), set(familiar)

    def band(self, name):
        return self._bands.get(name, "here")

    def familiar(self, name):
        return name in self._familiar


class TheYear(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _plants.init_db()
        conn = _plants.get_connection()
        try:
            cls.ids = {r["common_name"]: r["id"] for r in conn.execute(
                "SELECT id, common_name FROM plants")}
        finally:
            conn.close()
        names = ("Wild Bergamot", "Showy Milkweed", "Chokecherry",
                 "Prairie Crocus", "Smooth Aster")
        cls.placed = [{"plant_id": cls.ids[n]} for n in names for _ in range(3)]

    def test_twelve_months_with_people_kept_apart(self):
        y = ty.year(self.placed)
        self.assertEqual([m["month"] for m in y["months"]], list(range(1, 13)))
        august = y["months"][7]
        self.assertIn(("Chokecherry", "fruit"), august["harvest"])
        self.assertNotIn("Chokecherry", august["flowering"])
        for m in y["months"]:
            for job in m["jobs"]:
                self.assertFalse(job.lower().startswith("harvest"), job)

    def test_the_flowering_line_starts_when_the_design_does(self):
        """The page printed the growing season's first month (April) while
        the Overview said March; both read the design now."""
        y = ty.year(self.placed)
        first = min(m["month"] for m in y["months"] if m["flowering"])
        self.assertTrue(ty.flowering_line(y["months"]).startswith(
            f"In flower from {ty.MONTHS[first - 1]} "))

    def test_who_eats_here_is_one_named_species_on_a_food_record_that_month(self):
        who = ty.visitors(self.placed, records=_Records())
        food = feeds.plant_food({p["plant_id"] for p in self.placed})
        named = 0
        for m, rows in who.items():
            self.assertLessEqual(len(rows), ty.PER_MONTH)
            for v in rows:
                named += 1
                self.assertNotIn("spp", v["line"])
                self.assertTrue(v["line"].startswith(v["name"] + ": "))
                pid = self.ids[v["plant"]]
                months = feeds.months_for(v["kind"], food[pid]["bloom"],
                                          food[pid]["fruit"], v["taxon"])
                self.assertIn(m, months, v["line"])
        self.assertGreater(named, 10)

    def test_an_animal_not_recorded_near_the_yard_is_not_named(self):
        everyone = ty.visitors(self.placed, records=_Records())
        some = next(v["name"] for rows in everyone.values() for v in rows)
        sci = self._sci(some)
        fewer = ty.visitors(self.placed,
                            records=_Records({sci: "elsewhere"}))
        self.assertNotIn(some, [v["name"] for rows in fewer.values()
                                for v in rows])

    def test_the_year_is_not_the_same_four_animals(self):
        who = ty.visitors(self.placed, records=_Records())
        july = {v["name"] for v in who[7]}
        august = {v["name"] for v in who[8]}
        self.assertLess(len(july & august), len(july), "July and August named "
                        "the same animals")

    def test_the_overview_names_a_butterfly_bird_or_bee_first(self):
        names = ty.named_animals(self.placed, records=_Records())
        self.assertEqual(len(names), 3)
        conn = _plants.get_connection()
        try:
            taxa = [conn.execute("SELECT taxon FROM fauna WHERE common_name = ?",
                                 (n,)).fetchone()["taxon"] for n in names]
        finally:
            conn.close()
        self.assertTrue(set(taxa) <= {"lepidoptera", "bird", "bee"}, taxa)

    def test_the_milkweed_serves_the_monarch_from_the_documented_records(self):
        d = ty.depends({p["plant_id"] for p in self.placed}, records=_Records())
        lines = [r["line"] for r in d["served"]]
        self.assertIn("Monarch (Showy Milkweed)", lines)
        self.assertLessEqual(len(d["missing"]), 2)
        for r in d["served"] + d["missing"]:
            self.assertNotIn("spp", r["name"])

    def test_an_animal_recorded_away_from_the_yard_is_not_offered(self):
        sci = self._sci("Monarch")
        d = ty.depends({p["plant_id"] for p in self.placed},
                       records=_Records({sci: "elsewhere"}))
        self.assertNotIn("Monarch", [r["name"] for r in d["served"]])

    def test_an_empty_yard_has_nothing_served(self):
        d = ty.depends([], records=_Records())
        self.assertEqual(d["served"], [])
        for r in d["missing"]:
            self.assertRegex(r["line"], r"^[^()]+ \(.+\)$")

    def _sci(self, name):
        conn = _plants.get_connection()
        try:
            return conn.execute("SELECT scientific_name FROM fauna WHERE "
                                "common_name = ?", (name,)).fetchone()[0]
        finally:
            conn.close()


class Caterpillars(unittest.TestCase):
    """The chickadee nest in plain words: the arithmetic is
    ``chickadee_scenario``'s, the words say more or less than a nest."""

    def _say(self, rank, count=1):
        placed = [{"plant_id": 1, "common_name": "Pussy Willow"}] * count
        return ty.caterpillars(placed, get_keystone=lambda pid: rank,
                               supported_leps=lambda ids: list(range(rank)))

    def test_each_status_in_plain_words(self):
        for rank, count, status in ((0, 1, "none"), (5, 1, "short"),
                                    (20, 1, "partway"), (40, 2, "clears")):
            said = self._say(rank, count)
            self.assertEqual(said["status"], status)
            text = said["headline"] + " " + said["line"]
            for word in ("keystone", "larval", "host", "species", "~"):
                self.assertNotIn(word, text.lower(), (status, text))
            self.assertNotRegex(text, r"\d{2},\d{3}",
                                "a coarse proxy printed to the hundred")

    def test_short_names_the_plants_that_feed_the_most(self):
        self.assertIn("Willow, aspen", self._say(5)["line"])

    def test_a_line_each(self):
        said = self._say(40, 2)
        self.assertEqual(said["line"], "Mostly on your Pussy Willow.")


if __name__ == "__main__":
    unittest.main()
