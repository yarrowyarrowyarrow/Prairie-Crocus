"""
src/yard_kinds.py — every kind of thing in a yard, as one row of one table
(V3.71, F280's first increment).

Design principle P9 (uncertainty is a feature: never false precision) — see
docs/DESIGN_PHILOSOPHY.md. A pond is one thing; the app must not say two
different things about it depending on which tool put it on the map.

The V3.69 review (``docs/plans/V3.69-structures-and-shapes-reviewed.md``) found
each structure and the shape that draws the same thing meaning different things
to every part of the app: a placed Pond scored and got pond plants and was
counted as ground to plant, a drawn Water Feature the reverse; a placed Raised
Bed was planted over as if absent and a drawn Garden Bed was the plan's only
ground; a shed had plants inside it. Each reader held its own list of shape
words and structure ids. This module is the one list, and the readers ask it
(``docs/plans/V3.71-one-palette.md``):

* :data:`KINDS`, each a :class:`Kind`: its words, its verb, the names it has
  had (Draw › Shape's shape types, Placement › Structures' ids, a drawn line's
  style), and the answers the readers need: whether Plan My Yard plants it
  (:data:`FILL`) or keeps out of it (:data:`KEEP_OUT`), the ground it is (wet or
  dry, for F281), whether it is a habitat structure for the score, what it is to
  the Water page, its care cue, its look in 3D.
* :func:`kind_of`, :func:`is_fill`, :func:`is_keep_out`: what a feature is.
* :func:`footprint_ring`: a feature's outline on the map, drawn or placed (a
  placed structure's is the one ``placeStructureOnMap`` draws).
* :func:`structure_defs`: what the score, the Water page, the care hours and the
  costs are handed, a drawn pond included as a pond.
* The readers' old names, derived (:func:`shape_types`, :func:`struct_ids`), so
  ``yard_overview.BED_SHAPES`` and the rest keep their values and their callers.

Qt-free, DB-free (the catalogue is read only for a drawn twin's definition) and
network-free. ``tests/test_yard_kinds.py`` holds the readers to it and fails on
a structure id or a shape word written as a literal in a new reader.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Optional

#: What Plan My Yard does with a kind's ground: plants into it, or keeps out.
FILL = "fill"
KEEP_OUT = "keep_out"
NONE = ""

AREA, LINE, OBJECT = "area", "line", "object"
WET, DRY = "wet", "dry"


@dataclass(frozen=True)
class Kind:
    """One kind of thing in a yard."""
    key: str
    words: str
    verb: str                        # AREA | LINE | OBJECT
    shape_types: tuple = ()          # Draw › Shape's names for it
    struct_ids: tuple = ()           # Placement › Structures' ids for it
    line_styles: tuple = ()          # a drawn line's ``style``
    planting: str = NONE             # FILL | KEEP_OUT | NONE
    ground: str = ""                 # WET | DRY: what the planner should
                                     # read it as (F281 acts on it)
    habitat: bool = False            # a habitat structure, for the score
    water: str = ""                  # the Water page's input it answers
    cue: str = ""                    # a care cue: lawn | bed | path | border
    look: str = ""                   # its 3D surface (scene_site)
    drawn_twin: str = ""             # the structure a drawn one counts as


def _zone(key: str) -> str:
    """A lawn-conversion zone's label (``src/lawn_zones.py`` owns them)."""
    from src.lawn_zones import ZONE_TYPES
    return ZONE_TYPES[key]["label"]


