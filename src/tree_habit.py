"""How a tree is drawn once somebody has read its crown off its photographs
(F268, V3.50).

Design principle P5 — see docs/DESIGN_PHILOSOPHY.md

Until V3.50 every tree was one of a few baked crowns per genus: a trunk and a
handful of leaf clumps. Read against photographs of the region's ten native
trees, all ten had the wrong crown: the aspen a very long pole with a dozen
clumps near the top, the paper birch a white pole with four leaders, the
tamarack solid flat plates, the jack pine a narrow bottle brush, the balsam
poplar a narrow tuft on a square post. A crown is what a tree looks like from
a yard, and the catalogue said nothing about one.

A tree whose crown was **read** (``leaf_data_source`` is ``photo``, ``flora``
or ``measured``, with ``crown_shape``, ``crown_clear``, ``limb_habit`` and the
trunk count in ``woody_stems``) is drawn from those numbers by
``html/scene3d/03e-crowns.js``: as many trunks as it has, bare as high as was
read, limbs going the way they go to the outline that was read, ending in
leafy (or needled) shoots cut to the species' own outline. A tree still on the
seeder's estimate keeps the baked crown (P9).

**Decided once, here** (called from ``scene_contract.build_scene``), as a
``drawn`` block with body ``crown``, as the shrubs' (V3.49) are. Two things are
decided here rather than in the viewer because they are botany, not drawing:

* how a conifer's needles are carried (``spray``): along every side of the
  twig in flat fronds (a spruce, ``alternate``), in long bundles at the twig
  ends (a pine, ``fascicled`` 3 cm and over), or in soft rosettes on short
  spur shoots along the twig (a tamarack, ``fascicled`` under 3 cm);
* whether its catkins hang (``catkins_hang``): those of the poplars, the
  aspen, the birches, the alders and the hazel do, a willow's stand. A family
  character, stated here, not read off each photograph.

A read **vine** keeps the body ``vine_habit`` gives it (climbing what it
touches) and is drawn with its own leaf sprays and flowers by
``html/scene3d/22-vines.js`` once its leaves are read; ``form_for`` answers
``vine`` for one, so the reading tool can count it.
"""

from __future__ import annotations

from typing import Optional

from src.herb_habit import is_read

BODY = "crown"

#: The plant types the reading tool's ``trees`` group reads.
TYPES = ("tree", "vine")

#: Crown outlines and limb habits the viewer builds (``03e-crowns.js``
#: ``CROWN_SHAPES`` / ``LIMB_HABITS``; a test holds them equal, and
#: ``data_quality`` holds the vocabulary).
SHAPES = ("conical", "spire", "oval", "rounded", "irregular")
LIMBS = ("ascending", "spreading", "drooping")

#: How a conifer's needles are carried, and the viewer's word for a leafy shoot.
SPRAYS = ("leaf", "frond", "tuft", "rosette")

#: A pine's needles are 3 cm and more; a tamarack's 2 to 3.
LONG_NEEDLE_CM = 3.0

#: Genera whose catkins hang (Salicaceae's poplars, Betulaceae).
HANGING_CATKINS = ("populus", "betula", "alnus", "corylus")


def _genus(plant: dict) -> str:
    return (plant.get("scientific_name") or plant.get("genus") or "").split(" ")[0].lower()


def form_for(plant: dict) -> Optional[str]:
    """The crown ``plant`` is drawn with (its outline), ``"vine"`` for a read
    vine, or None when it keeps the body it had."""
    kind = (plant.get("plant_type") or "").lower()
    if not is_read(plant) or not plant.get("leaf_shape") \
            or not float(plant.get("leaf_size_cm") or 0):
        return None
    if kind == "vine":
        return "vine"
    if kind != "tree":
        return None
    shape = (plant.get("crown_shape") or "").lower()
    if shape not in SHAPES or (plant.get("limb_habit") or "").lower() not in LIMBS:
        return None
    if plant.get("crown_clear") in (None, "") or not int(plant.get("woody_stems") or 0):
        return None
    return shape


def spray_for(plant: dict) -> str:
    """How the tree's foliage is carried on a shoot."""
    if (plant.get("leaf_shape") or "").lower() not in ("needle", "awl", "scale"):
        return "leaf"
    if (plant.get("leaf_arrangement") or "").lower() != "fascicled":
        return "frond"
    return "tuft" if float(plant.get("leaf_size_cm") or 0) >= LONG_NEEDLE_CM else "rosette"


def drawn_block(plant: dict, shape: str) -> dict:
    """The ``drawn`` block for one tree. All but the height and the width is
    the species' own, so the viewer builds one crown a species (and a few
    individuals of it) and places it for each tree."""
    h = float(plant.get("height_m") or 0.0)
    c = float(plant.get("canopy_m") or 0.0)
    return {
        "body": BODY, "form": shape,
        "x": plant.get("x"), "y": plant.get("y"),
        "height_m": round(h, 3), "canopy_m": round(c, 3),
        "mature_h": round(float(plant.get("mature_height_m") or h), 3),
        "mature_w": round(float(plant.get("mature_canopy_m") or c), 3),
        "trunks": int(plant["woody_stems"]),
        "clear": round(float(plant["crown_clear"]), 3),
        "limbs": (plant.get("limb_habit") or "").lower(),
        "leaf_m": round(float(plant["leaf_size_cm"]) / 100.0, 4),
        "leaf_shape": (plant.get("leaf_shape") or "").lower(),
        "arrangement": (plant.get("leaf_arrangement") or "").lower(),
        "spray": spray_for(plant),
        "catkins_hang": _genus(plant) in HANGING_CATKINS,
    }


def apply_tree_habits(plants: list) -> None:
    """Write each read tree's ``drawn`` block, in place. A vine keeps the
    block ``vine_habit`` gave it."""
    for p in plants:
        if p.get("drawn") or (p.get("plant_type") or "").lower() != "tree":
            continue
        shape = form_for(p)
        if shape is not None:
            p["drawn"] = drawn_block(p, shape)
