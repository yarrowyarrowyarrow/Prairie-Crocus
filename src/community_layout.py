"""
community_layout.py — how many of each plant a community places, and where
(V3.59).

Design principle P1 — see docs/DESIGN_PHILOSOPHY.md.

The owner: "some communities ... only have 3 awkwardly placed plants". Every
seeded community placed **one plant of each species** at offsets typed by hand
a metre or two from the centre, under a tree whose mapped circle is five metres
across: Chokecherry Community showed one plant of its six, Pin Cherry one of
seven, the Edmonton Aspen Grove two of eight. One wild strawberry under an aspen
is a sampler, not a planting.

So a seeded community is laid out by rules rather than coordinates:

* **How many** (:func:`counts`): a tree once; a shrub once if it grows 2.5 m
  or more across, twice from 1.5 m, three times below that; a vine once; a
  wildflower, herb, grass, sedge, rush, fern or water plant in a drift of three;
  a groundcover in five. At least :data:`MIN_PLANTS` in all (the owner: "can be
  as low as 7"), the smallest drifts grown by one until there are; at most
  :data:`MAX_PLANTS`, the largest drifts cut by one (never below two) until
  there are.
* **Where** (:func:`lay_out`): the trees at the centre, the shrubs round them,
  then each drift in its own direction, every plant on a spiral out from its
  species' place until it stands clear of the rest by half of both spacings,
  which is where the map's circles meet. **A shade plant may stand under a
  tree's crown** (a woodland's floor is its point), never within a metre of
  the trunk; **a sun plant never does**. Deterministic: the same community lays
  out the same way every time.

Largest first, so the map draws the small plants over the big ones. A person's
own community keeps the places they gave it: only the seeded ones are laid out
here. Qt-free.
"""

from __future__ import annotations

import math
from typing import Callable, Optional

#: The fewest and most plants a seeded community places (V3.59, the owner).
MIN_PLANTS = 7
MAX_PLANTS = 25
#: Plants of one kind in a drift (``plant_type`` → count).
DRIFT = {"wildflower": 3, "herb": 3, "grass": 3, "sedge": 3, "rush": 3,
         "fern": 3, "aquatic": 3, "groundcover": 5}
#: How close to a trunk a shade plant may stand, metres.
TRUNK_CLEAR_M = 1.0
_WOODY = ("tree", "shrub")
_SIZE_ORDER = ("tree", "shrub", "vine", "fern", "wildflower", "herb", "grass",
               "sedge", "rush", "aquatic", "groundcover")
_GOLDEN = math.pi * (3 - math.sqrt(5))          # the sunflower's turn


def _spacing(row: dict) -> float:
    from src.planting_spacing import spacing_to_plant_m        # noqa: PLC0415
    return max(0.15, float(spacing_to_plant_m(row) or 1.0))


def _shade_ok(row: dict) -> bool:
    sun = (row.get("sun_requirement") or "").replace(" ", "_")
    return "partial_shade" in sun or "full_shade" in sun


def _type(row: dict) -> str:
    return (row.get("plant_type") or "").strip() or "wildflower"


def counts(rows: list) -> list:
    """How many of each row a community places, in the rows' order."""
    out = []
    for row in rows:
        kind = _type(row)
        if kind == "tree" or kind == "vine":
            out.append(1)
        elif kind == "shrub":
            wide = float(row.get("mature_canopy_m") or _spacing(row) * 1.5)
            out.append(1 if wide >= 2.5 else 2 if wide >= 1.5 else 3)
        else:
            out.append(DRIFT.get(kind, 3))
    drifts = [i for i, r in enumerate(rows) if _type(r) not in _WOODY + ("vine",)]
    while sum(out) < MIN_PLANTS and (drifts or rows):
        grow = drifts or list(range(len(rows)))
        i = min(grow, key=lambda k: (out[k], k))
        out[i] += 1
    while sum(out) > MAX_PLANTS:
        cut = [i for i in drifts if out[i] > 2] or [
            i for i, r in enumerate(rows) if _type(r) == "shrub" and out[i] > 1]
        if not cut:
            break
        i = max(cut, key=lambda k: (out[k], -k))
        out[i] -= 1
    return out


