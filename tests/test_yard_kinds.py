"""
tests/test_yard_kinds.py — one table of kinds every reader asks (V3.71, F280's
first increment; ``docs/plans/V3.71-one-palette.md``).

The V3.69 review found each structure and the shape that draws the same thing
meaning different things to the score, the Overview, Plan My Yard, the Water
page and the pond planting. These hold:

* the table covers everything the app can put down, each name once;
* the readers' old lists are the table's answers, the unchanged ones unchanged;
* each pair now agrees in every reader (the review's readers table);
* a placed structure's footprint is the one the map draws;
* a drawn pond is seated like a placed one;
* Plan My Yard plants a placed raised bed and nothing inside a shed;
* no new module writes a structure id or a shape word as a literal (a ratchet).
"""

import ast
import math
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import yard_kinds as Y                               # noqa: E402

_LAT, _LNG = 53.52, -113.52
_KY = 111320.0
_KX = 111320.0 * math.cos(math.radians(_LAT))


def _ll(east, north):
    return [_LNG + east / _KX, _LAT + north / _KY]


def _ring(points):
    ring = [_ll(e, n) for e, n in points]
    return ring + [ring[0]]


def _rect(cx, cy, ns, ew):
    return _ring(((cx - ew / 2, cy - ns / 2), (cx + ew / 2, cy - ns / 2),
                  (cx + ew / 2, cy + ns / 2), (cx - ew / 2, cy + ns / 2)))


def _ellipse(cx, cy, ew, ns, n=36):
    return _ring([(cx + ew / 2 * math.cos(t), cy + ns / 2 * math.sin(t))
                  for t in (i / n * math.tau for i in range(n))])


def _structure(sid, e=6.0, n=6.0, size_m=None):
    from src.db.structures import get_structure
    sd = dict(get_structure(sid))
    if size_m is not None:
        sd["size_m"] = float(size_m)
    return {"type": "Feature",
            "geometry": {"type": "Point", "coordinates": _ll(e, n)},
            "properties": {"element_type": "structure", "struct_id": sid,
                           "size_m": sd["size_m"], "struct_def": sd}}


def _shape(kind, ring):
    return {"type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [ring]},
            "properties": {"element_type": "custom_shape", "shape_type": kind,
                           "label": kind}}


def _yard(*features, w=12.0, d=12.0):
    return {"type": "FeatureCollection",
            "properties": {"site_config": {"latitude": _LAT + d / 2 / _KY,
                                           "longitude": _LNG + w / 2 / _KX}},
            "features": [{"type": "Feature",
                          "geometry": {"type": "Polygon", "coordinates": [
                              _ring(((0, 0), (w, 0), (w, d), (0, d)))]},
                          "properties": {"element_type": "property_boundary",
                                         "boundary_id": "b1"}}]
            + list(features)}


class TheTableCoversWhatTheAppPutsDown(unittest.TestCase):

    def test_every_structure_shape_and_line_has_one_kind(self):
        from src.db.structures import STRUCTURES
        from src.lawn_zones import ZONE_TYPES
        for s in STRUCTURES:
            self.assertIn(s["id"], Y._BY_STRUCT, s["id"])
        # Draw › Shape's seven area types (retired in V3.72; old designs
        # still hold them) and its four line styles.
        for name in ["Garden Bed", "Pathway", "Patio / Deck", "Lawn Area",
                     "Mulch Area", "Water Feature", "Custom"] + [
                         z["label"] for z in ZONE_TYPES.values()]:
            self.assertIn(name, Y._BY_SHAPE, name)
        for style in ("hedge", "fence", "living_fence", "windbreak"):
            self.assertIn(style, Y._BY_STYLE, style)

    def test_each_name_belongs_to_one_kind(self):
        keys = [k.key for k in Y.KINDS]
        self.assertEqual(len(keys), len(set(keys)))
        for field in ("shape_types", "struct_ids", "line_styles"):
            names = [n for k in Y.KINDS for n in getattr(k, field)]
            self.assertEqual(len(names), len(set(names)), field)

    def test_answers_are_from_the_vocabulary(self):
        for k in Y.KINDS:
            self.assertIn(k.verb, (Y.AREA, Y.LINE, Y.OBJECT), k.key)
            self.assertIn(k.planting, (Y.FILL, Y.KEEP_OUT, Y.NONE), k.key)
            self.assertIn(k.ground, ("", Y.WET, Y.DRY), k.key)


