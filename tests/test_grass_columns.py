"""
A grass's blades and seed head, and a species' leaf colour, have to survive
the database (schema v101, V3.51).

The viewer draws a grass from its own blades and head only when the row the
DATABASE returns carries them (src/grass_habit.py). Tested the v79, v98, v99
and v100 way, through a real reseed.
"""

import json
import os
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

_TMP_DIR = tempfile.mkdtemp(prefix="siteandpattern_grass_")

import src.db.plants as _plants_mod                   # noqa: E402

_plants_mod._DATA_DIR = _TMP_DIR
_plants_mod._DB_PATH = os.path.join(_TMP_DIR, "permadesign_test.db")

from src import data_quality as dq, grass_habit       # noqa: E402
from src.db.plants import (                           # noqa: E402
    _SCHEMA_VERSION, get_all_plants, get_connection, init_db,
)

COLUMNS = {"leaf_color", "blade_width_mm", "blade_habit", "head_length_cm",
           "head_width_cm", "head_count", "head_color", "head_attitude"}


class TestAGrassReachesTheDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = {r.get("scientific_name"): r for r in get_all_plants()}
        with open(os.path.join(_ROOT, "data", "plants_master.json"), encoding="utf-8") as fh:
            cls.master = json.load(fh)

    def test_the_columns_are_there(self):
        with get_connection() as conn:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(plants)")}
        self.assertLessEqual(COLUMNS, cols)

    def test_the_schema_version_was_bumped_or_nobody_reseeds(self):
        self.assertGreaterEqual(_SCHEMA_VERSION, 101)

    def test_an_older_database_gains_the_columns(self):
        with get_connection() as conn:
            conn.execute("CREATE TABLE old_plants (id INTEGER PRIMARY KEY)")
            conn.execute("ALTER TABLE plants RENAME TO plants_new")
            conn.execute("ALTER TABLE old_plants RENAME TO plants")
            try:
                _plants_mod._migrate_to_v101(conn)
                cols = {r[1] for r in conn.execute("PRAGMA table_info(plants)")}
                _plants_mod._migrate_to_v101(conn)
            finally:
                conn.execute("DROP TABLE plants")
                conn.execute("ALTER TABLE plants_new RENAME TO plants")
                conn.commit()
        self.assertLessEqual(COLUMNS, cols)

    def test_every_read_grass_arrives_as_it_was_written(self):
        read = [r for r in self.master if grass_habit.form_for(r)]
        self.assertGreaterEqual(len(read), 47)
        for row in read:
            got = self.db[row["scientific_name"]]
            for field in COLUMNS:
                want, have = row.get(field), got.get(field)
                if isinstance(want, float):
                    self.assertAlmostEqual(float(have), want, msg=f"{row['scientific_name']}: {field}")
                else:
                    self.assertEqual(have or None, want or None,
                                     f"{row['scientific_name']}: {field} dropped")
            self.assertEqual(grass_habit.form_for(got), grass_habit.form_for(row))

    def test_the_gate_refuses_a_bad_value(self):
        row = next(r for r in self.master if r["common_name"] == "Blue Grama Grass")
        def errors(**over):
            got = dq.validate_plant(dict(row, **over), source_label="test.json", idx=0,
                                    use_keys=dq._load_use_keys(),
                                    ecoregion_keys=dq._load_ecoregion_keys())[0]
            return [e for e in got if any(c in e for c in COLUMNS)]
        self.assertEqual(errors(), [])
        for bad in ({"head_color": "purple"}, {"blade_habit": "floppy"},
                    {"head_attitude": "sideways"}, {"head_count": 2.5},
                    {"blade_width_mm": 90}, {"leaf_color": "#12345"}):
            self.assertTrue(errors(**bad), bad)


if __name__ == "__main__":
    unittest.main()
