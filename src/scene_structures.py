"""
src/scene_structures.py — a placed structure, as the 3D scene draws it (V3.70,
F288).

Design principle P9 (uncertainty is a feature: never false precision) — see
docs/DESIGN_PHILOSOPHY.md. The 3D must not state a shape the map does not show.

The V3.69 review (``docs/plans/V3.69-structures-and-shapes-reviewed.md``) found
every rectangular structure drawn a quarter turn from the map: the map draws a
rectangle's ``size_m`` north-south and its ``width_m`` east-west
(``html/map/05-features.js``, ``placeStructureOnMap``), the models are authored
with the long side east-west, and the scene sent neither a width nor a turn.
That is the tester's raised bed (``docs/USER_FEEDBACK.md``, the fourth tester,
item 17). This module decides, once, what the viewer then only draws:

* :func:`record`: a structure's scene entry, with ``width_m`` and the
  ``bearing_deg`` of its long side for a rectangle, read **as the map reads
  them** (a definition with no ``shape`` is a rectangle there, and one with no
  width a square), so the two cannot disagree.
* :func:`fence_lines`: a Fence / Wall is drawn as a fence line, posts and rails
  along its length as a drawn Fence is, at the map's length and
  direction. Its stock model was 5 m of rail that stretched its posts with the
  Size box and never matched the drawn fence beside it.

Qt-free, DB-free, network-free: plain arithmetic in scene metres (+x east, +y
north). The catalogue is read only for a stored definition with no id.
"""

from __future__ import annotations

import math
from typing import Optional

#: Which way the map draws a rectangle's long side until it is turned: north
#: (0 degrees). Since V3.72 an object can be turned on the map; its
#: ``bearing_deg`` (clockwise from north) is stored on the feature, and the map,
#: :func:`footprint` and the viewer all read it.
MAP_BEARING_DEG = 0.0

#: The shape the map draws for a definition that names none.
MAP_DEFAULT_SHAPE = "rectangle"

#: Structures drawn as a line, not a model.
AS_LINE = frozenset({"fence"})


def _definition(props: dict) -> dict:
    """The stored definition, as the map is handed it (``project_to_map_data``
    passes ``struct_def`` through), with the id filled from the feature."""
    sd = dict((props or {}).get("struct_def") or {})
    if not sd.get("id") and props.get("struct_id"):
        sd["id"] = props["struct_id"]
    return sd


def bearing_of(props: dict) -> float:
    """Which way a placed structure faces, degrees clockwise from north."""
    props = props or {}
    try:
        return float(props.get("bearing_deg")
                     or (props.get("struct_def") or {}).get("bearing_deg")
                     or MAP_BEARING_DEG) % 360.0
    except (TypeError, ValueError):
        return MAP_BEARING_DEG


def footprint(props: dict) -> dict:
    """What the 2D map draws for a structure: ``{"shape", "size_m",
    "width_m", "bearing_deg"}``, by ``placeStructureOnMap``'s rules (size
    3 m, a rectangle, and a square where nothing says otherwise)."""
    sd = _definition(props)
    size = float(sd.get("size_m") or (props or {}).get("size_m") or 3.0)
    return {"shape": sd.get("shape") or MAP_DEFAULT_SHAPE, "size_m": size,
            "width_m": float(sd.get("width_m") or size),
            "bearing_deg": bearing_of(props)}


def record(props: dict, x: float, y: float) -> Optional[dict]:
    """A structure's entry in the scene's ``structures``, or ``None`` for one
    drawn as a line (:data:`AS_LINE`, see :func:`fence_lines`)."""
    sd = _definition(props)
    sid = sd.get("id", "")
    if sid in AS_LINE:
        return None
    rec = {"x": round(x, 2), "y": round(y, 2), "struct_id": sid,
           "name": sd.get("name", ""),
           "size_m": float(sd.get("size_m") or 1.0),
           "height_m": float(sd.get("height_m") or 1.0)}
    fp = footprint(props)
    if fp["shape"] == "rectangle":
        rec["width_m"] = round(fp["width_m"], 3)
    if fp["shape"] == "rectangle" or fp["bearing_deg"]:
        rec["bearing_deg"] = fp["bearing_deg"]
    return rec


def fence_lines(project: dict, proj) -> list:
    """Each placed Fence / Wall as a fence line, ``[{kind, points, width_m,
    height_m}]`` in :func:`src.scene_site.lines`' shape: its map rectangle's
    long side, centred on the structure, along :data:`MAP_BEARING_DEG`."""
    from src.scene_site import FENCE_WIDTH_M, LINE_HEIGHT_M
    out = []
    for f in (project or {}).get("features", []) or []:
        props = f.get("properties") or {}
        geom = f.get("geometry") or {}
        if (props.get("element_type") != "structure"
                or geom.get("type") != "Point"
                or _definition(props).get("id") not in AS_LINE):
            continue
        lng, lat = geom["coordinates"][:2]
        cx, cy = proj.to_xy(lat, lng)
        fp = footprint(props)
        half = fp["size_m"] / 2.0
        b = math.radians(fp["bearing_deg"])
        dx, dy = math.sin(b) * half, math.cos(b) * half
        out.append({"kind": "fence",
                    "points": [[round(cx - dx, 2), round(cy - dy, 2)],
                               [round(cx + dx, 2), round(cy + dy, 2)]],
                    "width_m": FENCE_WIDTH_M,
                    "height_m": LINE_HEIGHT_M["fence"]})
    return out
