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

Since V3.72 it is also the Yard palette's table (``src/yard_palette.py``,
``docs/plans/V3.72-the-yard-palette.md``): :data:`PALETTE`'s headings, each
kind's sentence, options and map colours, and :func:`drawn_props`, the one way
a drawn feature is stored (with its ``kind``, file format 1.11). A drawn kind
keeps an older copy's shape type, so :func:`kind_of` reads ``kind`` first.

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

#: The words on the button that puts a kind on the map (V3.72).
VERB_WORDS = {AREA: "Draw on the map", LINE: "Draw on the map",
              OBJECT: "Place on the map"}


@dataclass(frozen=True)
class Option:
    """One thing a person chooses about a kind (V3.72, the owner's Q6): a
    list of ``choices`` (``(value, words)``), a number between ``lo`` and
    ``hi`` when there are none, or free text when ``text``."""
    key: str                         # the feature property it is stored as
    words: str
    choices: tuple = ()
    default: object = None
    unit: str = ""
    lo: float = 0.0
    hi: float = 0.0
    step: float = 0.0
    text: bool = False


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
    # The palette (V3.72).
    about: str = ""                  # one sentence under its name
    options: tuple = ()              # :class:`Option`, in the order shown
    # How the 2D map draws a drawn one: fill, outline, opacity, dashes (an
    # area), or a line's colour. Draw › Shape's presets until V3.72.
    colours: tuple = ()
    # The shape type a drawn one is stored with, for a copy of the app older
    # than V3.72 (which reads no ``kind``): its own where it has one, else the
    # closest older name, else Custom (the V3.71 plan).
    legacy_shape: str = ""
    advanced: bool = False           # only with Advanced tools on


def _zone(key: str) -> str:
    """A lawn-conversion zone's label (``src/lawn_zones.py`` owns them)."""
    from src.lawn_zones import ZONE_TYPES
    return ZONE_TYPES[key]["label"]


def _zone_colours(key: str) -> tuple:
    from src.lawn_zones import ZONE_TYPES
    z = ZONE_TYPES[key]
    return (z["fill"], z["stroke"], z["opacity"], "")


#: The surfaces a path and a patio are made of (the owner's Q6).
PATH_SURFACES = (("flagstone", "Flagstone"), ("pavers", "Pavers"),
                 ("gravel", "Gravel"), ("wood_chips", "Wood chips"),
                 ("stepping_stones", "Stepping stones"))
PATIO_SURFACES = (("pavers", "Pavers"), ("flagstone", "Flagstone"),
                  ("concrete", "Concrete"))
#: A raised bed's height, centimetres; 0 is a bed at ground level.
RAISED_CM = ((0, "No, at ground level"), (30, "30 cm"), (45, "45 cm"),
             (60, "60 cm"), (90, "90 cm"))
FENCE_KINDS = (("rail", "Rail"), ("board", "Board"),
               ("chain_link", "Chain link"))
#: A building's height when a person names only what it is: **stated
#: estimates** (a bungalow's ridge, a single garage, a garden shed); the height
#: box beside it is theirs to change.
BUILDING_HEIGHT_M = {"house": 6.0, "garage": 4.0, "shed": 2.4}
BUILDINGS = (("house", "House"), ("garage", "Garage"), ("shed", "Shed"))


def _hedge_options(width: float) -> tuple:
    return (Option("width_m", "Width", default=width, unit="m", lo=0.5,
                   hi=5.0, step=0.5),
            Option("spacing_m", "How far apart", default=1.0, unit="m",
                   lo=0.3, hi=5.0, step=0.1),
            Option("species", "What is planted (optional)", default="",
                   text=True))


