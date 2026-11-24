"""How a grass, sedge or rush is drawn once its blades and seed head are read
(F268, V3.51).

Design principle P5 — see docs/DESIGN_PHILOSOPHY.md

Read against photographs in V3.48, the region's 50 grasses, sedges, rushes and
grass-like water plants were the lowest-scored group left: a mean of 3 out of
10, and 43 of them faulted for the seed head. Every one was the same baked
tuft of wide dark straps with a small pale billboard on top, so a blue grama's
eyelash combs, a needle-and-thread's silver awns, a cotton-grass's white tufts
and a water sedge's dark fingers were all one tan block, and a wire rush, which
has no flat leaves at all, was a fan of straps. A grass is known by its head,
and by how its blades are held; neither was drawn.

A plant whose blades and head were **read** (``leaf_data_source`` is ``photo``,
``flora`` or ``measured``, with the schema-v101 numbers) is now drawn from
them by ``html/scene3d/03f-tufts.js``: its blades at their length and width,
held as the photograph shows (upright, arching, drooping, flat on the ground,
or none at all), its flowering stems, and its head by its form
(``inflorescence_form``) at its recorded size, in its colour, held as it is
held. One that is not read keeps the baked tuft (P9).

**Decided once, here** (called from ``scene_contract.build_scene``), as a
``drawn`` block with body ``tuft``, as the herbs', shrubs' and trees' are. Two
forms:

* ``bunch`` — blades and stems from one crown (``tussock``, ``emergent``);
* ``sod`` — separate shoots spread over the ground the plant covers, from
  creeping roots (``colony``: a wire rush's rows, western wheatgrass's open
  patches, a spikerush's stand).

**When the heads stand** is decided here too, from the bloom period: from its
first month, coloured as read while it flowers, ripening toward straw after,
and held through the winter on the dry stems, except a cotton-grass's cotton,
a bur-reed's burs and a sweet flag's spike, which do not stand the winter
(``SHED``).
"""

from __future__ import annotations

from typing import Optional

BODY = "tuft"

#: The forms the viewer builds (``03f-tufts.js`` ``TUFT_FORMS``; a test holds
#: the two equal).
FORMS = ("bunch", "sod")

#: Recorded habit -> form.
FORM_OF = {"tussock": "bunch", "emergent": "bunch", "grassy": "bunch",
           "colony": "sod"}

#: ``leaf_data_source`` values that mean somebody read the numbers.
READ = ("photo", "flora", "measured")

#: Grass-like plants of any type. A water plant is one when its leaves are
#: narrow and it has a head form recorded (cattail, bulrush, bur-reed, sweet
#: flag); a horsetail (``jointed``) keeps its own builder.
GRAMINOIDS = ("grass", "sedge", "rush")
_NARROW = ("linear", "scale", "awl", "")

#: Head forms the viewer draws (``03f-tufts.js`` ``HEAD_FORMS``).
HEADS = ("turkey_foot", "open_panicle", "contracted_spike", "nodding_raceme",
         "one_sided_raceme", "bristly", "sedge_cluster", "rush_umbel",
         "cattail_spike", "cotton", "bur", "spadix")

#: Heads that do not stand the winter: the cotton blows away, the burs and
#: the spike break up in autumn. Every other head is held on the dry stems.
SHED = ("cotton", "bur", "spadix")

#: Months the head is in flower then ripening, before it is straw: a drawing
#: choice, stated (P9). Nothing records how long a head stays green.
RIPEN_MONTHS = 2

#: Flowering stems on a plant with none counted, by form. A drawing choice.
DEFAULT_STEMS = {"bunch": 12, "sod": 18}


def is_read(plant: dict) -> bool:
    return (plant.get("leaf_data_source") or "").strip().lower() in READ


