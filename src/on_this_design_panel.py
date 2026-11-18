"""
on_this_design_panel.py — what is on the design: the planted lists.

Split out of ``src/plant_panel.py`` in Chunk 4 of the strengthening plan.
Pure structural move: ``OnThisDesignPanel`` is now standalone and lives
beside the plant browser instead of inside it.

Two sub-tabs:
  • Species — species → count (driven by PlantPanel._placed_counts).
  • Communities — community-name → instance count + member count.

**Since V3.07 they sit in the Design tab** (``src/side_panel_layout.py``) as
**Planted**. The third, Stats, was the Design tab's **Report card** from V3.07
and was retired in V3.55 (F270, the owner's answer to the Design tab's review):
the Overview says its cost and signs of care, Habitat its score, and its *Where
to grow next* moved to Habitat as *What would raise it*. Until then all three were under
Plants › On This Design, "the best page in the app, three levels deep, under a
tab named for browsing plants" (the V3.05 surface audit).

App.py owns the instance and drives both inputs:
``set_plants_counts(plant_panel._placed_counts)`` whenever the Plants
tab signals ``placed_counts_changed``; ``set_design_data(enriched)``
inside ``_sync_planning_panel`` for Communities.
"""

from __future__ import annotations

from PyQt6.QtCore import QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QMenu,
    QSizePolicy, QStyledItemDelegate, QStyleOptionViewItem,
)


class _WrapToList(QStyledItemDelegate):
    """A wrapped row as wide as its list, and as tall as its words need there.
    Qt measured the wrap without the stylesheet's item padding, so the rows of
    "what eats it" came out 12 to 30 px wider than the list (V3.08): a
    sideways scroll bar under it, and the end of each line cut off."""

    def __init__(self, view: QListWidget):
        super().__init__(view)
        self._view = view

    def sizeHint(self, option, index):                    # noqa: N802
        width = self._view.viewport().width()
        if width <= 0:
            return super().sizeHint(option, index)
        opt = QStyleOptionViewItem(option)
        room, hint = width, QSize()
        for _ in range(3):              # padding is learnt from the overshoot
            opt.rect = QRect(0, 0, room, 10000)
            hint = super().sizeHint(opt, index)
            if hint.width() <= width:
                break
            room -= hint.width() - width
        return QSize(min(hint.width(), width), hint.height())


def _activate_on_keys(view: QListWidget, handler) -> None:
    """Enter or Space on a row does what a click does. Until V3.02 these lists
    were ``NoFocus``, so a keyboard could not reach the design's own contents;
    the Menu key opens a row's menu at the row, as a right-click does."""
    def run():
        item = view.currentItem()
        if item is not None:
            handler(item)
    for key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
        QShortcut(QKeySequence(key), view,
                  context=Qt.ShortcutContext.WidgetShortcut, activated=run)

from src.plant_list_view import _RESULTS_LIST_STYLE, _type_icon


