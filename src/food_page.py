"""
food_page.py — Design › Through the year: the design's year month by month,
who eats here when, and any animal looked up (V3.08; reordered V3.55, F270).

Design principle P10 — see docs/DESIGN_PHILOSOPHY.md.

The owner's "what it feeds" page, from the V3.05 surface audit (Analysis ›
Bees, Planning's Wildlife and Harvest calendars), and since V3.55 Over time's
*This month* too: one calendar, not two. Reviewing it, the owner: the month by
month "is far and away the most useful information", and "most people do not
know or aim to create a yard for a specific creature". So, top to bottom, in
the owner's order, and in the simple app:

  * **the year**: twelve months, each a line that opens to what is in flower,
    in fruit and to harvest (people kept apart and in their own colour), who is
    eating here, one thing to go and look at, and the month's jobs; this month
    open on arrival;
  * **caterpillars to birds**: the chickadee nest, in plain words;
  * **animals that depend on a few plants**, and whether the yard has one;
  * **look up any animal**: the old page's list, last. A bee keeps what the
    Bees page said (``bee_habitat``: tongue fit, nesting, its flight season);
    any other animal gets ``what_it_feeds.animal_plan``. *Show it on the map*
    greys every plant that does not feed it.

The arithmetic is ``src/through_the_year.py``, ``src/what_it_feeds.py`` and
``src/bee_habitat.py``; this only draws. The page fills itself when it is on
screen and the design changes (the Design tab's ``LiveRefresh``).
"""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QSizePolicy, QToolButton, QVBoxLayout, QWidget,
)

from src import through_the_year as year_of
from src import what_it_feeds as feeds

#: Tongue-fit chips for a bee's floral hosts (moved with the Bees page).
_FIT_CHIP = {
    "good":      ("#1b5e20", "#a5d6a7", "good fit"),
    "plausible": ("#33450f", "#dcedc8", "workable"),
    "unknown":   ("#37474f", "#b0bec5", "—"),
}

#: A month's lines, in order, each in its own colour: the foods, people last
#: of the three and in their own colour, then who eats, what to look at, jobs.
_FLOWER, _FRUIT, _PEOPLE = "#e6a5d0", "#ffcc80", "#80deea"
_WHO, _LOOK, _JOB = "#a5d6a7", "#ffe0b2", "#cfd8dc"

#: The page's headings, in reading order.
SECTIONS = ("The year, month by month", "Caterpillars to birds",
            "Animals that depend on a few plants", "Look up any animal")


def _month_cell(abbr: str, style: str) -> str:
    """One month of a strip. A label's rich text drops a span's padding and
    margin, so the strips read "MarAprMayJunJulAugSepOct" (V3.19, QF-7, R17):
    the room is spaces, inside the colour and between the months."""
    return f"<span style='{style}'>&nbsp;{abbr}&nbsp;</span>"


def _month_strip(cells: list) -> str:
    """The months on one line where they fit, and otherwise folded in half,
    never with one month alone on a line ("Dec" was, on a narrow panel: the
    V3.19 review of QF-7). Only the middle gap may break."""
    half = len(cells) // 2
    return "&nbsp;".join(cells[:half]) + " " + "&nbsp;".join(cells[half:])


_BODY_STYLE = ("color: #c8e6c9; font-size: 12px; padding: 8px; "
               "background: #1a2a1a; border: 1px solid #2e4a2e; "
               "border-radius: 4px;")
_HEAD_STYLE = ("color: #a5d6a7; font-size: 13px; font-weight: bold; "
               "padding: 10px 0 2px 0;")
_MUTED = "color: #90a4ae; font-size: 12px;"
_MONTH_STYLE = (
    "QToolButton { color: #c8e6c9; font-size: 12px; text-align: left; "
    "border: none; padding: 3px 2px; }"
    "QToolButton:checked { color: #e8f5e9; font-weight: bold; }"
    "QToolButton:hover { background: #1e2e1e; }")
_GAP_STYLE = _MONTH_STYLE.replace("color: #c8e6c9", "color: #ef9a9a")


def _esc(text: str) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


