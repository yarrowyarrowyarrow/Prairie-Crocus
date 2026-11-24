"""
A tree's crown has to survive the database (schema v100, V3.50).

The viewer draws a tree from its crown only when the row the DATABASE returns
carries `crown_shape`, `crown_clear` and `limb_habit` (src/tree_habit.py). A
field with no column behind it, or a column the seed INSERT forgets, leaves
every read tree on the baked crown with nothing raised: the v79, v98 and v99
lesson, tested the same way, through a real reseed.
"""

import json
import os
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

_TMP_DIR = tempfile.mkdtemp(prefix="siteandpattern_crown_")

import src.db.plants as _plants_mod                   # noqa: E402

_plants_mod._DATA_DIR = _TMP_DIR
_plants_mod._DB_PATH = os.path.join(_TMP_DIR, "permadesign_test.db")

from src import tree_habit                            # noqa: E402
from src.db.plants import (                           # noqa: E402
    _SCHEMA_VERSION, get_all_plants, get_connection, init_db,
)

CARRIED = ("crown_shape", "limb_habit", "woody_stems", "leaf_data_source", "leaf_shape")


class TestATreesCrownReachesTheDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = {r.get("scientific_name"): r for r in get_all_plants()}
        with open(os.path.join(_ROOT, "data", "plants_master.json"), encoding="utf-8") as fh:
            cls.master = json.load(fh)

    def test_the_columns_are_there(self):
        with get_connection() as conn:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(plants)")}
        self.assertLessEqual({"crown_shape", "crown_clear", "limb_habit"}, cols)

    def test_the_schema_version_was_bumped_or_nobody_reseeds(self):
        self.assertGreaterEqual(_SCHEMA_VERSION, 100)

    def test_an_older_database_gains_the_columns(self):
        with get_connection() as conn:
            conn.execute("CREATE TABLE old_plants (id INTEGER PRIMARY KEY)")
            conn.execute("ALTER TABLE plants RENAME TO plants_new")
            conn.execute("ALTER TABLE old_plants RENAME TO plants")
            try:
                _plants_mod._migrate_to_v100(conn)
                cols = {r[1] for r in conn.execute("PRAGMA table_info(plants)")}
                _plants_mod._migrate_to_v100(conn)
            finally:
                conn.execute("DROP TABLE plants")
                conn.execute("ALTER TABLE plants_new RENAME TO plants")
                conn.commit()
        self.assertLessEqual({"crown_shape", "crown_clear", "limb_habit"}, cols)

    def test_every_read_tree_arrives_as_it_was_written(self):
        read = [r for r in self.master if r.get("plant_type") == "tree" and tree_habit.form_for(r)]
        self.assertGreaterEqual(len(read), 10)
        for row in read:
            got = self.db[row["scientific_name"]]
            for field in CARRIED:
                self.assertEqual(got.get(field) or None, row.get(field) or None,
                                 f"{row['scientific_name']}: {field} dropped")
            self.assertAlmostEqual(float(got.get("crown_clear")), float(row["crown_clear"]))

    def test_the_database_row_decides_the_same_crown_as_the_file_row(self):
        for row in self.master:
            got = self.db.get(row["scientific_name"]) or {}
            self.assertEqual(tree_habit.form_for(got), tree_habit.form_for(row),
                             row["scientific_name"])


if __name__ == "__main__":
    unittest.main()
