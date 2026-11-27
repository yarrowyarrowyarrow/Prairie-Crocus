#!/usr/bin/env python3
"""
scripts/render_structures.py — every placeable structure through the real 3D
viewer, and each beside the shape that draws the same thing (V3.69).

    python scripts/render_structures.py --out /tmp/structures

Writes four contact sheets:

* ``models.jpg``: the fifteen structures of Placement › Structures, each on its
  own patch of lawn at its catalogue size, seen from a person's height.
* ``map.jpg``: the same structures from above, each over the footprint the 2D
  map draws for it (magenta, computed exactly as ``html/map/05-features.js``
  ``placeStructureOnMap`` draws it), so where the map and the 3D disagree shows.
* ``twins.jpg``: a structure beside the drawn shape or line that names the same
  thing (Pond and Water Feature, Fence / Wall and the Fence line, Native Lawn
  Patch and Lawn Area, Raised Bed and Garden Bed), in July and in January, plus
  a raised bed resized as the Size box allows and a Garden Bed given a height.
* ``shapes.jpg``: every area and line kind Draw › Shape offers, in July and
  January.

``--readers`` prints, without a browser, what the habitat score, the
Overview, Plan My Yard, the Water page, the shade model, the pond planting and
the 3D scene each make of a structure and of its drawn twin.

**Why it exists.** V3.43 put "the structure models" under *works, keep*, and the
plant models have been read against photographs four times since, but no one had
looked at the structures until a tester said a raised bed "does not appear the
same way in the 3D view" (``docs/USER_FEEDBACK.md``, the fourth tester, item
17). The V3.69 review read these sheets; run it again after any change to a
structure's model, its placement or the shapes, and lay the sheets side by side.

It uses a throwaway database, never touches your designs, and does not reach the
internet. It needs a Chromium or Chrome binary (``CHROME=``) and takes a few
minutes: software drawing changes light and edges, not shapes or sizes. Dev
tool: nothing in ``src/`` imports it.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.render_yard import (  # noqa: E402
    HTML, Server, find_chromium, images, run_probe, use_throwaway_database,
)

LAT0, LNG0 = 53.5232, -113.5263
KX = 111320 * math.cos(math.radians(LAT0))
KY = 111320.0

#: The structures in the panel's order (``structure_panel.STRUCTURE_GROUPS``),
#: each with a camera: (distance, camera height, look-at height) in metres.
CAMERAS = {
    "pond": (9.5, 3.6, 0.0), "brush_pile": (5.0, 1.7, 0.5),
    "bee_hotel": (2.6, 1.5, 1.0), "native_bee_log": (2.6, 1.2, 0.2),
    "snag": (6.5, 1.7, 1.8), "rock_xeriscape": (5.5, 2.2, 0.2),
    "rain_garden": (7.0, 2.8, 0.0), "rain_barrel": (2.8, 1.5, 0.6),
    "swale": (12.0, 3.6, 0.0), "raised_bed": (5.0, 2.2, 0.2),
    "compost_bin": (3.8, 1.8, 0.5), "shed": (7.5, 1.7, 1.3),
    "fence": (7.0, 1.7, 0.6), "fire_pit": (4.0, 1.9, 0.1),
    "native_lawn_patch": (8.5, 3.0, 0.0),
}
ORDER = ("pond", "brush_pile", "bee_hotel", "native_bee_log", "snag",
         "rock_xeriscape", "rain_garden", "rain_barrel", "swale",
         "raised_bed", "compost_bin", "shed", "fence", "fire_pit",
         "native_lawn_patch")
CELL = 16.0              # metres between structures: none in another's frame
COLS = 5
MAGENTA = "#ff00ff"


def _ll(east: float, north: float) -> list:
    return [LNG0 + east / KX, LAT0 + north / KY]


def _ring(points) -> list:
    ring = [_ll(e, n) for e, n in points]
    return ring + [ring[0]]


def _rect(cx, cy, along_ns, along_ew) -> list:
    hn, he = along_ns / 2.0, along_ew / 2.0
    return _ring(((cx - he, cy - hn), (cx + he, cy - hn),
                  (cx + he, cy + hn), (cx - he, cy + hn)))


def _ellipse(cx, cy, ew, ns, n=36) -> list:
    return _ring([(cx + ew / 2 * math.cos(t), cy + ns / 2 * math.sin(t))
                  for t in (i / n * math.tau for i in range(n))])


def _boundary_feature(w, d) -> dict:
    return {"type": "Feature",
            "geometry": {"type": "Polygon",
                         "coordinates": [_ring(((0, 0), (w, 0), (w, d),
                                                (0, d)))]},
            "properties": {"element_type": "property_boundary",
                           "boundary_id": "b1"}}


def structure(sid: str, east: float, north: float, size_m=None) -> dict:
    """A structure as Placement › Structures stores it
    (``map_events._on_structure_placed``)."""
    from src.db.structures import get_structure
    sd = dict(get_structure(sid))
    if size_m is not None:
        sd["size_m"] = float(size_m)
    lng, lat = _ll(east, north)
    return {"type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lng, lat]},
            "properties": {"element_type": "structure", "struct_id": sid,
                           "name": sd["name"], "size_m": sd["size_m"],
                           "struct_def": sd}}


def map_footprint(sid: str, east: float, north: float, size_m=None) -> dict:
    """What the 2D map draws for a structure, as a flat magenta shape:
    ``placeStructureOnMap`` draws a circle of ``size_m`` for a circle or an
    ellipse, and otherwise a rectangle ``size_m`` north-south by ``width_m``
    east-west."""
    from src.db.structures import get_structure
    sd = get_structure(sid)
    size = float(size_m if size_m is not None else sd["size_m"])
    if sd.get("shape") in ("circle", "ellipse"):
        ring = _ellipse(east, north, size, size)
    else:
        ring = _rect(east, north, size, float(sd.get("width_m") or size))
    return shape("Custom", ring, fill=MAGENTA)


def shape(kind: str, ring: list, *, fill: str = "", height_m: float = 0.0,
          label: str = "") -> dict:
    """A drawn area, as Draw › Shape stores it (``_on_shape_complete``): a
    height makes it a shade-casting ``canopy_footprint``."""
    props = {"element_type": "canopy_footprint" if height_m > 0
             else "custom_shape", "shape_type": kind, "label": label or kind,
             "fill_color": fill or "#4caf50", "fill_opacity": 0.3}
    if height_m > 0:
        props.update(height_m=float(height_m), cast_shade=True,
                     canopy_radius_m=2.0)
    return {"type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [ring]},
            "properties": props}


def line(style: str, points, width_m: float = 1.5) -> dict:
    """A hedge or fence line, as Draw › Shape stores one."""
    return {"type": "Feature",
            "geometry": {"type": "LineString",
                         "coordinates": [_ll(e, n) for e, n in points]},
            "properties": {"element_type": "hedgerow", "style": style,
                           "species": "", "width_m": width_m,
                           "spacing_m": 1.0, "color": "#4caf50"}}


def _project(name: str, features: list, w: float, d: float) -> dict:
    from src.project import new_project
    p = new_project(name)
    p["features"] = [_boundary_feature(w, d)] + features
    p.setdefault("properties", {})["site_config"] = {
        "latitude": LAT0 + d / 2 / KY, "longitude": LNG0 + w / 2 / KX}
    return p


def cell(i: int) -> tuple:
    return (CELL / 2 + (i % COLS) * CELL,
            CELL / 2 + (i // COLS) * CELL)


def models_lot(with_map: bool) -> dict:
    feats = []
    for i, sid in enumerate(ORDER):
        e, n = cell(i)
        if with_map:
            feats.append(map_footprint(sid, e, n))
        feats.append(structure(sid, e, n))
    rows = math.ceil(len(ORDER) / COLS)
    return _project("Structures", feats, COLS * CELL, rows * CELL)


#: The twins: (tag, what is there, caption). Positions in a 3 x 3 grid of 16 m.
def twins_lot() -> tuple:
    f, at = [], {}

    def put(tag, e, n, *features):
        at[tag] = (e, n)
        f.extend(features)

    # Pond (structure) and Water Feature (a drawn 6 x 4 m pool).
    put("pond", 6, 8, structure("pond", 6, 8))
    put("water", 20, 8, shape("Water Feature", _ellipse(20, 8, 6.0, 4.0)))
    # Fence / Wall (structure, 5 m) and a Fence line drawn 5 m north-south, as
    # the map draws the structure.
    put("fence_s", 34, 8, structure("fence", 34, 8))
    put("fence_l", 44, 8, line("fence", ((44, 5.5), (44, 10.5))))
    # Native Lawn Patch (structure, 6 x 4) and a Lawn Area drawn 6 x 4.
    put("patch", 6, 24, structure("native_lawn_patch", 6, 24))
    put("lawn", 20, 24, shape("Lawn Area", _rect(20, 24, 6.0, 4.0)))
    # Raised Bed (structure, 3 x 1.2) and a Garden Bed drawn 3 x 1.2, and the
    # same bed given a height, which is how a person might try for a raised bed.
    put("raised", 34, 24, structure("raised_bed", 34, 24))
    put("bed", 42, 24, shape("Garden Bed", _rect(42, 24, 3.0, 1.2)))
    put("bed_h", 48, 24, shape("Garden Bed", _rect(48, 24, 3.0, 1.2),
                               height_m=0.45, label="Raised bed"))
    # A raised bed resized to 6 m in the Size box, over its map footprint, and
    # a 20 m Fence / Wall.
    put("raised6", 10, 40, map_footprint("raised_bed", 10, 40, 6.0),
        structure("raised_bed", 10, 40, 6.0))
    put("fence20", 34, 40, map_footprint("fence", 34, 40, 20.0),
        structure("fence", 34, 40, 20.0))
    return _project("Twins", f, 56, 50), at


#: Draw › Shape's areas, two rows left to right, each 4 m east-west by 3 m
#: north-south, and its four lines, 6 m each, east-west.
SHAPE_ROWS = (("Garden Bed", "Mulch Area", "Pathway", "Patio / Deck",
               "Water Feature"),
              ("Lawn — to convert", "Restoration — Year 1",
               "Restoration — Year 3", "Established native", "Custom"))
LINE_STYLES = ("fence", "hedge", "living_fence", "windbreak")


def shapes_lot() -> tuple:
    """Every area kind and every line kind, as a person draws them. The
    outline is a meadow-free lot: its inside is lawn, so a Lawn Area would
    not show and is left out (it is on the twins sheet)."""
    f, rows = [], []
    for r, kinds in enumerate(SHAPE_ROWS):
        n = 6.0 + r * 9.0
        for i, kind in enumerate(kinds):
            e = 5.0 + i * 6.0
            f.append(shape(kind, _rect(e, n, 3.0, 4.0),
                           fill="#c48bd6" if kind == "Custom" else ""))
        rows.append((5.0 + 2 * 6.0, n))
    for i, style in enumerate(LINE_STYLES):
        n = 26.0 + i * 4.0
        f.append(line(style, ((8.0, n), (14.0, n))))
    lines_at = (11.0, 26.0 + 1.5 * 4.0)
    return _project("Shapes", f, 34, 42), rows, lines_at


def scene(project: dict, month: int = 7, hour: int = 14) -> dict:
    from src.scene_contract import build_scene
    return build_scene(project, year=0, when=datetime(2025, month, 21, hour))


def to_viewer(sc_xy: tuple) -> tuple:
    """Scene metres (+x east, +y north) → the viewer's (x, z)."""
    return sc_xy[0], -sc_xy[1]


