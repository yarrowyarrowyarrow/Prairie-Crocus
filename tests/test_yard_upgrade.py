"""
tests/test_yard_upgrade.py — an older design, read as the Yard palette stores
it (V3.72, F280; ``src/yard_upgrade.py``, ``docs/plans/V3.72-the-yard-palette.md``).

Each conversion rule, at the outline the map showed; that it is idempotent and
reaches every door a design comes in by; and what each reader then says about a
converted design, which is where the numbers move on purpose.
"""

import copy
import json
import math
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import yard_kinds as Y, yard_upgrade as U            # noqa: E402
from tests.test_yard_kinds import (                            # noqa: E402
    _ll, _rect, _shape, _structure, _yard)


def _canopy(shape_type, ring, height, **extra):
    props = {"element_type": "canopy_footprint", "shape_type": shape_type,
             "label": "", "height_m": height, "cast_shade": True,
             "canopy_radius_m": 2.0, "shape_id": "s_old"}
    props.update(extra)
    return {"type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [ring]},
            "properties": props}


def _line(style, points, **extra):
    props = {"element_type": "hedgerow", "style": style, "hedge_id": "h1",
             "width_m": 1.5, "spacing_m": 1.0, "species": ""}
    props.update(extra)
    return {"type": "Feature",
            "geometry": {"type": "LineString",
                         "coordinates": [_ll(e, n) for e, n in points]},
            "properties": props}


def _upgraded(feature):
    project = _yard(copy.deepcopy(feature))
    U.upgrade(project)
    return project["features"][1]


def _extent_m(ring):
    """East-west and north-south extent of a ring, in metres."""
    kx = 111320.0 * math.cos(math.radians(ring[0][1]))
    es = [p[0] * kx for p in ring]
    ns = [p[1] * 111320.0 for p in ring]
    return round(max(es) - min(es), 2), round(max(ns) - min(ns), 2)


class EachPlacedStructureWithAnOutline(unittest.TestCase):

    def test_a_pond_becomes_the_circle_the_map_drew(self):
        f = _upgraded(_structure("pond"))
        props = f["properties"]
        self.assertEqual(f["geometry"]["type"], "Polygon")
        self.assertEqual((props["element_type"], props["kind"]),
                         ("custom_shape", "pond"))
        self.assertEqual(props["shape_type"], "Water Feature")
        # The map drew a 6 m circle for a 6 m pond.
        self.assertEqual(_extent_m(f["geometry"]["coordinates"][0]),
                         (6.0, 6.0))
        self.assertAlmostEqual(props["area_m2"], math.pi * 9, delta=0.6)

    def test_a_rain_garden_and_a_rock_xeriscape_become_areas(self):
        rain = _upgraded(_structure("rain_garden"))["properties"]
        rock = _upgraded(_structure("rock_xeriscape"))["properties"]
        self.assertEqual(rain["kind"], "rain_garden")
        self.assertEqual(rain["shape_type"], "Custom")     # nothing older close
        self.assertEqual(rock["kind"], "rock_garden")

    def test_a_raised_bed_is_its_rectangle_raised_45_cm(self):
        f = _upgraded(_structure("raised_bed"))
        self.assertEqual(f["properties"]["kind"], "bed")
        self.assertEqual(f["properties"]["raised_cm"], 45)
        self.assertEqual(f["properties"]["shape_type"], "Garden Bed")
        # 3 m north-south by 1.2 m, as placeStructureOnMap drew it.
        self.assertEqual(_extent_m(f["geometry"]["coordinates"][0]),
                         (1.2, 3.0))

    def test_a_turned_raised_bed_keeps_its_turn(self):
        s = _structure("raised_bed")
        s["properties"]["bearing_deg"] = 90.0
        f = _upgraded(s)
        self.assertEqual(_extent_m(f["geometry"]["coordinates"][0]),
                         (3.0, 1.2))

    def test_a_shed_becomes_a_building_that_casts_shade(self):
        f = _upgraded(_structure("shed"))
        props = f["properties"]
        self.assertEqual((props["element_type"], props["kind"],
                          props["building"]),
                         ("canopy_footprint", "building", "shed"))
        self.assertTrue(props["cast_shade"])
        self.assertEqual(props["height_m"], 2.4)
        self.assertTrue(Y.is_building_footprint(props))
        from src.shade import casters_from_project
        casters = casters_from_project(_yard(f))
        self.assertEqual(len(casters), 1)
        self.assertEqual(casters[0]["height_m"], 2.4)

    def test_a_native_lawn_patch_becomes_a_native_lawn(self):
        props = _upgraded(_structure("native_lawn_patch"))["properties"]
        self.assertEqual(props["kind"], "native_lawn")
        self.assertEqual(props["shape_type"], "Lawn Area")

    def test_a_swale_becomes_a_line_at_its_width(self):
        f = _upgraded(_structure("swale"))
        props = f["properties"]
        self.assertEqual(f["geometry"]["type"], "LineString")
        self.assertEqual((props["kind"], props["style"]), ("swale", "swale"))
        self.assertEqual(props["width_m"], 1.5)
        self.assertAlmostEqual(
            Y.line_length_m(f["geometry"]["coordinates"]), 10.0, places=1)

    def test_a_fence_becomes_a_rail_fence_along_its_length(self):
        f = _upgraded(_structure("fence"))
        props = f["properties"]
        self.assertEqual((props["kind"], props["fence_kind"]),
                         ("fence", "rail"))
        self.assertAlmostEqual(
            Y.line_length_m(f["geometry"]["coordinates"]), 5.0, places=1)

    def test_an_object_stays_an_object(self):
        before = _structure("bee_hotel")
        after = _upgraded(before)
        self.assertEqual(after, before)

    def test_the_plan_that_placed_it_still_owns_it(self):
        s = _structure("pond")
        s["properties"]["plan_run"] = "g_1"
        self.assertEqual(_upgraded(s)["properties"]["plan_run"], "g_1")


