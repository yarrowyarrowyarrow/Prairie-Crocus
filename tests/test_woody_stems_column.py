"""
A shrub's reading has to survive the database (schema v99, V3.49).

`scripts/leaf_readings.py` writes what was read off a shrub's photographs into
`data/plants_master.json`: its leaf, its woody habit, how many stems it sends
up, and `leaf_data_source = "photo"`. The 3D viewer draws a shrub from those
numbers only when the row the DATABASE returns carries them
(`src/shrub_habit.py`), so a field with no column behind it, or a column the
seed INSERT forgets, leaves every read shrub on the baked figure with nothing
raised. That is the v79 lesson (`test_nativity_source_column`) and the v98 one
(`test_stem_leaf_nodes_column`), and it gets the same test: through a real
reseed, not against the JSON.
"""

import json
import os
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

# Redirect the DB before importing anything that opens it.
_TMP_DIR = tempfile.mkdtemp(prefix="siteandpattern_woody_stems_")

import src.db.plants as _plants_mod                   # noqa: E402

_plants_mod._DATA_DIR = _TMP_DIR
_plants_mod._DB_PATH = os.path.join(_TMP_DIR, "permadesign_test.db")

from src import herb_habit, shrub_habit               # noqa: E402
from src.db.plants import (                           # noqa: E402
    _SCHEMA_VERSION, get_all_plants, get_connection, init_db,
)

#: What a shrub's reading writes that its body is decided from.
CARRIED = ("leaf_data_source", "leaf_data_citation", "woody_stems", "branching",
           "leaf_shape", "leaf_arrangement")


class TestAShrubsReadingReachesTheDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = {r.get("scientific_name"): r for r in get_all_plants()}
        with open(os.path.join(_ROOT, "data", "plants_master.json"), encoding="utf-8") as fh:
            cls.master = json.load(fh)

    def test_the_column_is_there(self):
        with get_connection() as conn:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(plants)")}
        self.assertIn("woody_stems", cols)

    def test_the_schema_version_was_bumped_or_nobody_reseeds(self):
        self.assertGreaterEqual(_SCHEMA_VERSION, 99)

    def test_an_older_database_gains_the_column(self):
        """`CREATE TABLE IF NOT EXISTS` adds nothing to a table that exists:
        an installed copy gets the column from the migration or not at all."""
        with get_connection() as conn:
            conn.execute("CREATE TABLE old_plants (id INTEGER PRIMARY KEY)")
            conn.execute("ALTER TABLE plants RENAME TO plants_new")
            conn.execute("ALTER TABLE old_plants RENAME TO plants")
            try:
                _plants_mod._migrate_to_v99(conn)
                cols = {r[1] for r in conn.execute("PRAGMA table_info(plants)")}
                _plants_mod._migrate_to_v99(conn)          # and again, harmlessly
            finally:
                conn.execute("DROP TABLE plants")
                conn.execute("ALTER TABLE plants_new RENAME TO plants")
                conn.commit()
        self.assertIn("woody_stems", cols)

    def test_every_read_shrub_arrives_as_it_was_written(self):
        read = [r for r in self.master if herb_habit.is_read(r)
                and r.get("plant_type") in shrub_habit.TYPES]
        self.assertTrue(read, "no shrub in the catalogue has been read")
        for row in read:
            got = self.db.get(row["scientific_name"])
            self.assertIsNotNone(got, row["scientific_name"])
            for field in CARRIED:
                self.assertEqual(got.get(field) or None, row.get(field) or None,
                                 f"{row['scientific_name']}: {field} was dropped on "
                                 f"the way into the database")
            self.assertEqual(float(got.get("leaf_size_cm") or 0),
                             float(row.get("leaf_size_cm") or 0))

    def test_the_database_row_decides_the_same_body_as_the_file_row(self):
        """The viewer is fed from the database. A shrub the file says is drawn
        from its own numbers must be one the database says so too."""
        for row in self.master:
            got = self.db.get(row["scientific_name"]) or {}
            self.assertEqual(shrub_habit.form_for(got), shrub_habit.form_for(row),
                             row["scientific_name"])

    def test_an_unread_row_has_no_count(self):
        for row in self.master:
            if not herb_habit.is_read(row):
                self.assertFalse(row.get("woody_stems"),
                                 f"{row['scientific_name']}: a stem count with no reading")


if __name__ == "__main__":
    unittest.main()
