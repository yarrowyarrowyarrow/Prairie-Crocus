"""
species_page.py — one species, as a page you can read, select and hear
(F192, V3.00).

Design principle P5 — see docs/DESIGN_PHILOSOPHY.md.

The Plant Directory's page, moved out of its window so that two places show it:
the Directory, beside its list, and the Browse tab, beside the side panel over
the map (``src/species_flyout.py``). Until V3.00 Browse had a card painted into
the list row instead, drawn with QPainter at a height estimated in advance:
Saskatoon Berry's 26 animals stopped at the seventh with a trailing comma and
the next line drew over them, nothing on it could be selected or copied, and a
screen reader was given nothing at all. Every line here is a label.

Since V3.56 it is one page in both modes (``plant_page_sections``): the
short page with the details a design needs on it, and two folds that start
closed, the animals recorded on the plant with their sources, and where it
grows wild. A fold stays as the reader left it from one plant to the next, so
two plants can be compared with the same fold open. The long advanced page,
370 to 570 words over about two screens, is gone: its roles and badges said
the short page's reasons again, its safety line said "Not checked for poison"
again, its season line wrote out the months over the bar, and a third of it
was sources, eight photograph numbers printed twice.

**P12:** this shows only what the data model holds — horticultural and use
tags, edible parts, documented ecological relationships. Nothing
ethnobotanical is added and no field is relabelled to imply any.
"""

from __future__ import annotations

import html
from typing import Callable, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QToolButton,
    QVBoxLayout, QWidget,
)

from src import plant_page_sections as pps
# Re-exported: the calendar line is month_tasks' since V3.56, one table.
from src.month_tasks import month_runs as _month_runs  # noqa: F401
from src.month_tasks import page_line as _calendar_tasks  # noqa: F401
from src.month_tasks import _MONTHS

_HEAD = "color: #e8f5e9; font-size: 18px; font-weight: bold;"
_SCI = "color: #8fb98f; font-size: 13px; font-style: italic;"
_LABEL = "color: #7f9c82; font-size: 12px; font-weight: bold;"
_BODY = "color: #c8e6c9; font-size: 13px;"
_DIM = "color: #90a4ae; font-size: 12px;"
_LINK = "color: #ffe082;"

#: Wildlife names shown per group before "and N more". Boreal Yarrow has 296
#: documented animals; a page that lists them all opens on a wall of names.
_FIRST = 8


#: The folds, by key: (title, what it holds). Both start closed (V3.56).
ANIMALS, WILD = "animals", "wild"