class FoodPage(QScrollArea):
    """Design › Through the year. ``warm_images`` fetches photographs off the
    UI thread (the Design tab's photo warmer); call :meth:`on_image_ready`
    when one lands."""

    map_overlay_requested = pyqtSignal(dict)   # {"bee": label, "styles": {pid: fit}}
    map_overlay_cleared = pyqtSignal()

    def __init__(self, warm_images=None, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._warm = warm_images
        self._warmed: set = set()
        self._placed: list = []
        self._plant_ids: list = []
        self._site = (None, None)
        self._plan = None            # the bee plan or the animal plan shown
        self._plan_is_bee = False
        self._fed: list = []
        self._catalogue = None       # the catalogue's animals, read once
        self._opened: set = set()    # the months a person opened or closed
        self._now = datetime.now().month
        # Until a person picks one, the look-up shows the animal the design
        # feeds most; after, it keeps theirs while the design changes.
        self._user_chose = False
        body = QWidget()
        self.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # ── The year ────────────────────────────────────────────────────────
        layout.addWidget(self._heading(SECTIONS[0]))
        self._summary_line = QLabel("")
        self._summary_line.setWordWrap(True)
        self._summary_line.setTextFormat(Qt.TextFormat.RichText)
        self._summary_line.setStyleSheet("color: #c8e6c9; font-size: 13px;")
        layout.addWidget(self._summary_line)
        self._months = []
        for m in range(1, 13):
            button = QToolButton()
            button.setCheckable(True)
            button.setAutoRaise(True)
            button.setToolButtonStyle(
                Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            button.setArrowType(Qt.ArrowType.RightArrow)
            button.setText(year_of.MONTHS[m - 1])
            button.setAccessibleName(year_of.MONTHS[m - 1])
            button.setSizePolicy(QSizePolicy.Policy.Expanding,
                                 QSizePolicy.Policy.Fixed)
            button.setStyleSheet(_MONTH_STYLE)
            text = QLabel("")
            text.setWordWrap(True)
            text.setTextFormat(Qt.TextFormat.RichText)
            text.setAlignment(Qt.AlignmentFlag.AlignTop)
            text.setStyleSheet(_BODY_STYLE)
            text.setVisible(False)
            button.toggled.connect(
                lambda on, m=m: self._on_month_toggled(m, on))
            layout.addWidget(button)
            layout.addWidget(text)
            self._months.append((button, text))
        self._near_note = QLabel("")
        self._near_note.setWordWrap(True)
        self._near_note.setStyleSheet(_MUTED + " font-style: italic;")
        layout.addWidget(self._near_note)

        # ── Caterpillars to birds ───────────────────────────────────────────
        layout.addWidget(self._heading(SECTIONS[1]))
        self._caterpillars = QLabel("")
        self._caterpillars.setWordWrap(True)
        self._caterpillars.setTextFormat(Qt.TextFormat.RichText)
        self._caterpillars.setStyleSheet(
            "color: #cfe3f0; font-size: 12px; padding: 8px; "
            "background: #12202a; border: 1px solid #1e4a5a; border-radius: 4px;")
        layout.addWidget(self._caterpillars)

        # ── Animals that depend on a few plants ─────────────────────────────
        layout.addWidget(self._heading(SECTIONS[2]))
        self._depends = QLabel("")
        self._depends.setWordWrap(True)
        self._depends.setTextFormat(Qt.TextFormat.RichText)
        self._depends.setStyleSheet(_BODY_STYLE)
        layout.addWidget(self._depends)

        # ── Look up any animal ──────────────────────────────────────────────
        layout.addWidget(self._heading(SECTIONS[3]))
        self._find = QLineEdit()
        self._find.setPlaceholderText("Find an animal…")
        self._find.setAccessibleName("Find an animal in the list")
        self._find.setClearButtonEnabled(True)
        self._find.textChanged.connect(self._chose)
        self._find.textChanged.connect(self._fill_animals)
        layout.addWidget(self._find)
        self._animal = QComboBox()
        self._animal.setAccessibleName("Animal to look at")
        self._animal.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self._animal.setMinimumContentsLength(18)
        self._animal.currentIndexChanged.connect(self._show_animal)
        self._animal.activated.connect(self._chose)
        layout.addWidget(self._animal)

        self._map_btn = QPushButton("🗺  Show it on the map")
        self._map_btn.setCheckable(True)
        self._map_btn.setToolTip("Grey every plant on the map that does not "
                                 "feed this animal")
        self._map_btn.toggled.connect(self._on_map_toggle)
        layout.addWidget(self._map_btn)

        summ = QHBoxLayout()
        summ.setSpacing(8)
        photo_col = QVBoxLayout()
        photo_col.setSpacing(2)
        self._photo = QLabel("🐝")
        self._photo.setFixedSize(96, 72)
        self._photo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._photo.setStyleSheet("border: 1px solid #2e4a2e; border-radius: 3px; "
                                  "background: #14241a; font-size: 30px;")
        photo_col.addWidget(self._photo)
        # Visible photo credit — required for CC-BY reuse (harmless for CC0).
        self._credit = QLabel("")
        self._credit.setFixedWidth(96)
        self._credit.setWordWrap(True)
        self._credit.setStyleSheet("color: #90a4ae; font-size: 12px;")
        self._credit.setVisible(False)
        photo_col.addWidget(self._credit)
        summ.addLayout(photo_col, 0)
        self._who = QLabel("")
        self._who.setWordWrap(True)
        self._who.setTextFormat(Qt.TextFormat.RichText)
        self._who.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._who.setStyleSheet("color: #c8e6c9; font-size: 12px;")
        summ.addWidget(self._who, 1)
        layout.addLayout(summ)

        self._plants_box = self._section(layout, "Plants that feed it")
        self._needs_box = self._section(layout, "What else it needs")
        self._when_box = self._section(layout, "When it finds food here")
        self._footnote = QLabel("")
        self._footnote.setWordWrap(True)
        self._footnote.setStyleSheet(
            "color: #90a4ae; font-size: 12px; font-style: italic;")
        layout.addWidget(self._footnote)
        layout.addStretch()
        self._fill_animals()

    # ── Building blocks ──────────────────────────────────────────────────────

    @staticmethod
    def _heading(text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(_HEAD_STYLE)
        return label

    def _section(self, layout, title: str) -> QLabel:
        head = QLabel(title)
        head.setStyleSheet("color: #a5d6a7; font-size: 12px; font-weight: "
                           "bold; padding: 4px 0 2px 0;")
        layout.addWidget(head)
        body = QLabel("")
        body.setWordWrap(True)
        body.setTextFormat(Qt.TextFormat.RichText)
        body.setAlignment(Qt.AlignmentFlag.AlignTop)
        body.setStyleSheet(_BODY_STYLE)
        layout.addWidget(body)
        body.heading = head
        return body

    # ── Inputs ───────────────────────────────────────────────────────────────

    def set_placed_plants(self, plants: list) -> None:
        """Remember the design's plants; :meth:`refresh` draws them."""
        self._placed = [p for p in plants or [] if p.get("plant_id") is not None]
        ids = []
        for p in self._placed:
            try:
                ids.append(int(p.get("plant_id")))
            except (TypeError, ValueError):
                pass
        self._plant_ids = sorted(set(ids))

    def set_site(self, lat, lng) -> None:
        """Where the yard is: who is eating here is read against the animals
        recorded near it (``fauna_fit``)."""
        self._site = (lat, lng)

    def _records(self):
        try:
            from src import fauna_fit
            return fauna_fit.for_point(*self._site)
        except Exception:                                  # noqa: BLE001
            return None

    def refresh(self) -> None:
        """Redraw everything against the current design."""
        try:
            self._fed = feeds.animals_fed(self._plant_ids)
        except Exception:                                  # noqa: BLE001
            self._fed = []
        records = self._records()
        self._fill_months(records)
        self._summary_line.setText(self._fed_summary())
        self._fill_stories(records)
        self._fill_animals()

    def _fed_summary(self) -> str:
        if not self._plant_ids:
            return "Place plants to see their year, and who they feed."
        lines = [f"<b>{_esc(self._flowering)}</b>"] if self._flowering else []
        food = [a for a in self._fed if a["food"]]
        if not food:
            lines.append("No animal is recorded feeding on these plants yet.")
            return "<br>".join(lines)
        counts: dict = {}
        for a in food:
            counts[a["taxon"]] = counts.get(a["taxon"], 0) + 1
        groups = ", ".join(feeds.group_words(t, counts[t])
                           for t, _o, _p in feeds.GROUPS if counts.get(t))
        # The Overview's and Habitat's count, in their words (V3.20, OV-5).
        lines.append(f"Your plants are {feeds.food_words(counts)}: {groups}.")
        return "<br>".join(lines)

    # ── The year ─────────────────────────────────────────────────────────────

    _flowering = ""

    def _fill_months(self, records=None):
        """The twelve months: a line each, opened to the month's detail. This
        month is open until a person opens or closes one, and in a quiet month
        the first one ahead with something in flower or fruit too: in
        November the page had opened on "resting"."""
        try:
            data = (year_of.year(self._placed, records=records)
                    if self._plant_ids else None)
        except Exception:                                  # noqa: BLE001
            data = None
        self._year = data
        self._photos = self._visitor_photos(data)
        self._flowering = (year_of.flowering_line(data["months"])
                           if data else "")
        ahead = year_of.next_active(data["months"], self._now) if data else 0
        for m, (button, text) in enumerate(self._months, start=1):
            name = year_of.MONTHS[m - 1]
            if data is None:
                button.setText(name)
                button.setAccessibleName(name)
                button.setStyleSheet(_MONTH_STYLE)
                text.setText("")
                button.setEnabled(False)
                self._open(m, False)
                continue
            month = data["months"][m - 1]
            now = " (this month)" if m == self._now else ""
            button.setText(f"{name}{now}: {year_of.summary(month)}")
            button.setAccessibleName(button.text())
            button.setStyleSheet(_GAP_STYLE if month["gap"] else _MONTH_STYLE)
            button.setEnabled(True)
            text.setText(self._month_html(month, self._photos))
            if not self._opened:
                self._open(m, m in (self._now, ahead))
        self._near_note.setText(
            "" if data is None else
            "Who is eating here: " + (year_of.NEAR_WORDS if data["near"]
                                      else year_of.FAR_WORDS).lower()
            + " The month is when the plant offers the food: its flowers, its "
              "fruit, or its leaves from May to September.")

    def _open(self, m: int, on: bool) -> None:
        button, text = self._months[m - 1]
        button.blockSignals(True)
        button.setChecked(on)
        button.blockSignals(False)
        button.setArrowType(Qt.ArrowType.DownArrow if on
                            else Qt.ArrowType.RightArrow)
        text.setVisible(on)

    def _on_month_toggled(self, m: int, on: bool) -> None:
        self._opened.add(m)
        self._open(m, on)

    _year = None
    _photos: dict = {}

    def _visitor_photos(self, data) -> dict:
        """``{fauna_id: (local path or "", credit)}`` for the animals the year
        names that have a photograph: drawn where it is cached, fetched off
        the UI thread where it is not (the page redraws when one lands)."""
        if not data:
            return {}
        fids = {v["fauna_id"] for m in data["months"] for v in m["visitors"]}
        if not fids:
            return {}
        try:
            from src.db.plants import get_connection
            from src.image_cache import credit_line, get_cached_image
            conn = get_connection()
            try:
                ph = ",".join("?" * len(fids))
                rows = conn.execute(
                    f"SELECT id, image_url, image_attribution, image_license "
                    f"FROM fauna WHERE id IN ({ph}) AND image_url != ''",
                    sorted(fids)).fetchall()
            finally:
                conn.close()
        except Exception:                                  # noqa: BLE001
            return {}
        out, want = {}, []
        for r in rows:
            url = r["image_url"]
            path = get_cached_image(url) or ""
            out[r["id"]] = (path, credit_line(r["image_attribution"] or "",
                                              r["image_license"] or ""))
            if not path and url not in self._warmed and self._warm:
                self._warmed.add(url)
                want.append((url, r["image_attribution"] or "",
                             r["image_license"] or ""))
        if want:
            self._warm(want)
        return out

    @staticmethod
    def _visitor_html(v: dict, photos: dict) -> str:
        """One line of who is eating here, with the animal's photograph and
        its credit where it has one (a credit is the licence's condition)."""
        path, credit = photos.get(v.get("fauna_id"), ("", ""))
        if not path:
            return (f"<div style='padding:0 0 0 10px;'>• "
                    f"{_esc(v['line'])}</div>")
        from PyQt6.QtCore import QUrl
        src = QUrl.fromLocalFile(path).toString()
        return (f"<table cellspacing='0' cellpadding='2' style='margin-left:8px;'>"
                f"<tr><td valign='top'><img src='{src}' width='44' height='33'>"
                f"</td><td valign='top'>{_esc(v['line'])}<br>"
                f"<span style='color:#90a4ae;'>{_esc(credit)}</span></td></tr>"
                f"</table>")

    @staticmethod
    def _month_html(month: dict, photos: dict = None) -> str:
        def row(colour, label, body):
            return (f"<div style='padding:1px 0;'><b style='color:{colour}'>"
                    f"{label}</b> {body}</div>")
        parts = []
        if month["flowering"]:
            parts.append(row(_FLOWER, "In flower:",
                             _esc(", ".join(month["flowering"]))))
        if month["fruit"]:
            parts.append(row(_FRUIT, "In fruit:",
                             _esc(", ".join(month["fruit"]))))
        if month["harvest"]:
            parts.append(row(_PEOPLE, "For you to harvest:", _esc(", ".join(
                f"{name} ({part})" for name, part in month["harvest"]))))
        if month["gap"]:
            parts.append("<div style='color:#ef9a9a; padding:1px 0;'>Nothing "
                         "in flower: a plant that flowers now would fill the "
                         "gap.</div>")
        if month["visitors"]:
            parts.append(row(_WHO, "Who is eating here:", "") + "".join(
                FoodPage._visitor_html(v, photos or {})
                for v in month["visitors"]))
        if month["look"]:
            parts.append(row(_LOOK, "Go and look:", _esc(month["look"])))
        if month["jobs"]:
            parts.append(row(_JOB, "Jobs:", _esc("; ".join(month["jobs"]))))
        return "".join(parts) or "<i>Nothing recorded this month.</i>"

    # ── The two stories ──────────────────────────────────────────────────────

    def _fill_stories(self, records=None):
        if not self._plant_ids:
            self._caterpillars.setText(
                f"<i>{_esc(year_of.CATERPILLAR_WHY)}</i> Place plants to see "
                f"whether yours could feed a nest.")
            self._depends.setText("<i>Place plants to see which of these "
                                  "animals your yard serves.</i>")
            return
        try:
            c = year_of.caterpillars(self._placed)
        except Exception:                                  # noqa: BLE001
            c = None
        if c is not None:
            self._caterpillars.setText(
                f"<b>{_esc(c['headline'])}</b><br>{_esc(year_of.CATERPILLAR_WHY)}"
                f"<br>{_esc(c['line'])}<div style='color:#90a4ae; "
                f"padding-top:4px;'>A rough estimate from the caterpillars "
                f"recorded on each plant. Sources: "
                f"{_esc(year_of.CATERPILLAR_SOURCE)}.</div>")
        try:
            d = year_of.depends(self._plant_ids, records=records)
        except Exception:                                  # noqa: BLE001
            d = {"served": [], "missing": []}
        rows = []
        if d["served"]:
            rows.append("<b>Fed here:</b>")
            rows += [f"• {_esc(r['line'])}" for r in d["served"]]
        else:
            rows.append("<i>None of these animals is fed here yet.</i>")
        if d["missing"]:
            rows.append("<br><b>Not here yet:</b>")
            rows += [f"• {_esc(r['line'])}" for r in d["missing"]]
        rows.append("<span style='color:#90a4ae;'>Only animals the records "
                    "say depend on a few plants; most animals have many.</span>")
        self._depends.setText("".join(
            f"<div style='padding:1px 0;'>{r}</div>" for r in rows))

    # ── The animal list ──────────────────────────────────────────────────────

    def _entries(self) -> list:
        """``[(header, [(label, data)])]``: the design's animals first, then
        the catalogue (read once: it does not change while the app runs)."""
        out = []
        food = [a for a in self._fed if a["food"]]
        if food:
            out.append(("Fed by your design", [
                (f"{a['name']} · {len(a['plants'])} "
                 f"plant{'s' if len(a['plants']) != 1 else ''}",
                 {"fid": a["fauna_id"], "taxon": a["taxon"]})
                for a in food]))
        if self._catalogue is None:
            self._catalogue = self._catalogue_entries()
        return out + self._catalogue

    @staticmethod
    def _catalogue_entries() -> list:
        """Bees by genus (as the Bees page listed them), then each other
        group by name."""
        out = []
        try:
            from src.bee_habitat import list_target_bees
            bees = list_target_bees()
        except Exception:                                  # noqa: BLE001
            bees = []
        genus, rows = None, []
        for b in bees:
            if b["genus"] != genus:
                if rows:
                    out.append((f"Bees: {genus}", rows))
                genus, rows = b["genus"], []
            if b["is_group"]:
                label = f"{b['common_name']} (any {b['genus']})"
            elif b["common_name"] == b["scientific_name"]:
                label = b["scientific_name"]       # no English name (V3.05)
            else:
                label = f"{b['common_name']} · {b['scientific_name']}"
            rows.append((label, {"fid": b["id"], "taxon": "bee"}))
        if rows:
            out.append((f"Bees: {genus}", rows))
        try:
            from src.db.fauna import list_fauna
            for taxon, _one, plural in feeds.GROUPS:
                if taxon == "bee":
                    continue
                animals = sorted(list_fauna(taxon),
                                 key=lambda f: f["common_name"].lower())
                if animals:
                    out.append((plural.capitalize(), [
                        (f["common_name"], {"fid": f["id"], "taxon": taxon})
                        for f in animals]))
        except Exception:                                  # noqa: BLE001
            pass
        return out

    def _chose(self, *_):
        self._user_chose = True

    def _fill_animals(self, *_):
        """(Re)fill the list, narrowed by the find box, keeping the animal a
        person chose while it is still listed; else the first one, which is
        the animal the design feeds most."""
        current = self._animal.currentData() if self._user_chose else None
        words = self._find.text().strip().lower()
        combo = self._animal
        combo.blockSignals(True)
        combo.clear()
        for header, rows in self._entries():
            if words:
                rows = [r for r in rows if words in r[0].lower()]
            if not rows:
                continue
            combo.addItem(f"── {header} ──", None)
            item = combo.model().item(combo.count() - 1)
            if item is not None:
                item.setEnabled(False)
            for label, data in rows:
                combo.addItem(f"    {label}", data)
        chosen = -1
        for i in range(combo.count()):
            data = combo.itemData(i)
            if data is None:
                continue
            if chosen < 0:
                chosen = i
            if current and data == current:
                chosen = i
                break
        combo.blockSignals(False)
        if chosen >= 0:
            combo.setCurrentIndex(chosen)
        self._show_animal()

    # ── One animal ───────────────────────────────────────────────────────────

    def _show_animal(self, *_):
        data = self._animal.currentData()
        if not data:
            self._plan = None
            self._who.setText("<i>No animal matches.</i>"
                              if self._find.text().strip() else "")
            for box in (self._plants_box, self._needs_box, self._when_box):
                box.setText("—")
            self._footnote.setText("")
            return
        if data["taxon"] == "bee":
            self._show_bee(data["fid"])
        else:
            self._show_other(data["fid"])
        self._render_photo()
        if self._map_btn.isChecked():
            self.map_overlay_requested.emit(self._map_payload())

    def _show_bee(self, fid: int):
        try:
            from src.bee_habitat import build_bee_habitat_plan
            plan = build_bee_habitat_plan(fid, plant_ids=self._plant_ids)
        except Exception:                                  # noqa: BLE001
            plan = None
        self._plan, self._plan_is_bee = plan, True
        if plan is None:
            self._who.setText("<i>No data for this bee yet.</i>")
            for box in (self._plants_box, self._needs_box, self._when_box):
                box.setText("—")
            self._footnote.setText("")
            return
        self._needs_box.heading.setText("Nesting: give it a place to live")
        self._when_box.heading.setText("Food across its flight season")
        self._who.setText(self._bee_summary(plan))
        self._plants_box.setText(self._bee_floral(plan))
        self._needs_box.setText(self._bee_nesting(plan))
        self._when_box.setText(self._bee_forage(plan))
        conf = {"documented": "well-documented", "partial": "partly documented",
                "thin": "sparse"}.get(plan.data_confidence, plan.data_confidence)
        self._footnote.setText(
            f"Data confidence: {conf}. Floral matches shown as documented "
            f"(plant↔bee records) or inferred (genus-level hosts)."
            + self._sources((plan.attrs or {}).get("source")))

    def _show_other(self, fid: int):
        try:
            plan = feeds.animal_plan(fid, self._plant_ids)
        except Exception:                                  # noqa: BLE001
            plan = {}
        self._plan, self._plan_is_bee = plan or None, False
        if not plan:
            self._who.setText("<i>No data for this animal yet.</i>")
            for box in (self._plants_box, self._needs_box, self._when_box):
                box.setText("—")
            self._footnote.setText("")
            return
        f = plan["fauna"]
        self._needs_box.heading.setText("What else it needs")
        self._when_box.heading.setText("When it finds food here")
        bits = [f"<b>{f['common_name']}</b> <span style='color:#90a4ae;'>"
                f"<i>{f['scientific_name']}</i></span>"]
        if f.get("description"):
            bits.append(f"<span style='color:#c8e6c9;'>{f['description']}</span>")
        self._who.setText("<br>".join(bits))
        self._plants_box.setText(self._other_plants(plan))
        self._needs_box.setText(self._other_needs(plan))
        self._when_box.setText(self._months_strip(plan))
        self._footnote.setText(
            "When is read off the plants: flowers for nectar and pollen, fruit "
            "for fruit and seed, leaves (May to September) for larvae that eat "
            "the plant.")

    @staticmethod
    def _sources(source) -> str:
        """The works a bee's facts come from, by name as the website gives
        them (``citations.format_sources``, short form): the footnote printed
        the database keys, "anbc_alberta_native_bees,sheffield_et_al_2014_…"
        (V3.19, QF-7, R17). A placeholder names no work and is left out, as
        the 3D window's dossier leaves it out."""
        from src.citations import format_sources, is_placeholder
        keys = [k.strip() for k in (source or "").split(",") if k.strip()]
        named = format_sources(
            ",".join(k for k in keys if not is_placeholder(k)), short=True)
        return f" Sources: {named}." if named else ""

    @staticmethod
    def _kinds(kinds, taxon: str = "") -> str:
        return ", ".join(feeds.kind_words(k, taxon) for k in kinds)

    def _other_plants(self, plan) -> str:
        taxon = plan["fauna"].get("taxon") or ""
        rows = []
        if plan["here"]:
            rows.append("<b>In your design:</b>")
            rows += [f"★ {e['name']} <span style='color:#90a4ae;'>· "
                     f"{self._kinds(e['kinds'], taxon)}</span>"
                     for e in plan["here"]]
        if plan["elsewhere"]:
            more = plan["elsewhere_total"] - len(plan["elsewhere"])
            rows.append("<br><b>Would feed it too:</b>" if plan["here"]
                        else "<b>Plants that would feed it:</b>")
            rows += [f"{e['name']} <span style='color:#90a4ae;'>· "
                     f"{self._kinds(e['kinds'], taxon)}</span>"
                     for e in plan["elsewhere"]]
            if more > 0:
                rows.append(f"<span style='color:#90a4ae;'>and {more} more in "
                            f"the catalogue</span>")
        if not rows:
            return ("<i>No plant in the catalogue is recorded feeding it: a "
                    "gap in what is known, more often than a fact about it.</i>")
        return "".join(f"<div style='padding:1px 0;'>{r}</div>" for r in rows)

    @staticmethod
    def _other_needs(plan) -> str:
        if plan.get("no_host"):
            return ("<b>A caterpillar host.</b> Nothing in your design feeds its "
                    "caterpillars; the plants listed as a caterpillar host "
                    "above would.")
        if not plan["here"]:
            return "Nothing in your design serves it yet."
        return "<i>Nothing more is recorded.</i>"

    @staticmethod
    def _months_strip(plan) -> str:
        here = set(plan["months_here"])
        cells = []
        for m in range(1, 13):
            abbr = feeds.MONTH_ABBR[m - 1]
            style = ("background:#1b5e20; color:#c8e6c9; border-radius:3px;"
                     if m in here else "color:#5f7a6a;")
            cells.append(_month_cell(abbr, style))
        if not plan["here"]:
            note = "Nothing in your design feeds it yet."
        elif plan["gaps"]:
            note = (f"Growing-season months with nothing for it here: "
                    f"{feeds.span(plan['gaps'])}.")
        else:
            note = "Something for it all through the growing season."
        return _month_strip(cells) + f"<div style='padding-top:4px;'>{note}</div>"

    # ── A bee (the Bees page's renderers, moved in V3.08) ────────────────────

    @staticmethod
    def _bee_summary(plan) -> str:
        bee = plan.bee or {}
        a = plan.attrs or {}
        tongue = a.get("tongue_length")
        season = a.get("flight_season")
        cons = a.get("conservation_status")
        bits = [f"<b>{bee.get('common_name', '')}</b> <span style='color:#90a4ae;'>"
                f"<i>{bee.get('scientific_name', '')}</i></span>"]
        facts = []
        if tongue and tongue != "unknown":
            facts.append(f"{tongue}-tongued")
        elif tongue == "unknown":
            facts.append("tongue not characterised")
        if season:
            facts.append(f"flies {season}")
        if facts:
            bits.append("<span style='color:#a5d6a7;'>" + " · ".join(facts)
                        + "</span>")
        if cons:
            colour = "#ff8a65" if "risk" in cons.lower() else "#90a4ae"
            bits.append(f"<span style='color:{colour};'>{cons}</span>")
        if bee.get("description"):
            bits.append(f"<span style='color:#c8e6c9;'>{bee['description']}</span>")
        return "<br>".join(bits)

    @staticmethod
    def _bee_match_row(m) -> str:
        bg, fg, txt = _FIT_CHIP.get(m.tongue_form_fit, _FIT_CHIP["unknown"])
        chip = (f"<span style='background:{bg}; color:{fg}; border-radius:3px; "
                f"padding:0 4px; font-size:12px;'>{txt}</span>"
                if txt != "—" else "")     # a pill saying "—" says nothing (V3.05)
        bloom = (f" <span style='color:#90a4ae;'>· {m.bloom_period}</span>"
                 if m.bloom_period else "")
        basis = ("" if m.confidence == "documented" else
                 " <span style='color:#90a4ae; font-size:12px;'>(genus match)</span>")
        star = "★ " if m.in_users_list else ""
        return f"{star}{m.common_name} {chip}{bloom}{basis}"

    def _bee_floral(self, plan) -> str:
        matches = plan.floral_matches or []
        if not matches:
            return ("<i>No floral-host plants matched — this is often a cuckoo "
                    "bee that feeds itself by parasitising a host bee (see "
                    "Nesting).</i>")
        in_design = [m for m in matches if m.in_users_list]
        rows = []
        if in_design:
            rows.append("<b>In your design:</b>")
            rows += [self._bee_match_row(m) for m in in_design[:12]]
            rows.append("<br><b>Also good to add:</b>")
            others = [m for m in matches if not m.in_users_list]
        else:
            rows.append("<b>Plants that feed this bee:</b>")
            others = matches
        rows += [self._bee_match_row(m) for m in others[:14]]
        return "".join(f"<div style='padding:1px 0;'>{r}</div>" for r in rows)

    @staticmethod
    def _bee_nesting(plan) -> str:
        g = plan.nesting
        parts = [f"<b>{g.headline}</b>"]
        if g.structures:
            names = ", ".join(s.get("name", "") for s in g.structures)
            parts.append(f"<span style='color:#a5d6a7;'>Structures: {names}</span>")
        parts += [f"• {a}" for a in g.actions]
        return "".join(f"<div style='padding:1px 0;'>{p}</div>" for p in parts)

    @staticmethod
    def _bee_forage(plan) -> str:
        f = plan.forage
        if not f.flight_months:
            return f"<i>{f.note}</i>"
        flight, covered = set(f.flight_months), set(f.covered_months)
        cells = []
        for mo in range(3, 11):    # Mar–Oct strip
            abbr = feeds.MONTH_ABBR[mo - 1]
            if mo not in flight:
                style = "color:#5f7a6a;"
            elif mo in covered:
                style = "background:#1b5e20; color:#c8e6c9; border-radius:3px;"
            else:
                style = "background:#5d3a1a; color:#ffcc80; border-radius:3px;"
            cells.append(_month_cell(abbr, style))
        legend = ("<div style='color:#90a4ae; font-size:12px; padding-top:4px;'>"
                  "green = a plant in bloom for it · orange = flying but no "
                  "bloom (a gap to fill)</div>")
        sug = ""
        if f.suggestions:
            names = ", ".join(s.common_name for s in f.suggestions[:6])
            sug = (f"<div style='padding-top:4px; color:#a5d6a7;'>"
                   f"Fill the gap with: {names}</div>")
        return (_month_strip(cells) + f"<div style='padding-top:4px;'>{f.note}</div>"
                + legend + sug)

    # ── The photograph ───────────────────────────────────────────────────────

    def _animal_row(self) -> dict:
        if self._plan is None:
            return {}
        if self._plan_is_bee:
            return self._plan.bee or {}
        fid = self._plan["fauna"]["id"]
        try:
            from src.db.fauna import get_fauna
            return get_fauna(fid) or {}
        except Exception:                                  # noqa: BLE001
            return {}

    def on_image_ready(self) -> None:
        """A photograph finished downloading: draw it if it is this one, and
        any the year's months name."""
        self._render_photo()
        if self._year:
            self._photos = self._visitor_photos(self._year)
            for month, (_b, text) in zip(self._year["months"], self._months):
                text.setText(self._month_html(month, self._photos))

    def _render_photo(self):
        row = self._animal_row()
        icon = "🐝" if self._plan_is_bee else (row.get("icon") or "🐾")
        url = row.get("image_url") or ""
        path = None
        if url:
            try:
                from src.image_cache import get_cached_image
                path = get_cached_image(url)
            except Exception:                              # noqa: BLE001
                path = None
        pm = QPixmap(path) if path else QPixmap()
        if not pm.isNull():
            self._photo.setText("")
            self._photo.setScaledContents(True)
            self._photo.setPixmap(pm)
            from src.image_cache import credit_line
            text = credit_line(row.get("image_attribution", ""),
                               row.get("image_license", ""))
            self._credit.setText(text or "")
            self._credit.setVisible(bool(text))
            return
        self._photo.setPixmap(QPixmap())
        self._photo.setText(icon)
        self._credit.setVisible(False)
        if url and url not in self._warmed and self._warm is not None:
            self._warmed.add(url)
            self._warm([(url, row.get("image_attribution", ""),
                         row.get("image_license", ""))])

    # ── The map ──────────────────────────────────────────────────────────────

    def _map_payload(self) -> dict:
        """``{bee: label, styles: {pid: fit}}``, the map's forage view: a bee's
        floral hosts graded by tongue fit, any other animal's plants as hosts."""
        styles = {}
        label = ""
        if self._plan is not None and self._plan_is_bee:
            for m in self._plan.floral_matches:
                styles[str(m.plant_id)] = (m.tongue_form_fit if m.tongue_form_fit
                                           in ("good", "plausible") else "host")
            label = (self._plan.bee or {}).get("common_name", "")
        elif self._plan:
            for e in self._plan["here"] + self._plan["elsewhere"]:
                styles[str(e["plant_id"])] = "host"
            label = self._plan["fauna"]["common_name"]
        return {"bee": label, "styles": styles}

    def _on_map_toggle(self, on: bool):
        if on and self._plan is not None:
            self.map_overlay_requested.emit(self._map_payload())
        else:
            self.map_overlay_cleared.emit()
