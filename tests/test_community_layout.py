"""
tests/test_community_layout.py — the seeded communities, Edmonton's, laid out
by rule; and turning one before and after it is placed (V3.59).

The owner: "some communities ... only have 3 awkwardly placed plants. Each
should've 5-7 species", then "not all communities need to have 25 plants. Can
be as low as 7" and "can be more than 7 [species], no problem". Measured
before: Chokecherry Community showed one plant of six on the map, Pin Cherry
one of seven, the Edmonton Aspen Grove two of eight; 45 of the 74 held a plant
not native around Edmonton and were hidden from the Edmonton list.
"""

import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_TMP = tempfile.mkdtemp(prefix="community_layout_")
import src.db.plants as _plants  # noqa: E402
_plants._DATA_DIR = _TMP
_plants._DB_PATH = os.path.join(_TMP, "permadesign_test.db")

from src import community_layout as cl  # noqa: E402
from src import community_turn as ct  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def setUpModule():
    _plants.init_db()


def tearDownModule():
    shutil.rmtree(_TMP, ignore_errors=True)


def _seeded():
    from src.db import polycultures as P
    conn = _plants.get_connection()
    try:
        ids = [r[0] for r in conn.execute(
            "SELECT id FROM polycultures WHERE origin = 'seed'")]
    finally:
        conn.close()
    return [P.get_polyculture_by_id(i) for i in ids]


class TheLibrary(unittest.TestCase):

    def test_every_seeded_community_is_edmontons(self):
        from src import native_here
        local = native_here.native_names("edmonton")
        comms = _seeded()
        self.assertEqual(len(comms), 59)
        for c in comms:
            for m in c["members"]:
                row = _plants.get_plant(m["plant_id"])
                with self.subTest(community=c["name"], plant=m["common_name"]):
                    self.assertIn(row["scientific_name"], local)

    def test_five_kinds_or_more_and_seven_to_twenty_five_plants(self):
        for c in _seeded():
            kinds = {m["plant_id"] for m in c["members"]}
            with self.subTest(community=c["name"]):
                self.assertGreaterEqual(len(kinds), 5)
                self.assertGreaterEqual(len(c["members"]), cl.MIN_PLANTS)
                self.assertLessEqual(len(c["members"]), cl.MAX_PLANTS)

    def test_nothing_is_placed_out_of_sight(self):
        """The owner's three plants: a member wholly inside a bigger plant's
        circle, unless it is a shade plant under a tree."""
        for c in _seeded():
            with self.subTest(community=c["name"]):
                self.assertEqual(cl.hidden(c["members"]), 0)

    def test_the_regional_communities_are_retired(self):
        from src.db import polycultures as P
        names = {c["name"] for c in _seeded()}
        for gone in ("Montane Rock Garden", "Subalpine Wildflower Meadow",
                     "Bur Oak Community", "Prairie Cactus & Succulent Garden",
                     "Southwest Alberta River Grove"):
            self.assertNotIn(gone, names)
        self.assertIn("Wet Meadow Asters", names)
        self.assertTrue(all(k in names for k in P._PATTERN_TEXT))

    def test_the_chokecherry_community_is_a_planting(self):
        from src.db import polycultures as P
        c = P.get_polyculture_by_id(
            P.get_polyculture_by_name("Chokecherry Community")["id"])
        by_kind: dict = {}
        for m in c["members"]:
            by_kind[m["common_name"]] = by_kind.get(m["common_name"], 0) + 1
        self.assertEqual(by_kind["Chokecherry"], 1)
        self.assertEqual(by_kind["Wild Strawberry"], 5)    # a groundcover
        self.assertEqual(by_kind["Boreal Yarrow"], 3)      # a wildflower drift