def oblique(x, y, dist, cam_h, look_h, bearing_deg=150.0) -> dict:
    """A camera ``dist`` metres from (x, y) toward ``bearing_deg`` (from
    north, clockwise: 150 is south-south-east), looking back at it."""
    b = math.radians(bearing_deg)
    cx, cy = x + math.sin(b) * dist, y + math.cos(b) * dist
    vx, vz = to_viewer((cx, cy))
    tx, tz = to_viewer((x, y))
    return {"at": [round(vx, 2), cam_h, round(vz, 2)],
            "looks_at": [round(tx, 2), look_h, round(tz, 2)]}


def above(x, y, span) -> dict:
    vx, vz = to_viewer((x, y))
    return {"at": [round(vx, 2), round(span * 1.15, 2), round(vz + 0.01, 2)],
            "looks_at": [round(vx, 2), 0.0, round(vz, 2)]}


def _names() -> dict:
    from src.db.structures import get_structure
    return {sid: get_structure(sid)["name"] for sid in ORDER}


def _size_words(sid: str) -> str:
    from src.db.structures import get_structure
    sd = get_structure(sid)
    if sd.get("width_m"):
        return f"{sd['size_m']:g} x {sd['width_m']:g} m"
    return f"{sd['size_m']:g} m across"


def build_job(width: int, height: int) -> tuple:
    routes, shots, sheets = {}, [], []
    names = _names()

    sc_models = scene(models_lot(False))
    sc_map = scene(models_lot(True))
    routes["/__s/models.json"] = sc_models
    routes["/__s/map.json"] = sc_map
    # Where each one stands, from the lot's own layout and the scene's origin
    # (the boundary starts at the lot's corner): since V3.70 a Fence / Wall is
    # a fence line, not an entry in the scene's structures.
    ox, oy = sc_models["boundary"][0]
    where = {sid: (cell(i)[0] + ox, cell(i)[1] + oy)
             for i, sid in enumerate(ORDER)}

    model_tiles, map_tiles = [], []
    for sid in ORDER:
        x, y = where[sid]
        d, h, t = CAMERAS[sid]
        shots.append({"name": f"m_{sid}", "scene": "/__s/models.json",
                      "view": oblique(x, y, d, h, t)})
        model_tiles.append({"shot": f"m_{sid}",
                            "caption": f"{names[sid]} ({_size_words(sid)})"})
        from src.db.structures import get_structure
        span = max(4.0, get_structure(sid)["size_m"] * 1.6)
        shots.append({"name": f"p_{sid}", "scene": "/__s/map.json",
                      "view": above(x, y, span)})
        map_tiles.append({"shot": f"p_{sid}",
                          "caption": f"{names[sid]}: from above, north up, "
                                     f"over the map's footprint (magenta)"})
    sheets.append({"name": "models", "tiles": model_tiles,
                   "title": "Placement › Structures in 3D, at catalogue size",
                   "sub": "Each on lawn, fifth summer, July, 2 pm, from a "
                          "person's height. Drawn in software."})
    sheets.append({"name": "map", "tiles": map_tiles,
                   "title": "The map's footprint (magenta) under the 3D model",
                   "sub": "From above, north at the top. The map draws the "
                          "magenta shape; the 3D draws the model."})

    twins, at = twins_lot()
    routes["/__s/twins_jul.json"] = jul = scene(twins, 7, 14)
    routes["/__s/twins_jan.json"] = scene(twins, 1, 12)
    # ``at`` is in the lot's own metres; the scene's origin is its own. The
    # pond is at a known spot in both, and the projection is linear here.
    pond = next(s for s in jul["structures"] if s["struct_id"] == "pond")
    dx, dy = pond["x"] - at["pond"][0], pond["y"] - at["pond"][1]
    at = {k: (e + dx, n + dy) for k, (e, n) in at.items()}
    tw = [
        ("pond", "water", 17.0, 4.5, "A Pond (left) and a drawn Water Feature "
                                     "of about the same size (right)"),
        ("fence_s", "fence_l", 12.0, 2.2, "Fence / Wall, the structure (left), "
                                          "and a 5 m Fence line drawn "
                                          "north-south (right)"),
        ("patch", "lawn", 17.0, 4.0, "Native Lawn Patch, the structure (left), "
                                     "and a drawn Lawn Area 6 x 4 m (right)"),
        ("raised", "bed_h", 15.0, 3.2, "Raised Bed (left), a drawn Garden Bed "
                                       "3 x 1.2 m, and the same bed with a "
                                       "0.45 m height (right)"),
    ]
    tiles = []
    for i, (a, b, dist, cam_h, words) in enumerate(tw):
        mid = ((at[a][0] + at[b][0]) / 2, (at[a][1] + at[b][1]) / 2)
        for month, tag in ((7, "jul"), (1, "jan")):
            name = f"t{i}_{tag}"
            shots.append({"name": name, "scene": f"/__s/twins_{tag}.json",
                          "view": oblique(mid[0], mid[1], dist, cam_h, 0.2,
                                          bearing_deg=180.0)})
            tiles.append({"shot": name, "caption": words + (
                ", July." if month == 7 else ", January.")})
    for tag, words, span in (
            ("raised6", "A Raised Bed with the Size box at 6 m, from above, "
                        "over its map footprint (magenta)", 9.0),
            ("fence20", "A Fence / Wall with the Size box at 20 m, from "
                        "above, over its map footprint (magenta)", 22.0)):
        x, y = at[tag]
        shots.append({"name": f"z_{tag}", "scene": "/__s/twins_jul.json",
                      "view": above(x, y, span)})
        tiles.append({"shot": f"z_{tag}", "caption": words})
    sheets.append({"name": "twins", "tiles": tiles,
                   "title": "One thing, two ways: a structure beside its "
                            "drawn twin",
                   "sub": "Placement › Structures beside Draw › Shape. "
                          "Fifth summer. Drawn in software."})

    lot, rows, lines_at = shapes_lot()
    routes["/__s/shapes_jul.json"] = sj = scene(lot, 7, 14)
    routes["/__s/shapes_jan.json"] = scene(lot, 1, 12)
    ox, oy = sj["boundary"][0]          # the lot's (0, 0) corner
    tiles = []
    for r, (e, n) in enumerate(rows):
        words = ", ".join(SHAPE_ROWS[r])
        for month, tag in ((7, "jul"), (1, "jan")):
            name = f"s{r}_{tag}"
            shots.append({"name": name, "scene": f"/__s/shapes_{tag}.json",
                          "view": oblique(e + ox, n + oy, 17.0, 6.0, 0.0,
                                          bearing_deg=180.0)})
            tiles.append({"shot": name, "caption": f"Left to right: {words}"
                          + (". July." if month == 7 else ". January.")})
    for month, tag in ((7, "jul"), (1, "jan")):
        name = f"l_{tag}"
        shots.append({"name": name, "scene": f"/__s/shapes_{tag}.json",
                      "view": oblique(lines_at[0] + ox, lines_at[1] + oy,
                                      15.0, 3.0, 0.6, bearing_deg=150.0)})
        tiles.append({"shot": name, "caption": "Front to back: Fence, Hedge, "
                      "Living fence, Windbreak, each 6 m"
                      + (". July." if month == 7 else ". January.")})
    sheets.append({"name": "shapes", "tiles": tiles,
                   "title": "Draw › Shape in 3D: every area and line kind",
                   "sub": "Each area 4 x 3 m, each line 6 m, inside a lawn "
                          "outline. Fifth summer. Drawn in software."})
    spec = {"width": width, "height": height, "tile_width": 760,
            "shots": shots, "sheets": sheets}
    routes["/__s/shots.json"] = spec
    return routes, spec


