"""How a wildflower is drawn once somebody has read its leaves (F268, V3.48).

Design principle P5 — see docs/DESIGN_PHILOSOPHY.md

Until V3.48 every wildflower, herb and groundcover was one of seven baked
figures (erect, clump, rosette, ferny, grassy, mat, fern) in one of three leaf
sizes, stretched to the plant's height and width. Read against photographs of
the region's natives, 112 plants had leaves the wrong size, 87 the wrong
outline and 44 the wrong kind of body: a 1 cm pussytoes leaf and a 12 cm
coltsfoot leaf were the same plate, and a carpet of single stems was a mound.
Three sizes cannot span leaves from 5 mm to 30 cm, and a figure shared by
forty species cannot be any one of them.

A plant whose leaf and habit numbers were **read** (``leaf_data_source`` is
``photo``, ``flora`` or ``measured``) is now drawn from those numbers, at their
size: its own leaf length and outline, its own arrangement, its own count of
stems, by ``html/scene3d/03c-leafy.js``. A plant whose numbers are still the
seeder's genus estimate keeps the baked figure, because drawing a guess at
life size would state it as a measurement (P9).

**Decided once, here** (called from ``scene_contract.build_scene``), as a
``drawn`` block, as the vines (V2.89), the pond (V2.90) and the succulents
(V2.93) are. The block carries what is recorded, in metres, and the form:

* ``stems`` — leafy stems from one crown (``erect``, ``clump``, ``ferny``);
* ``colony`` — separate upright shoots spread over the ground the plant
  covers (``colony``: bunchberry, wild lily-of-the-valley);
* ``rosette`` — leaves at the ground under bare flower stalks;
* ``tuft`` — narrow basal leaves standing up, with bare stalks (``grassy``);
* ``mat`` — leafy shoots lying on the ground, or a carpet of small rosettes
  where the leaves are recorded basal (``mat``, ``cushion``, ``sprawling``).

How many leaves sit on a stem, how far apart, and how they are held is not
recorded for any plant; the viewer chunk derives them from the leaf's length
and arrangement and says so.
"""

from __future__ import annotations

from typing import Optional

BODY = "leafy"

#: The forms the viewer builds (``03c-leafy.js`` ``LEAFY_FORMS``; a test holds
#: the two equal). ``umbrella`` and ``fronds`` since V3.67b (``03h-leafyforms.js``):
#: a colony of shoots that are each one divided leaf (wild sarsaparilla), and a
#: fern's crown of fronds.
FORMS = ("stems", "colony", "rosette", "tuft", "mat", "umbrella", "fronds")

#: ``leaf_data_source`` values that mean somebody read the leaf and habit
#: numbers, where ``estimated`` (or nothing) means the seeder's genus default.
READ = ("photo", "flora", "measured")

#: The plant types these bodies are for. Grasses, sedges and rushes keep their
#: tufts. A fern whose fronds were read is drawn from them (V3.67b); until then
#: it was the baked fern, a bundle of stalks with a few blades on them. So is a
#: water plant whose habit is a herb's (water parsnip), where src/pond_habit.py
#: defers to this; one floating, submerged or emergent keeps the pond's body.
TYPES = ("wildflower", "herb", "groundcover", "fern", "aquatic")

#: Recorded habit -> form. A habit not listed (tussock, emergent, floating,
#: vining, jointed, pads...) is another module's or the baked figure's.
FORM_OF = {"erect": "stems", "clump": "stems", "ferny": "stems",
           "colony": "colony", "rosette": "rosette", "grassy": "tuft",
           "mat": "mat", "cushion": "mat", "sprawling": "mat", "fern": "fronds"}

#: Leaves that make a one-leaf shoot an umbrella: its divisions spread level at
#: the top of the leaf stalk (V3.67b). A bunchberry's one whorl and a Canada
#: anemone's one leaf keep the colony form.
UMBRELLA_LEAVES = ("ternate",)

#: A water plant's habits that are a herb's (src/pond_habit.py draws the rest).
AQUATIC_HERB_FORMS = ("erect", "clump", "rosette", "ferny", "mat", "cushion")

#: Fronds in a fern's crown, which nothing records: an estimate read off the
#: ostrich fern's photographs, five to nine sterile fronds a crown.
FRONDS = 7

#: Flower clusters one stem carries, by how it forks. ``flowering_stems``
#: counts the clusters on a grown plant (schema v54); the stems are that
#: divided by this. The forks are the viewer's (``03c-leafy.js`` ``FORKS``):
#: the stem's own tip, plus three side branches near the top, or seven from
#: low down.
TIPS_PER_STEM = {"unbranched": 1, "branched_above": 4,
                 "branched_throughout": 8}