class SpeciesPage(QWidget):
    """One species: a fixed head (name, and Place when ``actions``) over a
    scrolling body. ``show_plant(row)`` fills it from
    :func:`src.plant_directory.species_entry`."""

    #: The page's Place button: place this plant (the row given to show_plant).
    place_requested = pyqtSignal(dict)
    #: The page's Add to mix button.
    mix_requested = pyqtSignal(dict)
    #: The page's Swap… button, shown while the plant is in the design
    #: (V3.32: session task 5 had no way to do it in the simple app).
    swap_requested = pyqtSignal(dict)
    #: The ✕, or Esc while the page has focus.
    close_requested = pyqtSignal()

    def __init__(self, parent=None, *, actions: bool = False,
                 closable: bool = False,
                 entry_fn: Optional[Callable] = None,
                 photo_warmer: Optional[Callable] = None):
        super().__init__(parent)
        self.setObjectName("speciesPage")
        self._entry_fn = entry_fn
        self._photo_warmer = photo_warmer
        self._photo_shown: dict = {}        # {scientific name: thumbnail}
        self._row: dict = {}
        self._entry: dict = {}
        self._placed = 0
        self._in_mix = False
        self._advanced = False
        #: The folds the reader opened, kept from one plant to the next.
        self._open: set = set()
        #: The region the page speaks for (the picker's ``place``).
        self.place_fn: Optional[Callable] = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 10, 10, 8)
        outer.setSpacing(6)

        head = QHBoxLayout()
        head.setSpacing(6)
        names = QVBoxLayout()
        names.setSpacing(2)
        self._name = QLabel("")
        self._name.setStyleSheet(_HEAD)
        self._name.setWordWrap(True)
        self._name.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        names.addWidget(self._name)
        self._sci = QLabel("")
        self._sci.setStyleSheet(_SCI)
        self._sci.setWordWrap(True)
        self._sci.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        names.addWidget(self._sci)
        self._placed_line = QLabel("")
        self._placed_line.setStyleSheet(_DIM)
        self._placed_line.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        names.addWidget(self._placed_line)
        head.addLayout(names, 1)
        self._close = None
        if closable:
            self._close = QToolButton()
            self._close.setText("✕")
            self._close.setObjectName("speciesPageClose")
            self._close.setAccessibleName("Close the plant page")
            self._close.setToolTip("Close (Esc)")
            self._close.setCursor(Qt.CursorShape.PointingHandCursor)
            self._close.setFixedSize(28, 28)
            self._close.setStyleSheet(
                "QToolButton { color: #c8e6c9; background: transparent; "
                "border: 1px solid #2e4a2e; border-radius: 4px; "
                "font-size: 14px; }"
                "QToolButton:hover { border-color: #66bb6a; }"
                "QToolButton:focus { border: 2px solid #ffe082; }")
            self._close.clicked.connect(self.close_requested)
            head.addWidget(self._close, 0, Qt.AlignmentFlag.AlignTop)
        self._head = QWidget()
        self._head.setLayout(head)
        outer.addWidget(self._head)

        self._place_btn = None
        self._mix_btn = None
        self._swap_btn = None
        if actions:
            from src.place_action import PlaceButton
            row = QHBoxLayout()
            row.setSpacing(6)
            self._place_btn = PlaceButton("plant")
            self._place_btn.clicked.connect(
                lambda: self._row and self.place_requested.emit(self._row))
            row.addWidget(self._place_btn, 1)
            self._mix_btn = QPushButton("Add to mix")
            self._mix_btn.setObjectName("speciesPageMix")
            self._mix_btn.setToolTip(
                "Add this plant to the mix under the plant list, to place "
                "several species together in a row, grid, circle or area.")
            self._mix_btn.setStyleSheet(
                "QPushButton { background: #1e2e1e; color: #a5d6a7; "
                "border: 1px solid #2e4a2e; border-radius: 4px; "
                "padding: 4px 10px; font-size: 13px; min-height: 24px; }"
                "QPushButton:hover { border-color: #4a7a4a; }"
                "QPushButton:focus { border: 2px solid #ffe082; }"
                "QPushButton:disabled { color: #7f9c82; }")
            self._mix_btn.clicked.connect(
                lambda: self._row and self.mix_requested.emit(self._row))
            row.addWidget(self._mix_btn)
            self._swap_btn = QPushButton("Swap…")
            self._swap_btn.setObjectName("speciesPageSwap")
            self._swap_btn.setToolTip(
                "Put a plant that does a similar job here in its place, "
                "wherever it is in this design. Undo puts it back.")
            self._swap_btn.setStyleSheet(self._mix_btn.styleSheet())
            self._swap_btn.clicked.connect(
                lambda: self._row and self.swap_requested.emit(self._row))
            row.addWidget(self._swap_btn)
            self._actions = QWidget()
            self._actions.setLayout(row)
            outer.addWidget(self._actions)

        self._body = QWidget()
        self._col = QVBoxLayout(self._body)
        self._col.setContentsMargins(0, 4, 6, 8)
        self._col.setSpacing(6)
        self._scroll = QScrollArea()
        self._scroll.setAccessibleName("Species page")   # a Tab stop (V3.02)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setWidget(self._body)
        outer.addWidget(self._scroll, 1)
        self.show_empty()

    # ── What is shown ───────────────────────────────────────────────────────

    def shown_id(self) -> int:
        """The plant on the page, or 0."""
        return int(self._row.get("id") or 0) if self._entry else 0

    def entry(self) -> dict:
        return self._entry

    def show_empty(self, text: str = "Choose a plant to read about it."):
        self._row, self._entry = {}, {}
        self._head.setVisible(self._close is not None)
        self._name.setText("")
        self._sci.setText("")
        self._placed_line.setVisible(False)
        if self._place_btn is not None:
            self._actions.setVisible(False)
        self.setAccessibleName("Plant page")
        self._clear()
        hint = QLabel(text)
        hint.setStyleSheet(_DIM)
        hint.setWordWrap(True)
        hint.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._col.addWidget(hint)
        self._col.addStretch()

    def set_advanced_tools(self, on: bool) -> None:
        """Add to mix only with Advanced tools on (V3.21): the mix it fills
        is one of the builders the switch holds. Since V3.56 the page is the
        same in both modes but for the ID line under the photographs."""
        if self._mix_btn is not None:
            self._mix_btn.setVisible(bool(on))
        if bool(on) != self._advanced:
            self._advanced = bool(on)
            if self._entry:
                self._render()

    def show_plant(self, row: dict, *, placed: int = 0, in_mix: bool = False,
                   why: Optional[list] = None):
        """Fill the page for ``row`` (a catalogue row; only its id is read
        here, and it is what Place and Add to mix hand back). ``why`` is the
        generator's reasons for one placed plant's spot (F19), shown first
        when the page was opened from that plant on the map."""
        self._why = [w for w in (why or []) if w]
        entry_fn = self._entry_fn
        if entry_fn is None:
            from src.plant_directory import species_entry as entry_fn
        entry = entry_fn(int((row or {}).get("id") or 0)) if row else {}
        if not entry:
            self.show_empty()
            return
        same = self.shown_id() == int(row.get("id") or 0)
        self._row, self._entry = dict(row), entry
        self._placed, self._in_mix = int(placed or 0), bool(in_mix)
        if self._photo_warmer is not None:
            # The list warms a photo only when asked. Ask for this one now; the
            # owner calls refresh_photo when it lands.
            self._photo_warmer(row)
        self._render()
        if not same:
            self._scroll.verticalScrollBar().setValue(0)

    def set_placement(self, *, placed: Optional[int] = None,
                      in_mix: Optional[bool] = None):
        """How many are in the design, and whether it is in the mix, changed
        while the page was open."""
        if placed is not None:
            self._placed = int(placed)
        if in_mix is not None:
            self._in_mix = bool(in_mix)
        if self._entry:
            self._render_head()

    def refresh_photo(self, plant_id: int):
        """A photo finished downloading: redraw if it is this plant's."""
        if self._entry and int(plant_id) == self.shown_id():
            keep = self._scroll.verticalScrollBar().value()
            self._render()
            self._scroll.verticalScrollBar().setValue(keep)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self._close is not None:
            self.close_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    # ── Rendering ───────────────────────────────────────────────────────────

    def _render_head(self):
        entry = self._entry
        name = entry.get("name") or ""
        self._head.setVisible(True)
        self._name.setText(name)
        self._sci.setText(entry.get("scientific_name") or "")
        self._placed_line.setText(
            f"{self._placed} in this design" if self._placed else "")
        self._placed_line.setVisible(bool(self._placed))
        self.setAccessibleName(f"About {name}")
        if self._place_btn is not None:
            self._actions.setVisible(True)
            self._place_btn.set_subject(name)
            self._mix_btn.setText("In the mix" if self._in_mix else "Add to mix")
            self._mix_btn.setEnabled(not self._in_mix)
            self._mix_btn.setAccessibleName(
                f"{name} is in the mix" if self._in_mix
                else f"Add {name} to the mix")
            self._swap_btn.setVisible(bool(self._placed))
            self._swap_btn.setAccessibleName(f"Swap {name} for another plant")

    def _render(self):
        entry = self._entry
        self._render_head()
        self._clear()
        self._col.addWidget(self._photo_block(entry))
        if self._advanced:
            self._section("", pps.ID_LINE, dim=True)     # WD-8, W3
        if getattr(self, "_why", None):
            # F19 (V3.05): why the generator put this one here, read back
            # from the score that chose the spot.
            self._section("Why here", ". ".join(self._why) + ".")
        place = self.place_fn() if self.place_fn else ""
        for heading, body in pps.simple(entry, place=place):
            if heading == pps.SEASON:
                self._section(heading, body) if body else self._heading(heading)
                bloom, fruit = (entry.get("bloom_months") or [],
                                entry.get("fruit_months") or [])
                if bloom or fruit:
                    self._col.addWidget(SeasonBar(bloom, fruit))
            elif body:
                self._section(heading, body)
            else:
                self._heading(heading)
        self._animals_fold(entry)
        self._wild_fold(entry)
        self._col.addStretch()

    def _fold(self, key: str, title: str) -> Optional[QVBoxLayout]:
        """A fold's button, and its layout when it is open (else None)."""
        is_open = key in self._open
        btn = QPushButton(f"{title} {'▾' if is_open else '▸'}")
        btn.setObjectName(f"speciesPageFold_{key}")
        btn.setAccessibleName(title)
        btn.setCheckable(True)
        btn.setChecked(is_open)
        btn.setStyleSheet(
            "QPushButton { color: #ffe082; background: transparent; "
            "border: none; text-align: left; font-size: 13px; "
            "min-height: 24px; } QPushButton:focus { border: 2px solid "
            "#ffe082; }")
        btn.clicked.connect(lambda _c=False, k=key: self._toggle(k))
        self._col.addWidget(btn)
        return self._col if is_open else None

    def _toggle(self, key: str):
        keep = self._scroll.verticalScrollBar().value()
        self._open ^= {key}
        self._render()
        # The button was rebuilt: the keyboard goes back to it (V3.02).
        btn = self.findChild(QPushButton, f"speciesPageFold_{key}")
        if btn is not None:
            btn.setFocus(Qt.FocusReason.OtherFocusReason)
        self._scroll.verticalScrollBar().setValue(keep)

    def _animals_fold(self, entry: dict):
        """The animals recorded on it, by what they take, and the works the
        records came from (P9): a fold, closed until asked for."""
        w = entry.get("wildlife") or {}
        if not w.get("total"):
            return
        animals = int(w.get("animals") or w["total"])
        if self._fold(ANIMALS, f"Animals recorded on it ({animals})") is None:
            return
        special = int(w.get("specialist_animals") or w.get("specialists") or 0)
        if special:
            self._section("", f"{special} of them depend on it alone (⚑).")
        for group in w.get("groups") or []:
            label = self._section("", _group_html(group, _FIRST), rich=True)
            if label is not None and len(group.get("items") or []) > _FIRST:
                label.linkActivated.connect(
                    lambda _href, lab=label, g=group:
                    lab.setText(_group_html(g, None)))
        self._citation_block(w)

    def _wild_fold(self, entry: dict):
        """Where it is native and where it has been recorded, with the counts
        (P9): a region seen 242 times and one seen 5 times are different
        claims. Native before found (F220, F222, V3.12)."""
        from src.native_here import province_words
        native = province_words(entry)
        around = entry.get("around") or {}
        rows = entry.get("ranges") or []
        if not (native or around.get("words") or rows):
            return
        if self._fold(WILD, "Where it grows wild") is None:
            return
        self._section("Native to", native)
        if around.get("words"):
            self._section(f"Around {around['short']}", around["words"])
        if not rows:
            return
        bits = [f"{r['name']}, {r['occurrences']} records" if
                r.get("occurrences") else f"{r['name']} (no records counted)"
                for r in rows[:4]]
        if len(rows) > 4:
            bits.append(f"and {len(rows) - 4} more regions")
        self._section("Recorded in", "\n".join(bits))
        origins = []
        for r in rows:
            src = (r.get("source") or "").strip()
            if src and src not in origins:
                origins.append(src)
        if origins:
            self._section("", "From " + "; ".join(origins) + ".", dim=True)

    def _heading(self, text: str):
        head = QLabel(text)
        head.setStyleSheet(_LABEL)
        head.setWordWrap(True)
        head.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        self._col.addWidget(head)

    def _clear(self):
        while self._col.count():
            item = self._col.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _section(self, heading: str, body: str, *, dim: bool = False,
                 rich: bool = False) -> Optional[QLabel]:
        if not (body or "").strip():
            return None
        if heading:
            self._heading(heading)
        text = QLabel(body)
        text.setWordWrap(True)
        text.setStyleSheet(_DIM if dim else _BODY)
        flags = Qt.TextInteractionFlag.TextSelectableByMouse
        if rich:
            text.setTextFormat(Qt.TextFormat.RichText)
            flags |= (Qt.TextInteractionFlag.LinksAccessibleByMouse
                      | Qt.TextInteractionFlag.LinksAccessibleByKeyboard)
        else:
            text.setTextFormat(Qt.TextFormat.PlainText)
        text.setTextInteractionFlags(flags)
        self._col.addWidget(text)
        return text

    def _photo_block(self, entry: dict) -> QWidget:
        """The photographs (``src.photo_strip``: the first large, the rest
        as thumbnails, since V3.35), or an honest line about not having one.
        The thumbnail chosen is kept across a redraw."""
        from src.photo_strip import PhotoStrip
        sci = entry.get("scientific_name") or ""
        return PhotoStrip(
            entry.get("photos") or [], entry.get("name") or "",
            width=max(240, min(320, self.width() - 40)),
            selected=self._photo_shown.get(sci, 0),
            on_select=lambda i: self._photo_shown.__setitem__(sci, i))

    def _citation_block(self, wildlife: dict):
        """Where the wildlife relationships came from. Every edge has carried a
        citation; until V2.42 no screen showed one, so a sourced record and an
        invention looked the same."""
        from src.citations import format_citation, is_placeholder
        keys: list = []
        unattributed = 0
        for group in wildlife.get("groups") or []:
            for item in group.get("items") or []:
                for key in (k.strip() for k in
                            (item.get("source") or "").split(",")):
                    if not key:
                        continue
                    if is_placeholder(key):
                        unattributed += 1
                    elif key not in keys:
                        keys.append(key)
        if not keys and not unattributed:
            return
        bits = [format_citation(k, short=True) for k in keys]
        text = ("Sources: " + "; ".join(bits) + ".") if bits else ""
        if unattributed:
            text += (f" {unattributed} of these were seeded without naming a "
                     "work.").rstrip()
        self._section("", text.strip(), dim=True)