class TheReadersAskTheTable(unittest.TestCase):
    """The old lists are now the table's answers. The ones V3.71 did not mean
    to change are pinned to the values they had."""

    def test_the_overviews_shapes_are_unchanged(self):
        from src.yard_overview import BED_SHAPES, NOT_PLANTED
        self.assertEqual(BED_SHAPES, (
            "Garden Bed", "Mulch Area", "Lawn — to convert",
            "Restoration — Year 1", "Restoration — Year 3",
            "Established native"))
        self.assertEqual(NOT_PLANTED, (
            "Lawn Area", "Pathway", "Patio / Deck", "Water Feature",
            "Existing remnant"))

    def test_score_water_and_wet_ground_are_unchanged(self):
        from src.design_inputs import WATER_STRUCTURES
        from src.habitat_score import HABITAT_STRUCTURE_IDS
        from src.zoning import WET_STRUCTURE_IDS
        self.assertEqual(HABITAT_STRUCTURE_IDS, frozenset({
            "pond", "swale", "rain_garden", "rain_barrel", "native_bee_log",
            "bee_hotel", "brush_pile", "snag", "rock_xeriscape",
            "native_lawn_patch"}))
        self.assertEqual(WATER_STRUCTURES, {"rain_barrel": "rain_barrels",
                                            "pond": "ponds",
                                            "swale": "swales"})
        self.assertEqual(WET_STRUCTURE_IDS, frozenset(
            {"pond", "swale", "rain_garden", "rain_barrel"}))

    def test_every_structure_plan_my_yard_should_not_plant_is_kept_out(self):
        """V3.71's change: a shed, a fire pit and the other objects join the
        water structures and the brush pile."""
        from src.exclusion import EXCLUDING_STRUCTURE_IDS
        self.assertEqual(EXCLUDING_STRUCTURE_IDS, frozenset(
            Y.struct_ids(planting=Y.KEEP_OUT)))
        for sid in ("shed", "fire_pit", "compost_bin", "bee_hotel",
                    "native_lawn_patch", "pond", "brush_pile"):
            self.assertIn(sid, EXCLUDING_STRUCTURE_IDS, sid)
        for sid in ("raised_bed", "rock_xeriscape", "fence"):
            self.assertNotIn(sid, EXCLUDING_STRUCTURE_IDS, sid)

    def test_the_3d_looks_and_the_cues(self):
        import src.cues_to_care as C
        from src.scene_site import SURFACE_KINDS
        self.assertEqual(SURFACE_KINDS, Y.surface_looks())
        self.assertEqual(C._LAWN_STRUCTURES, ("native_lawn_patch",))
        self.assertIn("raised_bed", C._BORDER_STRUCTURES)    # a bed's edge


class EachPairNowAgrees(unittest.TestCase):
    """The review's pairs, through the real readers."""

    def _readers(self, project):
        from src.design_inputs import water_features
        from src.exclusion import fill_regions, keepout_areas
        from src.habitat_score import HABITAT_STRUCTURE_IDS
        from src.pond_planting import ponds_in
        from src.yard_overview import _parts
        defs = Y.structure_defs(project)
        keep = keepout_areas(project)
        _b, beds, holes = _parts(project)
        return {
            "habitat": sorted({d.get("id") for d in defs}
                              & HABITAT_STRUCTURE_IDS),
            "water": water_features(defs),
            "ponds": len(ponds_in(project["features"])),
            "fill": len(fill_regions(project)),
            "keep_out": len(keep.circles) + len(keep.shapes),
            "bed": len(beds), "hole": len(holes),
        }

    def test_a_placed_pond_and_a_drawn_water_feature(self):
        placed = self._readers(_yard(_structure("pond")))
        drawn = self._readers(_yard(_shape("Water Feature",
                                           _ellipse(6, 6, 6, 4))))
        self.assertEqual(placed, drawn)
        self.assertEqual(placed["habitat"], ["pond"])
        self.assertEqual(placed["ponds"], 1)
        self.assertEqual(placed["hole"], 1)       # off the planting area

    def test_a_raised_bed_and_a_drawn_garden_bed(self):
        placed = self._readers(_yard(_structure("raised_bed")))
        drawn = self._readers(_yard(_shape("Garden Bed", _rect(6, 6, 3, 1.2))))
        self.assertEqual(placed, drawn)
        self.assertEqual((placed["fill"], placed["bed"]), (1, 1))

    def test_a_native_lawn_patch_and_a_drawn_lawn(self):
        placed = self._readers(_yard(_structure("native_lawn_patch")))
        drawn = self._readers(_yard(_shape("Lawn Area", _rect(6, 6, 6, 4))))
        self.assertEqual({k: v for k, v in placed.items() if k != "habitat"},
                         {k: v for k, v in drawn.items() if k != "habitat"})
        # The native patch keeps its habitat point (F256 re-weighs them).
        self.assertEqual(placed["habitat"], ["native_lawn_patch"])

    def test_a_shed_is_off_the_planting_area_and_kept_out(self):
        r = self._readers(_yard(_structure("shed")))
        self.assertEqual((r["keep_out"], r["hole"]), (1, 1))


