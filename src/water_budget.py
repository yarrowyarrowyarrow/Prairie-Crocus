"""
water_budget.py — how much water a design needs, and the rule a person can
follow (V3.20, OV-7).

Design principle P9 — see docs/DESIGN_PHILOSOPHY.md.

Moved out of the Water page (``planning_panel``), which had three faults the
first review found:

  * **Rows missing (R4).** The table listed six fixed types, so wildflowers,
    grasses and sedges were in the total with no row: the generated bed's
    twelve wildflowers were invisible.
  * **A seasonal surplus (R38).** It weighed the season's demand against the
    season's rain and called the difference a surplus. A new planting dies in
    a two-week dry spell whatever the season's total, so the page now gives the
    care calendar's rule as a weekly quantity: a deep soak in any week without
    a good rain.
  * **One city's rainfall, wherever the pin.** Rainfall now comes from the
    site's own normals when they have been fetched, labelled with their source,
    and only otherwise from the region pack's station normals, labelled so
    (V3.25); a pin outside the provinces gets none.

The numbers are estimates per plant type and water need, the same constants
the page always used; the supply side stays as information.
"""

from __future__ import annotations

from typing import Optional

from src.plant_conditions import condition_tokens


#: Litres a week through the growing season, by plant type, before the
#: water-need multiplier. A type not listed uses :data:`DEFAULT_L_WEEK`.
PLANT_WATER_NEEDS_L_WEEK = {
    "tree": 40.0, "shrub": 15.0, "herb": 8.0, "groundcover": 3.0,
    "vine": 12.0, "root": 6.0,
}
DEFAULT_L_WEEK = 8.0

WATER_MULTIPLIER = {"low": 0.5, "medium": 1.0, "high": 1.5}

#: Year 1 waters everything in; from year 3 established natives are nearly
#: rain-fed and cultivars keep their full demand.
Y1_MULT = 1.5
Y3_MULT_NATIVE = 0.2
Y3_MULT_CULTIVATED = 1.0

#: May to September, the weeks the demand is spread over.
GROWING_WEEKS = 22

#: A good rain, the calendar's deep soak (``maintenance_calendar``, Year 1).
GOOD_RAIN = "15–20 mm"


def _plant_litres(plant: dict) -> tuple:
    """``(year 1, year 3+)`` seasonal litres for one placed plant."""
    ptype = (plant.get("plant_type") or "herb")
    tokens = condition_tokens(plant.get("water_needs"))
    need = tokens[0] if tokens else "medium"
    weekly = (PLANT_WATER_NEEDS_L_WEEK.get(ptype, DEFAULT_L_WEEK)
              * WATER_MULTIPLIER.get(need, 1.0))
    season = weekly * GROWING_WEEKS
    native = bool(plant.get("native", plant.get("native_to_alberta")))
    return (season * Y1_MULT,
            season * (Y3_MULT_NATIVE if native else Y3_MULT_CULTIVATED))


def demand_by_type(plants) -> dict:
    """``{plant type: {"count", "native", "y1", "y3"}}`` in seasonal litres,
    a row for every type present, in the plant key's order
    (``member_colors.TYPE_COLORS``), then any other type by name."""
    rows: dict = {}
    for p in plants or []:
        y1, y3 = _plant_litres(p)
        slot = rows.setdefault(p.get("plant_type") or "herb",
                               {"count": 0, "native": 0, "y1": 0.0, "y3": 0.0})
        slot["count"] += 1
        slot["native"] += 1 if p.get("native", p.get("native_to_alberta")) else 0
        slot["y1"] += y1
        slot["y3"] += y3
    from src.member_colors import TYPE_COLORS
    order = ([t for t in TYPE_COLORS if t in rows]
             + sorted(t for t in rows if t not in TYPE_COLORS))
    return {t: rows[t] for t in order}


def first_summer_weekly_litres(plants) -> float:
    """Litres a week in the first summer: the year-1 demand over the
    growing weeks."""
    return sum(_plant_litres(p)[0] for p in plants or []) / GROWING_WEEKS


