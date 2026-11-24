"""
plan_shade.py — a plan survives its own preview (F264, V3.52; 3D-5 of
docs/plans/V3.43-the-3d-preview-reviewed.md, the owner's decision D4).

Design principle P2 (the best designs disappear into their context) and P9
(confidence, never false precision) — see docs/DESIGN_PHILOSOPHY.md.

Until V3.52 Plan My Yard planted with no shade to read unless an elevation grid
could be fetched, and that grid is 10 m cells, coarser than most beds. The 3D
preview reads shade from the house and the trees already there, by the
succession engine, and on the review lot it shaded out 14 of the plan's plants
by the fifth summer and 38 by the tenth, every one in the bed north of the
house: sun plants put where the house shades the ground most of the day.

:func:`fit` runs last in the planner and asks **the preview's own model**
(:class:`~src.succession_engine.SuccessionEngine`, with ``fixed_only`` so only
the buildings and the trees already here cast) how much shade each plant of the
plan would stand in. A plant whose spot takes more than its sun needs allow
(``shade_ceiling``, the same limit that kills it in the preview) becomes a kind
that takes that shade, **where it stands**: the plan's layout, its drifts and
its cover stay, and only the shaded part of a drift changes kind, to one kind
per drift and shade, so it still reads as a drift. The replacement is the same
layer (``substitution.SUBSTITUTION_GROUPS``), of a similar height, from the
plan's own kinds first and then the site's ranked list the plan was drawn from,
never a plant of standing water, never one the street band refuses.

Shade from the plan's own plants is left alone: tall wildflowers slowly
crowding a short one over ten years is a thing that happens, and the preview
says so. Where nothing takes the shade, the plant is left out and the plan
says so.

A yard with no buildings and no trees already there is untouched: nothing here
runs without a fixed caster, so the plans of an open yard are what they were.

Qt-free.
"""

from __future__ import annotations

from typing import Callable, Iterable, Optional

#: Plants are judged at their first summer, when they are smallest and the most
#: casters overtop them: shade from a building never falls as a plant grows,
#: except for one that grows taller than the building, so the first year is the
#: most shade a plant will stand in from these casters.
JUDGED_YEAR = 1

#: A replacement's grown height may be at most this many times the original's,
#: or this much taller, whichever allows more; and at least this share of it.
TALLER_TIMES, TALLER_M, SHORTER_SHARE = 2.0, 0.5, 0.3

#: What a plant's page says (``why_here``) and the plan's note, by caster.
#: The part-shade limit (``succession_engine``'s): a drift's spots under it and
#: over it are told apart, so part shade does not get only full-shade plants.
_TIER = 0.70

WHY = "Shaded by {what} for much of the day: a kind that takes shade"
WHAT = {"building": "a building", "tree": "a tree already here",
        "both": "a building or a tree already here"}


