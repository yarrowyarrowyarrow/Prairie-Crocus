"""
A reading has to survive the database (schema v98, V3.48).

`scripts/leaf_readings.py` writes what was read off a plant's photographs into
`data/plants_master.json`: the leaf's length and outline, the habit, how many
leaves stand up a stem, and `leaf_data_source = "photo"`. The 3D viewer draws a
plant from those numbers only when the row the DATABASE returns says they were
read (`src/herb_habit.py`), so a field with no column behind it, or a column
the seed INSERT forgets, leaves every read plant on the baked figure with
nothing raised. That is the v79 lesson (`test_nativity_source_column`), and it
gets the same test: through a real reseed, not against the JSON.
"""

import json
import os
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

# Redirect the DB before importing anything that opens it.
_TMP_DIR = tempfile.mkdtemp(prefix="siteandpattern_stem_nodes_")

import src.db.plants as _plants_mod                   # noqa: E402

_plants_mod._DATA_DIR = _TMP_DIR
_plants_mod._DB_PATH = os.path.join(_TMP_DIR, "permadesign_test.db")

from src import herb_habit                            # noqa: E402
from src.db.plants import (                           # noqa: E402
    _SCHEMA_VERSION, get_all_plants, get_connection, init_db,
)

#: What a reading writes that the body is decided from.
CARRIED = ("leaf_data_source", "leaf_data_citation", "stem_leaf_nodes",
           "growth_form", "leaf_shape", "leaf_arrangement", "stem_branching")


class TestAReadingReachesTheDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = {r.get("scientific_name"): r for r in get_all_plants()}
        with open(os.path.join(_ROOT, "data", "plants_master.json"), encoding="utf-8") as fh:
            cls.master = json.load(fh)

    def test_the_column_is_there(self):
        with get_connection() as conn:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(plants)")}
        self.assertIn("stem_leaf_nodes", cols)

    def test_the_schema_version_was_bumped_or_nobody_reseeds(self):
        self.assertGreaterEqual(_SCHEMA_VERSION, 98)

    def test_an_older_database_gains_the_column(self):
        """`CREATE TABLE IF NOT EXISTS` adds nothing to a table that exists:
        an installed copy gets the column from the migration or not at all."""
        with get_connection() as conn:
            conn.execute("CREATE TABLE old_plants (id INTEGER PRIMARY KEY)")
            conn.execute("ALTER TABLE plants RENAME TO plants_new")
            conn.execute("ALTER TABLE old_plants RENAME TO plants")
            try:
                _plants_mod._migrate_to_v98(conn)
                cols = {r[1] for r in conn.execute("PRAGMA table_info(plants)")}
                _plants_mod._migrate_to_v98(conn)          # and again, harmlessly
            finally:
                conn.execute("DROP TABLE plants")
                conn.execute("ALTER TABLE plants_new RENAME TO plants")
                conn.commit()
        self.assertIn("stem_leaf_nodes", cols)

    def test_every_read_row_arrives_as_it_was_written(self):
        read = [r for r in self.master if herb_habit.is_read(r)]
        for row in read:
            got = self.db.get(row["scientific_name"])
            self.assertIsNotNone(got, row["scientific_name"])
            for field in CARRIED:
                self.assertEqual(got.get(field) or None, row.get(field) or None,
                                 f"{row['scientific_name']}: {field} was dropped on "
                                 f"the way into the database")
            self.assertEqual(float(got.get("leaf_size_cm") or 0),
                             float(row.get("leaf_size_cm") or 0))
            self.assertEqual(bool(got.get("basal_rosette")), bool(row.get("basal_rosette")))

    def test_the_database_row_decides_the_same_body_as_the_file_row(self):
        """The viewer is fed from the database. A plant the file says is drawn
        from its own numbers must be one the database says so too."""
        for row in self.master:
            got = self.db.get(row["scientific_name"]) or {}
            self.assertEqual(herb_habit.form_for(got), herb_habit.form_for(row),
                             row["scientific_name"])

    def test_an_unread_row_has_no_count(self):
        for row in self.master:
            if not herb_habit.is_read(row):
                self.assertFalse(row.get("stem_leaf_nodes"),
                                 f"{row['scientific_name']}: a leaf count with no reading")


if __name__ == "__main__":
    unittest.main()