#: The table. **Order matters**: the readers' derived tuples keep the order
#: they had (``yard_overview.BED_SHAPES`` then ``NOT_PLANTED``).
KINDS: tuple = (
    # Beds and ground Plan My Yard plants.
    Kind("bed", "Bed", AREA, shape_types=("Garden Bed",),
         struct_ids=("raised_bed",), planting=FILL, cue="bed", look="bed"),
    Kind("mulch", "Mulch", AREA, shape_types=("Mulch Area",), planting=FILL,
         cue="bed", look="mulch"),
    Kind("lawn_to_convert", _zone("lawn_remaining"), AREA,
         shape_types=(_zone("lawn_remaining"),), planting=FILL,
         cue="lawn_zone", look="lawn"),
    Kind("restoration_1", _zone("restoration_year_1"), AREA,
         shape_types=(_zone("restoration_year_1"),), planting=FILL,
         look="seeded"),
    Kind("restoration_3", _zone("restoration_year_3"), AREA,
         shape_types=(_zone("restoration_year_3"),), planting=FILL,
         look="young_meadow"),
    Kind("established", _zone("established_native"), AREA,
         shape_types=(_zone("established_native"),), planting=FILL,
         look="meadow"),
    Kind("rock_garden", "Rock garden", AREA,
         struct_ids=("rock_xeriscape",), planting=FILL, ground=DRY,
         habitat=True),
    # Ground Plan My Yard keeps out of.
    Kind("lawn", "Lawn", AREA, shape_types=("Lawn Area",), planting=KEEP_OUT,
         cue="lawn", look="lawn"),
    Kind("native_lawn", "Native lawn", AREA,
         struct_ids=("native_lawn_patch",), planting=KEEP_OUT, habitat=True,
         cue="lawn"),
    Kind("path", "Path", AREA, shape_types=("Pathway",), planting=KEEP_OUT,
         cue="path", look="path"),
    Kind("patio", "Patio", AREA, shape_types=("Patio / Deck",),
         planting=KEEP_OUT, cue="path", look="patio"),
    Kind("pond", "Pond", AREA, shape_types=("Water Feature",),
         struct_ids=("pond",), planting=KEEP_OUT, ground=WET, habitat=True,
         water="ponds", look="water", drawn_twin="pond"),
    Kind("remnant", _zone("existing_remnant"), AREA,
         shape_types=(_zone("existing_remnant"),), planting=KEEP_OUT,
         look="meadow"),
    # A rain garden is kept out of until F281 can plant it with what takes wet
    # feet: the planner's cells carry no moisture, and ordinary plants in a
    # rain garden's floor would be worse than none (the V3.71 plan).
    Kind("rain_garden", "Rain garden", AREA, struct_ids=("rain_garden",),
         planting=KEEP_OUT, ground=WET, habitat=True),
    Kind("building", "Building", AREA, struct_ids=("shed",),
         planting=KEEP_OUT),
    Kind("custom", "Custom", AREA, shape_types=("Custom",), look="custom"),
    # Lines.
    Kind("swale", "Swale", LINE, struct_ids=("swale",), planting=KEEP_OUT,
         ground=WET, habitat=True, water="swales"),
    Kind("fence", "Fence", LINE, struct_ids=("fence",), line_styles=("fence",),
         cue="border"),
    Kind("hedge", "Hedge", LINE, line_styles=("hedge",)),
    Kind("living_fence", "Living fence", LINE, line_styles=("living_fence",)),
    Kind("windbreak", "Windbreak", LINE, line_styles=("windbreak",)),
    # Objects: kept out of at their footprint (until V3.71 only a barrel and a
    # brush pile were, so a plan could put plants in a fire pit).
    Kind("bee_hotel", "Bee hotel", OBJECT, struct_ids=("bee_hotel",),
         planting=KEEP_OUT, habitat=True),
    Kind("bee_log", "Bee log", OBJECT, struct_ids=("native_bee_log",),
         planting=KEEP_OUT, habitat=True),
    Kind("snag", "Snag", OBJECT, struct_ids=("snag",), planting=KEEP_OUT,
         habitat=True),
    Kind("brush_pile", "Brush pile", OBJECT, struct_ids=("brush_pile",),
         planting=KEEP_OUT, habitat=True),
    Kind("compost_bin", "Compost bin", OBJECT, struct_ids=("compost_bin",),
         planting=KEEP_OUT),
    Kind("rain_barrel", "Rain barrel", OBJECT, struct_ids=("rain_barrel",),
         planting=KEEP_OUT, ground=WET, habitat=True, water="rain_barrels"),
    Kind("fire_pit", "Fire pit", OBJECT, struct_ids=("fire_pit",),
         planting=KEEP_OUT),
)

BY_KEY: dict = {k.key: k for k in KINDS}
_BY_SHAPE: dict = {t: k for k in KINDS for t in k.shape_types}
_BY_STRUCT: dict = {s: k for k in KINDS for s in k.struct_ids}
_BY_STYLE: dict = {s: k for k in KINDS for s in k.line_styles}


# ── the readers' old names, derived ─────────────────────────────────────────

def shape_types(**where) -> tuple:
    """The shape types of the kinds whose fields equal ``where``, in the
    table's order: ``shape_types(planting=FILL)`` is the Overview's beds."""
    return tuple(t for k in KINDS
                 if all(getattr(k, f) == v for f, v in where.items())
                 for t in k.shape_types)


def struct_ids(**where) -> tuple:
    """The structure ids of the kinds whose fields equal ``where``; a field
    given as ``True`` matches any value that is set (``water=True``)."""
    def ok(k):
        return all((bool(getattr(k, f)) if v is True else getattr(k, f) == v)
                   for f, v in where.items())
    return tuple(s for k in KINDS if ok(k) for s in k.struct_ids)