class EachDrawnShapeAndLine(unittest.TestCase):

    def test_a_water_feature_is_a_pond(self):
        props = _upgraded(_shape("Water Feature", _rect(6, 6, 3, 4)))[
            "properties"]
        self.assertEqual(props["kind"], "pond")
        self.assertEqual(props["shape_type"], "Water Feature")

    def test_every_old_shape_gains_its_kind(self):
        for shape_type, key in (("Garden Bed", "bed"), ("Pathway", "path"),
                                ("Patio / Deck", "patio"),
                                ("Lawn Area", "lawn"), ("Custom", "custom"),
                                ("Lawn — to convert", "lawn_to_convert")):
            props = _upgraded(_shape(shape_type, _rect(6, 6, 3, 4)))[
                "properties"]
            self.assertEqual(props["kind"], key, shape_type)
            self.assertEqual(props["shape_type"], shape_type)

    def test_a_garden_bed_with_a_height_is_a_raised_bed(self):
        """The V3.69 trap: a Garden Bed given 0.6 m drew as a building."""
        f = _upgraded(_canopy("Garden Bed", _rect(6, 6, 3, 4), 0.6))
        props = f["properties"]
        self.assertEqual((props["element_type"], props["kind"],
                          props["raised_cm"]), ("custom_shape", "bed", 60))
        self.assertNotIn("cast_shade", props)
        self.assertNotIn("height_m", props)

    def test_any_other_shape_with_a_height_is_a_building(self):
        f = _upgraded(_canopy("Patio / Deck", _rect(6, 6, 3, 4), 5.0))
        props = f["properties"]
        self.assertEqual((props["kind"], props["shape_type"],
                          props["building"]), ("building", "Building",
                                               "house"))
        self.assertEqual(props["height_m"], 5.0)
        self.assertEqual(props["shape_id"], "s_old")

    def test_a_tall_garden_bed_is_a_building_too(self):
        props = _upgraded(_canopy("Garden Bed", _rect(6, 6, 3, 4), 3.5))[
            "properties"]
        self.assertEqual((props["kind"], props["building"]),
                         ("building", "garage"))

    def test_scanned_and_marked_buildings_keep_everything(self):
        for st in ("Building (OSM)", "Building footprint"):
            before = _canopy(st, _rect(6, 6, 8, 10), 6.0, source="osm")
            after = _upgraded(before)["properties"]
            self.assertEqual(after["kind"], "building", st)
            self.assertEqual(after["shape_type"], st)
            self.assertEqual(after["height_m"], 6.0)

    def test_a_tree_crown_and_an_imported_footprint_are_left(self):
        crown = _canopy("Tree canopy", _rect(6, 6, 6, 6), 8.0,
                        caster_kind="tree")
        imported = _canopy("Imported footprint", _rect(6, 6, 6, 6), 4.0)
        for f in (crown, imported):
            self.assertEqual(_upgraded(f), f)

    def test_lines_gain_their_kind(self):
        props = _upgraded(_line("fence", [(0, 0), (8, 0)]))["properties"]
        self.assertEqual((props["kind"], props["fence_kind"]),
                         ("fence", "rail"))
        props = _upgraded(_line("windbreak", [(0, 0), (8, 0)]))["properties"]
        self.assertEqual(props["kind"], "windbreak")