#: ``--readers``: one thing in a 12 x 12 m yard, drawn or placed.
def _reader_cases() -> list:
    c = 6.0

    def yard(*features):
        return _project("readers", list(features), 12, 12)

    return [
        ("Pond (structure)", yard(structure("pond", c, c))),
        ("Water Feature (drawn 6x4)",
         yard(shape("Water Feature", _ellipse(c, c, 6, 4)))),
        ("Fence / Wall (structure)", yard(structure("fence", c, c))),
        ("Fence line (drawn 5 m)",
         yard(line("fence", ((c, c - 2.5), (c, c + 2.5))))),
        ("Native Lawn Patch (structure)",
         yard(structure("native_lawn_patch", c, c))),
        ("Lawn Area (drawn 6x4)",
         yard(shape("Lawn Area", _rect(c, c, 6, 4)))),
        ("Raised Bed (structure)", yard(structure("raised_bed", c, c))),
        ("Garden Bed (drawn 3x1.2)",
         yard(shape("Garden Bed", _rect(c, c, 3, 1.2)))),
        ("Garden Bed + 0.45 m height",
         yard(shape("Garden Bed", _rect(c, c, 3, 1.2), height_m=0.45))),
        ("Tool Shed (structure)", yard(structure("shed", c, c))),
        ("Rain Garden (structure)", yard(structure("rain_garden", c, c))),
        ("Rock Xeriscape (structure)", yard(structure("rock_xeriscape", c, c))),
        ("Fire Pit (structure)", yard(structure("fire_pit", c, c))),
        ("Mulch Area (drawn 4x4)",
         yard(shape("Mulch Area", _rect(c, c, 4, 4)))),
    ]