#: Clusters on a plant with no count recorded. A drawing choice.
DEFAULT_TIPS = 6


def is_read(plant: dict) -> bool:
    """Were this plant's leaf and habit numbers read, not estimated?"""
    return (plant.get("leaf_data_source") or "").strip().lower() in READ


def form_for(plant: dict) -> Optional[str]:
    """The form ``plant`` is drawn in, or None when it keeps the body it had:
    not a wildflower, herb or groundcover; numbers not read; no leaf length
    or outline recorded; or a habit these forms do not draw."""
    if (plant.get("plant_type") or "").lower() not in TYPES:
        return None
    if not is_read(plant):
        return None
    if not plant.get("leaf_shape") or not float(plant.get("leaf_size_cm") or 0):
        return None
    # A water plant only where its habit is a herb's (water parsnip), never a
    # grass-like one drawn from its blades and head (src/grass_habit.py: a
    # cattail, a bulrush) or one the pond draws (src/pond_habit.py).
    if (plant.get("plant_type") or "").lower() == "aquatic":
        from src import grass_habit                       # noqa: PLC0415
        if (grass_habit.form_for(plant) or (plant.get("growth_form") or "").lower()
                not in AQUATIC_HERB_FORMS):
            return None
    # A woody mat (creeping juniper: branching prostrate, its stems counted) is
    # drawn as the shrub it is, by src/shrub_habit.py (V3.67b).
    if ((plant.get("branching") or "").lower() == "prostrate"
            and int(plant.get("woody_stems") or 0)):
        return None
    form = FORM_OF.get((plant.get("growth_form") or "").lower())
    if (form == "colony" and int(plant.get("stem_leaf_nodes") or 0) == 1
            and (plant.get("leaf_shape") or "").lower() in UMBRELLA_LEAVES):
        return "umbrella"
    return form


def stems_for(plant: dict, form: str) -> int:
    """Stems on the grown plant: the recorded clusters over the tips one stem
    carries. A rosette's, a tuft's and a mat's stalks carry one cluster each."""
    if form == "fronds":
        return FRONDS
    tips = int(plant.get("flowering_stems") or 0) or DEFAULT_TIPS
    per = 1
    if form in ("stems", "colony"):
        per = TIPS_PER_STEM.get((plant.get("stem_branching") or "").lower(), 1)
    return max(1, round(tips / per))


def drawn_block(plant: dict, form: str) -> dict:
    """The ``drawn`` block for one plant. Everything but the height and the
    width is the species' own, the same for every plant of it, so the viewer
    builds one body a species and places it for each plant."""
    h = float(plant.get("height_m") or 0.0)
    c = float(plant.get("canopy_m") or 0.0)
    arrangement = (plant.get("leaf_arrangement") or "").lower()
    return {
        "body": BODY, "form": form,
        # The recorded habit itself: how far a clump's outer stems lean.
        "habit": (plant.get("growth_form") or "").lower(),
        "x": plant.get("x"), "y": plant.get("y"),
        "height_m": round(h, 3), "canopy_m": round(c, 3),
        # The grown plant's size: the body is built at it and scaled to this
        # year's, so a young plant's leaves are a young plant's.
        "mature_h": round(float(plant.get("mature_height_m") or h), 3),
        "mature_w": round(float(plant.get("mature_canopy_m") or c), 3),
        "stems": stems_for(plant, form),
        # Leaves (or pairs, or whorls) up one stem, where somebody counted;
        # 0 leaves it to the viewer's spacing estimate.
        "nodes": int(plant.get("stem_leaf_nodes") or 0),
        "leaf_m": round(float(plant["leaf_size_cm"]) / 100.0, 4),
        "leaf_shape": (plant.get("leaf_shape") or "").lower(),
        "arrangement": arrangement,
        "branching": (plant.get("stem_branching") or "").lower(),
        # Leaves at the ground as well as on the stems. A rosette, a tuft and
        # a carpet of rosettes are nothing else.
        "basal": bool(plant.get("basal_rosette")) or arrangement == "basal"
                 or form in ("rosette", "tuft"),
        # A narrow leaf measured across (V3.67b): wild chives' 3 mm tubes,
        # where the linear outline's ratio drew a 1.5 cm strap. 0: not measured.
        "blade_m": round(float(plant.get("blade_width_mm") or 0) / 1000.0, 4),
    }


def apply_herb_habits(plants: list) -> None:
    """Write each read wildflower's ``drawn`` block, in place. A plant that
    already has one (a vine, a wetland plant, a succulent) is left alone."""
    for p in plants:
        if p.get("drawn"):
            continue
        form = form_for(p)
        if form is not None:
            p["drawn"] = drawn_block(p, form)