#: The table. **Order matters**: the readers' derived tuples keep the order
#: they had (``yard_overview.BED_SHAPES`` then ``NOT_PLANTED``).
KINDS: tuple = (
    # Beds and ground Plan My Yard plants.
    Kind("bed", "Bed", AREA, shape_types=("Garden Bed",),
         struct_ids=("raised_bed",), planting=FILL, cue="bed", look="bed",
         drawn_twin="raised_bed",
         about="Ground to plant. Raised, it is a bed built up in a frame.",
         options=(Option("raised_cm", "Raised", RAISED_CM, 0),),
         colours=("#4caf50", "#2e7d32", 0.25, ""), legacy_shape="Garden Bed"),
    Kind("mulch", "Mulch", AREA, shape_types=("Mulch Area",), planting=FILL,
         cue="bed", look="mulch",
         about="A mulched bed: ground to plant, under wood chips.",
         colours=("#795548", "#5d4037", 0.30, ""), legacy_shape="Mulch Area"),
    Kind("lawn_to_convert", _zone("lawn_remaining"), AREA,
         shape_types=(_zone("lawn_remaining"),), planting=FILL,
         cue="lawn_zone", look="lawn",
         about="Lawn you mean to turn into planting.",
         colours=_zone_colours("lawn_remaining"),
         legacy_shape=_zone("lawn_remaining")),
    Kind("restoration_1", _zone("restoration_year_1"), AREA,
         shape_types=(_zone("restoration_year_1"),), planting=FILL,
         look="seeded", about="Ground prepared and newly seeded.",
         colours=_zone_colours("restoration_year_1"),
         legacy_shape=_zone("restoration_year_1")),
    Kind("restoration_3", _zone("restoration_year_3"), AREA,
         shape_types=(_zone("restoration_year_3"),), planting=FILL,
         look="young_meadow", about="A planting in its third year.",
         colours=_zone_colours("restoration_year_3"),
         legacy_shape=_zone("restoration_year_3")),
    Kind("established", _zone("established_native"), AREA,
         shape_types=(_zone("established_native"),), planting=FILL,
         look="meadow", about="Native planting that has filled in.",
         colours=_zone_colours("established_native"),
         legacy_shape=_zone("established_native")),
    Kind("rock_garden", "Rock garden", AREA,
         struct_ids=("rock_xeriscape",), planting=FILL, ground=DRY,
         habitat=True, look="rock", drawn_twin="rock_xeriscape",
         about="Rocks and dry ground, planted with what likes it dry.",
         colours=("#bcaaa4", "#8d6e63", 0.35, ""), legacy_shape="Garden Bed"),
    # Ground Plan My Yard keeps out of.
    Kind("lawn", "Lawn", AREA, shape_types=("Lawn Area",), planting=KEEP_OUT,
         cue="lawn", look="lawn", about="Lawn you are keeping.",
         colours=("#66bb6a", "#43a047", 0.15, "2 4"),
         legacy_shape="Lawn Area"),
    Kind("native_lawn", "Native lawn", AREA,
         struct_ids=("native_lawn_patch",), planting=KEEP_OUT, habitat=True,
         cue="lawn", look="young_meadow", drawn_twin="native_lawn_patch",
         about="A low-mow lawn of native grasses and low flowers.",
         colours=("#9ccc65", "#689f38", 0.25, "2 4"),
         legacy_shape="Lawn Area"),
    Kind("path", "Path", AREA, shape_types=("Pathway",), planting=KEEP_OUT,
         cue="path", look="path", about="A path you walk on.",
         options=(Option("surface", "Surface", PATH_SURFACES, "flagstone"),),
         colours=("#8d6e63", "#5d4037", 0.35, "8 4"), legacy_shape="Pathway"),
    Kind("patio", "Patio", AREA, shape_types=("Patio / Deck",),
         planting=KEEP_OUT, cue="path", look="patio",
         about="Paving to sit out on.",
         options=(Option("surface", "Surface", PATIO_SURFACES, "pavers"),),
         colours=("#78909c", "#546e7a", 0.40, ""),
         legacy_shape="Patio / Deck"),
    Kind("pond", "Pond", AREA, shape_types=("Water Feature",),
         struct_ids=("pond",), planting=KEEP_OUT, ground=WET, habitat=True,
         water="ponds", look="water", drawn_twin="pond",
         about="Standing water. Plan My Yard plants what grows in water in "
               "it, and nothing else.",
         colours=("#42a5f5", "#1565c0", 0.30, ""),
         legacy_shape="Water Feature"),
    Kind("remnant", _zone("existing_remnant"), AREA,
         shape_types=(_zone("existing_remnant"),), planting=KEEP_OUT,
         look="meadow", about="Wild ground already there, to keep as it is.",
         colours=_zone_colours("existing_remnant"),
         legacy_shape=_zone("existing_remnant")),
    # A rain garden is kept out of until F281 can plant it with what takes wet
    # feet: the planner's cells carry no moisture, and ordinary plants in a
    # rain garden's floor would be worse than none (the V3.71 plan).
    Kind("rain_garden", "Rain garden", AREA, struct_ids=("rain_garden",),
         planting=KEEP_OUT, ground=WET, habitat=True, look="rain_garden",
         drawn_twin="rain_garden",
         about="A shallow dip that takes the rain off a roof or a path.",
         colours=("#4db6ac", "#00796b", 0.30, ""), legacy_shape="Custom"),
    Kind("building", "Building", AREA, struct_ids=("shed",),
         planting=KEEP_OUT,
         about="A house, garage or shed. It casts shade, and nothing is "
               "planted inside it.",
         options=(Option("building", "It is a", BUILDINGS, "shed"),
                  Option("height_m", "Height", default=2.4, unit="m",
                         lo=1.0, hi=30.0, step=0.5)),
         colours=("#8d6e63", "#5d4037", 0.30, ""), legacy_shape="Building"),
    Kind("custom", "Custom", AREA, shape_types=("Custom",), look="custom",
         about="Any other area, in your own colours.",
         colours=("#9e9e9e", "#616161", 0.25, ""), legacy_shape="Custom",
         advanced=True),
    # Lines.
    # A line with a look lies on the ground as a strip at its width (V3.72).
    Kind("swale", "Swale", LINE, struct_ids=("swale",), line_styles=("swale",),
         planting=KEEP_OUT, ground=WET, habitat=True, water="swales",
         drawn_twin="swale", look="rain_garden",
         about="A shallow ditch along the slope that slows rain and soaks "
               "it in. Draw it along the slope's contour.",
         options=(Option("width_m", "Width", default=1.5, unit="m", lo=0.5,
                         hi=3.0, step=0.25),),
         colours=("#4fc3f7",)),
    Kind("fence", "Fence", LINE, struct_ids=("fence",), line_styles=("fence",),
         cue="border", about="A fence, often along a lot line.",
         options=(Option("fence_kind", "Kind", FENCE_KINDS, "rail"),),
         colours=("#795548",)),
    Kind("wall", "Wall", LINE, line_styles=("wall",), cue="border",
         about="A wall of brick, block or stone.", colours=("#9e9e9e",)),
    Kind("hedge", "Hedge", LINE, line_styles=("hedge",),
         about="A row of one kind of shrub.", options=_hedge_options(1.5),
         colours=("#4caf50",)),
    Kind("living_fence", "Living fence", LINE, line_styles=("living_fence",),
         about="A mixed row of two or three kinds of shrub.",
         options=_hedge_options(1.5), colours=("#66bb6a",)),
    Kind("windbreak", "Windbreak", LINE, line_styles=("windbreak",),
         about="Trees and tall shrubs against the wind.",
         options=_hedge_options(3.0), colours=("#2e7d32",)),
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
    # A deck sits after the objects so the readers' derived tuples keep the
    # order they had: it has no shape type of its own (V3.72).
    Kind("deck", "Deck", AREA, planting=KEEP_OUT, cue="path", look="deck",
         about="A wooden deck.", colours=("#a1887f", "#6d4c41", 0.40, ""),
         legacy_shape="Patio / Deck"),
)