def readers_table(upgraded: bool = True) -> list:
    """What each part of the app makes of one thing in a 12 x 12 m yard: the
    habitat score's structure types, the Overview's planting area, Plan My
    Yard's fill zones and keep-outs, the Water page's counts, the shade
    model's casters, the ponds the pond planting sees, and the 3D scene.

    Each case is converted as the app converts a design it opens
    (``src/yard_upgrade.py``, V3.72) unless ``upgraded`` is false, which reads
    it as V3.71 stored it."""
    from src import yard_upgrade
    from src.design_inputs import water_features
    from src.exclusion import fill_regions, keepout_areas
    from src.habitat_score import compute_habitat_score
    from src.pond_planting import ponds_in
    from src.scene_contract import build_scene
    from src.shade import casters_from_project
    from src.yard_overview import bed_area_m2

    rows = []
    for name, p in _reader_cases():
        if upgraded:
            yard_upgrade.upgrade(p)
        from src.yard_kinds import structure_defs
        defs = structure_defs(p)        # what the app hands the score (V3.71)
        hs = compute_habitat_score([], defs)
        keep = keepout_areas(p)
        sc = build_scene(p, year=0)
        drawn = [f"model {s['struct_id']}" for s in sc["structures"]]
        drawn += [f"surface {s['kind']}" for s in sc["surfaces"]
                  if not s.get("base")]
        drawn += [f"line {ln['kind']}" for ln in sc["lines"]]
        drawn += [f"building {b['height_m']:g} m, {b['roof']['form']} roof"
                  for b in sc["buildings"]]
        rows.append({
            "case": name,
            "habitat": ", ".join(getattr(hs, "habitat_struct_types", None)
                                 or []) or "-",
            "planting_m2": round(bed_area_m2(p), 1),
            "fill_zones": len(fill_regions(p)),
            "keep_out": len(keep.circles) + len(keep.shapes),
            "water_page": ", ".join(f"{k} {v}" for k, v in
                                    water_features(defs).items() if v) or "-",
            "shade": len(casters_from_project(p)),
            "ponds": len(ponds_in(p["features"])),
            "in_3d": "; ".join(drawn),
        })
    return rows