def rainfall(site_config: Optional[dict]) -> tuple:
    """``(monthly mm × 12, where it is from)``: the site's own normals when
    fetched (``site_config["rainfall"]["monthly_mm"]``), else the region
    pack's normals (V3.25, ED-6: a hand-rounded copy of Edmonton's had been
    the fallback for every pin), else none at all for a pin outside the
    provinces, which reads as twelve zeros and says so."""
    rain = ((site_config or {}).get("rainfall") or {})
    months = rain.get("monthly_mm") or []
    if len(months) == 12:
        try:
            values = tuple(float(m) for m in months)
        except (TypeError, ValueError):
            values = ()
        if values:
            source = (rain.get("source") or "").strip()
            return values, (f"this site's normals ({source})" if source
                            else "this site's normals")
    from src import region_climate                           # noqa: PLC0415
    months, label = region_climate.rainfall(site_config)
    return (months or (0.0,) * 12), label


def weekly_rule(plants) -> str:
    """The sentence the page and the overview give instead of a surplus."""
    litres = first_summer_weekly_litres(plants)
    if litres <= 0:
        return ""
    return (f"First summer: about {_round_litres(litres)} L a week in any "
            f"week without a good rain ({GOOD_RAIN}). From year 3: only in a "
            f"drought.")


def _round_litres(litres: float) -> str:
    """To 10 L, or 5 under 100, with a thousands comma: an estimate, said as
    one (P9)."""
    step = 5 if litres < 100 else 10
    return f"{max(step, int(round(litres / step)) * step):,}"


# ── City water: the spigot (V3.76) ──────────────────────────────────────────

#: The garden hoses a person is likely to own, metres: 50 ft and 75 ft.
HOSE_M = (15.0, 23.0)
#: Litres a minute through a garden hose on city pressure: **a stated
#: estimate** (a 5/8" hose runs about 10 to 20).
TAP_L_MIN = 12.0


def tap_reach(project) -> dict:
    """``{"taps": n, "metres": [...]}``: how many spigots are on the map, and
    each placed plant's straight-line distance to the nearest one (empty
    with none). ``src/yard_kinds.py`` says what a spigot is."""
    from src import yard_kinds                               # noqa: PLC0415
    from src.project_store import ProjectStore               # noqa: PLC0415
    from src.projection import Projector                     # noqa: PLC0415
    taps = []
    for f in (project or {}).get("features", []) or []:
        props = f.get("properties") or {}
        geom = f.get("geometry") or {}
        k = yard_kinds.kind_of(f)
        if (k is not None and k.water == "spigots"
                and geom.get("type") == "Point"):
            lng, lat = geom["coordinates"][:2]
            taps.append((lat, lng))
    if not taps:
        return {"taps": 0, "metres": []}
    proj = Projector(*taps[0])
    xy = [proj.to_xy(lat, lng) for lat, lng in taps]
    metres = []
    for p in ProjectStore(project).placed_plants:
        px, py = proj.to_xy(p["lat"], p["lng"])
        metres.append(min(((px - x) ** 2 + (py - y) ** 2) ** 0.5
                          for x, y in xy))
    return {"taps": len(taps), "metres": metres}


def tap_words(reach: dict, plants) -> str:
    """What the Water page says about city water: how far the planting is
    from a spigot, how much of it a garden hose reaches, and how long the
    first summer's weekly watering is at the tap. ``""`` with no plants."""
    metres = (reach or {}).get("metres") or []
    litres = first_summer_weekly_litres(plants)
    if not (reach or {}).get("taps"):
        return ("No spigot is on the map yet. Placement › Yard › Water › "
                "Spigot puts one on a wall, and this says how far a hose from "
                "it reaches." if plants else "")
    if not metres:
        return ""
    far = max(metres)
    short, long_ = HOSE_M
    words = (f"From the nearest spigot the farthest plant is {far:.0f} m "
             f"away in a straight line. ")
    if far <= short:
        words += f"A {short:.0f} m (50 ft) hose reaches all of them."
    else:
        n_short = sum(m <= short for m in metres)
        n_long = sum(m <= long_ for m in metres)
        words += (f"A {short:.0f} m (50 ft) hose reaches {n_short} of "
                  f"{len(metres)} plants, a {long_:.0f} m (75 ft) one "
                  f"{n_long}.")
    words += " Going round the house takes more hose."
    if litres > 0:
        minutes = max(1, int(round(litres / TAP_L_MIN)))
        words += (f" The first summer's weekly watering, about "
                  f"{_round_litres(litres)} L, is about {minutes} minutes "
                  f"at the tap.")
    return words
