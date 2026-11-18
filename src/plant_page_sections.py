"""
plant_page_sections.py — what the plant page says (PR-4, V3.26; one page in
both modes since V3.56; docs/homeowner/05-plants-that-lead.md §7).

Design principle P6 — see docs/DESIGN_PHILOSOPHY.md.

The page was three to four screens of nineteen sections, the longest of them
citations (§7.1). V3.26 cut the simple app's to about a hundred words and kept
the long one for the advanced app; the owner, V3.56: still "overwhelming with
data and simply too much", and the details a design needs (when it flowers,
in what colour, how big, what soil) belong on the short page. So there is one
page: the band, why to plant it (naming two or three of the animals, by the
Overview's rule), what to know, how to grow it, its season, how it looks,
buying it and whether it is native here. The animal list and where it grows
wild wait in two folds (``species_page``); the roles, the badges, the photo
numbers and the repeated sentences are gone.

Every word comes from structured fields and the ranking
(``src.plant_priority``); the free-text notes are never shown on the desktop,
in either mode (decision L8, P12). Qt-free: the page draws what this returns.
"""

from __future__ import annotations

from typing import Mapping, Optional

#: The section the season bar goes under: the colours and the form in words,
#: then the months drawn (the long page wrote the months out over the bar).
SEASON = "Looks like"
#: The ID line (WD-8, W3): with Advanced tools on, and in Help › About.
ID_LINE = ("These photos help you choose plants. They are not a guide to "
           "identifying plants in the wild.")

_SUN = {"full sun": "Full sun", "full_sun": "Full sun",
        "part shade": "part shade", "partial shade": "part shade",
        "partial_shade": "part shade", "part_shade": "part shade",
        "full shade": "shade", "full_shade": "shade", "shade": "shade"}
_WATER = {"low": "dry", "medium": "average", "high": "moist"}


def _tokens(value) -> list:
    return [t.strip() for t in str(value or "").replace(";", ",").split(",")
            if t.strip()]


def growing_words(entry: Mapping) -> str:
    """"Full sun to part shade. Dry to average soil." in words."""
    sun = []
    for t in _tokens(entry.get("sun")):
        w = _SUN.get(t.lower())
        if w and w not in sun:
            sun.append(w)
    water = []
    for t in _tokens(entry.get("water")):
        w = _WATER.get(t.lower())
        if w and w not in water:
            water.append(w)
    water.sort(key=["dry", "average", "moist"].index)
    out = []
    if sun:
        s = sun[0] if len(sun) == 1 else f"{sun[0]} to {sun[-1]}"
        out.append(s[:1].upper() + s[1:] + ".")
    if water:
        w = water[0] if len(water) == 1 else f"{water[0]} to {water[-1]}"
        out.append(w[:1].upper() + w[1:] + " soil.")
    return " ".join(out)


def _num(value) -> Optional[float]:
    try:
        v = float(str(value).strip().rstrip("?"))
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


def size_words(entry: Mapping) -> str:
    """"Grows to 5 m tall and 4.5 m wide in about 6 years. Plant 3 m apart."""
    h, w = _num(entry.get("mature_height_m")), _num(entry.get("mature_canopy_m"))
    years = _num(entry.get("years_to_maturity"))
    parts = []
    if h and w:
        parts.append(f"Grows to {h:g} m tall and {w:g} m wide")
    elif h:
        parts.append(f"Grows to {h:g} m tall")
    text = parts[0] if parts else ""
    if text and years:
        text += f" in about {years:g} year{'' if years == 1 else 's'}"
    if text:
        text += "."
    from src.planting_spacing import spacing_words           # noqa: PLC0415
    apart = spacing_words(entry.get("spacing_m"))    # one number (QF-9)
    if apart:
        text = (text + " " if text else "") + f"Plant {apart} apart."
    return text


def buying_words(entry: Mapping, place: str = "") -> str:
    from src import local_stock                              # noqa: PLC0415
    price = ((entry.get("sourcing") or {}).get("price") or "").strip()
    price = price.replace(" (estimate)", "").replace("per plant", "a plant")
    price = (price[:1].upper() + price[1:] + ".") if price else ""
    stock = local_stock.clause(entry.get("scientific_name") or "", place)
    return " ".join(p for p in (price, stock) if p)


