"""
through_the_year.py — Design › Through the year: the design's year month by
month, who eats here when, and the two stories the animal records tell best
(F270, V3.55; docs/plans/V3.55-the-year-and-who-it-feeds.md).

Design principle P10 — see docs/DESIGN_PHILOSOPHY.md.

The owner, reviewing the Design tab: the month by month "is far and away the
most useful information", and "most people do not know or aim to create a yard
for a specific creature". So the animals come to the person instead of the
person choosing one from 1,603:

  * :func:`year` — twelve months, each with what is in flower, in fruit and to
    harvest (people kept apart, as ``what_it_feeds.month_by_month`` keeps
    them), **who is eating here** (:func:`visitors`), one thing to go and look
    at and the month's jobs. It replaces Over time's *This month*: one
    calendar, not two.
  * :func:`caterpillars` — the chickadee brood in plain words.
    ``chickadee_scenario`` stays the arithmetic; the words here say more or
    less than a brood, never the coarse proxy's "106,500–284,000".
  * :func:`depends` — animals recorded as depending on a few plants (the
    documented ``specificity = 'specialist'`` records only, never "few records
    in the catalogue", which is as often a gap in what is known, P9), and
    whether this yard has one of them.

**Who is eating here** is read off the records as the rest of the page is:
food edges only, an animal active in a month when its plant flowers, fruits or
is in leaf by ``what_it_feeds.months_for``. Only animals with an English name
and one species each (WD-7; no *spp.* groups), and inside a region pack only
animals recorded near the yard (``fauna_fit`` *here*). Nothing says an animal
*will* come: the records say it has been seen eating the plant, and seen near
the yard.

Qt-free.
"""

from __future__ import annotations

from typing import Callable, Iterable, Optional

from src import what_it_feeds as feeds

MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")

#: How many animals a month names.
PER_MONTH = 3
#: How many jobs a month lists.
JOBS = 2

#: Which record makes the better line, first first: a caterpillar on the plant
#: or a bird at its fruit says more than one more bee at a flower.
_KIND_RANK = {"larval_host": 0, "fruit_food": 1, "seed_food": 2,
              "pollen": 3, "nectar": 4}

#: The groups, in the order a month takes its first of each.
_GROUP_ORDER = ("lepidoptera", "bird", "bee", "other_insect", "mammal")

#: What a month's "who is eating here" rests on, inside a pack and outside.
NEAR_WORDS = "Recorded eating these plants, and recorded near you."
FAR_WORDS = "Recorded eating these plants in Alberta and Saskatchewan."


# ── Who an animal is ────────────────────────────────────────────────────────

def one_species(animal: dict) -> bool:
    """A single species with an English name (WD-7): not "Mining Bees",
    *Andrena spp.*, nor a name that is only its Latin one."""
    from src.yard_overview_items import english_name
    sci = (animal.get("scientific_name") or "").strip()
    if not english_name(animal) or "spp" in sci or len(sci.split()) < 2:
        return False
    return True


def _near(records, animal: dict) -> bool:
    """Recorded near the yard, inside a pack; anything outside one (the app
    has no counts there and borrows none)."""
    if records is None:
        return True
    from src.fauna_fit import HERE
    return records.band(animal.get("scientific_name") or "") == HERE


def _familiar(records, animal: dict) -> bool:
    return bool(records is not None
                and records.familiar(animal.get("scientific_name") or ""))


def line(name: str, kind: str, taxon: str, plant: str) -> str:
    """'Monarch: caterpillars on Oval-leaf Milkweed' (V3.55's owner: "be
    more concise")."""
    if kind == "larval_host" and taxon == "lepidoptera":
        what = f"caterpillars on {plant}"
    elif kind == "larval_host" and taxon != "bee":
        what = f"young on {plant}"
    elif kind in ("pollen", "larval_host"):
        what = f"pollen from {plant}"
    elif kind == "nectar":
        what = f"nectar from {plant}"
    elif kind == "fruit_food":
        what = f"fruit of {plant}"
    elif kind == "seed_food":
        what = f"seed of {plant}"
    else:
        what = plant
    return f"{name}: {what}"


# ── Who eats here, month by month ───────────────────────────────────────────