class SeasonBar(QWidget):
    """Twelve months, a row for flowers and a row for fruit, each row named in
    words so the colour is never the only cue. The accessible name is the
    sentence (``phenology_bar.alt_text``), which is what a screen reader reads
    and what the tooltip says."""

    BLOOM = "#d98b3a"
    FRUIT = "#b98aa6"
    EMPTY = "#2c3b2c"
    _LABEL_W = 60
    _ROW_H = 16           # room for its 12 px words (V3.03)
    _HEAD_H = 16

    def __init__(self, bloom, fruit, parent=None):
        super().__init__(parent)
        from src.phenology_bar import alt_text
        self._rows = [(name, set(int(m) for m in months), colour)
                      for name, months, colour in (
                          ("Flowers", bloom, self.BLOOM),
                          ("Fruit", fruit, self.FRUIT)) if months]
        text = alt_text(bloom, fruit)
        self.setAccessibleName(text)
        self.setToolTip(text)
        self.setMinimumWidth(220)
        self.setFixedHeight(self._HEAD_H + 2 + len(self._rows) * (self._ROW_H + 3))

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont(self.font())
        font.setPixelSize(12)
        p.setFont(font)
        left = self._LABEL_W
        cell = (self.width() - left) / 12.0
        p.setPen(QColor("#90a4ae"))
        for i, month in enumerate(_MONTHS):
            p.drawText(int(left + i * cell), 0, int(cell), self._HEAD_H,
                       int(Qt.AlignmentFlag.AlignCenter), month[0])
        for r, (name, months, colour) in enumerate(self._rows):
            top = self._HEAD_H + 2 + r * (self._ROW_H + 3)
            p.setPen(QColor("#c8e6c9"))
            p.drawText(0, top, left - 4, self._ROW_H,
                       int(Qt.AlignmentFlag.AlignVCenter
                           | Qt.AlignmentFlag.AlignLeft), name)
            for i in range(12):
                filled = (i + 1) in months
                p.setPen(QPen(QColor("#3a4d3a"), 1))
                p.setBrush(QColor(colour if filled else self.EMPTY))
                p.drawRoundedRect(int(left + i * cell) + 1, top,
                                  max(2, int(cell) - 2), self._ROW_H, 2, 2)
        p.end()


def _group_html(group: dict, first: Optional[int]) -> str:
    """One wildlife group as rich text: its first ``first`` names and a link
    to the rest, or all of them when ``first`` is None."""
    items = group.get("items") or []
    shown = items if first is None else items[:first]
    names = ", ".join(html.escape(i.get("name") or "")
                      + (" ⚑" if i.get("specialist") else "") for i in shown)
    how = group.get("how") or ""
    text = f"<b>{html.escape(how[:1].upper() + how[1:])}</b>: {names}"
    more = len(items) - len(shown)
    if more > 0:
        text += (f' <a href="more" style="{_LINK}">and {more} more</a>')
    return text
