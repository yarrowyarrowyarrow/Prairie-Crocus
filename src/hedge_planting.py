"""
src/hedge_planting.py — a hedge, a living fence or a windbreak as plants
(V3.74, F280's fourth increment).

Design principle P1 (living systems self-organize from the bottom up: encode
generative rules, not fixed layouts) — see docs/DESIGN_PHILOSOPHY.md. A hedge
is laid along the line the person drew by rule, from each plant's own size.

Until V3.74 a hedge was a green line with a species typed into a box: nothing
bought, scored, fed or shaded by it. Now drawing one plants the region's
shrubs along it (``docs/plans/V3.74-hedges-you-can-plant.md``):

* :func:`choices` / :func:`default_choice`: the plants a role can be (a
  hedge's shrub, a windbreak's back or front row), and which comes first.
* :func:`layout`: where each plant stands along the line.
* :func:`plant`: put them in the design through ``project_store``, grouped
  under the line (``placement_group_id`` is its ``hedge_id``), replacing any
  it had.
* :func:`planted` / :func:`unplanted`: whether a line has plants, **read from
  its plants**, never stored.
* :func:`match`: the shrub an old hedge's typed words name.

Every number here is a **stated estimate**, read from the catalogue where it
can be (P9). Qt-free and network-free; the catalogue is read through
``src.db.plants`` unless rows are handed in.
"""

from __future__ import annotations

import math
from typing import Callable, Iterable, Mapping, Optional

from src import yard_kinds

#: A hedge's or a living fence's shrubs stand at least knee high: below it a
#: row of shrubs is an edging, not a hedge.
HEDGE_MIN_M = 0.75
#: A windbreak's back row: trees and shrubs at least this tall; its front
#: row: shrubs at least this tall.
TALL_MIN_M = 4.0
FRONT_MIN_M = 2.0
#: A windbreak's two rows stand apart by this share of the back row's
#: spacing, and at least this far: close enough to read as one belt, far
#: enough that the front row is not under the back row's young crowns.
ROW_GAP_SHARE = 0.5
ROW_GAP_MIN_M = 1.5
#: A spacing the catalogue does not record, or records as nothing.
FALLBACK_SPACING_M = 1.0
MIN_SPACING_M = 0.3
#: An old hedge's typed word counts toward a match at this many letters
#: ("rose" does, "red" does not).
MATCH_MIN = 4
#: What a planted hedge's plants are filed as.
PATTERN_KIND = "hedge"

#: The roles an option asks a plant for (``yard_kinds.Option.plants``).
SHRUB, TALL, FRONT = "shrub", "tall", "front"
ROLE_WORDS = {SHRUB: "shrub", TALL: "tree or tall shrub", FRONT: "shrub"}


# ── which plants ────────────────────────────────────────────────────────────

def _region_rows(plant_type: str) -> list:
    """The region's natives of a type (the list every plant list searches),
    else the province's where no pack has a list."""
    from src import region                                   # noqa: PLC0415
    from src.db.plants import search_plants                  # noqa: PLC0415
    home = region.default()
    rows = []
    if home is not None:
        try:
            rows = search_plants(plant_type=plant_type, native_near=home.key)
        except Exception:                                    # noqa: BLE001
            rows = []
    if not rows:
        rows = search_plants(plant_type=plant_type, native_only=True)
    return list(rows)


