"""How a shrub is drawn once somebody has read its leaves and counted its stems
(F268, V3.49).

Design principle P5 — see docs/DESIGN_PHILOSOPHY.md

Until V3.49 every shrub was one of eight baked figures (vase, spreading, mound,
thicket, irregular, arching, prostrate, upright) in a few leaf classes: five to
eleven stems as thick as an arm, with leaf cards at their ends. Read against
photographs of the region's 34 native shrubs, 23 had the wrong stems, 16 were
far too sparse and 22 had leaves the wrong size: a saskatoon, which is a
thicket of slender stems leafy to the ground, was a fan of square sticks; a
snowberry was a pile of plates; the common juniper, a dense evergreen mat, was
bare brown spokes. A figure eight species share cannot be any one of them.

A shrub whose leaf, habit and stem numbers were **read** (``leaf_data_source``
is ``photo``, ``flora`` or ``measured``, and ``woody_stems`` is recorded) is
drawn from those numbers by ``html/scene3d/03d-woody.js``: as many stems as it
sends up, as slender as that many stems sharing one crown are, branching to
leafy shoots that carry its own leaf, in its outline and arrangement. A shrub
still on the seeder's estimate keeps the baked figure, because drawing a guess
in a species' own body would state it as a reading (P9).

**Decided once, here** (called from ``scene_contract.build_scene``), as a
``drawn`` block, as the vines (V2.89), the pond (V2.90), the succulents (V2.93)
and the wildflowers (V3.48) are. The form comes from the recorded woody habit:

* ``clump`` — stems from one base, spreading as they rise (``multi_stem``:
  saskatoon, dogwood, the currants, cinquefoil);
* ``thicket`` — separate upright stems spread over the ground the shrub
  covers (``suckering``: the roses, snowberry, sandbar willow, meadowsweet);
* ``arching`` — canes that rise and bow over (``arching``: raspberry,
  gooseberry, the sprawling currants);
* ``mat`` — limbs along the ground with their shoots turned up
  (``prostrate``: common juniper).

A habit not listed (``decurrent``, ``excurrent``, ``rosette``) is a tree's or
another module's, and the shrub keeps the body it had.

**The crown's outline (V3.63)** is read too, in a shrub's own words
(``crown_shape``: ``CROWNS``), with ``crown_clear`` where a big shrub stands on
a short bare trunk (chokecherry, hawthorn). The form says how the stems grow;
the crown says what the whole shrub looks like from across a yard, which is
what tells a saskatoon's vase from a snowberry's rounded bush and a highbush
cranberry's broad spread when the leaves are too small to see. Until V3.63
twenty of the 34 natives were one ``clump`` outline. A shrub with no crown
read keeps its form's outline.

What nothing records is derived in the viewer chunk and said there: how thick
a stem is (from the stem count and the crown they share), where the side
branches leave, and how many leaves a shoot holds. A grown shrub carries tens
of thousands of leaves and no budget draws them all, so each drawn leaf stands
for several and is drawn larger than life by a factor the chunk states.
"""

from __future__ import annotations

from typing import Optional

from src.data_quality import SHRUB_CROWN_SHAPES
from src.herb_habit import is_read

BODY = "woody"

#: The forms the viewer builds (``03d-woody.js`` ``WOODY_FORMS``; a test holds
#: the two equal).
FORMS = ("clump", "thicket", "arching", "mat")

#: The crown outlines the viewer draws (``03d-woody.js`` ``WOODY_CROWNS``; a
#: test holds the two equal). The vocabulary is ``data_quality``'s.
CROWNS = SHRUB_CROWN_SHAPES

#: The plant types this body is for. A tree keeps its crown.
TYPES = ("shrub",)

#: Recorded woody habit (``branching``, schema v47) -> form.
FORM_OF = {"multi_stem": "clump", "suckering": "thicket",
           "arching": "arching", "prostrate": "mat"}


def form_for(plant: dict) -> Optional[str]:
    """The form ``plant`` is drawn in, or None when it keeps the body it had:
    not a shrub; numbers not read; no leaf length, outline or stem count
    recorded; or a habit these forms do not draw."""
    if (plant.get("plant_type") or "").lower() not in TYPES:
        return None
    if not is_read(plant):
        return None
    if not plant.get("leaf_shape") or not float(plant.get("leaf_size_cm") or 0):
        return None
    if not int(plant.get("woody_stems") or 0):
        return None
    return FORM_OF.get((plant.get("branching") or "").lower())


def drawn_block(plant: dict, form: str) -> dict:
    """The ``drawn`` block for one shrub. Everything but the height and the
    width is the species' own, the same for every plant of it, so the viewer
    builds one body a species and places it for each plant."""
    h = float(plant.get("height_m") or 0.0)
    c = float(plant.get("canopy_m") or 0.0)
    crown = (plant.get("crown_shape") or "").lower()
    return {
        "body": BODY, "form": form,
        "x": plant.get("x"), "y": plant.get("y"),
        "height_m": round(h, 3), "canopy_m": round(c, 3),
        # The grown shrub's size: the body is built at it and scaled to this
        # year's, so a young shrub is a small one of the same kind.
        "mature_h": round(float(plant.get("mature_height_m") or h), 3),
        "mature_w": round(float(plant.get("mature_canopy_m") or c), 3),
        "stems": int(plant["woody_stems"]),
        "leaf_m": round(float(plant["leaf_size_cm"]) / 100.0, 4),
        "leaf_shape": (plant.get("leaf_shape") or "").lower(),
        "arrangement": (plant.get("leaf_arrangement") or "").lower(),
        # Its outline, and how much of its height is bare stem below the
        # lowest leafy branch (V3.63). Empty: the form's own outline.
        "crown": crown if crown in CROWNS else "",
        "clear": round(float(plant.get("crown_clear") or 0.0), 3) if crown in CROWNS else 0.0,
    }


def apply_shrub_habits(plants: list) -> None:
    """Write each read shrub's ``drawn`` block, in place. A plant that already
    has one (a succulent recorded as a shrub: the yucca) is left alone."""
    for p in plants:
        if p.get("drawn"):
            continue
        form = form_for(p)
        if form is not None:
            p["drawn"] = drawn_block(p, form)