BY_KEY: dict = {k.key: k for k in KINDS}
_BY_SHAPE: dict = {t: k for k in KINDS for t in k.shape_types}
_BY_STRUCT: dict = {s: k for k in KINDS for s in k.struct_ids}
_BY_STYLE: dict = {s: k for k in KINDS for s in k.line_styles}

#: Placement › Yard (V3.72): the headings, and the kinds under each in the
#: order shown. Every kind is under exactly one (a test holds it).
PALETTE: tuple = (
    ("Beds and ground", ("bed", "mulch", "path", "patio", "deck", "lawn",
                         "lawn_to_convert", "restoration_1", "restoration_3",
                         "established", "remnant")),
    ("Water", ("pond", "rain_garden", "swale", "rain_barrel")),
    ("For wildlife", ("native_lawn", "rock_garden", "brush_pile",
                      "bee_hotel", "bee_log", "snag")),
    ("Fences and hedges", ("fence", "wall", "hedge", "living_fence",
                           "windbreak")),
    ("Buildings", ("building",)),
    ("Around the yard", ("compost_bin", "fire_pit", "custom")),
)


def option(kind: Kind, key: str) -> Optional[Option]:
    return next((o for o in kind.options if o.key == key), None)


def defaults(kind: Kind) -> dict:
    """Each option's default, by its key."""
    return {o.key: o.default for o in kind.options}


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