def surface_looks() -> dict:
    """``{shape_type: look}``: what each drawn area is in 3D."""
    return {t: k.look for k in KINDS for t in k.shape_types if k.look}


# ── what a feature is ───────────────────────────────────────────────────────

def struct_id_of(props: dict) -> str:
    """A structure feature's id, wherever it was stored (the interactive path
    stores ``struct_id``, the generator ``struct_def``, an old file
    ``structure_id``)."""
    props = props or {}
    return (props.get("struct_id")
            or (props.get("struct_def") or {}).get("id")
            or props.get("structure_id") or "")


def kind_of(feature: dict) -> Optional[Kind]:
    """The kind a feature is, or ``None`` (a plant, a boundary, a building
    footprint, an existing tree, anything the table does not name)."""
    props = (feature or {}).get("properties") or {}
    et = props.get("element_type")
    if et == "structure":
        return _BY_STRUCT.get(struct_id_of(props))
    if et in ("custom_shape", "canopy_footprint"):
        return _BY_SHAPE.get(props.get("shape_type") or "")
    if et == "hedgerow":
        return _BY_STYLE.get(props.get("style") or "")
    return None


def is_fill(feature: dict) -> bool:
    """Ground Plan My Yard plants into (a bed, a placed raised bed, a rock
    garden, a lawn-conversion zone)."""
    k = kind_of(feature)
    return k is not None and k.planting == FILL


def is_keep_out(feature: dict) -> bool:
    """Ground Plan My Yard keeps out of."""
    k = kind_of(feature)
    return k is not None and k.planting == KEEP_OUT


# ── where it is ─────────────────────────────────────────────────────────────

_M_PER_DEG = 111320.0
_CIRCLE_SIDES = 32


def footprint_ring(feature: dict) -> Optional[list]:
    """The feature's outline as a closed ring of ``[lng, lat]``: a drawn
    area's own ring, or a placed structure's as the 2D map draws it (a circle
    of ``size_m`` for a circle or an ellipse, otherwise a rectangle ``size_m``
    north-south by ``width_m`` east-west, ``src/scene_structures.footprint``).
    ``None`` for a line or anything else."""
    geom = (feature or {}).get("geometry") or {}
    props = (feature or {}).get("properties") or {}
    if geom.get("type") == "Polygon":
        ring = (geom.get("coordinates") or [None])[0]
        return ring if ring and len(ring) >= 3 else None
    if props.get("element_type") != "structure" or geom.get("type") != "Point":
        return None
    coords = geom.get("coordinates") or []
    if len(coords) < 2:
        return None
    from src.scene_structures import footprint
    fp = footprint(props)
    lng0, lat0 = float(coords[0]), float(coords[1])
    kx = _M_PER_DEG * (math.cos(math.radians(lat0)) or 1e-9)
    if fp["shape"] in ("circle", "ellipse"):
        r = fp["size_m"] / 2.0
        pts = [(r * math.cos(t), r * math.sin(t))
               for t in (i / _CIRCLE_SIDES * math.tau
                         for i in range(_CIRCLE_SIDES))]
    else:
        hn, he = fp["size_m"] / 2.0, fp["width_m"] / 2.0
        pts = [(-he, -hn), (he, -hn), (he, hn), (-he, hn)]
    ring = [[lng0 + e / kx, lat0 + n / _M_PER_DEG] for e, n in pts]
    return ring + [ring[0]]


def features_of(project_or_features) -> list:
    if isinstance(project_or_features, dict):
        return list(project_or_features.get("features") or [])
    return list(project_or_features or [])


def fill_rings(project_or_features) -> list:
    """The outlines Plan My Yard plants into, drawn or placed."""
    return [r for f in features_of(project_or_features)
            if is_fill(f) and (r := footprint_ring(f))]


# ── what the score, the Water page, the hours and the costs are handed ──────

def structure_defs(project_or_features: Iterable) -> list:
    """The structure definitions of a design, as the habitat score, the Water
    page, the care hours and the buy list read them: each placed structure's
    stored ``struct_def``, and **a drawn kind's twin** (a drawn pond is a pond,
    with the catalogue pond's definition, marked ``drawn``)."""
    from src.db.structures import get_structure
    out = []
    for f in features_of(project_or_features):
        props = f.get("properties") or {}
        if props.get("element_type") == "structure":
            sd = props.get("struct_def") or {}
            out.append(sd if sd else {"id": struct_id_of(props)})
            continue
        k = kind_of(f)
        if (k is not None and k.drawn_twin
                and props.get("element_type") == "custom_shape"):
            twin = dict(get_structure(k.drawn_twin) or {"id": k.drawn_twin})
            twin["drawn"] = True
            out.append(twin)
    return out
