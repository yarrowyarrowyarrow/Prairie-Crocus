"""
src/scene_kinds.py — what a drawn kind adds in 3D at its outline (V3.73, F280's
third increment).

Design principle P1 (living systems self-organize from the bottom up: encode
generative rules, not fixed layouts) — see docs/DESIGN_PHILOSOPHY.md. A rock
garden's rocks are laid by rule, never placed one by one.

V3.72 drew the Yard palette's kinds plainly: a pond a blue sheet with a hard
edge, a rain garden a dark patch, a rock garden a grey texture with no rocks,
every fence posts and rails. This module decides, once, what each adds; the
viewer (``html/scene3d/02d-kinds.js``) only draws it
(``docs/plans/V3.73-drawn-kinds-in-3d.md``):

* :func:`dress`: a drawn area's extras on its surface row: a shore for water
  (``shore_m``), a floor for wet ground that is not water (``floor``, the
  outline inset), rocks for dry ground (``rocks``, by rule).
* :func:`fence_height`: a fence's height by its kind.

A kind is read by **its answers in the table** (``src/yard_kinds.py``: its
look, its ground), never by its name, so a new wet or dry kind is dressed the
same way. Every size here is a **stated estimate**: nothing in a design
records how wide a pond's shore is, how deep a rain garden's dip, how big a
rock or how tall a board fence (P9). Qt-free, DB-free, network-free; shapely
for the inset (with none, no floor is drawn).
"""

from __future__ import annotations

import math
import random
import zlib
from typing import Optional

from src import yard_kinds

#: A pond's band of pebbles along its outline, half in the water.
POND_SHORE_M = 0.5
#: A rain garden's floor: its outline inset by this share of its width, and
#: at least this far, so the planted rim reads as a shallow dip.
FLOOR_SHARE = 0.2
FLOOR_MIN_M = 0.3
#: A swale's floor down its middle, as a share of its width.
SWALE_FLOOR_SHARE = 0.4
#: A rock garden's rocks: about one per this many square metres, this big
#: (radius), never within this far of the edge, of each other or of a plant
#: (whose own reach is taken as ``PLANT_REACH_M``), and at most this many.
ROCK_EVERY_M2 = 4.0
ROCK_R_M = (0.25, 0.55)
ROCK_CLEAR_M = 0.3
PLANT_REACH_M = 0.3
ROCK_MAX = 40
#: A fence's height by its kind: a rail fence a person sees over (as V3.45
#: drew every fence), a board fence at the usual privacy height, a chain link
#: fence at the usual lot-line height.
FENCE_HEIGHT_M = {"rail": 1.2, "board": 1.8, "chain_link": 1.2}


def fence_height(fence_kind: str, default: float) -> float:
    return FENCE_HEIGHT_M.get(fence_kind or "", default)


# ── geometry (scene metres, open rings) ─────────────────────────────────────

def _inside(x: float, y: float, ring: list) -> bool:
    hit = False
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            hit = not hit
    return hit


def _edge_distance(x: float, y: float, ring: list) -> float:
    best = math.inf
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        dx, dy = x1 - x0, y1 - y0
        t = ((x - x0) * dx + (y - y0) * dy) / (dx * dx + dy * dy or 1e-12)
        t = max(0.0, min(1.0, t))
        best = min(best, math.hypot(x - x0 - t * dx, y - y0 - t * dy))
    return best


def _area(ring: list) -> float:
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1)
                   in zip(ring, ring[1:] + ring[:1]))) / 2.0


def inset(ring: list, by_m: float) -> Optional[list]:
    """``ring`` moved inward by ``by_m``, or ``None`` where nothing is left
    (or there is no shapely). The largest piece of a shape that splits."""
    try:
        from shapely.geometry import Polygon
    except ImportError:                                     # pragma: no cover
        return None
    shape = Polygon(ring).buffer(-by_m)
    if shape.is_empty:
        return None
    if shape.geom_type == "MultiPolygon":
        shape = max(shape.geoms, key=lambda g: g.area)
    out = [[round(x, 2), round(y, 2)] for x, y in shape.exterior.coords[:-1]]
    return out if len(out) >= 3 else None


def _width(ring: list) -> float:
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    return min(max(xs) - min(xs), max(ys) - min(ys))


# ── the rules ───────────────────────────────────────────────────────────────

def rocks(ring: list, seed: str, plants_xy=()) -> list:
    """A rock garden's rocks, ``[[x, y, r], …]``: about one per
    :data:`ROCK_EVERY_M2`, laid by a seed from the area's id (the same design
    draws the same rocks), each wholly inside with :data:`ROCK_CLEAR_M` to
    spare from the edge, the others and every plant."""
    if len(ring) < 3:
        return []
    want = min(ROCK_MAX, int(round(_area(ring) / ROCK_EVERY_M2)))
    if want <= 0:
        return []
    rng = random.Random(zlib.crc32(str(seed).encode("utf-8")))
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    out: list = []
    for _ in range(want * 40):
        if len(out) >= want:
            break
        r = rng.uniform(*ROCK_R_M)
        x, y = rng.uniform(min(xs), max(xs)), rng.uniform(min(ys), max(ys))
        if (not _inside(x, y, ring)
                or _edge_distance(x, y, ring) < r + ROCK_CLEAR_M):
            continue
        if any(math.hypot(x - ox, y - oy) < r + orr + ROCK_CLEAR_M
               for ox, oy, orr in out):
            continue
        if any(math.hypot(x - px, y - py) < r + PLANT_REACH_M + ROCK_CLEAR_M
               for px, py in plants_xy):
            continue
        out.append([round(x, 2), round(y, 2), round(r, 2)])
    return out


def dress(row: dict, feature: dict, ring: list, plants_xy=()) -> dict:
    """Add a drawn area's extras to its surface ``row`` (in place, and
    returned): by its kind's answers, a shore for water, a floor for wet
    ground, rocks for dry ground."""
    k = yard_kinds.kind_of(feature)
    if k is None or len(ring) < 3:
        return row
    if k.look == "water":
        row["shore_m"] = POND_SHORE_M
    elif k.ground == yard_kinds.WET:
        floor = inset(ring, max(FLOOR_MIN_M, FLOOR_SHARE * _width(ring)))
        if floor:
            row["floor"] = floor
    elif k.ground == yard_kinds.DRY:
        props = feature.get("properties") or {}
        seed = props.get("shape_id") or ",".join(
            f"{x:.1f}:{y:.1f}" for x, y in ring)
        row["rocks"] = rocks(ring, seed, plants_xy)
    return row


def plants_xy(project: dict, proj) -> list:
    """Where the design's plants stand, in scene metres."""
    out = []
    for f in (project or {}).get("features", []) or []:
        props = f.get("properties") or {}
        geom = f.get("geometry") or {}
        if (props.get("element_type") == "plant"
                and geom.get("type") == "Point"):
            lng, lat = geom["coordinates"][:2]
            out.append(proj.to_xy(lat, lng))
    return out
