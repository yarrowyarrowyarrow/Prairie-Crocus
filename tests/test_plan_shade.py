"""
tests/test_plan_shade.py — a plan survives its own preview (F264, V3.52; 3D-5).

Plan My Yard had no shade to read without an elevation grid, and the 3D preview
then shaded its sun plants out north of the house: 14 of the review lot's 365
by the fifth summer, 39 by the tenth. ``src.plan_shade`` asks the preview's own
shade model, with only the buildings and the trees already there casting, and
trades a plant that stands in more shade than it takes for a kind that takes it,
where it stands. The review lot itself is held by
``scripts/probe_plan_my_yard.py --assert`` (``tests/test_plan_my_yard_probe``).
"""

import math
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.db.plants as _plants_mod  # noqa: E402

_TMP = tempfile.mkdtemp(prefix="permadesign_plan_shade_test_")

LAT0, LNG0 = 53.5232, -113.5263
KX = 111320 * math.cos(math.radians(LAT0))
KY = 111320.0
BOUNDARY = [[LAT0 + n / KY, LNG0 + e / KX]
            for e, n in ((0, 0), (15, 0), (15, 10), (0, 10))]
SITE = {"latitude": LAT0 + 5 / KY, "longitude": LNG0 + 7 / KX}


def _ll(e, n):
    return [LNG0 + e / KX, LAT0 + n / KY]


