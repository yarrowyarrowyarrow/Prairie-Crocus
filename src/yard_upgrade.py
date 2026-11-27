"""
src/yard_upgrade.py — an older design, read as the Yard palette stores it
(V3.72, F280's second increment).

Design principle P9 (uncertainty is a feature: never false precision) — see
docs/DESIGN_PHILOSOPHY.md. A design opened in a newer app must show what the
person drew, where they drew it, and nothing the app guessed.

Until V3.72 a pond could be placed (a point and a size) or drawn (an outline),
and the two meant different things (the V3.69 review). The Yard palette draws
what has an outline and places only objects. :func:`upgrade` turns a design
saved by any earlier version into that form, **at the outline the map showed**
(the owner's answer in the V3.71 plan):

* a placed Pond, Rain Garden or Rock Xeriscape becomes the circle the map drew
  for it, as a drawn pond, rain garden or rock garden;
* a placed Raised Bed or Native Lawn Patch becomes its rectangle, as a bed raised
  45 cm or a native lawn; a Tool Shed becomes a building on its rectangle;
* a placed Bioswale or Fence / Wall becomes a line along the rectangle's length
  (a swale at its width, a rail fence);
* a Garden Bed or Mulch Area given a height up to 1.2 m becomes a raised bed at
  that height, and any other shape given a height (not a tree's crown) a
  building, which is what the shade map already took it for;
* every other drawn area and line gains the ``kind`` it already was.

It is idempotent, and it changes the design in memory only: the windows call it
before they mark a design open, so it is never an undo step and never asks to
be saved; the file becomes 1.11 the next time it is saved.

Qt-free, DB-free (the catalogue is read for a structure with no stored
definition), network-free. ``tests/test_yard_upgrade.py`` holds each rule.
"""

from __future__ import annotations

import math
import uuid
from typing import Optional

from src import yard_kinds

#: The file format a converted design is in (``src/project.py``).
UPGRADED_VERSION = "1.11"

#: A placed structure that becomes a drawn area, and the kind it becomes.
AREA_STRUCTURES = {"pond": "pond", "rain_garden": "rain_garden",
                   "rock_xeriscape": "rock_garden", "raised_bed": "bed",
                   "native_lawn_patch": "native_lawn", "shed": "building"}
#: A placed structure that becomes a drawn line.
LINE_STRUCTURES = {"swale": "swale", "fence": "fence"}
#: What a converted one is: a placed raised bed was 45 cm (the catalogue's
#: model), a shed 2.4 m (``yard_kinds.BUILDING_HEIGHT_M``).
CONVERTED_OPTIONS = {"raised_bed": {"raised_cm": 45},
                     "shed": {"building": "shed"},
                     "fence": {"fence_kind": "rail"}}
#: The tallest shape given a height that is read as a raised bed rather than
#: a building: a bed is not built higher (the V3.71 plan).
RAISED_BED_MAX_M = 1.2
#: The shape types a raised bed came from.
_BED_SHAPES_WITH_HEIGHT = ("Garden Bed", "Mulch Area")


def _new_id(prefix: str) -> str:
    return f"{prefix}_up_{uuid.uuid4().hex[:12]}"


def _carry(old: dict, new: dict) -> dict:
    """What a converted feature keeps: the plan that placed it, so replacing
    the plan still takes it away, and the person's name for it."""
    for key in ("plan_run", "feature_id"):
        if old.get(key):
            new[key] = old[key]
    return new


def _building_props(props: dict, ring: list, height: float) -> dict:
    """A building's properties on ``ring``, as ``map_events`` writes a drawn
    one: a shade caster with the keep-out's radius and centre."""
    from src.osm_features import ring_centroid, ring_radius_m
    kind = ("shed" if height <= 3.0 else "garage" if height <= 4.5
            else "house")
    new = yard_kinds.drawn_props("building", building=props.get("building")
                                 or kind, height_m=height)
    centre = ring_centroid(ring)
    new["canopy_radius_m"] = max(0.5, ring_radius_m(ring, centre))
    return new


def _area_from_structure(f: dict) -> Optional[dict]:
    props = f.get("properties") or {}
    sid = yard_kinds.struct_id_of(props)
    key = AREA_STRUCTURES.get(sid)
    ring = yard_kinds.footprint_ring(f) if key else None
    if not ring:
        return None
    opts = dict(CONVERTED_OPTIONS.get(sid, {}))
    if key == "building":
        new = _building_props(props, ring, yard_kinds.BUILDING_HEIGHT_M["shed"])
    else:
        new = yard_kinds.drawn_props(key, **opts)
    new.update({"shape_id": _new_id("shape"), "label": "",
                "area_m2": round(yard_kinds.ring_area_m2(ring), 1)})
    return {"type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [ring]},
            "properties": _carry(props, new)}