def _candidates(plant_ids, records, counts, connect) -> list:
    """The animals that may be named, each with what it eats here when:
    ``[{animal, familiar, by_month: {m: (kind, plant name)}}]``."""
    from src.yard_overview_items import english_name
    ids = sorted({int(p) for p in plant_ids})
    if not ids:
        return []
    food = feeds.plant_food(ids, connect=connect)
    names = {pid: r["common_name"]
             for pid, r in feeds._plant_rows(ids, connect).items()}
    out = []
    for a in feeds.animals_fed(ids, connect=connect):
        if not a["food"] or not one_species(a) or not _near(records, a):
            continue
        by_month: dict = {}
        for pid, kinds in a["plants"].items():
            f = food.get(pid) or {}
            for kind in kinds:
                if kind not in _KIND_RANK:
                    continue
                for m in feeds.months_for(kind, f.get("bloom") or (),
                                          f.get("fruit") or (), a["taxon"]):
                    best = by_month.get(m)
                    cand = (_KIND_RANK[kind], -counts.get(pid, 0),
                            names.get(pid, ""), kind)
                    if best is None or cand < best:
                        by_month[m] = cand
        if by_month:
            out.append({"animal": a, "name": english_name(a),
                        "familiar": _familiar(records, a),
                        "by_month": by_month})
    return out


def _pick(cands: list, month: Optional[int], k: int,
          shown: Optional[dict] = None, minor: tuple = ()) -> list:
    """Up to ``k`` of ``cands`` for ``month`` (any month when ``None``):
    familiar first, an animal shown fewer times this year before one shown
    more, one of each group before a second of any (a group in ``minor`` only
    after a second of the others), the better record, most plants."""
    shown = shown or {}

    def best(c):
        if month is None:
            return min(c["by_month"].values())
        return c["by_month"].get(month)

    pool = [c for c in cands if best(c) is not None]
    chosen: list = []
    groups: dict = {}
    while pool and len(chosen) < k:
        def key(c):
            taxon = c["animal"]["taxon"]
            rank = best(c)
            return (not c["familiar"], shown.get(c["name"], 0),
                    groups.get(taxon, 0) + (1.5 if taxon in minor else 0),
                    _GROUP_ORDER.index(taxon) if taxon in _GROUP_ORDER
                    else len(_GROUP_ORDER),
                    rank[0], -len(c["animal"]["plants"]), c["name"].lower())
        c = min(pool, key=key)
        pool.remove(c)
        taxon = c["animal"]["taxon"]
        groups[taxon] = groups.get(taxon, 0) + 1
        chosen.append(c)
    return chosen


def _counts(placed_plants) -> dict:
    counts: dict = {}
    for p in placed_plants or []:
        try:
            pid = int(p.get("plant_id"))
        except (TypeError, ValueError):
            continue
        counts[pid] = counts.get(pid, 0) + 1
    return counts


def visitors(placed_plants, *, records=None, per_month: int = PER_MONTH,
             connect: Optional[Callable] = None) -> dict:
    """``{month: [{name, taxon, kind, plant, line}]}``: who is eating here,
    each month, as :func:`year` shows it."""
    counts = _counts(placed_plants)
    cands = _candidates(counts, records, counts, connect)
    out: dict = {}
    shown: dict = {}
    for m in range(1, 13):
        picked = _pick(cands, m, per_month, shown)
        out[m] = [_row(c, c["by_month"][m]) for c in picked]
        for c in picked:
            shown[c["name"]] = shown.get(c["name"], 0) + 1
    return out


def named_animals(placed_plants, *, records=None, k: int = 3,
                  connect: Optional[Callable] = None) -> list:
    """The ``k`` animals the Overview names, by the same rule over the whole
    year, a butterfly, a bird or a bee before a fly or a beetle: ``[name]``."""
    counts = _counts(placed_plants)
    cands = _candidates(counts, records, counts, connect)
    return [c["name"] for c in _pick(cands, None, k,
                                     minor=("other_insect", "mammal"))]


def _row(c: dict, rank: tuple) -> dict:
    _r, _n, plant, kind = rank
    taxon = c["animal"]["taxon"]
    return {"name": c["name"], "taxon": taxon, "kind": kind, "plant": plant,
            "fauna_id": c["animal"]["fauna_id"],
            "line": line(c["name"], kind, taxon, plant)}


# ── The year ────────────────────────────────────────────────────────────────

def summary(month: dict) -> str:
    """'6 in flower · 4 in fruit · 5 to harvest', or what a quiet month is."""
    bits = []
    if month["flowering"]:
        bits.append(f"{len(month['flowering'])} in flower")
    if month["fruit"]:
        bits.append(f"{len(month['fruit'])} in fruit")
    if month["harvest"]:
        bits.append(f"{len(month['harvest'])} to harvest")
    if bits:
        return " · ".join(bits)
    return "nothing in flower" if month["gap"] else "resting"


