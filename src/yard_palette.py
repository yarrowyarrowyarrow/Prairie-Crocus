"""
src/yard_palette.py — Placement › Yard: everything put in a yard that is not a
plant, in one list (V3.72, F280's second increment).

Until V3.72 there were two tools for the same things: Placement › Structures
placed a pond, a raised bed or a shed as a point and a size, and Draw › Shape
drew a Water Feature, a Garden Bed or a building's outline, and the app read the
two differently (the V3.69 review). The owner's answers to the V3.71 plan: one
tab called Yard, Draw › Shape retired, fences and hedges in the simple app.

A person chooses a kind under six headings (``yard_kinds.PALETTE``) and sees a
sentence about it, its few options (``Kind.options``: a path's surface, a bed
raised or not, a fence's kind, a building's height…) and one button with its
verb: **Draw on the map** for an area or a line, **Place on the map** for an
object. What the button sends is what the map's tools already take; the stored
kind and options are made by ``yard_kinds.drawn_props``, so this panel, the
conversion on open and the scripting API store a kind the same way.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog, QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QLabel,
    QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from src import yard_kinds as yk

#: How an area is put on the map (V3.75): drawn corner by corner, or placed
#: whole as a rectangle or a circle of the size typed.
PLACE_AS = (("outline", "Outline"), ("rectangle", "Rectangle"),
            ("circle", "Circle"))

#: Every row highlights the same way, hovered or chosen. Until V3.75 the
#: alternate rows' colour was declared after the chosen one's, so it won on
#: every second row (the owner: "only every 2nd item highlights").
LIST_STYLE = (
    "QTreeWidget { background: #1a2a1a; border: 1px solid #2e4a2e; "
    "show-decoration-selected: 1; }"
    "QTreeWidget::item { padding: 5px 4px; }"
    "QTreeWidget::item:hover, QTreeWidget::branch:hover "
    "{ background: #24402a; }"
    "QTreeWidget::item:selected, QTreeWidget::branch:selected "
    "{ background: #2e6a36; color: #f1f8e9; }")


def _object_def(kind) -> dict:
    """An object's catalogue definition (``src/db/structures.py``)."""
    from src.db.structures import get_structure
    sid = kind.struct_ids[0]
    return dict(get_structure(sid) or {"id": sid, "name": kind.words,
                                       "size_m": 1.0})