def _height(row: Mapping) -> float:
    try:
        return float(row.get("mature_height_meters") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _stands(row: Mapping) -> bool:
    """Not a mat, and not a plant that needs standing water."""
    from src import zoning                                   # noqa: PLC0415
    if (row.get("branching") or "").strip() == "prostrate":
        return False
    return not zoning.needs_standing_water(row)


def fits(role: str, row: Mapping) -> bool:
    """Whether ``row`` can fill ``role``."""
    ptype = (row.get("plant_type") or "").strip().lower()
    h = _height(row)
    if not _stands(row):
        return False
    if role == TALL:
        return ptype == "tree" or (ptype == "shrub" and h >= TALL_MIN_M)
    if role == FRONT:
        return ptype == "shrub" and h >= FRONT_MIN_M
    return ptype == "shrub" and h >= HEDGE_MIN_M


def candidates(role: str, rows: Optional[Iterable[Mapping]] = None) -> list:
    """The plants ``role`` can be, best first: sold locally, then the plant
    list's own order (``plant_priority.rank``); a windbreak's back row an
    evergreen first, because a windbreak is mostly for winter."""
    if rows is None:
        rows = _region_rows("shrub") + (_region_rows("tree")
                                        if role == TALL else [])
    pool = [r for r in rows if fits(role, r)]
    try:
        from src import plant_priority                       # noqa: PLC0415
        pool = plant_priority.rank(pool)
    except Exception:                                        # noqa: BLE001
        pool.sort(key=lambda r: (r.get("common_name") or "").lower())
    try:
        from src import local_stock                          # noqa: PLC0415
        sold = {id(r): local_stock.easy_to_find(r) for r in pool}
    except Exception:                                        # noqa: BLE001
        sold = {id(r): True for r in pool}
    evergreen_first = role == TALL
    pool = sorted(pool, key=lambda r: (
        evergreen_first and (r.get("deciduous_evergreen") or "") != "evergreen",
        not sold[id(r)]))                   # stable: the rank breaks ties
    return pool


def choices(role: str, rows: Optional[Iterable[Mapping]] = None) -> list:
    """``[(plant id, name)]`` for a list a person picks from, by name."""
    return sorted(((int(r["id"]), r.get("common_name") or "")
                   for r in candidates(role, rows)),
                  key=lambda c: c[1].lower())


def default_choices(kind_key: str,
                    rows: Optional[Iterable[Mapping]] = None) -> dict:
    """``{option key: plant id}`` chosen first for a kind: the best for each
    role, never the same plant twice in one line; an optional one none."""
    k = yard_kinds.BY_KEY[kind_key]
    rows = None if rows is None else list(rows)
    used: set = set()
    out: dict = {}
    for o in k.options:
        if not o.plants:
            continue
        if o.optional:
            out[o.key] = None
            continue
        for r in candidates(o.plants, rows):
            if int(r["id"]) not in used:
                out[o.key] = int(r["id"])
                used.add(int(r["id"]))
                break
        else:
            out[o.key] = None
    return out


def chosen_ids(kind_key: str, options: Mapping) -> list:
    """The plant ids a line's options name, in the kind's order (a living
    fence's two or three; a windbreak's back row then front row)."""
    k = yard_kinds.BY_KEY.get(kind_key)
    if k is None:
        return []
    out = []
    for o in k.options:
        if not o.plants:
            continue
        try:
            pid = int(options.get(o.key))
        except (TypeError, ValueError):
            continue
        if pid > 0:
            out.append(pid)
    return out


# ── where they stand ────────────────────────────────────────────────────────

def spacing_of(row: Mapping) -> float:
    """A plant's own spacing: the catalogue's crown is 1.5 times it, so
    neighbours' crowns overlap by half a spacing once grown and the hedge
    closes as it grows."""
    try:
        s = float(row.get("spacing_meters") or 0.0)
    except (TypeError, ValueError):
        s = 0.0
    return max(MIN_SPACING_M, s or FALLBACK_SPACING_M)


def _along(xy: list, steps: list) -> list:
    """Points ``steps`` metres along the polyline ``xy``, each with the
    segment's direction ``(x, y, ux, uy)``."""
    segs = []
    for (x0, y0), (x1, y1) in zip(xy, xy[1:]):
        length = math.hypot(x1 - x0, y1 - y0)
        if length > 0:
            segs.append((x0, y0, (x1 - x0) / length, (y1 - y0) / length,
                         length))
    out = []
    if not segs:
        return out
    for d in steps:
        rest = d
        for i, (x0, y0, ux, uy, length) in enumerate(segs):
            if rest <= length or i == len(segs) - 1:
                t = min(rest, length)
                out.append((x0 + ux * t, y0 + uy * t, ux, uy))
                break
            rest -= length
    return out


def _even(length: float, spacing: float) -> list:
    """``n`` = round(length / spacing) steps (at least one), evenly, half a
    step in from each end."""
    n = max(1, int(round(length / spacing)))
    step = length / n
    return [(i + 0.5) * step for i in range(n)]


def layout(points: list, kind_key: str, rows: list) -> list:
    """``[(row, lat, lng)]`` along a line of ``points`` (``[lng, lat]``, as
    GeoJSON stores it): a hedge one row of its shrub, a living fence its two
    or three repeated in order at their mean spacing, a windbreak two rows
    either side, the back row on the side facing more north."""
    from src.projection import Projector                     # noqa: PLC0415
    rows = [r for r in rows if r]
    if len(points) < 2 or not rows:
        return []
    proj = Projector(points[0][1], points[0][0])
    xy = [proj.to_xy(p[1], p[0]) for p in points]
    length = sum(math.hypot(b[0] - a[0], b[1] - a[1])
                 for a, b in zip(xy, xy[1:]))
    if length <= 0:
        return []
    out = []

    def _put(row, x, y):
        lat, lng = proj.to_latlng(x, y)
        out.append((row, lat, lng))

    if kind_key == "windbreak" and len(rows) >= 2:
        back, front = rows[0], rows[1]
        gap = max(ROW_GAP_MIN_M, ROW_GAP_SHARE * spacing_of(back))
        # One side for the whole line, so a bent windbreak's rows never swap
        # at a corner: its left side when that faces more north than south
        # along its length, else its right (east for a line due north).
        north = sum((b[0] - a[0]) for a, b in zip(xy, xy[1:]))
        east = sum(-(b[1] - a[1]) for a, b in zip(xy, xy[1:]))
        left = 1.0 if (north > 1e-9 or (abs(north) <= 1e-9 and east > 0)) \
            else -1.0
        for row, side in ((back, left), (front, -left)):
            for x, y, ux, uy in _along(xy, _even(length, spacing_of(row))):
                off = side * gap / 2.0              # along the left normal
                _put(row, x - uy * off, y + ux * off)
        return out
    spacing = sum(spacing_of(r) for r in rows) / len(rows)
    for i, (x, y, _ux, _uy) in enumerate(_along(xy, _even(length, spacing))):
        _put(rows[i % len(rows)], x, y)
    return out


# ── in the design ───────────────────────────────────────────────────────────

def _lines(project: Mapping) -> list:
    return [f for f in (project or {}).get("features", []) or []
            if (f.get("properties") or {}).get("element_type") == "hedgerow"
            and yard_kinds.is_living_line(f)]


def line_by_id(project: Mapping, hedge_id: str) -> Optional[dict]:
    for f in _lines(project):
        if (f.get("properties") or {}).get("hedge_id") == hedge_id:
            return f
    return None


def plants_of(project: Mapping, hedge_id: str) -> list:
    """The plant features grouped under the line ``hedge_id``."""
    if not hedge_id:
        return []
    return [f for f in (project or {}).get("features", []) or []
            if (f.get("properties") or {}).get("element_type") == "plant"
            and (f.get("properties") or {}).get("placement_group_id")
            == hedge_id]


def planted(project: Mapping) -> set:
    """The ``hedge_id`` of every hedge, living fence and windbreak with
    plants standing on it."""
    groups = {(f.get("properties") or {}).get("placement_group_id")
              for f in (project or {}).get("features", []) or []
              if (f.get("properties") or {}).get("element_type") == "plant"}
    return {(f.get("properties") or {}).get("hedge_id")
            for f in _lines(project)
            if (f.get("properties") or {}).get("hedge_id") in groups}


def unplanted(project: Mapping) -> list:
    """The living lines with no plants, longest first."""
    done = planted(project)
    out = [f for f in _lines(project)
           if (f.get("properties") or {}).get("hedge_id") not in done]
    return sorted(out, key=lambda f: -yard_kinds.line_length_m(
        (f.get("geometry") or {}).get("coordinates") or []))


def plant(project: dict, feature: dict, rows: list, *, store=None,
          on_added: Optional[Callable] = None) -> list:
    """Plant the line ``feature`` with ``rows`` (the plants its options
    named, in order), replacing any plants it had. Returns the records added.
    ``store`` is the design's ``ProjectStore`` (one is made when absent);
    ``on_added(record)`` is told of each, for a map to draw it."""
    from src import why_here                                 # noqa: PLC0415
    from src.project_store import ProjectStore               # noqa: PLC0415
    store = store if store is not None else ProjectStore(project)
    props = feature.setdefault("properties", {})
    hid = props.get("hedge_id") or ""
    gone = plants_of(project, hid)
    if gone:
        store.remove_plants_batch(
            (f["properties"].get("plant_id"),
             f["geometry"]["coordinates"][1],
             f["geometry"]["coordinates"][0]) for f in gone)
    k = yard_kinds.kind_of(feature)
    key = k.key if k is not None else "hedge"
    spots = layout((feature.get("geometry") or {}).get("coordinates") or [],
                   key, rows)
    why = [why_here.HEDGE.format(line=(k.words if k else "hedge").lower())]
    added = []
    for row, lat, lng in spots:
        rec = store.add_plant(int(row["id"]), row.get("common_name") or "",
                              lat, lng, placement_group_id=hid,
                              pattern_kind=PATTERN_KIND, why_here=why)
        added.append(rec)
        if on_added is not None:
            on_added(rec)
    props["plant_ids"] = [int(r["id"]) for r in rows]
    props["num_plants"] = len(added)
    if rows:
        props["spacing_m"] = round(sum(spacing_of(r) for r in rows)
                                   / len(rows), 2)
    return added


def remove(project: dict, hedge_id: str, *, store=None) -> list:
    """Take the line ``hedge_id`` and its plants out of the design. Returns
    the plant records removed."""
    from src.project_store import ProjectStore               # noqa: PLC0415
    store = store if store is not None else ProjectStore(project)
    gone = plants_of(project, hedge_id)
    removed = store.remove_plants_batch(
        (f["properties"].get("plant_id"), f["geometry"]["coordinates"][1],
         f["geometry"]["coordinates"][0]) for f in gone) if gone else []
    project["features"] = [
        f for f in project.get("features", [])
        if (f.get("properties") or {}).get("hedge_id") != hedge_id]
    return removed


# ── an old hedge's words (the owner's Q5) ───────────────────────────────────

def match(feature: Mapping, rows: Optional[Iterable[Mapping]] = None) -> \
        Optional[dict]:
    """The candidate an old line's typed ``species`` names (the reader that
    takes a nursery's names, renames and old names, ``stock_lists.match``),
    or ``None``."""
    from src import stock_lists                              # noqa: PLC0415
    words = ((feature or {}).get("properties") or {}).get("species") or ""
    if not words.strip():
        return None
    k = yard_kinds.kind_of(feature) or yard_kinds.BY_KEY["hedge"]
    rows = None if rows is None else list(rows)
    pool, seen = [], set()
    for o in k.options:                     # every role the line plants
        for r in (candidates(o.plants, rows) if o.plants else ()):
            if int(r["id"]) not in seen:
                seen.add(int(r["id"]))
                pool.append(r)
    found, _unread = stock_lists.match(words, stock_lists.name_table(pool))
    by_sci = {(r.get("scientific_name") or "").strip(): r for r in pool}
    for sci in found:
        if sci in by_sci:
            return dict(by_sci[sci])
    # "saskatoon" or "dogwood" names no catalogue row whole: the candidate
    # sharing most of its words wins, the best-ranked first among equals.
    said = {w for w in stock_lists.norm(words).split() if len(w) >= MATCH_MIN}
    best, score = None, 0
    for r in pool:
        names = set(stock_lists.norm(" ".join(
            [r.get("common_name") or "", r.get("scientific_name") or ""])
        ).split())
        n = len(said & names)
        if n > score:
            best, score = r, n
    return dict(best) if best is not None else None


def offer_choices(feature: Mapping,
                  rows: Optional[Iterable[Mapping]] = None) -> dict:
    """The choices *Plant this hedge…* opens with: the line's own plants if
    it had some, else the defaults with its words' match first."""
    k = yard_kinds.kind_of(feature)
    key = k.key if k is not None else "hedge"
    rows = None if rows is None else list(rows)
    out = default_choices(key, rows)
    keys = [o.key for o in yard_kinds.BY_KEY[key].options if o.plants]
    own = ((feature or {}).get("properties") or {}).get("plant_ids") or []
    if own:
        for okey, pid in zip(keys, own):
            out[okey] = int(pid)
        return out
    found = match(feature, rows)
    if found is None:
        return out
    plant_opts = [o for o in yard_kinds.BY_KEY[key].options if o.plants]
    slot = next((o for o in plant_opts if fits(o.plants, found)), None)
    if slot is None:
        return out
    fid = int(found["id"])
    out[slot.key] = fid
    for o in plant_opts:                    # never the same plant twice
        if o.key != slot.key and out.get(o.key) == fid:
            used = set(out.values())
            out[o.key] = next((int(r["id"]) for r in candidates(o.plants, rows)
                               if int(r["id"]) not in used), None)
    return out