def next_active(months: list, now: int) -> int:
    """``now`` when something is in flower or fruit then, else the first
    month after it that has (round the year), else 0."""
    for step in range(12):
        m = (now - 1 + step) % 12 + 1
        month = months[m - 1]
        if month["flowering"] or month["fruit"]:
            return m
    return 0


def flowering_line(months: list) -> str:
    """'In flower from March to October.' with the growing season's empty
    months named, from the design's own first and last flowering months (the
    page had printed April, the growing season's first month)."""
    flowering = [m["month"] for m in months if m["flowering"]]
    if not flowering:
        return "Nothing here has a recorded flowering time yet."
    first, last = MONTHS[flowering[0] - 1], MONTHS[flowering[-1] - 1]
    text = (f"In flower from {first} to {last}." if first != last
            else f"In flower in {first}.")
    gaps = [MONTHS[m["month"] - 1] for m in months if m["gap"]]
    if gaps:
        text += (" Nothing in flower in " + ", ".join(gaps[:-1])
                 + (" or " if len(gaps) > 1 else "") + gaps[-1] + ".")
    return text


def year(placed_plants, *, records=None,
         connect: Optional[Callable] = None,
         get_calendar: Optional[Callable] = None,
         get_plant: Optional[Callable] = None) -> dict:
    """The design's year: ``{"months": [{month, name, flowering, fruit,
    harvest, gap, visitors, look, jobs}], "near": bool, "gaps": [m…]}``.

    ``flowering`` is the plants in flower for pollinators, ``fruit`` the
    plants in fruit, ``harvest`` ``[(plant, part)]`` (``what_it_feeds``);
    ``gap`` a growing-season month with nothing in flower; ``look`` one thing
    to go outside and check (``phenology``, P11); ``jobs`` the month's jobs
    from the planting calendar, and the first summer's (harvest is not a job
    here: it is its own line)."""
    from src import phenology
    counts = _counts(placed_plants)
    ids = sorted(counts)
    base = feeds.month_by_month(ids, connect=connect)
    who = visitors(placed_plants, records=records, connect=connect)
    pheno = (phenology.build_phenology(placed_plants, get_calendar=get_calendar,
                                       get_plant=get_plant)
             if ids else None)
    growing = set(feeds.GROWING_SEASON_MONTHS)
    months = []
    for slot in base["months"]:
        m = slot["month"]
        look, jobs = "", []
        if pheno is not None:
            p = pheno["months"][m - 1]
            before = base["months"][m - 2]
            look = _look(slot, before, p, who.get(m, []))
            seen: set = set()
            for t in p["tasks"]:
                if t["status"] == "harvest":
                    continue
                words = f"{t['verb'].capitalize()} {t['name']}"
                if words not in seen:
                    seen.add(words)
                    jobs.append(words)
            # The first year's care is the printed care plan's (the owner:
            # "no one will read all that"); the month keeps its own jobs.
            jobs = jobs[:JOBS]
        months.append({
            "month": m, "name": MONTHS[m - 1],
            "flowering": slot["pollinators"], "fruit": slot["birds"],
            "harvest": slot["people"],
            "gap": bool(ids) and m in growing and not slot["pollinators"],
            "visitors": who.get(m, []), "look": look, "jobs": jobs,
        })
    return {"months": months, "near": records is not None,
            "gaps": [x["month"] for x in months if x["gap"]]}


WINTER_LOOK = "Leave the stems standing: they shelter insects all winter."


def _look(slot: dict, before: dict, pheno: dict, who: list) -> str:
    """One thing to go outside and see this month (P11): the first flowers
    of a plant that starts this month, else its first fruit, else who comes
    to a plant in flower, else the first green, else the standing stems."""
    new = [n for n in slot["pollinators"] if n not in before["pollinators"]]
    if new:
        return f"First flowers on the {new[0]}: note the date."
    fruit = [n for n in slot["birds"] if n not in before["birds"]]
    if fruit:
        return f"First fruit on the {fruit[0]}: who finds it?"
    at_flowers = [v for v in who if v["kind"] in ("nectar", "pollen")
                  and v["plant"] in slot["pollinators"]]
    if at_flowers:
        return f"Watch who visits the {at_flowers[0]['plant']}."
    if pheno.get("waking"):
        return f"First green on the {pheno['waking'][0]}: note the date."
    if slot["pollinators"]:
        return f"See what is still in flower."
    return WINTER_LOOK


# ── Caterpillars to birds ───────────────────────────────────────────────────