def _line_from_structure(f: dict) -> Optional[dict]:
    """A placed swale or fence as a line along its rectangle's length, centred
    where it stood, at its bearing (``scene_structures.fence_lines``' rule)."""
    from src.scene_structures import footprint
    props = f.get("properties") or {}
    sid = yard_kinds.struct_id_of(props)
    key = LINE_STRUCTURES.get(sid)
    coords = (f.get("geometry") or {}).get("coordinates") or []
    if not key or len(coords) < 2:
        return None
    fp = footprint(props)
    lng0, lat0 = float(coords[0]), float(coords[1])
    half = fp["size_m"] / 2.0
    b = math.radians(fp["bearing_deg"])
    de, dn = math.sin(b) * half, math.cos(b) * half
    kx = yard_kinds._M_PER_DEG * math.cos(math.radians(lat0))
    line = [[lng0 - de / kx, lat0 - dn / yard_kinds._M_PER_DEG],
            [lng0 + de / kx, lat0 + dn / yard_kinds._M_PER_DEG]]
    opts = dict(CONVERTED_OPTIONS.get(sid, {}))
    if key == "swale":
        opts["width_m"] = round(fp["width_m"], 2)
    new = yard_kinds.drawn_props(key, **opts)
    new.update({"hedge_id": _new_id("hedge"), "species": "",
                "length_m": round(fp["size_m"], 2), "num_plants": 0,
                "width_m": float(opts.get("width_m") or 0.3),
                "spacing_m": 1.0})
    return {"type": "Feature",
            "geometry": {"type": "LineString", "coordinates": line},
            "properties": _carry(props, new)}


def _is_tree_crown(props: dict) -> bool:
    return (props.get("caster_kind") == "tree"
            or props.get("shape_type") == "Tree canopy")


def _upgrade_shape(f: dict) -> bool:
    """Give a drawn area its kind, in place. A shape with a height is a raised
    bed or a building. ``True`` when anything changed."""
    props = f.setdefault("properties", {})
    if props.get("kind") in yard_kinds.BY_KEY or _is_tree_crown(props):
        return False
    height = float(props.get("height_m") or 0.0)
    if props.get("element_type") == "canopy_footprint" and height > 0:
        if yard_kinds.is_building_footprint(props):
            props["kind"] = "building"        # scanned or drawn: as it was
            return True
        ring = yard_kinds.footprint_ring(f)
        if yard_kinds.kind_of(f) is None or not ring:
            return False         # an imported footprint, or no outline
        if (props.get("shape_type") in _BED_SHAPES_WITH_HEIGHT
                and height <= RAISED_BED_MAX_M):
            for key in ("cast_shade", "height_m", "canopy_radius_m",
                        "caster_kind"):
                props.pop(key, None)
            props.update({"element_type": "custom_shape", "kind": "bed",
                          "shape_type": "Garden Bed",
                          "raised_cm": int(round(height * 100))})
            return True
        keep = {k: props[k] for k in ("shape_id", "label", "area_m2",
                                      "plan_run", "source", "lat", "lng")
                if k in props}
        props.clear()
        props.update(_building_props({}, ring, height))
        props.update(keep)
        return True
    k = yard_kinds.kind_of(f)
    if k is None:
        return False
    props["kind"] = k.key
    return True


def _upgrade_line(f: dict) -> bool:
    props = f.setdefault("properties", {})
    if props.get("kind") in yard_kinds.BY_KEY:
        return False
    k = yard_kinds.kind_of(f)
    if k is None:
        return False
    props["kind"] = k.key
    if k.key == "fence" and not props.get("fence_kind"):
        props["fence_kind"] = "rail"
    return True


def upgrade_feature(f: dict) -> tuple:
    """``(feature, changed)``: ``f`` as the Yard palette stores it. A placed
    structure that has an outline comes back as a new feature; anything else
    is changed in place, or not at all."""
    props = (f or {}).get("properties") or {}
    et = props.get("element_type")
    if et == "structure":
        new = _area_from_structure(f) or _line_from_structure(f)
        return (new, True) if new is not None else (f, False)
    if et in ("custom_shape", "canopy_footprint"):
        return f, _upgrade_shape(f)
    if et == "hedgerow":
        return f, _upgrade_line(f)
    return f, False


def upgrade(project: dict) -> int:
    """Convert ``project`` in place; the number of features changed (0 the
    second time). Sets ``schema_version`` to 1.11 when anything changed."""
    if not isinstance(project, dict):
        return 0
    features = project.get("features")
    if not isinstance(features, list):
        return 0
    changed = 0
    out = []
    for f in features:
        new, did = upgrade_feature(f)
        out.append(new)
        changed += bool(did)
    if changed:
        project["features"] = out
        project.setdefault("properties", {})["schema_version"] = \
            UPGRADED_VERSION
    return changed
