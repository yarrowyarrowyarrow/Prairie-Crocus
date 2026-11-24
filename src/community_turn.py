"""
community_turn.py — turning a community before it is placed (V3.59).

Design principle P2 — see docs/DESIGN_PHILOSOPHY.md.

The owner: "I'd like to be able to rotate the communities after (or before?)
placing them". A community came down one way only: its trees to the north of
its drifts, or a hedge running east to west, whatever the yard's own lines.

**Before placing**: while a community follows the cursor, *Turn 45°* on the
bar over the map (and **R** while the map has focus) turns it 45° clockwise,
the preview with it, and it stays turned for the next click. **After
placing**: a right-click on any of its plants turns it either way about its
own centre (``html/map/11b-turn.js``), sent to Python as the group move a drag
is, so one undo step.

:func:`turned` is the arithmetic, Qt-free; the rest is wiring.
"""

from __future__ import annotations

import math

#: One press, in degrees clockwise as the map is seen (north up).
STEP = 45


def turned(members: list, degrees: float) -> list:
    """``members`` (dicts with ``offset_x`` east and ``offset_y`` north, in
    metres from the community's centre) turned ``degrees`` clockwise; new
    dicts, everything else on them kept."""
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    out = []
    for m in members or []:
        x = float(m.get("offset_x") or 0.0)
        y = float(m.get("offset_y") or 0.0)
        out.append({**m, "offset_x": round(x * c + y * s, 3),
                    "offset_y": round(-x * s + y * c, 3)})
    return out


def turn_pending(main, degrees: float = STEP) -> bool:
    """Turn the community following the cursor, if one is. Returns whether
    one was turned."""
    if getattr(main, "_current_mode", "") != "polyculture":
        return False
    pending = getattr(main, "_pending_polyculture", None)
    if not pending or not pending.get("members"):
        return False
    pending = {**pending, "members": turned(pending["members"], degrees),
               "turned": (float(pending.get("turned") or 0) + degrees) % 360}
    main._pending_polyculture = pending
    from src.placement_footprint import community_footprint    # noqa: PLC0415
    main.map_widget.set_polyculture_mode(community_footprint(pending))
    turns = int(round(pending["turned"])) % 360
    main.statusBar().showMessage(
        f"Turned {turns}° from how it was made" if turns
        else "Back the way it was made", 2000)
    return True


def install(main) -> None:
    """The bar's *Turn 45°* button, on the communities page, for a single
    placement (a row or grid of communities keeps them as made)."""
    from PyQt6.QtWidgets import QPushButton                     # noqa: PLC0415
    button = QPushButton("Turn 45°")
    button.setObjectName("communityTurn")
    button.setAccessibleName("Turn the community 45 degrees clockwise")
    button.setToolTip("Turn the community you are placing 45° clockwise "
                      "(R on the map). A placed one: right-click it.")
    button.clicked.connect(lambda: turn_pending(main))
    main.polyculture_panel.placement_widget.add_extra(button, ("single",))
    main.community_turn_button = button
