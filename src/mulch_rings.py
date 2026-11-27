"""
src/mulch_rings.py — a ring of mulch round a plant (V3.76; the owner's Q4 in
``docs/plans/V3.71-one-palette.md``, and ``docs/plans/V3.76-doors-taps-and-mulch-rings.md``).

Design principle P2 (the best designs disappear into their context: "grown,
not designed") — see docs/DESIGN_PHILOSOPHY.md. A ring round every plant reads
as designed rather than grown, so **none is drawn unless asked for**: Plan My
Yard's box gives its plants one, the placing box the plants a person places,
and a plant's right-click menu one plant or its group. Which plants have one
is the plant's own ``mulch_ring``, carried by ``project_store``.

* :func:`ring_diameter_m`: about as wide as the plant's spacing, so rings at
  the plant's own spacing just touch, inside :data:`RING_M`.
* :func:`rings`: every ring, and whether it is drawn: a plant standing in a
  drawn bed or mulch area (``yard_kinds.is_mulched``) has mulch already.
* :func:`mulch_area_m2`: the ground mulch is bought for, the beds' planting
  area and the rings outside it, so nothing is counted twice. Every mulch
  figure reads it: the Overview, the PDF's prep and buy pages, the planting
  plan.

Every size here is a **stated estimate** (P9). Qt-free and network-free;
the catalogue is read for a plant's spacing unless ``get_plant`` is handed in.
"""

from __future__ import annotations

import math
from typing import Callable, Optional

from src import yard_kinds

#: A ring's width across, metres: never less (a small plant still gets a
#: ring a trowel can make) and never more (a tree's ring, not its drip line).
RING_M = (0.4, 1.5)
#: The sides a ring is drawn with.
RING_SIDES = 16


def ring_diameter_m(row: Optional[dict]) -> float:
    """About the plant's spacing (``spacing_meters``), within :data:`RING_M`;
    the smallest when nothing is recorded."""
    try:
        spacing = float((row or {}).get("spacing_meters") or 0.0)
    except (TypeError, ValueError):
        spacing = 0.0
    return round(min(RING_M[1], max(RING_M[0], spacing)), 2)


def _getter(get_plant: Optional[Callable]) -> Callable:
    if get_plant is not None:
        return get_plant
    cache: dict = {}

    def _get(pid):
        if pid not in cache:
            try:
                from src.db.plants import get_plant as _db  # noqa: PLC0415
                cache[pid] = _db(pid) or {}
            except Exception:                                # noqa: BLE001
                cache[pid] = {}
        return cache[pid]
    return _get


def _inside(x: float, y: float, ring: list) -> bool:
    hit = False
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            hit = not hit
    return hit


def _mulched_rings(project) -> list:
    """The drawn beds and mulch areas' outlines, ``[lng, lat]``."""
    out = []
    for f in (project or {}).get("features", []) or []:
        geom = f.get("geometry") or {}
        if (geom.get("type") == "Polygon" and geom.get("coordinates")
                and yard_kinds.is_mulched(f)):
            out.append(geom["coordinates"][0])
    return out


def rings(project, get_plant: Optional[Callable] = None) -> list:
    """``[{lat, lng, r, shown, plant_id}]`` for every plant with a mulch ring:
    ``r`` its radius in metres, ``shown`` False where it stands in a drawn
    bed or mulch area, which is mulched already."""
    from src.project_store import ProjectStore               # noqa: PLC0415
    get = _getter(get_plant)
    beds = _mulched_rings(project)
    out = []
    for p in ProjectStore(project).placed_plants:
        if not p.get("mulch_ring"):
            continue
        lat, lng = float(p["lat"]), float(p["lng"])
        shown = not any(_inside(lng, lat, ring) for ring in beds)
        out.append({"lat": lat, "lng": lng, "plant_id": p.get("plant_id"),
                    "r": ring_diameter_m(get(p.get("plant_id"))) / 2.0,
                    "shown": shown})
    return out


def ring_area_m2(project, get_plant: Optional[Callable] = None) -> float:
    """The rings' ground outside the beds' planting area, m²: what mulch is
    bought for besides the beds. Overlapping rings count once."""
    shown = [r for r in rings(project, get_plant) if r["shown"]]
    if not shown:
        return 0.0
    try:
        from shapely.geometry import Point
        from shapely.ops import unary_union
    except ImportError:                                      # pragma: no cover
        return sum(math.pi * r["r"] ** 2 for r in shown)
    from src.projection import Projector                     # noqa: PLC0415
    from src.yard_overview import local_area                 # noqa: PLC0415
    proj, area = local_area(project)
    if proj is None:
        proj = Projector(shown[0]["lat"], shown[0]["lng"])
    discs = unary_union([Point(*proj.to_xy(r["lat"], r["lng"])).buffer(
        r["r"], RING_SIDES // 4) for r in shown])
    if area is not None and not area.is_empty:
        discs = discs.difference(area)
    return float(discs.area)


def mulch_area_m2(project, get_plant: Optional[Callable] = None) -> float:
    """The ground mulch is bought for: the beds' planting area
    (``yard_overview.bed_area_m2``) and the rings outside it."""
    from src.yard_overview import bed_area_m2                # noqa: PLC0415
    return bed_area_m2(project) + ring_area_m2(project, get_plant)


def scene_rings(project, proj, get_plant: Optional[Callable] = None) -> list:
    """The drawn rings for the 3D, ``[[x, y, r], …]`` in scene metres."""
    return [[round(x, 2), round(y, 2), round(r["r"], 2)]
            for r in rings(project, get_plant) if r["shown"]
            for x, y in [proj.to_xy(r["lat"], r["lng"])]]