class OnceAndEverywhere(unittest.TestCase):

    def _everything(self):
        return _yard(*[_structure(s) for s in (
            "pond", "rain_garden", "rock_xeriscape", "raised_bed",
            "native_lawn_patch", "shed", "swale", "fence", "bee_hotel")],
            _shape("Garden Bed", _rect(3, 3, 2, 2)),
            _line("hedge", [(0, 11), (11, 11)]))

    def test_it_is_idempotent(self):
        project = self._everything()
        # Ten: everything but the bee hotel, which is an object.
        self.assertEqual(U.upgrade(project), 10)
        self.assertEqual(project["properties"]["schema_version"], "1.11")
        snapshot = json.dumps(project, sort_keys=True)
        self.assertEqual(U.upgrade(project), 0)
        self.assertEqual(json.dumps(project, sort_keys=True), snapshot)

    def test_a_design_with_nothing_to_convert_is_untouched(self):
        project = _yard()
        project["properties"]["schema_version"] = "1.10"
        self.assertEqual(U.upgrade(project), 0)
        self.assertEqual(project["properties"]["schema_version"], "1.10")

    def test_load_project_converts_and_leaves_the_file(self):
        from src.project import load_project
        tmp = tempfile.mkdtemp(prefix="yard_up_")
        path = os.path.join(tmp, "old.perma.geojson")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self._everything(), fh)
        before = open(path, encoding="utf-8").read()
        data = load_project(path)
        kinds = {(f["properties"] or {}).get("kind")
                 for f in data["features"]}
        self.assertTrue({"pond", "bed", "building", "swale", "fence",
                         "hedge"} <= kinds)
        self.assertEqual(open(path, encoding="utf-8").read(), before)

    def test_the_example_is_in_the_palettes_form(self):
        from src.onboarding import build_example_project
        project, _missing = build_example_project(
            lookup=lambda name: {"id": 1, "common_name": name})
        lines = [f for f in project["features"]
                 if f["properties"].get("element_type") == "hedgerow"]
        self.assertTrue(lines)
        for f in lines:
            self.assertEqual(f["properties"]["kind"], "fence")
        self.assertEqual(U.upgrade(project), 0)


class WhatTheReadersSayAfterwards(unittest.TestCase):
    """Where the numbers move, on purpose (the V3.71 plan's list)."""

    def test_a_converted_pond_is_still_a_pond_everywhere(self):
        project = _yard(_structure("pond"))
        U.upgrade(project)
        defs = Y.structure_defs(project)
        self.assertEqual([d["id"] for d in defs], ["pond"])
        self.assertTrue(defs[0]["drawn"])
        self.assertAlmostEqual(defs[0]["scale"], 1.0, delta=0.05)
        from src.pond_planting import ponds_in
        self.assertEqual(len(ponds_in(project["features"])), 1)

    def test_its_score_does_not_move(self):
        from src.habitat_score import HABITAT_STRUCTURE_IDS
        before = _yard(*[_structure(s, 2 + 3 * i, 2 + 3 * i) for i, s in
                         enumerate(("pond", "rain_garden", "rock_xeriscape",
                                    "native_lawn_patch", "swale"))])
        after = copy.deepcopy(before)
        U.upgrade(after)

        def habitat(project):
            return sorted(d["id"] for d in Y.structure_defs(project)
                          if d["id"] in HABITAT_STRUCTURE_IDS)
        self.assertEqual(habitat(before), habitat(after))
        self.assertEqual(len(habitat(after)), 5)

    def test_a_converted_swale_is_still_kept_out_of(self):
        from src.exclusion import keepout_areas
        project = _yard(_structure("swale"))
        U.upgrade(project)
        keep = keepout_areas(project)
        self.assertEqual(len(keep.shapes), 1)
        self.assertEqual(Y.structure_defs(project)[0]["id"], "swale")

    def test_a_raised_bed_is_still_where_plan_my_yard_plants(self):
        from src.exclusion import fill_regions
        project = _yard(_structure("raised_bed"))
        U.upgrade(project)
        self.assertEqual(len(fill_regions(project)), 1)
        self.assertEqual(Y.structure_defs(project)[0]["id"], "raised_bed")

    def test_a_bed_at_ground_level_costs_nothing(self):
        project = _yard(_shape("Garden Bed", _rect(6, 6, 3, 4)))
        U.upgrade(project)
        self.assertEqual(Y.structure_defs(project), [])

    def test_a_converted_shed_and_fence_leave_the_buy_list(self):
        """A drawn building or fence is most often there already (V3.72)."""
        project = _yard(_structure("shed"), _structure("fence"))
        self.assertEqual(len(Y.structure_defs(project)), 2)
        U.upgrade(project)
        self.assertEqual(Y.structure_defs(project), [])


if __name__ == "__main__":
    unittest.main()