def _height(row: dict) -> float:
    try:
        return float(row.get("mature_height_meters") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _takes(row: dict, shade: float) -> bool:
    """Whether a plant's recorded sun needs take ``shade``. A plant whose needs
    are not recorded is never chosen to stand in shade: the engine gives it a
    forgiving limit so as not to invent a death, which is not a reason to plant
    it there (P9)."""
    from src.succession_engine import shade_ceiling
    return bool((row.get("sun_requirement") or "").strip()) \
        and shade_ceiling(row.get("sun_requirement")) >= shade


def misfits(placed: list, static_casters: list,
            get_plant: Callable) -> list:
    """The plan's plants that stand in more shade from the fixed casters than
    their sun needs take: ``[(index, shade, what)]``, ``what`` being
    "building" or "tree". ``[]`` with no fixed caster."""
    if not placed or not static_casters:
        return []
    from src.succession_engine import SuccessionEngine, shade_ceiling
    engine = SuccessionEngine(placed, get_plant=get_plant,
                              static_casters=static_casters, fixed_only=True)
    out = []
    for i, p in enumerate(placed):
        shade = engine.experienced_shade(i, JUDGED_YEAR)
        if shade <= 0.0:
            continue
        row = get_plant(p.get("plant_id")) or {}
        if shade <= shade_ceiling(row.get("sun_requirement")):
            continue
        by = engine.main_shader(i, JUDGED_YEAR) or {}
        out.append((i, shade, "tree" if by.get("is_tree") else "building"))
    return out


def _fits_size(row: dict, original: dict) -> bool:
    h0, h = _height(original), _height(row)
    if h0 <= 0.0 or h <= 0.0:
        return True
    return SHORTER_SHARE * h0 <= h <= max(h0 * TALLER_TIMES, h0 + TALLER_M)


def choose(original: dict, shade: float, candidates: Iterable[dict], *,
           allowed: Optional[Callable] = None) -> Optional[dict]:
    """The kind to plant instead of ``original`` in ``shade``: the first of
    ``candidates`` (plan's own kinds first, then the ranked list) of the same
    layer and a similar height that takes the shade, or ``None``. ``allowed``
    is asked of each candidate row (the street band, standing water)."""
    from src.substitution import _layer_of
    layer = _layer_of(original)
    if not layer:
        return None
    for strict in (True, False):
        for row in candidates:
            if (row.get("id") == original.get("id")
                    or _layer_of(row) != layer or not _takes(row, shade)):
                continue
            if strict and not _fits_size(row, original):
                continue
            if allowed is not None and not allowed(row):
                continue
            return row
    return None


def fit(project, existing_features: Optional[list], pool: list, *,
        refuse: Optional[Callable] = None,
        get_plant: Optional[Callable] = None) -> dict:
    """Trade each plant of ``project`` the fixed shade would kill for a kind
    that takes it, where it stands. ``pool`` is the site's ranked list the plan
    drew from; ``refuse(lat, lng, row)`` is the street band's rule. Returns
    ``{"swapped": {old_name: new_name}, "dropped": [names], "what": key}``,
    empty when nothing needed it."""
    from src.project_store import ProjectStore
    from src.succession_engine import static_casters_from_project
    from src.zoning import needs_standing_water
    if get_plant is None:
        from src.db.plants import get_plant
    statics = static_casters_from_project(
        {"features": list(existing_features or [])})
    store = ProjectStore(project.as_dict())
    placed = [p for p in store.placed_plants if p.get("feature_id")]
    found = misfits(placed, statics, get_plant)
    if not found:
        return {}
    rows: dict = {}

    def row_of(pid):
        if pid not in rows:
            rows[pid] = get_plant(pid) or {}
        return rows[pid]

    in_plan = [row_of(pid) for pid in dict.fromkeys(
        p.get("plant_id") for p in placed)]
    candidates = [r for r in in_plan + list(pool or []) if r.get("id")
                  and not needs_standing_water(r)]
    # One kind per drift and shade: the drift's shaded part reads as a drift.
    groups: dict = {}
    for i, shade, what in found:
        p = placed[i]
        key = (p.get("plant_id"), p.get("placement_group_id") or "",
               _TIER if shade <= _TIER else 1.0)
        groups.setdefault(key, []).append((p, shade, what))
    swapped: dict = {}
    dropped: list = []
    whats = set()
    for (pid, _group, _tier), members in groups.items():
        original = row_of(pid)
        shade = max(s for _p, s, _w in members)
        spots = [(p["lat"], p["lng"]) for p, _s, _w in members]
        what = {w for _p, _s, w in members}
        whats |= what

        def allowed(row, spots=spots):
            return refuse is None or not any(refuse(la, ln, row)
                                             for la, ln in spots)
        new = choose(original, shade, candidates, allowed=allowed)
        name = original.get("common_name") or ""
        if new is None:
            store.remove_plants_batch(
                [(p["plant_id"], p["lat"], p["lng"]) for p, _s, _w in members])
            dropped.append(name)
            continue
        why = [WHY.format(what=WHAT["both" if len(what) > 1
                                    else next(iter(what))])]
        for p, _s, _w in members:
            store.change_species(p["feature_id"], new["id"],
                                 new.get("common_name") or "", why_here=why)
        swapped.setdefault(name, new.get("common_name") or "")
    return {"swapped": swapped, "dropped": list(dict.fromkeys(dropped)),
            "what": "both" if len(whats) > 1 else next(iter(whats))}


def merged(*done: dict) -> dict:
    """Several :func:`fit` answers for one plan, as one."""
    out: dict = {"swapped": {}, "dropped": [], "what": ""}
    whats = set()
    for d in done:
        if not d:
            continue
        out["swapped"].update(d.get("swapped") or {})
        out["dropped"] += [n for n in d.get("dropped") or []
                           if n not in out["dropped"]]
        whats.add(d.get("what") or "both")
    out["what"] = (next(iter(whats)) if len(whats) == 1 else "both")
    return out if (out["swapped"] or out["dropped"]) else {}


def note_fields(done: dict) -> dict:
    """The plan note's fields for :func:`fit`'s answer."""
    return {"what": WHAT.get(done.get("what"), WHAT["both"]),
            "names": sorted(set((done.get("swapped") or {}).values())),
            "left": list(done.get("dropped") or [])}