#: The element types a drawn kind is stored as.
DRAWN_TYPES = ("custom_shape", "canopy_footprint", "hedgerow")


def is_building_footprint(props: dict) -> bool:
    """A building's outline, drawn or scanned: a ``canopy_footprint`` named a
    building (the scan's "Building (OSM)", Site › Features' "Building
    footprint", the Yard palette's Building since V3.72). An imported
    footprint may be a building or a crown, and is left as it was."""
    props = props or {}
    return (props.get("element_type") == "canopy_footprint"
            and props.get("caster_kind") != "tree"
            and (props.get("kind") == "building"
                 or (props.get("shape_type") or "").startswith("Building")))


def kind_of(feature: dict) -> Optional[Kind]:
    """The kind a feature is, or ``None`` (a plant, a boundary, an existing
    tree, a tree's crown, anything the table does not name). A feature saved
    by V3.72 or later says its ``kind``; an older one is read by the name it
    had (a structure id, a shape type, a line style)."""
    props = (feature or {}).get("properties") or {}
    et = props.get("element_type")
    if et == "structure":
        return _BY_STRUCT.get(struct_id_of(props))
    if et in DRAWN_TYPES and props.get("kind") in BY_KEY:
        return BY_KEY[props["kind"]]
    if et in ("custom_shape", "canopy_footprint"):
        # An old shape given a height cast shade, and the planting readers
        # still read its shape type (the V3.69 trap, which the conversion on
        # open ends, src/yard_upgrade.py).
        return _BY_SHAPE.get(props.get("shape_type") or "")
    if et == "hedgerow":
        return _BY_STYLE.get(props.get("style") or "")
    return None


#: What a chosen surface is drawn as in 3D (V3.73): a look each, so a gravel
#: path and a flagstone path differ. A path or patio with none chosen (every
#: converted one) keeps its kind's own look.
MATERIAL_LOOKS = {value: value for value, _w in PATH_SURFACES + PATIO_SURFACES}
#: What each is called where the 3D names a place (``scene_timeline``).
MATERIAL_WORDS = {"flagstone": "flagstone", "pavers": "paving",
                  "gravel": "gravel", "wood_chips": "wood-chip path",
                  "stepping_stones": "stepping stones",
                  "concrete": "concrete"}


def look_of(feature: dict) -> str:
    """What a drawn area is in 3D (``scene_site``): its chosen surface's look
    (V3.73), else its kind's look, else ``custom`` (the person's own
    colour)."""
    k = kind_of(feature)
    if k is None:
        return "custom"
    surface = ((feature or {}).get("properties") or {}).get("surface")
    if option(k, "surface") is not None and surface in MATERIAL_LOOKS:
        return MATERIAL_LOOKS[surface]
    return k.look or "custom"


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
        b = math.radians(fp.get("bearing_deg") or 0.0)
        cb, sb = math.cos(b), math.sin(b)
        # Turned clockwise from north, as the map turns it (V3.72).
        pts = [(e * cb + n * sb, -e * sb + n * cb)
               for e, n in ((-he, -hn), (he, -hn), (he, hn), (-he, hn))]
    ring = [[lng0 + e / kx, lat0 + n / _M_PER_DEG] for e, n in pts]
    return ring + [ring[0]]