class OnThisDesignPanel(QWidget):
    """Third inner tab (sibling of Plants and Plant Communities) reviewing
    what's currently placed. Three sub-tabs:

    - **Plants**: species → count.
    - **Communities**: community name → number of instances on the map.
    - **Stats**: species count, native %, layer breakdown, ecological-
      function tags.

    App.py owns the instance and drives both inputs:
    ``set_plants_counts(plant_panel._placed_counts)`` whenever the Plants
    tab signals ``placed_counts_changed``; ``set_design_data(enriched)``
    inside ``_sync_planning_panel`` for Communities + Stats.

    V2.13: the lists are an instrument, not a readout — clicking a species
    or community row locates it on the map, and the species context menu
    selects / removes / opens it in the Plant Library. The panel only emits;
    app.py wires the signals to ``design_review_flow``."""

    species_focus_requested = pyqtSignal(int)            # click → select+zoom
    species_select_requested = pyqtSignal(int)           # ctx: select on map
    species_remove_requested = pyqtSignal(int)           # ctx: remove all (confirmed downstream)
    species_show_in_library_requested = pyqtSignal(int)  # ctx: Plant Library
    species_substitute_requested = pyqtSignal(int)       # ctx: the nursery is out (F91)
    community_focus_requested = pyqtSignal(str)          # click → zoom to members

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(2)
        from src.fill_tab_widget import FillTabWidget
        self._tabs = FillTabWidget()
        # Third level in the tree (Design › Planted › here since V3.07), so it
        # takes the quietest tab style. This strip used to invent a boxed look of its
        # own, which made the deepest level the loudest of the three.
        from src.ui_style import leaf_tab_stylesheet
        self._tabs.setStyleSheet(leaf_tab_stylesheet())
        root.addWidget(self._tabs)

        # Plants sub-tab
        plants_widget = QWidget()
        pl = QVBoxLayout(plants_widget)
        pl.setContentsMargins(2, 2, 2, 2)
        pl.setSpacing(2)
        self._plants_count_label = QLabel("None placed yet")
        self._plants_count_label.setStyleSheet("color: #90a4ae; font-size: 12px;")
        pl.addWidget(self._plants_count_label)
        self._plants_list = QListWidget()
        self._plants_list.setMinimumHeight(60)
        self._plants_list.setStyleSheet(_RESULTS_LIST_STYLE)
        self._plants_list.setAccessibleName("Species in this design")
        # Two lines a row since V3.08, the second what eats it and when, which
        # wraps in a narrow panel rather than running off its edge.
        self._plants_list.setWordWrap(True)
        self._plants_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self._plants_list.setItemDelegate(_WrapToList(self._plants_list))
        self._plants_list.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._plants_list.setToolTip(
            "Click a species to select and frame it on the map;\n"
            "right-click for select / remove / open in Plant Library.")
        self._plants_list.itemClicked.connect(self._on_plant_row_clicked)
        _activate_on_keys(self._plants_list, self._on_plant_row_clicked)
        self._plants_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self._plants_list.customContextMenuRequested.connect(
            self._on_plant_row_menu)
        pl.addWidget(self._plants_list, 1)
        # "Species", not "Plants" — see the note in app.py's inner tab strip.
        self._tabs.addTab(plants_widget, "Species")

        # Communities sub-tab
        communities_widget = QWidget()
        cl = QVBoxLayout(communities_widget)
        cl.setContentsMargins(2, 2, 2, 2)
        cl.setSpacing(2)
        self._communities_count_label = QLabel("No communities placed yet")
        self._communities_count_label.setStyleSheet(
            "color: #90a4ae; font-size: 12px;"
        )
        cl.addWidget(self._communities_count_label)
        self._communities_list = QListWidget()
        self._communities_list.setMinimumHeight(60)
        self._communities_list.setStyleSheet(_RESULTS_LIST_STYLE)
        self._communities_list.setAccessibleName("Communities in this design")
        self._communities_list.setWordWrap(True)
        self._communities_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self._communities_list.setItemDelegate(
            _WrapToList(self._communities_list))
        self._communities_list.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._communities_list.setToolTip(
            "Click a community to frame its placed members on the map.")
        self._communities_list.itemClicked.connect(
            self._on_community_row_clicked)
        _activate_on_keys(self._communities_list, self._on_community_row_clicked)
        cl.addWidget(self._communities_list, 1)
        self._tabs.addTab(communities_widget, "Communities")

        # Latest enriched snapshot, as set_design_data last had it.
        self._latest_enriched: list[dict] = []
        # What each plant feeds (src/what_it_feeds.py), by plant id, and what
        # each community's members feed between them, by their ids: neither
        # changes while the app runs, and these lists redraw on every edit.
        self._food_of: dict = {}
        self._group_food: dict = {}

    def _eater_lines(self, plant_ids) -> dict:
        """``{plant_id: "feeds 12: … · flowers Jul–Aug"}`` (V3.08: the
        owner's "what eats this when", under each species)."""
        from src.what_it_feeds import eaters_line, plant_food
        need = [p for p in plant_ids if p not in self._food_of]
        if need:
            try:
                found = plant_food(need)
            except Exception:  # noqa: BLE001 — the rows still name the plants
                return {}
            for pid in need:
                self._food_of[pid] = found.get(pid)
        return {pid: eaters_line(self._food_of[pid]) for pid in plant_ids
                if self._food_of.get(pid) is not None}

    def _group_line(self, plant_ids) -> str:
        """One line for a community: what its members feed between them, each
        animal once, and when."""
        from src.what_it_feeds import eaters_line, together
        key = frozenset(plant_ids)
        if key not in self._group_food:
            try:
                self._group_food[key] = together(key)
            except Exception:  # noqa: BLE001
                return ""
        return eaters_line(self._group_food[key])

    # ── Plants sub-tab ────────────────────────────────────────────────

    def set_plants_counts(self, counts: dict):
        self._plants_list.clear()
        if not counts:
            self._plants_count_label.setText("None placed yet")
            return
        try:
            from src.db.plants import get_plant
            total = 0
            lines = self._eater_lines([int(pid) for pid in counts])
            for pid, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
                p = get_plant(pid)
                name = p["common_name"] if p else f"Plant #{pid}"
                line = lines.get(int(pid))
                item = QListWidgetItem(f"{name}  ×{count}"
                                       + (f"\n{line}" if line else ""))
                item.setIcon(_type_icon(p["plant_type"] if p else ""))
                item.setData(Qt.ItemDataRole.UserRole, int(pid))
                self._plants_list.addItem(item)
                total += count
            self._plants_count_label.setText(
                f"{total} plant{'s' if total != 1 else ''} placed"
                f" ({len(counts)} species) · click a row to see it"
            )
        except Exception:
            self._plants_count_label.setText(
                f"{sum(counts.values())} plants placed"
            )

    # ── Row interactions (V2.13) ──────────────────────────────────────

    def _on_plant_row_clicked(self, item: QListWidgetItem):
        pid = item.data(Qt.ItemDataRole.UserRole)
        if pid is not None:
            self.species_focus_requested.emit(int(pid))

    def _on_plant_row_menu(self, pos):
        item = self._plants_list.itemAt(pos)
        if item is None:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        if pid is None:
            return
        pid = int(pid)
        menu = QMenu(self._plants_list)
        act_focus = menu.addAction("Zoom to on map")
        act_select = menu.addAction("Select on map")
        act_library = menu.addAction("Show in Plant Library")
        menu.addSeparator()
        # F91. Placed next to Remove because it belongs to the same moment: you
        # are about to lose this plant — the nursery is out, or it is over
        # budget — and the question is what to put there instead.
        act_sub = menu.addAction("Find a substitute…")
        act_remove = menu.addAction("Remove all from design…")
        chosen = menu.exec(self._plants_list.mapToGlobal(pos))
        if chosen is act_focus:
            self.species_focus_requested.emit(pid)
        elif chosen is act_select:
            self.species_select_requested.emit(pid)
        elif chosen is act_library:
            self.species_show_in_library_requested.emit(pid)
        elif chosen is act_sub:
            self.species_substitute_requested.emit(pid)
        elif chosen is act_remove:
            self.species_remove_requested.emit(pid)

    def _on_community_row_clicked(self, item: QListWidgetItem):
        name = item.data(Qt.ItemDataRole.UserRole)
        if name:
            self.community_focus_requested.emit(str(name))

    # ── Communities sub-tab ──────────────────────────────────

    def set_design_data(self, enriched: list[dict]):
        """Refresh the Communities sub-tab from the full enriched
        list of placed-plant features. Each entry should carry at least
        ``plant_id`` and (for community grouping) ``polyculture_name`` +
        ``polyculture_center_lat`` / ``polyculture_center_lng``."""
        self._latest_enriched = list(enriched or [])
        self._refresh_communities(enriched or [])

    def _refresh_communities(self, enriched: list[dict]):
        self._communities_list.clear()
        # Group by community name; count distinct (centre lat, centre lng)
        # pairs per name to get instance count, plus total member count.
        from collections import defaultdict
        instances: dict[str, set] = defaultdict(set)
        member_counts: dict[str, int] = defaultdict(int)
        species: dict[str, set] = defaultdict(set)
        for p in enriched:
            name = (p.get("polyculture_name") or "").strip()
            if not name:
                continue
            clat = p.get("polyculture_center_lat")
            clng = p.get("polyculture_center_lng")
            key = (round(float(clat), 6), round(float(clng), 6)) if (
                clat is not None and clng is not None
            ) else p.get("placement_group_id")
            instances[name].add(key)
            member_counts[name] += 1
            if p.get("plant_id") is not None:
                species[name].add(int(p["plant_id"]))
        if not instances:
            self._communities_count_label.setText("No communities placed yet")
            return
        for name in sorted(instances.keys(), key=str.lower):
            n_inst = len(instances[name])
            n_mem = member_counts[name]
            line = self._group_line(species[name]) if species[name] else ""
            item = QListWidgetItem(
                f"{name}  — {n_inst} instance{'s' if n_inst != 1 else ''}"
                f", {n_mem} member{'s' if n_mem != 1 else ''}"
                + (f"\n{line}" if line else "")
            )
            item.setData(Qt.ItemDataRole.UserRole, name)
            self._communities_list.addItem(item)
        total_inst = sum(len(v) for v in instances.values())
        self._communities_count_label.setText(
            f"{total_inst} community instance{'s' if total_inst != 1 else ''} "
            f"across {len(instances)} community name"
            f"{'s' if len(instances) != 1 else ''}"
        )