class TheRules(unittest.TestCase):

    def _rows(self):
        def row(i, kind, sp, sun="full_sun", canopy=None):
            return {"id": i, "common_name": f"P{i}", "plant_type": kind,
                    "spacing_meters": sp, "mature_canopy_m": canopy or sp * 1.5,
                    "sun_requirement": sun}
        return {"tree": row(1, "tree", 5.0), "shade": row(2, "herb", 0.4,
                "partial_shade,full_shade"), "sun": row(3, "wildflower", 0.3),
                "shrub": row(4, "shrub", 1.0), "ground": row(5, "groundcover",
                0.3)}

    def test_how_many_by_kind(self):
        r = self._rows()
        self.assertEqual(cl.counts([r["tree"], r["shrub"], r["sun"],
                                    r["ground"]]), [1, 2, 3, 5])

    def test_at_least_seven(self):
        r = self._rows()
        self.assertEqual(sum(cl.counts([r["tree"], r["shrub"], r["sun"]])), 7)

    def test_a_sun_plant_stands_outside_the_crown_a_shade_plant_under_it(self):
        r = self._rows()
        lookup = {v["common_name"]: v for v in r.values()}.get
        laid = cl.lay_out([("P1", ""), ("P2", ""), ("P3", "")], lookup=lookup)
        self.assertEqual(laid[0]["plant_id"], 1)            # largest first
        tree = laid[0]
        for m in laid[1:]:
            d = math.hypot(m["offset_x"] - tree["offset_x"],
                           m["offset_y"] - tree["offset_y"])
            if m["plant_id"] == 3:
                self.assertGreaterEqual(d, (5.0 + 0.3) / 2 - 1e-6)
            else:
                self.assertLess(d, 2.5)                     # under the crown
                self.assertGreaterEqual(d, cl.TRUNK_CLEAR_M)

    def test_the_same_community_lays_out_the_same_way(self):
        r = self._rows()
        lookup = {v["common_name"]: v for v in r.values()}.get
        pairs = [("P1", ""), ("P4", ""), ("P3", ""), ("P5", "")]
        self.assertEqual(cl.lay_out(pairs, lookup=lookup),
                         cl.lay_out(pairs, lookup=lookup))


class Turning(unittest.TestCase):

    def test_a_quarter_turn_clockwise_takes_east_to_south(self):
        out = ct.turned([{"offset_x": 1.0, "offset_y": 0.0, "plant_id": 7}], 90)
        self.assertAlmostEqual(out[0]["offset_x"], 0.0)
        self.assertAlmostEqual(out[0]["offset_y"], -1.0)
        self.assertEqual(out[0]["plant_id"], 7)

    def test_eight_turns_come_back(self):
        start = [{"offset_x": 1.3, "offset_y": -0.4}]
        out = start
        for _ in range(8):
            out = ct.turned(out, ct.STEP)
        self.assertAlmostEqual(out[0]["offset_x"], 1.3, places=2)
        self.assertAlmostEqual(out[0]["offset_y"], -0.4, places=2)

    def test_the_pending_community_turns_and_its_preview_with_it(self):
        sent = []

        class _Map:
            def set_polyculture_mode(self, footprint):
                sent.append(footprint)

        class _Bar:
            def showMessage(self, *_a):
                pass

        class _Main:
            _current_mode = "polyculture"
            map_widget = _Map()
            _pending_polyculture = {"name": "X", "members": [
                {"plant_id": None, "offset_x": 2.0, "offset_y": 0.0}]}

            def statusBar(self):
                return _Bar()

        main = _Main()
        self.assertTrue(ct.turn_pending(main, 90))
        self.assertAlmostEqual(main._pending_polyculture["members"][0]
                               ["offset_y"], -2.0)
        self.assertEqual(len(sent), 1)
        main._current_mode = "none"
        self.assertFalse(ct.turn_pending(main))

    def test_r_is_the_key_and_the_map_loads_the_turn(self):
        from src import keyboard_help
        self.assertIn(("R", "turn"), [(k, a) for k, a, _w in
                                      keyboard_help.MAP_LETTERS])
        page = open(os.path.join(ROOT, "html", "map.html"),
                    encoding="utf-8").read()
        self.assertIn('src="map/11b-turn.js"', page)
        self.assertLess(page.index('src="map/11b-turn.js"'),
                        page.index('src="map/12-legend.js"'))


@unittest.skipIf(not (shutil.which("node") or shutil.which("nodejs")),
                 "no node binary")
class TheMapTurnsAPlacedOne(unittest.TestCase):

    def test_turned_points_keep_their_centre_and_their_spacing(self):
        src = open(os.path.join(ROOT, "html", "map", "11b-turn.js"),
                   encoding="utf-8").read()
        script = src + """
var pts = [{lat: 53.5, lng: -113.5}, {lat: 53.5, lng: -113.49985}];
var out = turnedPoints(pts, 90);
console.log(JSON.stringify(out));
"""
        node = shutil.which("node") or shutil.which("nodejs")
        proc = subprocess.run([node, "-"], input=script, capture_output=True,
                              text=True, encoding="utf-8", timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        # The two plants sat side by side east to west; a quarter turn
        # clockwise puts them north to south, the same distance apart.
        self.assertAlmostEqual(out[0]["lng"], out[1]["lng"], places=7)
        self.assertGreater(out[0]["lat"], out[1]["lat"])
        mid_lat = (out[0]["lat"] + out[1]["lat"]) / 2
        self.assertAlmostEqual(mid_lat, 53.5, places=7)
        d_before = 0.00015 * 111320 * math.cos(math.radians(53.5))
        d_after = (out[0]["lat"] - out[1]["lat"]) * 111320
        self.assertAlmostEqual(d_before, d_after, places=2)


if __name__ == "__main__":
    unittest.main()