class TheFootprintIsTheMaps(unittest.TestCase):

    def _xy(self, ring):
        return [((p[0] - _LNG) * _KX, (p[1] - _LAT) * _KY) for p in ring[:-1]]

    def test_a_rectangle_runs_north_south_at_its_size_and_width(self):
        xy = self._xy(Y.footprint_ring(_structure("raised_bed", 0, 0, 6.0)))
        ew = max(x for x, _ in xy) - min(x for x, _ in xy)
        ns = max(y for _, y in xy) - min(y for _, y in xy)
        self.assertAlmostEqual(ns, 6.0, places=2)
        self.assertAlmostEqual(ew, 1.2, places=2)

    def test_a_circle_is_its_size_across(self):
        xy = self._xy(Y.footprint_ring(_structure("pond", 0, 0)))
        for x, y in xy:
            self.assertAlmostEqual(math.hypot(x, y), 3.0, places=2)


class ADrawnPondIsSeatedLikeAPlacedOne(unittest.TestCase):

    def test_its_seats_are_fractions_of_the_way_to_its_edge(self):
        from src.pond_planting import DrawnPond, ponds_in
        f = _shape("Water Feature", _ellipse(0, 0, 6, 4, n=72))
        (pond,) = ponds_in([f])
        self.assertIsInstance(pond, DrawnPond)
        for (u, v), (ex, ny) in (((0.7, 0), (2.1, 0)), ((0, 0.7), (0, 1.4)),
                                 ((0, 0.85), (0, 1.7))):
            x, y = pond.xy(*pond.at(u, v))
            self.assertAlmostEqual(x, ex, delta=0.02)
            self.assertAlmostEqual(y, ny, delta=0.02)
        self.assertTrue(pond.holds(_LAT, _LNG))
        self.assertFalse(pond.holds(_LAT + 4 / _KY, _LNG))
        self.assertAlmostEqual(pond.water_m2, math.pi * 6, delta=0.1)

    def test_it_is_a_pond_to_the_score_and_the_water_page(self):
        from src.design_inputs import water_features
        defs = Y.structure_defs([_shape("Water Feature",
                                        _ellipse(0, 0, 6, 4))])
        self.assertEqual([d["id"] for d in defs], ["pond"])
        self.assertTrue(defs[0]["drawn"])
        self.assertEqual(water_features(defs)["ponds"], 1)