def lay_out(members: list, lookup: Optional[Callable] = None) -> list:
    """``members`` are ``(common name, role)`` pairs or dicts with
    ``plant_id``; returns member dicts ``{plant_id, common_name, role,
    offset_x, offset_y}``, one per plant, largest first. ``lookup(name or
    id)`` returns the catalogue row (the database's, by default); a member it
    cannot find is left out."""
    if lookup is None:
        lookup = _lookup
    species = []
    for m in members:
        name, role = (m if isinstance(m, (tuple, list))
                      else (m.get("common_name") or m.get("plant_id"),
                            m.get("role") or ""))[:2]
        row = lookup(name)
        if row and all(row.get("id") != s[0].get("id") for s in species):
            species.append((row, role))
    species.sort(key=lambda s: (_SIZE_ORDER.index(_type(s[0]))
                                if _type(s[0]) in _SIZE_ORDER
                                else len(_SIZE_ORDER), -_spacing(s[0])))
    how_many = counts([s[0] for s in species])
    placed: list = []                    # (x, y, spacing, row)
    trees = [s for s in species if _type(s[0]) == "tree"]
    out = []
    n_drift = sum(1 for s in species if _type(s[0]) not in _WOODY)
    drift_i = 0
    for (row, role), n in zip(species, how_many):
        kind = _type(row)
        sp = _spacing(row)
        if kind == "tree":
            anchor, start = (0.0, 0.0), 0.0
        elif kind == "shrub":
            reach = max((_spacing(t[0]) for t in trees), default=0.0)
            anchor, start = (0.0, 0.0), reach / 2 + sp / 2 if trees else 0.0
        else:
            angle = drift_i * 2 * math.pi / max(1, n_drift) + 0.4
            drift_i += 1
            canopy = max((_spacing(t[0]) for t in trees), default=0.0)
            ring = (canopy / 2 * 0.6 if _shade_ok(row) and trees
                    else canopy / 2 + 1.0 if trees else 1.2)
            anchor = (ring * math.cos(angle), ring * math.sin(angle))
            start = 0.0
        for _k in range(n):
            x, y = _seat(anchor, start, sp, row, placed)
            placed.append((x, y, sp, row))
            out.append({"plant_id": row.get("id"),
                        "common_name": row.get("common_name") or "",
                        "role": role, "offset_x": round(x, 2),
                        "offset_y": round(y, 2)})
    return out


def _seat(anchor, start, sp, row, placed) -> tuple:
    """The first spot on a spiral out from ``anchor`` (beginning ``start``
    out) that stands clear of every plant placed."""
    shade = _shade_ok(row)
    woody = _type(row) in _WOODY
    step = max(0.12, sp * 0.35)
    for i in range(4000):
        r = start + step * math.sqrt(i)
        x = anchor[0] + r * math.cos(i * _GOLDEN)
        y = anchor[1] + r * math.sin(i * _GOLDEN)
        if all(_clear(x, y, sp, shade, woody, p) for p in placed):
            return x, y
    return anchor


def _clear(x, y, sp, shade, woody, other) -> bool:
    ox, oy, osp, orow = other
    d = math.hypot(x - ox, y - oy)
    if _type(orow) == "tree" and not woody:
        # Under a crown: a shade plant may stand there, clear of the trunk;
        # a sun plant stands outside it.
        return d >= TRUNK_CLEAR_M + sp / 2 if shade else d >= (osp + sp) / 2
    return d >= (osp + sp) / 2 - 1e-6


def _lookup(key):
    from src.db import plants                                   # noqa: PLC0415
    if isinstance(key, int):
        return plants.get_plant(key)
    from src.db.polycultures import _get_plant_by_name           # noqa: PLC0415
    return _get_plant_by_name(key)


def hidden(laid: list, lookup: Optional[Callable] = None) -> int:
    """How many plants of a layout lie wholly inside a bigger plant's circle
    and are not a shade plant under a tree: what the owner saw as missing."""
    if lookup is None:
        lookup = _lookup
    rows = [lookup(m["plant_id"]) or {} for m in laid]
    n = 0
    for i, (m, row) in enumerate(zip(laid, rows)):
        r = _spacing(row) / 2
        for j, (o, orow) in enumerate(zip(laid, rows)):
            R = _spacing(orow) / 2
            if i == j or R <= r:
                continue
            if _type(orow) == "tree" and _shade_ok(row):
                continue
            d = math.hypot(m["offset_x"] - o["offset_x"],
                           m["offset_y"] - o["offset_y"])
            if d + r <= R + 1e-6:
                n += 1
                break
    return n