def footprint_rings(feature: dict) -> list:
    """The ground a feature covers, as rings: an area's or a placed
    structure's one (:func:`footprint_ring`), or a line's strip, one
    rectangle a segment at its ``width_m`` (V3.72: a swale drawn as a line is
    still ground the planner keeps out of, as its placed rectangle was)."""
    ring = footprint_ring(feature)
    if ring:
        return [ring]
    geom = (feature or {}).get("geometry") or {}
    props = (feature or {}).get("properties") or {}
    pts = geom.get("coordinates") or []
    if geom.get("type") != "LineString" or len(pts) < 2:
        return []
    half = float(props.get("width_m") or 1.0) / 2.0
    out = []
    for a, b in zip(pts, pts[1:]):
        kx = _M_PER_DEG * math.cos(math.radians((a[1] + b[1]) / 2.0))
        de, dn = (b[0] - a[0]) * kx, (b[1] - a[1]) * _M_PER_DEG
        length = math.hypot(de, dn)
        if length <= 0:
            continue
        ue, un = -dn / length * half, de / length * half      # across it
        corners = [(a, 1), (b, 1), (b, -1), (a, -1)]
        ring = [[p[0] + s * ue / kx, p[1] + s * un / _M_PER_DEG]
                for p, s in corners]
        out.append(ring + [ring[0]])
    return out