def print_readers(upgraded: bool = True) -> None:
    cols = ("case", "habitat", "planting_m2", "fill_zones", "keep_out",
            "water_page", "shade", "ponds", "in_3d")
    rows = readers_table(upgraded)
    width = {c: max(len(c), *(len(str(r[c])) for r in rows)) for c in cols}
    print("  ".join(c.ljust(width[c]) for c in cols))
    for r in rows:
        print("  ".join(str(r[c]).ljust(width[c]) for c in cols))


def compose(spec: dict, pictures: dict, tile_w: int = 760) -> bytes:
    """One contact sheet, two tiles a row with a caption under each, as
    ``yard_probe.html`` lays its sheets out. Composed here rather than in the
    page: with fifteen tiles a sheet the page's decoding outran Chromium's
    virtual time, and the DOM was dumped before any sheet was in it."""
    import io
    from PIL import Image, ImageDraw, ImageFont

    def font(size, bold=False):
        for name in (("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),):
            for folder in ("/usr/share/fonts/truetype/dejavu",
                           "/Library/Fonts", "C:/Windows/Fonts"):
                try:
                    return ImageFont.truetype(os.path.join(folder, name), size)
                except OSError:
                    continue
        return ImageFont.load_default()

    first = Image.open(io.BytesIO(next(iter(pictures.values()))))
    tile_h = round(tile_w * first.height / first.width)
    pad, cap, head, cols = 14, 62, 92, 2
    rows = math.ceil(len(spec["tiles"]) / cols)
    sheet = Image.new("RGB", (pad + cols * (tile_w + pad),
                              head + rows * (tile_h + cap + pad) + pad),
                      "#16201a")
    g = ImageDraw.Draw(sheet)
    g.text((pad, 18), spec["title"], fill="#eaf1e6", font=font(28, True))
    g.text((pad, 56), spec.get("sub", ""), fill="#9fb096", font=font(17))
    words_font = font(18)
    for i, tile in enumerate(spec["tiles"]):
        x = pad + (i % cols) * (tile_w + pad)
        y = head + (i // cols) * (tile_h + cap + pad)
        data = pictures.get(tile["shot"])
        if data:
            im = Image.open(io.BytesIO(data)).convert("RGB")
            sheet.paste(im.resize((tile_w, tile_h)), (x, y))
        else:
            g.rectangle((x, y, x + tile_w, y + tile_h), fill="#402020")
        line, lines = "", []
        for word in tile["caption"].split():
            t = f"{line} {word}".strip()
            if g.textlength(t, font=words_font) <= tile_w - 6:
                line = t
            else:
                lines.append(line)
                line = word
        lines.append(line)
        for k, text in enumerate(lines[:2]):
            g.text((x + 2, y + tile_h + 8 + k * 24), text, fill="#d6e8cd",
                   font=words_font)
    out = io.BytesIO()
    sheet.save(out, "JPEG", quality=88)
    return out.getvalue()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", help="folder for the sheets")
    ap.add_argument("--size", default="1200x760", help="a tile, WxH")
    ap.add_argument("--tiles", action="store_true",
                    help="also save every tile on its own")
    ap.add_argument("--viewer-root", default=HTML,
                    help="another checkout's html/ folder")
    ap.add_argument("--readers", action="store_true",
                    help="no pictures: print what each part of the app makes "
                         "of a structure and its drawn twin (no browser)")
    ap.add_argument("--as-stored", action="store_true",
                    help="with --readers: read each case as V3.71 stored it, "
                         "without the conversion on open (V3.72)")
    args = ap.parse_args(argv)
    if args.readers:
        import tests  # noqa: F401  (its __init__ blocks the internet)
        use_throwaway_database()
        print_readers(upgraded=not args.as_stored)
        return 0
    if not args.out:
        ap.error("--out is needed for the pictures (or use --readers)")
    if find_chromium() is None:
        print("No Chromium or Chrome binary found. Set CHROME= to one.")
        return 2
    import tests  # noqa: F401  (its __init__ blocks the internet)
    use_throwaway_database()
    width, height = (int(v) for v in args.size.lower().split("x"))
    routes, spec = build_job(width, height)
    sheets = spec.pop("sheets")
    spec["keep_shots"] = True
    print(f"rendering {len(spec['shots'])} pictures (a few minutes)…")
    server = Server(routes, viewer_root=args.viewer_root)
    try:
        dom = run_probe(server.url("yard_probe.html?shots=/__s/shots.json"),
                        budget_ms=1800000, timeout=3000)
    finally:
        server.stop()
    errors = re.search(r'<pre id="probe-errors"[^>]*>(.*?)</pre>', dom, re.S)
    if errors and errors.group(1).strip():
        print("the viewer threw:\n" + errors.group(1).strip())
    pictures = images(dom, "shot")
    if not pictures:
        print("No pictures came back: the viewer did not start (no WebGL "
              "here?) or threw before it finished.")
        return 1
    missing = [s["name"] for s in spec["shots"] if s["name"] not in pictures]
    if missing:
        print("missing pictures:", ", ".join(missing))
    os.makedirs(args.out, exist_ok=True)
    for sheet in sheets:
        path = os.path.join(args.out, f"{sheet['name']}.jpg")
        with open(path, "wb") as fh:
            fh.write(compose(sheet, pictures))
        print("wrote", path)
    if args.tiles:
        for key, data in pictures.items():
            with open(os.path.join(args.out, f"tile_{key}.jpg"), "wb") as fh:
                fh.write(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