class YardPalette(QWidget):
    """The Yard tab: the list, the chosen kind's options, and its verb."""

    draw_area_requested = pyqtSignal(dict)      # the map's shape tool
    draw_line_requested = pyqtSignal(dict)      # the map's line tool
    place_object_requested = pyqtSignal(dict)   # a structure definition

    def __init__(self, parent=None):
        super().__init__(parent)
        self._advanced = False
        self._inputs: dict = {}
        self._shape: dict = {}
        self._place = "outline"         # kept from one area to the next
        self._colours = {}
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(6)

        # Seven groups, closed until opened (V3.75, the owner: "the list is a
        # bit messy ... some collapsing groupings").
        self._list = QTreeWidget()
        self._list.setAccessibleName("Things in a yard")
        self._list.setHeaderHidden(True)
        self._list.setRootIsDecorated(True)
        self._list.setIndentation(14)
        self._list.setStyleSheet(LIST_STYLE)
        self._list.currentItemChanged.connect(self._on_chosen)
        self._list.itemClicked.connect(self._on_clicked)
        self._list.itemDoubleClicked.connect(self._on_double)
        root.addWidget(self._list, 1)

        self._detail = QFrame()
        self._detail.setObjectName("yardDetail")
        self._detail.setStyleSheet(
            "QFrame#yardDetail { background: #1e2e1e; border: 1px solid "
            "#2e4a2e; border-radius: 4px; }")
        box = QVBoxLayout(self._detail)
        box.setContentsMargins(8, 6, 8, 6)
        box.setSpacing(4)
        self._name = QLabel("")
        self._name.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #a5d6a7;")
        self._about = QLabel("")
        self._about.setWordWrap(True)
        self._about.setStyleSheet("color: #b0bec5; font-size: 12px;")
        self._form_box = QWidget()
        self._form = QFormLayout(self._form_box)
        self._form.setContentsMargins(0, 2, 0, 0)
        box.addWidget(self._name)
        box.addWidget(self._about)
        box.addWidget(self._form_box)
        self._detail.setVisible(False)
        root.addWidget(self._detail)

        self._verb = QPushButton(yk.VERB_WORDS[yk.AREA])
        self._verb.setEnabled(False)
        self._verb.setStyleSheet(
            "QPushButton { background: #2e7d32; color: #e8f5e9; border: 1px "
            "solid #43a047; border-radius: 4px; padding: 6px; "
            "font-weight: bold; }"
            "QPushButton:hover { background: #388e3c; }"
            "QPushButton:disabled { background: #263238; color: #90a4ae; "
            "border-color: #37474f; }")
        self._verb.clicked.connect(self._on_verb)
        root.addWidget(self._verb)
        self._fill()

    # ── The list ─────────────────────────────────────────────────────────────

    def _fill(self) -> None:
        """The kinds under their headings, each heading a group that opens
        and closes and cannot itself be chosen. All closed at first; a kind
        chosen before a refill is chosen again, its group open."""
        current = self.kind()
        self._list.clear()
        for heading, keys in yk.PALETTE:
            kinds = [yk.BY_KEY[k] for k in keys
                     if self._advanced or not yk.BY_KEY[k].advanced]
            if not kinds:
                continue
            head = QTreeWidgetItem([f"{heading} ({len(kinds)})"])
            head.setFlags(Qt.ItemFlag.ItemIsEnabled)
            head.setData(0, Qt.ItemDataRole.AccessibleTextRole, heading)
            font = head.font(0)
            font.setBold(True)
            head.setFont(0, font)
            head.setForeground(0, QColor("#a5d6a7"))
            self._list.addTopLevelItem(head)
            for k in kinds:
                item = QTreeWidgetItem([self._words(k)])
                item.setData(0, Qt.ItemDataRole.UserRole, k.key)
                item.setToolTip(0, self._about_of(k))
                head.addChild(item)
        if current is not None:
            self.choose(current.key)

    def groups(self) -> list:
        """The group rows, in order."""
        return [self._list.topLevelItem(i)
                for i in range(self._list.topLevelItemCount())]

    def _on_clicked(self, item, _column=0) -> None:
        """A click on a group opens or closes it."""
        if item is not None and item.parent() is None:
            item.setExpanded(not item.isExpanded())

    def _on_double(self, item, _column=0) -> None:
        if item is not None and item.parent() is not None:
            self._on_verb()

    @staticmethod
    def _words(kind) -> str:
        if kind.verb == yk.OBJECT:
            sd = _object_def(kind)
            return f"{sd.get('icon', '')}  {kind.words}".strip()
        return kind.words

    @staticmethod
    def _about_of(kind) -> str:
        if kind.about:
            return kind.about
        return _object_def(kind).get("description", "") \
            if kind.verb == yk.OBJECT else ""

    def kind(self):
        """The chosen :class:`yard_kinds.Kind`, or ``None``."""
        item = self._list.currentItem()
        key = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        return yk.BY_KEY.get(key) if key else None

    def choose(self, key: str) -> bool:
        """Choose a kind by its key (the Overview's buttons do), opening its
        group. Returns whether it is listed."""
        for head in self.groups():
            for i in range(head.childCount()):
                item = head.child(i)
                if item.data(0, Qt.ItemDataRole.UserRole) == key:
                    head.setExpanded(True)
                    self._list.setCurrentItem(item)
                    return True
        return False

    def set_advanced_tools(self, on: bool) -> None:
        """Custom, with its colours, only with Advanced tools on (V3.21's rule,
        kept). Fences and hedges are in the simple app (the owner's Q2)."""
        if bool(on) != self._advanced:
            self._advanced = bool(on)
            self._fill()

    # ── The chosen kind ──────────────────────────────────────────────────────

    def _on_chosen(self, *_):
        kind = self.kind()
        while self._form.rowCount():
            self._form.removeRow(0)
        self._inputs = {}
        self._detail.setVisible(kind is not None)
        self._verb.setEnabled(kind is not None)
        if kind is None:
            return
        self._name.setText(self._words(kind))
        self._about.setText(self._about_of(kind))
        self._verb.setText(yk.VERB_WORDS[kind.verb])
        self._verb.setAccessibleName(
            f"{yk.VERB_WORDS[kind.verb]}: {kind.words}")
        self._shape = {}
        for opt in kind.options:
            self._add_option(kind, opt)
        if kind.verb == yk.AREA:
            self._add_shape(kind)
        if kind.verb == yk.OBJECT:
            self._add_size(kind)
        if kind.key == "custom":
            self._add_colours(kind)

    def _add_option(self, kind, opt) -> None:
        if opt.choices:
            w = QComboBox()
            for value, words in opt.choices:
                w.addItem(words, value)
            w.setCurrentIndex(max(0, w.findData(opt.default)))
            if opt.key == "building":
                w.currentIndexChanged.connect(self._on_building)
            if opt.key == "hedge_kind":
                w.currentIndexChanged.connect(self._on_hedge)
        elif opt.text:
            w = QLineEdit()
        else:
            w = QDoubleSpinBox()
            w.setRange(opt.lo, opt.hi)
            w.setSingleStep(opt.step or 0.5)
            w.setDecimals(2 if (opt.step or 0.5) < 0.5 else 1)
            w.setSuffix(f" {opt.unit}" if opt.unit else "")
            w.setValue(float(opt.default or opt.lo))
        w.setAccessibleName(opt.words)
        self._inputs[opt.key] = w
        self._form.addRow(opt.words + ":", w)
        if opt.key == "building":
            self._on_building()

    def _add_shape(self, kind) -> None:
        """*Place it as* (V3.75): the outline drawn corner by corner, or a
        rectangle or a circle of the size typed, put down whole with a click.
        The sizes start at ``yard_kinds``' stated guesses for the kind."""
        place = QComboBox()
        for value, words in PLACE_AS:
            place.addItem(words, value)
        place.setAccessibleName("Place it as")
        length, width = yk.SHAPE_SIZE_M.get(kind.key, (3.0, 2.0))
        self._shape = {"place": place,
                       "length": self._metres("Length", length),
                       "width": self._metres("Width", width),
                       "across": self._metres("Across",
                                              yk.SHAPE_ACROSS_M.get(kind.key,
                                                                    3.0))}
        self._form.addRow("Place it as:", place)
        for key in ("length", "width", "across"):
            box = self._shape[key]
            self._form.addRow(box.accessibleName() + ":", box)
        place.setCurrentIndex(max(0, place.findData(self._place)))
        place.currentIndexChanged.connect(self._on_place)
        self._on_place()

    @staticmethod
    def _metres(words: str, value: float) -> QDoubleSpinBox:
        box = QDoubleSpinBox()
        box.setRange(0.3, 100.0)
        box.setSingleStep(0.1)
        box.setDecimals(1)
        box.setSuffix(" m")
        box.setValue(float(value))
        box.setAccessibleName(words)
        return box

    def _on_place(self, *_) -> None:
        """Only the sizes the chosen way of placing needs."""
        place = self._shape["place"].currentData()
        self._place = place
        for key, wanted in (("length", "rectangle"), ("width", "rectangle"),
                            ("across", "circle")):
            self._form.setRowVisible(self._shape[key], place == wanted)

    def _on_hedge(self, *_) -> None:
        """A hedge's height and width follow what it is until changed."""
        what = self._inputs.get("hedge_kind")
        if what is None:
            return
        h, w = yk.HEDGE_SIZE_M.get(what.currentData(), yk.HEDGE_SIZE_M["other"])
        for key, value in (("height_m", h), ("width_m", w)):
            box = self._inputs.get(key)
            if box is not None:
                box.setValue(value)

    def _on_building(self, *_):
        """A building's height follows what it is until changed by hand."""
        what = self._inputs.get("building")
        height = self._inputs.get("height_m")
        if what is not None and height is not None:
            height.setValue(yk.BUILDING_HEIGHT_M.get(what.currentData(), 2.4))

    def _add_size(self, kind) -> None:
        from src.db.structures import size_range, size_words
        sd = _object_def(kind)
        w = QDoubleSpinBox()
        w.setRange(*size_range(sd["id"]))
        w.setSingleStep(0.1 if sd.get("size_m", 1) < 2 else 0.5)
        w.setDecimals(1)
        w.setValue(float(sd.get("size_m") or 1.0))
        words = size_words(sd).rstrip(":")
        w.setAccessibleName(words)
        self._inputs["size_m"] = w
        self._form.addRow(words + ":", w)

    def _add_colours(self, kind) -> None:
        fill, stroke, _opacity, _dash = kind.colours
        self._colours = {"fill_color": fill, "stroke_color": stroke}
        for key, words in (("fill_color", "Fill colour"),
                           ("stroke_color", "Outline colour")):
            btn = QPushButton()
            btn.setAccessibleName(words)
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(self._swatch(self._colours[key]))
            btn.clicked.connect(lambda _c=False, k=key, b=btn:
                                self._pick(k, b))
            self._form.addRow(words + ":", btn)

    @staticmethod
    def _swatch(colour: str) -> str:
        return (f"background: {colour}; border: 1px solid #4a7a4a; "
                "border-radius: 4px;")

    def _pick(self, key: str, button) -> None:
        colour = QColorDialog.getColor(QColor(self._colours[key]), self,
                                       "Choose a colour")
        if colour.isValid():
            self._colours[key] = colour.name()
            button.setStyleSheet(self._swatch(colour.name()))

    def options(self) -> dict:
        """What is set for the chosen kind, by option key."""
        out = {}
        for key, w in self._inputs.items():
            if isinstance(w, QComboBox):
                out[key] = w.currentData()
            elif isinstance(w, QLineEdit):
                out[key] = w.text().strip()
            else:
                out[key] = round(w.value(), 2)
        return out

    # ── The verb ─────────────────────────────────────────────────────────────

    def payload(self) -> dict:
        """What the map's tool for the chosen kind is handed."""
        kind = self.kind()
        opts = self.options()
        if kind.verb == yk.OBJECT:
            sd = _object_def(kind)
            sd["size_m"] = opts.get("size_m", sd.get("size_m"))
            return sd
        opts.update(self._colours if kind.key == "custom" else {})
        props = yk.drawn_props(kind.key, **opts)
        props.pop("element_type", None)
        if kind.verb == yk.LINE:
            props.setdefault("width_m", opts.get("width_m", 0.3))
            return props
        props.update({"label": "", "height_m": props.get("height_m", 0.0),
                      "kind_words": kind.words})
        props.update(self.placing())
        return props

    def placing(self) -> dict:
        """How the chosen area goes on the map: ``{"place": "outline"}``, or a
        rectangle's length and width, or a circle's width across, in metres."""
        if not self._shape:
            return {}
        place = self._shape["place"].currentData()
        out = {"place": place}
        if place == "rectangle":
            out["place_length_m"] = round(self._shape["length"].value(), 2)
            out["place_width_m"] = round(self._shape["width"].value(), 2)
        elif place == "circle":
            out["place_across_m"] = round(self._shape["across"].value(), 2)
        return out

    def _on_verb(self) -> None:
        kind = self.kind()
        if kind is None:
            return
        payload = self.payload()
        signal = {yk.AREA: self.draw_area_requested,
                  yk.LINE: self.draw_line_requested,
                  yk.OBJECT: self.place_object_requested}[kind.verb]
        signal.emit(payload)
