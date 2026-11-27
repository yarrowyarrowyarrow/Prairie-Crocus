"""
src/mulch_rings_flow.py — the window's side of the mulch rings (V3.76).

``src/mulch_rings.py`` says which plants have a ring and how big it is; this
puts that in the window: the placing box on the bar over the map (*A ring of
mulch round each*, remembered between sessions, off until ticked), which sets
the store's ``mulch_new_plants`` so every plant or community a person places
gets one; a plant's right-click menu, which gives or takes away its ring or
its group's as one undo step; and the map's ring layer, drawn again a moment
after any change and after every full redraw.
"""

from __future__ import annotations

from PyQt6.QtCore import QSettings, QTimer
from PyQt6.QtWidgets import QCheckBox

#: The QSettings key for the placing box; off unless ticked (the owner's Q4).
SETTINGS_KEY = "placing/mulch_rings"
#: How long after an edit the rings are drawn again, ms: a community of eight
#: placed in one go is one redraw.
DELAY_MS = 120


def placing_on(settings: QSettings = None) -> bool:
    s = settings if settings is not None else QSettings()
    return bool(s.value(SETTINGS_KEY, False, type=bool))


def install(main) -> QCheckBox:
    """The placing box on the bar over the map, its state restored and handed
    to the store."""
    from src.project_store import store_for
    box = QCheckBox("A ring of mulch round each")
    box.setAccessibleName("A ring of mulch round each plant placed")
    box.setToolTip("Plants you place get a ring of wood chips round them, "
                   "drawn on the map and in 3D and counted in the mulch to "
                   "buy. Off until ticked.")
    on = placing_on()
    box.setChecked(on)
    store_for(main).mulch_new_plants = on

    def _toggled(state: bool) -> None:
        QSettings().setValue(SETTINGS_KEY, bool(state))
        store_for(main).mulch_new_plants = bool(state)

    box.toggled.connect(_toggled)
    bar = getattr(main, "placement_bar", None)
    if bar is not None and hasattr(bar, "add_shared"):
        bar.add_shared(box)
    main.mulch_box = box
    return box


def request(main) -> None:
    """Draw the rings again once the edits pause."""
    timer = getattr(main, "_mulch_timer", None)
    if timer is None:
        timer = QTimer(main)
        timer.setSingleShot(True)
        timer.setInterval(DELAY_MS)
        timer.timeout.connect(lambda: send(main))
        main._mulch_timer = timer
    timer.start()


def send(main) -> None:
    """Hand the map every ring (``mulch_rings.rings``). From a timer, so
    nothing may escape."""
    try:
        from src import mulch_rings
        main.map_widget.set_mulch_rings(mulch_rings.rings(main._project))
    except Exception:                                      # noqa: BLE001
        pass


def toggle(main, plant_id, lat: float, lng: float, group_id: str,
           on: bool) -> int:
    """A plant's right-click menu: give the plant (or every plant of its
    group) a ring, or take it away. One undo step. Returns how many
    changed."""
    from src.project_store import store_for
    store = store_for(main)
    if group_id:
        keys = [(p["plant_id"], p["lat"], p["lng"])
                for p in store.placed_plants
                if p.get("placement_group_id") == group_id]
    else:
        keys = [(plant_id, lat, lng)]
    with main._persistence.checkpoint("mulch rings"):
        changed = store.set_mulch_rings(keys, on)
    if changed:
        main._mark_modified()
        main._sync_planning_panel()
        send(main)
    return changed