CATERPILLAR_WHY = ("Most garden birds raise their young on caterpillars, not "
                   "on berries or seed: a nest of chickadees takes 6,000 to "
                   "9,000.")
CATERPILLAR_SOURCE = "Tallamy & Shropshire 2009; Narango, Tallamy & Shropshire 2020"


def caterpillars(placed_plants, **inject) -> dict:
    """``{status, headline, line, plants}``: whether the design's plants could
    grow enough caterpillars to raise a nest of chickadees, in plain words.
    ``status`` is ``chickadee_scenario``'s (none, short, partway, clears)."""
    from src.chickadee_scenario import _KEYSTONE_SUGGESTIONS, chickadee_provision
    r = chickadee_provision(list(placed_plants or []), **inject)
    names = [h["common_name"] for h in r["host_plants"][:3]]
    tops = (names[0] if len(names) == 1 else
            ", ".join(names[:-1]) + " and " + names[-1] if names else "")
    status = r["status"]
    more = (f"{_KEYSTONE_SUGGESTIONS[0].upper()}{_KEYSTONE_SUGGESTIONS[1:]} "
            f"feed the most.")
    if status == "clears":
        headline = "Enough caterpillars for a nest of chickadees."
        text = f"Mostly on your {tops}."
    elif status == "partway":
        headline = "About enough caterpillars for a nest of chickadees."
        text = f"Mostly on your {tops}. {more}"
    elif status == "short":
        headline = "Not yet enough caterpillars for a nest of chickadees."
        text = more
    else:
        headline = "No caterpillars recorded on these plants yet."
        text = more
    return {"status": status, "headline": headline, "line": text,
            "plants": names}


# ── Animals that depend on a few plants ─────────────────────────────────────

def _depends_words(kind: str, taxon: str) -> str:
    if kind == "larval_host":
        return ("its caterpillars depend on a few plants"
                if taxon == "lepidoptera" else
                "its young depend on a few plants")
    if kind == "pollen":
        return "it gathers pollen from only a few plants"
    if kind == "seed_food":
        return "it depends on the seed of a few plants"
    if kind == "nesting":
        return "it nests in only a few plants"
    return "it depends on a few plants"


def depends(plant_ids: Iterable[int], *, records=None, missing: int = 2,
            connect: Optional[Callable] = None) -> dict:
    """``{"served": [row], "missing": [row]}``, each row ``{name, taxon,
    fauna_id, words, plants: [names], line}``: the animals recorded as
    depending on a few plants that this yard has one of, and, up to
    ``missing``, ones it has none of, recorded near the yard, with the plants
    that would serve them. From the documented specialist records only."""
    from src.fauna_fit import DRAWN
    present = {int(p) for p in plant_ids}
    conn = feeds._connect(connect)
    try:
        rows = conn.execute(
            "SELECT pf.plant_id, pf.relationship, p.common_name AS plant, "
            "f.id AS fauna_id, f.common_name, f.scientific_name, f.taxon "
            "FROM plant_fauna pf JOIN plants p ON p.id = pf.plant_id "
            "JOIN fauna f ON f.id = pf.fauna_id "
            "WHERE pf.specificity = 'specialist'").fetchall()
    finally:
        conn.close()
    by_animal: dict = {}
    for r in rows:
        a = by_animal.setdefault(r["fauna_id"], {
            "fauna_id": r["fauna_id"], "name": r["common_name"],
            "common_name": r["common_name"],
            "scientific_name": r["scientific_name"], "taxon": r["taxon"],
            "kind": r["relationship"], "here": [], "other": []})
        (a["here"] if r["plant_id"] in present else a["other"]).append(
            r["plant"])
    served, wanting = [], []
    for a in by_animal.values():
        if not one_species(a):
            continue
        if records is not None and records.band(a["scientific_name"]) not in DRAWN:
            continue
        words = _depends_words(a["kind"], a["taxon"])
        row = {"name": a["name"], "taxon": a["taxon"],
               "fauna_id": a["fauna_id"], "words": words,
               "familiar": _familiar(records, a)}
        if a["here"]:
            here = sorted(set(a["here"]))
            row["plants"] = here
            row["line"] = f"{a['name']} ({', '.join(here)})"
            served.append(row)
        else:
            others = sorted(set(a["other"]))
            row["plants"] = others
            row["line"] = f"{a['name']} ({_or(others[:2])})"
            wanting.append(row)

    def order(r):
        return (not r["familiar"], r["name"].lower())
    served.sort(key=order)
    wanting.sort(key=order)
    return {"served": served, "missing": wanting[:missing]}


def _or(names: list) -> str:
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " or " + names[-1]