def is_graminoid(plant: dict) -> bool:
    """Grass-like: a grass, sedge or rush, or a narrow-leaved water plant with
    a head form; never a horsetail."""
    form = (plant.get("growth_form") or "").lower()
    if form == "jointed":
        return False
    ptype = (plant.get("plant_type") or "").lower()
    if ptype in GRAMINOIDS:
        return True
    return (ptype == "aquatic"
            and (plant.get("leaf_shape") or "").lower() in _NARROW
            and bool(plant.get("inflorescence_form")))


def form_for(plant: dict) -> Optional[str]:
    """The form ``plant`` is drawn in, or None when it keeps the baked tuft:
    not grass-like, not read, or a head or blade habit not recorded."""
    if not is_graminoid(plant) or not is_read(plant):
        return None
    if (plant.get("inflorescence_form") or "") not in HEADS:
        return None
    if not plant.get("blade_habit") or not float(plant.get("head_length_cm") or 0):
        return None
    if plant.get("blade_habit") != "none" and not float(plant.get("leaf_size_cm") or 0):
        return None
    habit = (plant.get("growth_form") or "").lower()
    # A leafless emergent (three-square) stands in water in spreading stands.
    # Its habit stays `emergent`, which is what tells the planner it needs
    # standing water (zoning.needs_standing_water).
    if habit == "emergent" and plant.get("blade_habit") == "none":
        return "sod"
    return FORM_OF.get(habit)


def _months(plant: dict):
    """(first, last) bloom month: the scene's window (``bloom_start``,
    ``bloom_end``), else the catalogue's period, else June to July."""
    lo, hi = int(plant.get("bloom_start") or 0), int(plant.get("bloom_end") or 0)
    if lo:
        return lo, hi or lo
    from src.habitat_score import parse_month_range       # noqa: PLC0415
    got = parse_month_range(plant.get("bloom_period") or "")
    return (got[0], got[-1]) if got else (6, 7)


def drawn_block(plant: dict, form: str) -> dict:
    """The ``drawn`` block for one plant. All but the size are the species'
    own, so the viewer builds one body a species and places it per plant."""
    h = float(plant.get("height_m") or 0.0)
    c = float(plant.get("canopy_m") or 0.0)
    head = plant.get("inflorescence_form") or ""
    first, last = _months(plant)
    leafless = plant.get("blade_habit") == "none"
    width_cm = float(plant.get("head_width_cm") or 0) or float(plant["head_length_cm"]) * 0.2
    return {
        "body": BODY, "form": form,
        "x": plant.get("x"), "y": plant.get("y"),
        "height_m": round(h, 3), "canopy_m": round(c, 3),
        "mature_h": round(float(plant.get("mature_height_m") or h), 3),
        "mature_w": round(float(plant.get("mature_canopy_m") or c), 3),
        "stems": int(plant.get("flowering_stems") or 0) or DEFAULT_STEMS[form],
        "blade_m": 0.0 if leafless else round(float(plant["leaf_size_cm"]) / 100.0, 4),
        "blade_w": 0.0 if leafless else round(
            float(plant.get("blade_width_mm") or 3.0) / 1000.0, 5),
        "blades": plant.get("blade_habit"),
        "head": head,
        "head_m": round(float(plant["head_length_cm"]) / 100.0, 4),
        "head_w": round(width_cm / 100.0, 4),
        "heads": int(plant.get("head_count") or 1),
        "attitude": plant.get("head_attitude") or "erect",
        "head_color": plant.get("head_color") or plant.get("flower_color") or "#b8a070",
        # When the heads stand: from `head_from`, as read until `ripe`, then
        # ripening, and held through the winter unless `holds` is false.
        "head_from": first, "ripe": min(12, last + RIPEN_MONTHS),
        "holds": head not in SHED,
    }


def apply_grass_habits(plants: list) -> None:
    """Write each read graminoid's ``drawn`` block, in place. A plant that
    already has one is left alone."""
    for p in plants:
        if p.get("drawn"):
            continue
        form = form_for(p)
        if form is not None:
            p["drawn"] = drawn_block(p, form)
