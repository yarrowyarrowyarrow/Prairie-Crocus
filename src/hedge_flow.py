"""
src/hedge_flow.py — the window's side of a hedge you can plant (V3.74).

``src/hedge_planting.py`` decides what goes where; this module puts it in the
window: it plants a line when it is drawn with plants chosen (inside the map
handler's undo step, so the line and its plants are one), plants or replants
a line from its right-click menu or the Overview's offer (*Plant this
hedge…*, one undo step), and takes a line's plants with it when the line is
removed. The choice of plants is a small dialog, which goes through
``_exec`` so tests never wait on it.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QVBoxLayout,
)

from src import hedge_planting, yard_kinds


def _exec(dialog) -> int:
    return dialog.exec()


def _rows(ids) -> list:
    from src.db.plants import get_plant
    out = []
    for pid in ids or []:
        try:
            row = get_plant(int(pid))
        except Exception:                                    # noqa: BLE001
            row = None
        if row:
            out.append(row)
    return out


def _plant(main, feature: dict, ids) -> int:
    """Plant ``feature`` with ``ids`` and show it: the plants' markers, the
    line redrawn as planted, the plant list and the read-outs."""
    import src.project as project_io
    from src.project_store import store_for
    hid = (feature.get("properties") or {}).get("hedge_id") or ""
    had = hedge_planting.plants_of(main._project, hid)
    batch: list = []

    def _drawn(rec):
        pid, name = rec["plant_id"], rec.get("common_name") or ""
        batch.append((pid, name))
        if had:
            return                         # redrawn whole below
        spacing, ptype, colour = main._plant_info(pid)
        main.map_widget.place_plant_marker(
            pid, name, rec["lat"], rec["lng"], spacing_m=spacing,
            plant_type=ptype, color=colour, group_id=hid)

    added = hedge_planting.plant(main._project, feature, _rows(ids),
                                 store=store_for(main), on_added=_drawn)
    if had:
        main._persistence.redraw()         # the old plants' markers go
        main.plant_panel.on_plants_removed_batch(
            [f["properties"].get("plant_id") for f in had])
    else:
        line = project_io.feature_to_hedgerow(feature, plants=len(added))
        if line:
            main.map_widget.load_hedgerow(line)
    if batch:
        main.plant_panel.on_plants_placed_batch(batch)
    main._mark_modified()
    main._sync_planning_panel()
    return len(added)


def plant_new_line(main, feature: dict) -> int:
    """A line just drawn: planted with what the palette chose, if it is a
    hedge, a living fence or a windbreak. Called inside the map handler's
    undo step."""
    ids = (feature.get("properties") or {}).get("plant_ids") or []
    if not ids or not yard_kinds.is_living_line(feature):
        return 0
    return _plant(main, feature, ids)


def plant_line(main, hedge_id: str, ids) -> int:
    """Plant (or replant) the line ``hedge_id`` with ``ids``: one undo
    step. Returns the number planted."""
    feature = hedge_planting.line_by_id(main._project, hedge_id)
    if feature is None or not ids:
        return 0
    with main._persistence.checkpoint("plant a hedge"):
        n = _plant(main, feature, ids)
    k = yard_kinds.kind_of(feature)
    main.statusBar().showMessage(
        f"Planted {n} along the {(k.words if k else 'hedge').lower()}", 3000)
    return n


def remove_line(main, hedge_id: str) -> int:
    """Take the line and its plants out (inside the map handler's undo
    step). Returns the number of plants removed."""
    from src.project_store import store_for
    removed = hedge_planting.remove(main._project, hedge_id,
                                    store=store_for(main))
    if removed:
        main._persistence.redraw()
        main.plant_panel.on_plants_removed_batch(
            [r.get("plant_id") for r in removed])
        main._sync_planning_panel()
    return len(removed)


# ── Plant this hedge… ───────────────────────────────────────────────────────

class HedgeDialog(QDialog):
    """The plants a line is planted with, one list a role, chosen first as
    :func:`hedge_planting.offer_choices` says."""

    def __init__(self, parent, feature: dict):
        super().__init__(parent)
        k = yard_kinds.kind_of(feature) or yard_kinds.BY_KEY["hedge"]
        self.kind = k
        self.setWindowTitle(f"Plant this {k.words.lower()}")
        self.choice: list = []
        first = hedge_planting.offer_choices(feature)
        layout = QVBoxLayout(self)
        words = ((feature.get("properties") or {}).get("species") or "").strip()
        about = k.about
        if words:
            about += f" It was written down as “{words}”."
        note = QLabel(about)
        note.setWordWrap(True)
        layout.addWidget(note)
        form = QFormLayout()
        self.lists: dict = {}
        for o in k.options:
            if not o.plants:
                continue
            box = QComboBox()
            box.setAccessibleName(o.words)
            if o.optional:
                box.addItem("None", None)
            for pid, name in hedge_planting.choices(o.plants):
                box.addItem(name, pid)
            box.setCurrentIndex(max(0, box.findData(first.get(o.key))))
            self.lists[o.key] = box
            form.addRow(o.words + ":", box)
        layout.addLayout(form)
        buttons = QDialogButtonBox()
        plant = buttons.addButton("Plant it",
                                  QDialogButtonBox.ButtonRole.AcceptRole)
        plant.setDefault(True)
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def options(self) -> dict:
        return {key: box.currentData() for key, box in self.lists.items()}

    def _accept(self) -> None:
        self.choice = hedge_planting.chosen_ids(self.kind.key, self.options())
        self.accept()


def offer(main, hedge_id: str) -> int:
    """*Plant this hedge…*: ask which plants, then plant them (one undo
    step). Never plants without the person's answer (the owner's Q5).
    Returns the number planted."""
    feature = hedge_planting.line_by_id(main._project, hedge_id)
    if feature is None:
        return 0
    from PyQt6.QtWidgets import QWidget
    dialog = HedgeDialog(main if isinstance(main, QWidget) else None, feature)
    _exec(dialog)
    if not dialog.choice:
        return 0
    return plant_line(main, hedge_id, dialog.choice)