def ring_area_m2(ring: list) -> float:
    """A ``[lng, lat]`` ring's area in square metres (the shoelace formula
    over the cosLat metric, ``src/projection.py``'s default)."""
    if not ring or len(ring) < 3:
        return 0.0
    lat0 = sum(p[1] for p in ring) / len(ring)
    kx = _M_PER_DEG * math.cos(math.radians(lat0))
    pts = [(p[0] * kx, p[1] * _M_PER_DEG) for p in ring]
    s = sum(x0 * y1 - x1 * y0
            for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    return abs(s) / 2.0


def line_length_m(points: list) -> float:
    """A ``[lng, lat]`` line's length in metres."""
    total = 0.0
    for a, b in zip(points or [], (points or [])[1:]):
        kx = _M_PER_DEG * math.cos(math.radians((a[1] + b[1]) / 2.0))
        total += math.hypot((b[0] - a[0]) * kx, (b[1] - a[1]) * _M_PER_DEG)
    return total


def features_of(project_or_features) -> list:
    if isinstance(project_or_features, dict):
        return list(project_or_features.get("features") or [])
    return list(project_or_features or [])


def fill_rings(project_or_features) -> list:
    """The outlines Plan My Yard plants into, drawn or placed."""
    return [r for f in features_of(project_or_features)
            if is_fill(f) and (r := footprint_ring(f))]


# ── what the score, the Water page, the hours and the costs are handed ──────

def twin_of(feature: dict) -> str:
    """The catalogue structure a drawn feature counts as for the score, the
    Water page, the care hours and the buy list, or ``""``. A bed is a raised
    bed only when it is raised; a fence, a wall and a building have none: a
    drawn one is most often already there, as a drawn house always was
    (V3.72)."""
    k = kind_of(feature)
    props = (feature or {}).get("properties") or {}
    if (k is None or not k.drawn_twin
            or props.get("element_type") not in DRAWN_TYPES):
        return ""
    if k.key == "bed" and not props.get("raised_cm"):
        return ""
    return k.drawn_twin


def _catalogue_measure(sd: dict, verb: str) -> float:
    """A catalogue structure's default footprint: area (m²) for an area, the
    length for a line, as the map drew it placed (a circle of ``size_m`` for
    a circle or an ellipse, else ``size_m`` by ``width_m``)."""
    size = float(sd.get("size_m") or 0.0)
    if verb == LINE:
        return size
    if (sd.get("shape") or "rectangle") in ("circle", "ellipse"):
        return math.pi * (size / 2.0) ** 2
    return size * float(sd.get("width_m") or size)


def scale_of(feature: dict, twin: dict) -> float:
    """How many of the catalogue's default a drawn feature is: its area over
    the default's, a line's length over its default length. Costs and care
    hours are multiplied by it, the ranges staying the estimates they were
    (P9)."""
    k = kind_of(feature)
    geom = (feature or {}).get("geometry") or {}
    default = _catalogue_measure(twin, k.verb if k else AREA)
    if default <= 0:
        return 1.0
    if geom.get("type") == "LineString":
        here = line_length_m(geom.get("coordinates") or [])
    else:
        here = ring_area_m2(footprint_ring(feature) or [])
    # To a tenth, at least a tenth: the ranges are estimates, and a converted
    # 6 m pond (its circle drawn with 32 sides) stays exactly one pond.
    return max(0.1, round(here / default, 1)) if here > 0 else 1.0


def structure_defs(project_or_features: Iterable) -> list:
    """The structure definitions of a design, as the habitat score, the Water
    page, the care hours and the buy list read them: each placed structure's
    stored ``struct_def``, and **a drawn kind's twin** (:func:`twin_of`: a
    drawn pond is a pond, with the catalogue pond's definition, marked
    ``drawn`` and carrying its ``scale``)."""
    from src.db.structures import get_structure
    out = []
    for f in features_of(project_or_features):
        props = f.get("properties") or {}
        if props.get("element_type") == "structure":
            sd = props.get("struct_def") or {}
            out.append(sd if sd else {"id": struct_id_of(props)})
            continue
        sid = twin_of(f)
        if sid:
            twin = dict(get_structure(sid) or {"id": sid})
            twin["drawn"] = True
            twin["scale"] = scale_of(f, twin)
            out.append(twin)
    return out


def scale(sd) -> float:
    """The ``scale`` a definition carries (1 for a placed one, or anything
    else): what the two cost paths and the care hours multiply by."""
    try:
        return float((sd or {}).get("scale") or 1.0) if isinstance(sd, dict) \
            else 1.0
    except (TypeError, ValueError):
        return 1.0


# ── a new drawn feature's properties ────────────────────────────────────────

def drawn_props(key: str, **options) -> dict:
    """The properties a drawn ``key`` is stored with (file format 1.11): its
    ``kind``, the shape type an older copy reads (:attr:`Kind.legacy_shape`),
    its map colours, and its options, each defaulted. The palette, the
    conversion on open and the scripting API all make features through this,
    so the three cannot store a kind differently."""
    k = BY_KEY[key]
    props: dict = {"kind": key}
    for o in k.options:
        value = options.get(o.key, o.default)
        if value is not None and value != "":
            props[o.key] = value
    if k.verb == LINE:
        props["element_type"] = "hedgerow"
        props["style"] = k.line_styles[0] if k.line_styles else key
        props["color"] = options.get("color") or k.colours[0]
        return props
    fill, stroke, opacity, dash = k.colours
    props.update({
        "element_type": "custom_shape",
        "shape_type": k.legacy_shape or k.words,
        "fill_color": options.get("fill_color") or fill,
        "stroke_color": options.get("stroke_color") or stroke,
        "fill_opacity": float(options.get("fill_opacity", opacity)),
        "dash_array": options.get("dash_array", dash),
    })
    if key == "building":
        # Stored as a scanned building is (a shade caster with a height), so
        # the shade map, the house view, the Overview's front and back and the
        # 3D's buildings read it as they read those.
        kind = props.get("building") or "shed"
        props["height_m"] = float(options.get("height_m")
                                  or BUILDING_HEIGHT_M.get(kind, 2.4))
        props.update({"element_type": "canopy_footprint", "cast_shade": True})
    return props