class PlanMyYardPlantsWhereTheTableSays(unittest.TestCase):
    """The review's planner cases, through the real offline generator."""

    @classmethod
    def setUpClass(cls):
        import src.db.plants as plants
        cls._tmp = tempfile.mkdtemp(prefix="yard_kinds_")
        cls._saved = (plants._DATA_DIR, plants._DB_PATH)
        plants._DATA_DIR = cls._tmp
        plants._DB_PATH = os.path.join(cls._tmp, "yard_kinds.db")
        plants.init_db()

    @classmethod
    def tearDownClass(cls):
        import src.db.plants as plants
        plants._DATA_DIR, plants._DB_PATH = cls._saved

    def _inside(self, feature):
        from src.llm_design import generate_design_offline
        from src.onboarding import FIRST_RUN_GOALS
        yard = _yard(feature)
        ring = yard["features"][0]["geometry"]["coordinates"][0][:-1]
        made = generate_design_offline(
            site_config=yard["properties"]["site_config"],
            boundary=[[p[1], p[0]] for p in ring], goals=list(FIRST_RUN_GOALS),
            density="balanced", cover=0.70,
            existing_features=[feature]).as_dict()
        from src.geometry import point_in_ring
        foot = Y.footprint_ring(feature)
        plants = [f for f in made["features"]
                  if (f.get("properties") or {}).get("plant_id")]
        inside = sum(1 for f in plants
                     if point_in_ring(f["geometry"]["coordinates"][1],
                                      f["geometry"]["coordinates"][0], foot))
        return len(plants), inside

    def test_a_placed_raised_bed_is_where_the_plan_goes(self):
        total, inside = self._inside(_structure("raised_bed", 6, 6, 6.0))
        self.assertGreater(total, 0)
        self.assertEqual(inside, total)

    def test_nothing_is_planted_inside_a_shed(self):
        total, inside = self._inside(_structure("shed"))
        self.assertGreater(total, 0)
        self.assertEqual(inside, 0)


#: Structure ids and shape words written as literals, per module, outside the
#: modules that own them. A ratchet, like ``tests/test_vocabulary.py``: a new
#: module or a higher count fails (ask ``src/yard_kinds.py``); a lower count
#: fails until it is lowered here, so the list only shrinks.
OWNERS = {"src/yard_kinds.py", "src/db/structures.py", "src/lawn_zones.py",
          # The conversion on open names what it converts (V3.72).
          "src/yard_upgrade.py"}
KNOWN = {
    "src/advanced_tools.py": 1,     # the Custom shape is an advanced tool
    "src/analysis_panel.py": 10,    # the habitat structures' display names
    "src/bee_habitat.py": 5,        # which structures a bee nests in
    "src/bird_body_plan.py": 1,     # a duck stands on a pond
    "src/llm_design.py": 2,         # the back yard's two structures (Y5)
    "src/plan_notes.py": 2,         # their words in a plan's notes
    "src/pond_habit.py": 1,         # the pond's water surface
    "src/pond_planting.py": 1,      # a pond is the pond kind
    "src/project.py": 1,            # a shape with no type is Custom
    "src/scene_site.py": 2,         # the fence line style
    "src/scene_structures.py": 3,   # a Fence / Wall is a fence line
    "src/sprite_gallery.py": 2,     # the gallery's specimens
}


def _literal_counts() -> dict:
    words = {n for k in Y.KINDS for n in k.struct_ids + k.shape_types}
    out = {}
    src = os.path.join(ROOT, "src")
    for folder, _dirs, files in os.walk(src):
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(folder, name)
            rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            docs = set()
            for node in ast.walk(tree):
                body = getattr(node, "body", None)
                if (isinstance(node, (ast.Module, ast.FunctionDef,
                                      ast.AsyncFunctionDef, ast.ClassDef))
                        and body and isinstance(body[0], ast.Expr)
                        and isinstance(body[0].value, ast.Constant)):
                    docs.add(id(body[0].value))
            n = sum(1 for node in ast.walk(tree)
                    if isinstance(node, ast.Constant)
                    and isinstance(node.value, str) and node.value in words
                    and id(node) not in docs)
            if n and rel not in OWNERS:
                out[rel] = n
    return out


class NoNewReaderGrowsItsOwnList(unittest.TestCase):

    def test_the_ratchet(self):
        found = _literal_counts()
        grew = {m: n for m, n in found.items() if n > KNOWN.get(m, 0)}
        self.assertEqual(grew, {}, "ask src/yard_kinds.py instead of writing "
                                   "a structure id or a shape word")
        shrank = {m: (KNOWN[m], found.get(m, 0)) for m in KNOWN
                  if found.get(m, 0) < KNOWN[m]}
        self.assertEqual(shrank, {}, "lower KNOWN to the new count")


if __name__ == "__main__":
    unittest.main()