def _building(x0, y0, x1, y1, height=6.5):
    """A scanned building, as Site › Features › Scan this area stores one."""
    ring = [_ll(e, n) for e, n in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    ring.append(ring[0])
    return {"type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [ring]},
            "properties": {"element_type": "canopy_footprint",
                           "shape_id": "shape_osm_house",
                           "shape_type": "Building (OSM)", "label": "House",
                           "height_m": height, "cast_shade": True,
                           "canopy_radius_m": 6.0,
                           "lat": LAT0 + (y0 + y1) / 2 / KY,
                           "lng": LNG0 + (x0 + x1) / 2 / KX,
                           "source": "osm"}}


#: A house across the yard's south edge: its shadow lies on the yard's south
#: half for much of the day, and never on the north end.
HOUSE = _building(0, -9, 15, -0.5)

ROWS = {
    1: {"id": 1, "common_name": "Sun Flower", "plant_type": "wildflower",
        "sun_requirement": "full_sun", "mature_height_meters": 0.6},
    2: {"id": 2, "common_name": "Shade Flower", "plant_type": "wildflower",
        "sun_requirement": "partial_shade,full_shade",
        "mature_height_meters": 0.5},
    3: {"id": 3, "common_name": "Tall Shade Flower",
        "plant_type": "wildflower", "sun_requirement": "full_shade",
        "mature_height_meters": 2.5},
    4: {"id": 4, "common_name": "Shade Grass", "plant_type": "grass",
        "sun_requirement": "full_shade", "mature_height_meters": 0.5},
    5: {"id": 5, "common_name": "Unrecorded Flower",
        "plant_type": "wildflower", "sun_requirement": "",
        "mature_height_meters": 0.5},
}


def _get(pid):
    return ROWS.get(pid)


class _Project:
    """What the planner hands the step: an object with ``as_dict``."""

    def __init__(self, d):
        self._d = d

    def as_dict(self):
        return self._d


def _yard(*spots, pid=1, group=""):
    from src.project_store import ProjectStore
    store = ProjectStore()
    for e, n in spots:
        store.add_plant(pid, ROWS[pid]["common_name"], LAT0 + n / KY,
                        LNG0 + e / KX, placement_group_id=group,
                        plan_run="run1")
    return store


class TheStoreChangesAKindWhereItStands(unittest.TestCase):

    def test_identity_spot_group_and_plan_are_kept(self):
        store = _yard((5, 1), group="g1")
        fid = store.placed_plants[0]["feature_id"]
        self.assertTrue(store.change_species(fid, 2, "Shade Flower",
                                             why_here=["Because"]))
        rec, feat = store.placed_plants[0], store.features[0]["properties"]
        for d in (rec, feat):
            self.assertEqual((d["plant_id"], d["common_name"], d["why_here"]),
                             (2, "Shade Flower", ["Because"]))
            self.assertEqual(d["feature_id"], fid)
            self.assertEqual(d["placement_group_id"], "g1")
        self.assertEqual(feat["plan_run"], "run1")
        self.assertFalse(store.check_consistency())

    def test_an_unknown_id_changes_nothing(self):
        store = _yard((5, 1))
        self.assertFalse(store.change_species("pf_nothing", 2, "X"))
        self.assertEqual(store.placed_plants[0]["plant_id"], 1)


class TheFixedShadeIsThePreviewsOwn(unittest.TestCase):
    """``misfits`` asks the succession engine with only fixed casters."""

    def _statics(self, *feats):
        from src.succession_engine import static_casters_from_project
        return static_casters_from_project({"features": list(feats)})

    def test_a_sun_plant_by_the_house_is_a_misfit_and_one_far_off_is_not(self):
        from src.plan_shade import misfits
        store = _yard((5, 0.5), (5, 9.5))
        found = misfits(store.placed_plants, self._statics(HOUSE), _get)
        self.assertEqual([i for i, _s, _w in found], [0])
        self.assertEqual(found[0][2], "building")
        self.assertGreater(found[0][1], 0.35)

    def test_nothing_is_a_misfit_without_a_fixed_caster(self):
        from src.plan_shade import misfits
        store = _yard((5, 0.5))
        self.assertEqual(misfits(store.placed_plants, [], _get), [])

    def test_the_plans_own_plants_cast_nothing_here(self):
        """A tall plant of the plan beside a short one is crowding, which the
        preview shows and the planner leaves: only fixed casters count."""
        from src.succession_engine import SuccessionEngine
        store = _yard((5, 5), pid=1)
        store.add_plant(3, "Tall Shade Flower", LAT0 + 4.5 / KY,
                        LNG0 + 5 / KX)
        fixed = SuccessionEngine(store.placed_plants, get_plant=_get,
                                 static_casters=[], fixed_only=True)
        self.assertEqual(fixed.experienced_shade(0, 5), 0.0)


class AReplacementIsLikeTheOriginal(unittest.TestCase):

    def test_same_layer_that_takes_the_shade(self):
        from src.plan_shade import choose
        pool = [ROWS[4], ROWS[1], ROWS[2]]
        self.assertEqual(choose(ROWS[1], 0.9, pool)["id"], 2)

    def test_a_similar_height_first(self):
        from src.plan_shade import choose
        self.assertEqual(choose(ROWS[1], 0.9, [ROWS[3], ROWS[2]])["id"], 2)
        # ... and a taller one only when nothing of its size takes the shade.
        self.assertEqual(choose(ROWS[1], 0.9, [ROWS[3]])["id"], 3)

    def test_unrecorded_sun_needs_are_never_chosen_for_shade(self):
        from src.plan_shade import choose
        self.assertIsNone(choose(ROWS[1], 0.5, [ROWS[5]]))

    def test_allowed_is_asked(self):
        from src.plan_shade import choose
        self.assertIsNone(choose(ROWS[1], 0.9, [ROWS[2]],
                                 allowed=lambda row: False))


class FitTradesWhereItStands(unittest.TestCase):

    def test_the_shaded_plants_change_and_the_sunny_ones_do_not(self):
        from src.plan_shade import WHY, WHAT, fit
        store = _yard((4, 0.5), (6, 0.5), (5, 9.5), group="g1")
        before = [(p["feature_id"], p["lat"], p["lng"])
                  for p in store.placed_plants]
        done = fit(_Project(store.project), [HOUSE], [ROWS[2]],
                   get_plant=_get)
        self.assertEqual(done["swapped"], {"Sun Flower": "Shade Flower"})
        self.assertEqual(done["what"], "building")
        from src.project_store import ProjectStore
        after = ProjectStore(store.project).placed_plants
        self.assertEqual([(p["feature_id"], p["lat"], p["lng"])
                          for p in after], before)
        self.assertEqual([p["plant_id"] for p in after], [2, 2, 1])
        self.assertEqual(after[0]["why_here"],
                         [WHY.format(what=WHAT["building"])])

    def test_no_replacement_leaves_it_out_and_says_so(self):
        from src.plan_shade import fit
        store = _yard((5, 0.5), (5, 9.5))
        done = fit(_Project(store.project), [HOUSE], [ROWS[4]],
                   get_plant=_get)
        self.assertEqual(done["dropped"], ["Sun Flower"])
        from src.project_store import ProjectStore
        self.assertEqual(len(ProjectStore(store.project).placed_plants), 1)

    def test_the_street_band_is_asked(self):
        from src.plan_shade import fit
        store = _yard((5, 0.5))
        done = fit(_Project(store.project), [HOUSE], [ROWS[2]],
                   refuse=lambda la, ln, row: row["id"] == 2, get_plant=_get)
        self.assertEqual(done["dropped"], ["Sun Flower"])

    def test_an_open_yard_is_untouched(self):
        from src.plan_shade import fit
        store = _yard((5, 0.5))
        self.assertEqual(fit(_Project(store.project), [], [ROWS[2]],
                             get_plant=_get), {})


class ThePlanSaysWhatItDid(unittest.TestCase):

    def test_a_swap_is_a_line_and_a_plant_left_out_is_could_not(self):
        from src import plan_notes
        self.assertIn("shade_swap", plan_notes.known_codes())
        notes = [{"code": "shade_swap", "what": "a building",
                  "names": ["Dwarf Raspberry", "Lindley's Aster"]},
                 {"code": "shade_left", "what": "a building",
                  "names": ["A", "B"]}]
        self.assertEqual(
            plan_notes.could_not(notes, plan_notes.DID),
            ["Where a building shades the ground for much of the day, it "
             "chose plants that take shade: Dwarf Raspberry and Lindley's "
             "Aster."])
        self.assertEqual(plan_notes.could_not(notes),
                         ["Nothing that grows here takes the shade of a "
                          "building, so A and B were left out there."])


class PlanMyYardReadsTheShade(unittest.TestCase):
    """The real planner on the probe's yard with a house along its south
    edge: nothing it plants stands in more shade than it takes."""

    @classmethod
    def setUpClass(cls):
        _plants_mod._DATA_DIR = _TMP
        _plants_mod._DB_PATH = os.path.join(_TMP, "t.db")
        _plants_mod.init_db()

    def _plan(self, features):
        from src.llm_design import generate_design_offline
        from src.onboarding import FIRST_RUN_GOALS
        return generate_design_offline(
            site_config=SITE, boundary=BOUNDARY, goals=list(FIRST_RUN_GOALS),
            density="balanced", existing_features=features).as_dict()

    def test_nothing_planted_stands_in_more_shade_than_it_takes(self):
        from src.db.plants import get_plant
        from src.plan_shade import misfits
        from src.project_store import ProjectStore
        from src.succession_engine import static_casters_from_project
        project = self._plan([HOUSE])
        placed = ProjectStore(project).placed_plants
        statics = static_casters_from_project({"features": [HOUSE]})
        self.assertEqual(misfits(placed, statics, get_plant), [])
        codes = [n["code"] for n in project["properties"]["generation_notes"]]
        self.assertIn("shade_swap", codes)
        self.assertTrue(any("Shaded by a building" in w
                            for p in placed for w in p.get("why_here") or []))

    def test_an_open_yard_plans_what_it_planned_before(self):
        def spots(project):
            return sorted((f["properties"]["plant_id"],
                           round(f["geometry"]["coordinates"][0], 8),
                           round(f["geometry"]["coordinates"][1], 8))
                          for f in project["features"]
                          if f["properties"].get("plant_id"))
        now = spots(self._plan([]))
        with mock.patch("src.plan_shade.fit", return_value={}):
            self.assertEqual(spots(self._plan([])), now)


if __name__ == "__main__":
    unittest.main()
