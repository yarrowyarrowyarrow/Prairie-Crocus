"""
community_filters.py — the community list's search, filters and order, folded
like the plant list's (V3.58).

Design principle P9 — see docs/DESIGN_PHILOSOPHY.md.

The owner, of the plant filters: "still kinda messy ... extend this work into
the Communities tab as well". The tab had a title saying what the tab says, a
*Show variations* switch (each community's arrow opens its variations
already), a *Group by* list, five dropdowns (sun, moisture, structure, 28
habitats from Cypress Upland to Tazin Lake Upland), a seven-way sort and an
*Edmonton natives only* box with a line counting the 47 it hid, above 27
communities.

Now it is the plant list's shape, in the plant list's words: a search box,
the *Filters* line (chips while folded, ``filter_status.FilterLine``), and
inside it Sun, Soil and What it does; then the count and a three-way order.
With the region's list as the catalogue (``plant_filters.catalogue_scope``,
the owner's "Edmonton only, even in Advanced") the list is the region's
communities and nothing says so; without one the habitat tree stays.

The words map onto the library index's own labels (``DISPLAY``), which stay
the keys: a community is filed by what its members are, and only what is
shown changed.
"""

from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import QSettings, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout,
    QWidget,
)

from src.filter_status import DIM, FilterLine
from src.filter_widgets import COMBO_STYLE, make_multi_combo

#: How each facet reads, the plant filters' words, over the index's labels.
#: A label not here is not offered (V3.58: "Generalist" and "Medicinal /
#: Useful" are not what a yard is chosen for).
DISPLAY: dict = {
    "sun": {"Full Sun": "Full sun", "Partial Shade": "Part shade",
            "Shade": "Shade"},
    "moisture": {"Dry": "Dry", "Medium moisture": "Average", "Wet": "Moist"},
    "function": {"Pollination": "Bees and butterflies",
                 "Host Community": "Caterpillar food",
                 "Keystone Species": "Feeds many caterpillars",
                 "Bird Food": "Bird food",
                 "Shelter / Nesting": "Nesting",
                 "Shelter / Windbreak": "Windbreak",
                 "Nitrogen / Soil": "Adds nitrogen",
                 "Erosion / Groundcover": "Holds a slope",
                 "Water / Riparian": "By water", "Beauty": "Showy"},
}
#: ``(facet, name, placeholder)`` in the order drawn.
FACETS = (("sun", "Sun", "Any sun"), ("moisture", "Soil", "Any soil"),
          ("function", "What it does", "What it does…"))
#: The orders (``polycultures.sort_community_ids`` keys), as the plant list's.
ORDERS = (("best", "Most wildlife first"), ("name", "Name"),
          ("easiest", "Easiest to buy"))


def facts_word(facet: str, label: str) -> str:
    """A row's fact in the filters' words ("Full Sun" → "Full sun"); a row
    says "Average soil", where the dropdown under "Soil" says "Average"."""
    if facet == "moisture" and label == "Medium moisture":
        return "Average soil"
    return DISPLAY.get(facet, {}).get(label, label)


class CommunityFilters(QWidget):
    """Search, the Filters line, the folded filters, the count and the order.
    ``changed`` asks the owner to refresh its list; ``combos`` holds the
    facets by key, ``search_box``, ``order_combo`` and ``count_label`` the
    rest."""

    changed = pyqtSignal()

    def __init__(self, choices: dict, *, scoped: bool,
                 habitat_combo: Callable = None, parent=None):
        super().__init__(parent)
        col = QVBoxLayout(self)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(4)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search communities…")
        self.search_box.setAccessibleName("Search communities")
        self.search_box.setClearButtonEnabled(True)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self.changed)
        self.search_box.textChanged.connect(lambda _t: self._timer.start())
        col.addWidget(self.search_box)

        self.filter_line = FilterLine()
        self.filter_line.filters_button.toggled.connect(self.set_open)
        self.filter_line.remove_requested.connect(self._remove)
        self.filter_line.clear_requested.connect(self.clear)
        col.addWidget(self.filter_line)

        self.area = QWidget()
        self.area.setAccessibleName("Community filters")
        grid = QGridLayout(self.area)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)
        self.combos: dict = {}
        self._names: dict = {}
        facets = list(FACETS)
        if not scoped and habitat_combo is not None:
            facets.append(("habitat", "Habitat", "Any habitat"))
        for i, (facet, name, placeholder) in enumerate(facets):
            if facet == "habitat":
                combo = habitat_combo(placeholder, self._on_facet)
            else:
                shown = DISPLAY.get(facet, {})
                labels = {k: shown[k] for k in shown
                          if k in set(choices.get(facet) or ())}
                combo = make_multi_combo(placeholder, labels,
                                         on_change=self._on_facet)
            combo.setAccessibleName(f"{name} filter")
            combo.lineEdit().setAccessibleName(f"{name} filter")
            grid.addWidget(combo, i // 3, i % 3)
            self.combos[facet] = combo
            self._names[facet] = name
        col.addWidget(self.area)

        row = QHBoxLayout()
        row.setSpacing(6)
        self.count_label = QLabel("")
        self.count_label.setStyleSheet(DIM)
        row.addWidget(self.count_label, 1)
        order_label = QLabel("Order")
        order_label.setStyleSheet(DIM)
        row.addWidget(order_label)
        self.order_combo = QComboBox()
        self.order_combo.setAccessibleName("Order communities by")
        order_label.setBuddy(self.order_combo)
        self.order_combo.setStyleSheet(COMBO_STYLE)
        for key, label in ORDERS:
            self.order_combo.addItem(label, key)
        saved = QSettings().value("plant_communities/sort_by", "best", type=str)
        at = self.order_combo.findData(saved)
        self.order_combo.setCurrentIndex(max(0, at))
        self.order_combo.currentIndexChanged.connect(self._on_order)
        row.addWidget(self.order_combo)
        col.addLayout(row)

        self.set_open(False)
        self._refresh_chips()

    # ── What is on ──────────────────────────────────────────────────────────

    def order(self) -> str:
        return self.order_combo.currentData() or "best"

    def active(self) -> dict:
        """Facet → ticked keys, for facets with anything ticked."""
        return {f: c.checked_keys() for f, c in self.combos.items()
                if c.checked_keys()}

    def is_open(self) -> bool:
        return self.area.isVisibleTo(self)

    def set_open(self, on: bool) -> None:
        self.area.setVisible(bool(on))
        button = self.filter_line.filters_button
        button.blockSignals(True)
        button.setChecked(bool(on))
        button.blockSignals(False)
        button.setText("Filters ▾" if on else "Filters ▸")
        self.filter_line.set_folded(not on)

    def clear(self) -> None:
        for combo in self.combos.values():
            combo.set_checked_keys([])
        self._on_facet()

    def _remove(self, facet: str) -> None:
        if facet in self.combos:
            self.combos[facet].set_checked_keys([])
            self._on_facet()

    def _on_facet(self) -> None:
        self._refresh_chips()
        self.changed.emit()

    def _on_order(self, _index: int = 0) -> None:
        QSettings().setValue("plant_communities/sort_by", self.order())
        self.changed.emit()

    def _refresh_chips(self) -> None:
        entries = []
        for facet, keys in self.active().items():
            words = [facts_word(facet, k) for k in keys]
            text = words[0] if len(words) == 1 else (
                f"{words[0]} or {words[1]}" if len(words) == 2
                else f"{words[0]}, {words[1]} or {len(words) - 2} more")
            entries.append((facet, f"{self._names[facet]}: {text}"))
        self.filter_line.set_entries(entries)
