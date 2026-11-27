"""
src/wall_objects.py — a door, a downspout or a spigot goes on a building's
wall (V3.76, F280's last increment; ``docs/plans/V3.76-doors-taps-and-mulch-rings.md``).

Design principle P9 (uncertainty is a feature: never false precision) — see
docs/DESIGN_PHILOSOPHY.md. Nothing in a design records where a building's
doors, downspouts and taps are; a person places them, and this puts each one
where it plainly belongs, on the wall nearest the click, saying nothing it
was not told.

:func:`snap` takes a click and a catalogue definition with ``on_wall``
(``src/db/structures.py``) and returns where the object stands: on the
nearest wall of any building (a drawn Building or a scanned footprint,
``yard_kinds.is_building_footprint``) within :data:`WALL_SNAP_M`, its long
side along the wall, standing out from it by its own ``width_m`` (a door's
doorstep, a downspout's splash block, a spigot's reach), facing away from the
building. Further from every building, ``None``: it stands where it was
clicked (a yard hydrant is a spigot too).

Qt-free, DB-free and network-free.
"""

from __future__ import annotations

import math
from typing import Iterable, Optional

from src import yard_kinds

#: How far from a wall a click still means that wall: **a stated estimate**,
#: about the length of a step and a half either side of a wall drawn from a
#: photograph a little off.
WALL_SNAP_M = 3.0
#: How far off the wall's outline the object sits, so it is drawn on the
#: outside of a building drawn a little small.
WALL_GAP_M = 0.05


def _rings(project) -> Iterable[tuple]:
    """``(ring, height_m)`` for every building's outline, ``[lng, lat]``."""
    for f in (project or {}).get("features", []) or []:
        props = f.get("properties") or {}
        geom = f.get("geometry") or {}
        if (geom.get("type") != "Polygon" or not geom.get("coordinates")
                or not yard_kinds.is_building_footprint(props)):
            continue
        ring = geom["coordinates"][0]
        if len(ring) >= 3:
            try:
                height = float(props.get("height_m") or 0.0)
            except (TypeError, ValueError):
                height = 0.0
            yield ring, height


def _inside(x: float, y: float, ring: list) -> bool:
    hit = False
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            hit = not hit
    return hit


def snap(project, lat: float, lng: float, struct_def: dict) -> Optional[dict]:
    """Where a wall object clicked at ``(lat, lng)`` stands: ``{lat, lng,
    bearing_deg, facing_deg, wall_h_m}``, or ``None`` when no building's wall
    is within :data:`WALL_SNAP_M`. ``bearing_deg`` is the wall's direction
    (the map draws the object's long side along it), ``facing_deg`` the way
    out of the building, ``wall_h_m`` the building's recorded height (0 when
    none)."""
    from src.projection import Projector
    proj = Projector(lat, lng)
    size = float((struct_def or {}).get("size_m") or 0.3)
    out_m = float((struct_def or {}).get("width_m") or size) / 2.0 + WALL_GAP_M
    best = None
    for ring, height in _rings(project):
        xy = [proj.to_xy(p[1], p[0]) for p in ring]
        if xy[0] == xy[-1]:
            xy = xy[:-1]
        if len(xy) < 3:
            continue
        for a, b in zip(xy, xy[1:] + xy[:1]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            if length <= 1e-6:
                continue
            ux, uy = dx / length, dy / length
            t = max(0.0, min(length, -(a[0] * ux + a[1] * uy)))
            qx, qy = a[0] + ux * t, a[1] + uy * t
            dist = math.hypot(qx, qy)
            if dist > WALL_SNAP_M or (best is not None and dist >= best[0]):
                continue
            # The whole object on this wall: slid in from a corner.
            half = min(size / 2.0, length / 2.0)
            t = max(half, min(length - half, t))
            qx, qy = a[0] + ux * t, a[1] + uy * t
            nx, ny = uy, -ux
            if _inside(qx + nx * 0.1, qy + ny * 0.1, xy):
                nx, ny = -nx, -ny                  # out of the building
            best = (dist, qx + nx * out_m, qy + ny * out_m, ux, uy, nx, ny,
                    height)
    if best is None:
        return None
    _d, x, y, ux, uy, nx, ny, height = best
    s_lat, s_lng = proj.to_latlng(x, y)
    return {"lat": s_lat, "lng": s_lng,
            "bearing_deg": round(math.degrees(math.atan2(ux, uy)) % 180.0, 1),
            "facing_deg": round(math.degrees(math.atan2(nx, ny)) % 360.0, 1),
            "wall_h_m": round(height, 2)}


def is_wall_object(struct_def: Optional[dict]) -> bool:
    """Whether a catalogue definition goes on a wall."""
    return bool((struct_def or {}).get("on_wall"))


def place(project, props: dict, lat: float, lng: float) -> tuple:
    """Snap a placed wall object's stored ``props`` in place: its bearing,
    facing and wall height set (on the definition too, which the map draws
    from). Returns the ``(lat, lng)`` it stands at, the click's when no wall
    is near."""
    sd = props.get("struct_def") or {}
    got = snap(project, lat, lng, sd)
    if got is None:
        for key in ("facing_deg", "wall_h_m"):
            props.pop(key, None)
        return lat, lng
    for key in ("bearing_deg", "facing_deg", "wall_h_m"):
        props[key] = got[key]
    if isinstance(sd, dict):
        sd["bearing_deg"] = got["bearing_deg"]
    return got["lat"], got["lng"]