def simple(entry: Mapping, row: Optional[Mapping] = None, *,
           place: str = "") -> list:
    """``[(heading, body), …]`` for the page; the page draws the season bar
    under :data:`SEASON`. ``row`` is the catalogue row (read when not given);
    ``place`` the region (the edition's when empty)."""
    from src import native_here, plant_priority, region     # noqa: PLC0415
    if row is None:
        from src.db.plants import get_plant                  # noqa: PLC0415
        row = get_plant(int(entry.get("id") or 0)) or {}
    home = region.regions().get(place) if place else region.default()
    home = home or region.default()
    a = plant_priority.assess(row, place=home.key)
    good = list(a.cautions) + _safety(row)
    if entry.get("edible_parts"):
        good.append("Edible parts: " + ", ".join(_tokens(entry["edible_parts"])))
    # An off-list plant's band is said by the last line instead.
    sections = [(a.band if a.band != plant_priority.AWAY else "", ""),
                ("Why this plant", _sentences(named_reasons(a, home.key))),
                ("Good to know", _sentences(good)),
                ("Growing it", " ".join(p for p in (
                    growing_words(entry), _hardy(row), size_words(entry),
                    _tasks(entry)) if p)),
                (SEASON, " ".join(p for p in (season_words(entry, row),
                                              looks_words(entry, row)) if p)),
                ("Buying it", buying_words(entry, home.key))]
    try:
        native = native_here.native_around(row, home.key)
    except ValueError:
        native = None
    if native is not None:
        sections.append((f"Native around {home.short}." if native else
                         f"Not native around {home.short}.", ""))
    # A heading with nothing under it is dropped, except the band and the
    # native line, which are whole sentences on their own, and the season,
    # whose bar may be all it has.
    lone = {a.band, f"Native around {home.short}.",
            f"Not native around {home.short}."}
    bar = bool(entry.get("bloom_months") or entry.get("fruit_months"))
    return [(h, b) for h, b in sections
            if h and (b or h in lone or (h == SEASON and bar))]


#: How many animals the page names, in all (the owner, V3.56: "2–3").
NAMED = 3


def named_reasons(a, place: str = "", *, names_fn=None) -> list:
    """The ranking's reasons with up to :data:`NAMED` animals named, at most
    two to a reason, in the reasons' order: "Caterpillar food for 4 kinds of
    moth and butterfly, among them Mourning Cloak and Polyphemus Moth". An animal
    is named by the Overview's rule (``through_the_year``): one species with
    an English name, recorded near the place inside a pack, familiar first."""
    if names_fn is None:
        from src.through_the_year import names_for         # noqa: PLC0415
        names_fn = lambda ids: names_for(ids, place)       # noqa: E731
    out, left = [], NAMED
    for reason in a.reasons:
        ids = (getattr(a, "who", None) or {}).get(reason) or set()
        found = names_fn(ids) if ids and left else []
        names = found[:min(2, left)]
        if len(ids) - len(names) == 1 and len(found) > len(names):
            names = found[:len(names) + 1]     # never "and 1 more"
        if names:
            left = max(0, left - len(names))
            listed = " and ".join(names)
            reason = (f"{reason}, among them {listed}"
                      if len(ids) > len(names) else f"{reason}: {listed}")
        out.append(reason)
    return out


def _safety(row: Mapping) -> list:
    """What is recorded about poison and thorns, once (the long page said it
    twice, in two wordings). A high risk is the ranking's caution."""
    low = [who for field, who in (("toxicity_pets", "pets"),
                                  ("toxicity_humans", "people"))
           if (row.get(field) or "").strip() == "low"]
    said = ["Low poison risk to " + " and ".join(low)] if low else []
    if row.get("has_thorns"):
        said.append("Has thorns or prickles")
    if not (row.get("toxicity_pets") or row.get("toxicity_humans")):
        said.append("Not checked for poison")
    return said


def _hardy(row: Mapping) -> str:
    from src.plant_directory import _number                 # noqa: PLC0415
    zone = _number(row.get("hardiness_zone_min"))
    return f"Hardy to zone {zone}." if zone else ""


def season_words(entry: Mapping, row: Mapping) -> str:
    """The colours the season bar cannot show: "White flowers, then purple
    fruit." The months are the bar's."""
    from src.confidence import mark                          # noqa: PLC0415
    bits = []
    label = (entry.get("bloom_colour_label") or "").strip()
    if label:
        flowers = (label if entry.get("bloom_colour") == "straw"
                   else f"{label} flowers")
        if mark(row.get("flower_colour_source")).inferred:
            flowers += " (a guess from its genus)"
        bits.append(flowers[:1].upper() + flowers[1:].lower())
    fruit = (entry.get("fruit_color") or "").strip()
    if fruit and not fruit.startswith("#"):
        bits.append(f"{fruit.lower()} fruit")
    text = ", then ".join(bits)
    return text + "." if text else ""


def _tasks(entry: Mapping) -> str:
    """The calendar's jobs as sentences: "Prune in March. Harvest in July"."""
    from src.month_tasks import page_line                    # noqa: PLC0415
    tasks = page_line(entry.get("calendar") or [],
                      edible=bool(entry.get("edible_parts")))
    return tasks.replace(" · ", ". ") + "." if tasks else ""


def looks_words(entry: Mapping, row: Mapping) -> str:
    from src.confidence import mark                          # noqa: PLC0415
    parts = list(entry.get("morphology") or [])
    if not parts:
        return ""
    text = "; ".join(parts)
    if mark(row.get("leaf_data_source")).inferred:
        text += " (a guess from its genus)"
    return text[:1].upper() + text[1:] + "."


def _sentences(items) -> str:
    return " ".join(i.rstrip(".") + "." for i in items if i)


def word_count(sections) -> int:
    return sum(len(f"{h} {b}".split()) for h, b in sections)
