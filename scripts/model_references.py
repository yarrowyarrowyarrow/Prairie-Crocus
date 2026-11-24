#!/usr/bin/env python3
"""
model_references.py — reference photographs beside each plant's 3D model, for
the region's native plants (V3.47; docs/plans/V3.47-reference-photos-for-the-models.md).

Run in a session (the photographs are on iNaturalist's open-data store, which a
cloud session can reach; iNaturalist's API is not, so the candidate list comes
from the owner's PC):

    python scripts/model_references.py status
    python scripts/model_references.py fetch            # photographs, ~5 min
    python scripts/model_references.py render           # the models, ~10 min
    python scripts/model_references.py sheets           # one sheet a plant
    python scripts/model_references.py all --only "Monarda fistulosa"

``fetch`` reads ``data/fetched/photo_candidates.json`` (written on the owner's
PC by ``scripts/fetch_photo_candidates.py``, then committed) and downloads each
plant's candidates at 500 px: in flower, leaves and the whole plant, fruit,
winter, its iNaturalist page's own photos, and the one it has now. A plant the
candidates file does not hold falls back to the photographs the catalogue
ships (``data/plant_photos.json``, else ``image_url``), and says so.

``render`` draws each plant's model through the app's real viewer
(``html/yard_probe.html``'s shots mode), fully grown, from the side and from
above at 45 degrees. The scene is built here, from the catalogue as it stands,
by the sprite gallery's own builder, so a change to a plant's row shows on the
next render with no other step. A wildflower is drawn in the middle of its
flowering; a tree, shrub or vine in July, with a second picture in flower when
July is outside its flowering; anything with a recorded fruit colour gets one
in fruit (V3.48). Re-run it after changing the viewer or the catalogue.

``sheets`` puts the renders and the photographs on one JPEG per plant, under
what the catalogue records of the plant's shape (the numbers the model was
drawn from), each photograph labelled with what it shows, where it was taken
and its credit, and writes ``INDEX.md`` listing every plant by its model
group. Where ``scripts/model_review.py`` holds a reading of the sheet, the
photographs picked as references are framed and the verdict is printed.

Everything goes to ``data/fetched/model_refs/`` (ignored by git, never shipped).
The photographs are CC0, CC BY or CC BY-SA and keep their credits in
``manifest.json``; they are references for modelling, not app content.

The plants are the region pack's reviewed native list (``native_here``); pass
``--place`` for another pack, ``--only`` for named plants, ``--all-plants``
for the whole catalogue.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src import native_here, photo_picks  # noqa: E402
from src.http_utils import user_agent  # noqa: E402
import model_review  # noqa: E402

CANDIDATES = ROOT / "data" / "fetched" / "photo_candidates.json"
MASTER = ROOT / "data" / "plants_master.json"
SHIPPED_PHOTOS = ROOT / "data" / "plant_photos.json"
OUT = ROOT / "data" / "fetched" / "model_refs"
#: What a reader of the sheets decided (scripts/model_review.py): the sheet
#: frames the photographs picked as references and prints the verdict.
REVIEW = ROOT / "data" / "fetched" / "model_review.json"

#: The order a sheet shows the kinds in, and what each is called on it.
GROUPS = ("flower", "plant", "fruit", "winter", "chosen", "now", "shipped")
WORDS = {"flower": "in flower", "plant": "leaves / whole plant",
         "fruit": "fruit", "winter": "winter", "chosen": "its iNaturalist page",
         "now": "the app's photo now", "shipped": "the app's photo"}
RENDER_PX = 640
BATCH = 24          # plants per headless browser run
DELAY = 0.25        # seconds between downloads


def slug(sci: str) -> str:
    """``Monarda fistulosa`` -> ``monarda_fistulosa``, the gallery's key."""
    return re.sub(r"[^a-z0-9]+", "_", sci.lower()).strip("_")


def _load(path: Path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


# ── which plants ────────────────────────────────────────────────────────────

def plants(args) -> list:
    """Catalogue rows for the plants asked for, in catalogue order."""
    rows = _load(MASTER, [])
    if args.only:
        want = {n.lower() for n in args.only}
        return [r for r in rows if r["scientific_name"].lower() in want
                or r["common_name"].lower() in want]
    if args.all_plants:
        return rows
    names = native_here.native_names(args.place) if args.place \
        else native_here.native_names()
    return [r for r in rows if r["scientific_name"] in names]


def photos_for(row: dict, candidates: dict, shipped: dict) -> tuple:
    """``(photos, source)`` for one plant: the candidates file's when it holds
    the plant, else what the catalogue ships."""
    sci = row["scientific_name"]
    entry = candidates.get(sci)
    out, seen = [], set()
    if entry and entry.get("groups"):
        for group in GROUPS:
            for c in entry["groups"].get(group, []):
                if c.get("url") and c["url"] not in seen:
                    seen.add(c["url"])
                    out.append({**c, "group": group})
        return out, "candidates"
    for p in shipped.get(sci, []):
        if p.get("url") and p["url"] not in seen:
            seen.add(p["url"])
            out.append({"url": p["url"], "group": "shipped",
                        "attribution": p.get("attribution", ""),
                        "license": p.get("license", ""), "place": "",
                        "taken_on": p.get("taken_on", "")})
    url = (row.get("image_url") or "").strip()
    if url and url not in seen:
        out.append({"url": url, "group": "shipped",
                    "attribution": row.get("image_attribution", ""),
                    "license": row.get("image_license", ""), "place": "",
                    "taken_on": ""})
    return out, "shipped"


def _shipped_index() -> dict:
    by = {}
    for p in _load(SHIPPED_PHOTOS, []):
        by.setdefault(p["scientific_name"], []).append(p)
    return by


# ── fetch ───────────────────────────────────────────────────────────────────

def fetch(rows: list) -> dict:
    candidates = _load(CANDIDATES, {})
    shipped = _shipped_index()
    manifest = _load(OUT / "manifest.json", {})
    got = failed = 0
    for n, row in enumerate(rows, 1):
        sci = row["scientific_name"]
        folder = OUT / "photos" / slug(sci)
        folder.mkdir(parents=True, exist_ok=True)
        photos, source = photos_for(row, candidates, shipped)
        kept = []
        for i, p in enumerate(photos):
            pid = photo_picks.photo_id(p["url"]) or i
            name = f"{GROUPS.index(p['group']):d}_{p['group']}_{pid}.jpg"
            path = folder / name
            if not path.exists():
                try:
                    req = urllib.request.Request(
                        p["url"], headers={"User-Agent": user_agent()})
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        path.write_bytes(resp.read())
                    got += 1
                    time.sleep(DELAY)
                except Exception as exc:              # noqa: BLE001
                    failed += 1
                    print(f"    could not fetch {p['url']}: {exc}")
                    continue
            kept.append({"file": f"photos/{slug(sci)}/{name}",
                         "group": p["group"], "url": p["url"],
                         "attribution": p.get("attribution", ""),
                         "license": p.get("license", ""),
                         "place": p.get("place", ""),
                         "taken_on": p.get("taken_on", ""),
                         "observation": p.get("observation")})
        manifest[sci] = {"common_name": row["common_name"],
                         "plant_type": row.get("plant_type", ""),
                         "source": source, "photos": kept}
        print(f"  {n:3d}/{len(rows)} {row['common_name']}: {len(kept)} "
              f"photographs ({'candidates' if source == 'candidates' else 'catalogue only'})")
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
    print(f"Downloaded {got}, failed {failed}. Manifest: {OUT / 'manifest.json'}")
    return manifest


# ── render ──────────────────────────────────────────────────────────────────

WOODY = ("tree", "shrub", "vine")
MONTHS = ("", "January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")


def _middle(start: int, end: int) -> int:
    """The month in the middle of a window that may run past December."""
    if not start:
        return 0
    span = (end - start) % 12
    return (start - 1 + span // 2) % 12 + 1


def _in(month: int, start: int, end: int) -> bool:
    return bool(start) and (month - start) % 12 <= (end - start) % 12


def months(row: dict) -> dict:
    """The months a plant is drawn in: ``main``, and ``flower`` and ``fruit``
    where those differ from it.

    A wildflower is drawn in the middle of its flowering, because in flower is
    most of what it looks like and July shows no bloom on a plant that flowers
    in May. A tree, shrub or vine is drawn in July, in leaf (a poplar flowers
    before its leaves), with a second picture in flower when July is outside
    its flowering. Anything with a recorded fruit colour gets one in fruit."""
    from src.scene_contract import _bloom_months
    bs, be = _bloom_months(row.get("bloom_period"))
    fs, fe = _bloom_months(row.get("fruit_period"))
    woody = row.get("plant_type") in WOODY
    out = {"main": 7 if woody or not bs else _middle(bs, be)}
    if bs and not _in(out["main"], bs, be):
        out["flower"] = _middle(bs, be)
    if fs and row.get("fruit_color") and not _in(out["main"], fs, fe):
        out["fruit"] = _middle(fs, fe)
    return out


def views(plant: dict) -> dict:
    """The two cameras, in the viewer's axes (y up), framed on the plant.

    A plant shorter than a person is looked at from above, so the side view
    tilts down to it: 20 degrees for anything up to 1.2 m, level from 3 m up.
    Seen level from half its own height, a knee-high plant shows the undersides
    of its flowers, which nobody standing in a yard sees."""
    import math
    h = max(float(plant.get("height_m") or 0.3), 0.3)
    r = max(float(plant.get("canopy_m") or 0.3), 0.3) / 2
    s = max(h, 2 * r)
    tilt = 20.0 * min(1.0, max(0.0, (3.0 - h) / 1.8))
    d = s * 1.35
    return {"side": {"at": [0, h * 0.5 + d * math.tan(math.radians(tilt)), d],
                     "looks_at": [0, h * 0.5, 0]},
            "high": {"at": [s * 0.9, h * 0.5 + s * 0.9, s * 0.9],
                     "looks_at": [0, h * 0.45, 0]}}


def scene_for(row: dict, i: int, month: int) -> dict:
    """The plant's specimen scene in ``month``, by the gallery's own builder,
    so it is the sprite a design holding that plant shows."""
    import datetime
    from src import sprite_gallery as sg
    return sg._scene_for(sg._species_specimen(row), i + 1, row["common_name"], i + 1,
                         when=datetime.datetime(2024, month, 15, 12, 0))


def _subject(scene: dict, row: dict) -> dict:
    """The plant the cameras frame: the tallest thing in the scene (a vine is
    drawn on a shrub, and the pair is what there is to look at)."""
    plants = scene.get("plants") or [{}]
    return max(plants, key=lambda q: float(q.get("height_m") or 0))


def render(rows: list) -> list:
    import render_yard as ry
    out = OUT / "model"
    out.mkdir(parents=True, exist_ok=True)
    drawn = _load(OUT / "renders.json", {})
    jobs = []
    for i, row in enumerate(rows):
        s = slug(row["scientific_name"])
        when = months(row)
        drawn[row["scientific_name"]] = when
        for old in out.glob(f"{s}_*.jpg"):
            old.unlink()
        for kind, month in when.items():
            scene = scene_for(row, i, month)
            view = views(_subject(scene, row))
            shots = [(f"{s}__side" if kind == "main" else f"{s}__{kind}", view["side"])]
            if kind == "main":
                shots.append((f"{s}__high", view["high"]))
            jobs.append((f"/__yard/{s}_{kind}.json", scene, shots))
    done = 0
    for b in range(0, len(jobs), BATCH):
        batch = jobs[b:b + BATCH]
        routes, shots = {}, []
        for url, scene, named in batch:
            routes[url] = scene
            shots += [{"name": n, "scene": url, "view": v} for n, v in named]
        routes["/__yard/shots.json"] = {"width": RENDER_PX, "height": RENDER_PX,
                                        "shots": shots, "keep_shots": True}
        srv = ry.Server(routes)
        try:
            dom = ry.run_probe(srv.url("/yard_probe.html?shots=/__yard/shots.json"),
                               budget_ms=30000 + 4000 * len(shots))
        finally:
            srv.stop()
        pics = ry.images(dom, "shot")
        for name, data in pics.items():
            key, view = name.split("__")
            (out / f"{key}_{view}.jpg").write_bytes(data)
        done += len(pics)
        print(f"  rendered {min(b + BATCH, len(jobs))}/{len(jobs)} scenes "
              f"({len(pics)} of {len(shots)} pictures this batch)")
    with open(OUT / "renders.json", "w", encoding="utf-8") as f:
        json.dump(drawn, f, indent=1)
    print(f"{done} pictures of {len(rows)} plants.")
    return []


# ── sheets ──────────────────────────────────────────────────────────────────

def _font(size: int):
    from PIL import ImageFont
    for name in ("DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _fit(im, w, h):
    im = im.convert("RGB")
    im.thumbnail((w, h))
    return im


def _wrap(draw, text, font, width):
    lines, cur = [], ""
    for word in str(text).split():
        t = f"{cur} {word}".strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = word
    return lines + ([cur] if cur else [])


def facts(row: dict) -> str:
    bits = [row.get("plant_type", ""),
            f"{row['mature_height_m']} m tall" if row.get("mature_height_m") else "",
            f"blooms {row['bloom_period']}" if row.get("bloom_period") else "",
            f"flower {row['flower_color']}" if row.get("flower_color") else ""]
    return " · ".join(b for b in bits if b)


def recorded(row: dict) -> str:
    """What the catalogue records of the plant's shape: the numbers the model
    was drawn from, so a fault can be told apart as data or as drawing."""
    def v(key, unit=""):
        x = row.get(key)
        return f"{x}{unit}" if x not in ("", None) else ""
    leaf = " ".join(b for b in (v("leaf_shape"), v("leaf_size_cm", " cm"),
                                v("leaf_arrangement"), v("leaf_surface")) if b)
    flower = " ".join(b for b in (
        v("flower_arch"), v("flower_symmetry"), v("petal_shape"),
        f"x{v('petal_count')}" if v("petal_count") else "",
        v("flower_diameter_cm", " cm"),
        f"{v('florets_per_head')}/head" if v("florets_per_head") else "",
        f"{v('flowering_stems')} stems" if v("flowering_stems") else "",
        f"centre {v('flower_center_color')}" if v("flower_center_color") else "",
        f"at {v('flower_height_frac')}" if v("flower_height_frac") else "") if b)
    bits = [f"body: {v('growth_form') or v('branching') or 'not recorded'}",
            v("stem_branching"), "basal rosette" if row.get("basal_rosette") else "",
            f"leaf: {leaf}" if leaf else "", f"flower: {flower}" if flower else "",
            f"seed head: {v('inflorescence_form')}" if v("inflorescence_form") else "",
            f"fruit: {v('fruit_form')} {v('fruit_color')}".strip() if v("fruit_form") else "",
            f"bark: {v('bark_texture')} {v('bark_color')}".strip() if v("bark_texture") else "",
            f"form: {v('flower_form')}" if v("flower_form") else ""]
    return " · ".join(b for b in bits if b)


#: The sheet's grid. The model from the side takes a 2 x 2 block (it is what
#: is being judged), the model from above one cell, the photographs the rest.
COLS, TILE, PAD, CAP, TOP = 6, 256, 6, 32, 96


def _cells(n: int, extras: int = 0):
    """Grid cells (col, row) for ``n`` photographs, around the models: the side
    view's 2 x 2 block, the view from above, and ``extras`` more pictures of
    the model (in flower, in fruit) after it on the top row."""
    out, row = [], 0
    while len(out) < n:
        for col in range(COLS):
            if (row < 2 and col < 2) or (row == 0 and 2 <= col < 3 + extras):
                continue
            out.append((col, row))
        row += 1
    return out[:n]


def sheet(row: dict, entry: dict, review: dict = None) -> Path:
    from PIL import Image, ImageDraw
    sci = row["scientific_name"]
    s = slug(sci)
    photos = entry.get("photos", []) if entry else []
    picked = {}
    for kind, ids in ((review or {}).get("refs") or {}).items():
        for pid in ids:
            picked.setdefault(str(pid), []).append(kind)
    when = _load(OUT / "renders.json", {}).get(sci) or {"main": 7}
    extras = [k for k in ("flower", "fruit") if k in when]
    cells = _cells(len(photos), len(extras))
    rows_n = max(2, 1 + max((r for _, r in cells), default=0))
    step_x, step_y = TILE + PAD, TILE + CAP + PAD
    width = PAD + COLS * step_x
    height = TOP + rows_n * step_y + PAD
    im = Image.new("RGB", (width, height), "#16201a")
    d = ImageDraw.Draw(im)
    small = _font(13)
    d.text((PAD, 6), f"{row['common_name']}  ({sci})", fill="#eaf1e6", font=_font(24))
    d.text((PAD, 38), facts(row), fill="#9fb096", font=_font(15))
    for k, line in enumerate(_wrap(d, recorded(row), small, width - 2 * PAD)[:2]):
        d.text((PAD, 60 + k * 16), line, fill="#c9b98a", font=small)
    if review and review.get("verdict"):
        d.text((width - PAD - 330, 10), review["verdict"][:44], fill="#ffd27a",
               font=_font(15))

    def paste(path, x, y, box):
        try:
            pic = _fit(Image.open(path), box, box)
            im.paste(pic, (x + (box - pic.width) // 2, y + (box - pic.height) // 2))
        except OSError:
            d.rectangle([x, y, x + box, y + box], fill="#402020")

    big = 2 * TILE + PAD + CAP
    paste(OUT / "model" / f"{s}_side.jpg", PAD, TOP, big)
    d.text((PAD + 4, TOP + 4),
           f"MODEL: from the side, {MONTHS[when['main']]}, fully grown",
           fill="#ffd27a", font=_font(14))
    x2 = PAD + 2 * step_x
    paste(OUT / "model" / f"{s}_high.jpg", x2, TOP, TILE)
    d.text((x2, TOP + TILE + 2), "MODEL: from above, 45°", fill="#ffd27a", font=small)
    for k, kind in enumerate(extras):
        x3 = x2 + (k + 1) * step_x
        paste(OUT / "model" / f"{s}_{kind}.jpg", x3, TOP, TILE)
        d.text((x3, TOP + TILE + 2), f"MODEL: in {kind}, {MONTHS[when[kind]]}",
               fill="#ffd27a", font=small)
    for i, (p, (col, r)) in enumerate(zip(photos, cells)):
        x, y = PAD + col * step_x, TOP + r * step_y
        paste(OUT / p["file"], x, y, TILE)
        pid = str(photo_picks.photo_id(p["url"]) or "")
        if pid in picked:
            d.rectangle([x, y, x + TILE - 1, y + TILE - 1], outline="#ffd27a", width=3)
        where = ", ".join(b for b in (p.get("place", "")[:26], p.get("taken_on", "")) if b)
        label = f"{i + 1}. {WORDS.get(p['group'], p['group'])}"
        if pid in picked:
            label += " [REF " + "/".join(picked[pid]) + "]"
        elif where:
            label += f" · {where}"
        for k, (line, fill) in enumerate((
                (_wrap(d, label, small, TILE)[:1], "#d6e8cd"),
                (_wrap(d, p.get("attribution", "") or "no credit recorded",
                       small, TILE)[:1], "#8a9a84"))):
            if line:
                d.text((x, y + TILE + 1 + k * 15), line[0], fill=fill, font=small)
    path = OUT / "sheets" / f"{s}.jpg"
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, quality=85)
    return path


def body_group(row: dict) -> str:
    """The body a plant is drawn with, as far as the catalogue says: its type
    and its recorded growth form (a herb) or branching (a woody plant). The
    index lists the sheets by it, so plants that share a builder read together."""
    kind = row.get("growth_form") or row.get("branching") or "not recorded"
    return f"{row.get('plant_type') or 'plant'} · {kind}"


def sheets(rows: list) -> None:
    manifest = _load(OUT / "manifest.json", {})
    review = _load(REVIEW, {})
    by_group: dict = {}
    for row in rows:
        rec = review.get(row["scientific_name"])
        if rec and rec.get("read_in") != model_review.PASS:
            # An earlier pass's verdict is not printed on a sheet being read
            # again (V3.62): the reader should not start from the old score.
            # Its reference photographs are still framed.
            rec = {"refs": rec.get("refs") or {}}
        elif rec:
            rec = {**rec, "verdict": f"{rec.get('score')}/10  "
                                     + " ".join(rec.get("faults") or [])}
        sheet(row, manifest.get(row["scientific_name"]), rec)
        by_group.setdefault(body_group(row), []).append(row)
    lines = ["# Model reference sheets", "",
             "One sheet a plant: the 3D model and its reference photographs, "
             "listed by the body the plant is drawn with. Written by "
             "`scripts/model_references.py`; not in git. The last column is what "
             "a reader of the sheet decided (`scripts/model_review.py`).",
             ""]
    for group in sorted(by_group):
        lines += [f"## {group}", "",
                  "| Plant | Scientific name | Photos | Sheet | Read |",
                  "|---|---|---|---|---|"]
        for row in by_group[group]:
            e = manifest.get(row["scientific_name"]) or {}
            rec = review.get(row["scientific_name"]) or {}
            read = (f"{rec.get('score')}/10 " + " ".join(rec.get("faults") or [])
                    if rec else "")
            lines.append(f"| {row['common_name']} | *{row['scientific_name']}* | "
                         f"{len(e.get('photos', []))} | "
                         f"`sheets/{slug(row['scientific_name'])}.jpg` | {read} |")
        lines.append("")
    (OUT / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(rows)} sheets and {OUT / 'INDEX.md'}")


# ── status ──────────────────────────────────────────────────────────────────

def status(rows: list) -> None:
    candidates = _load(CANDIDATES, {})
    held = [r for r in rows if (candidates.get(r["scientific_name"]) or {}).get("groups")]
    print(f"{len(rows)} plants asked for.")
    if not CANDIDATES.exists():
        print(f"No {CANDIDATES.relative_to(ROOT)}: commit it from the PC that ran "
              "scripts/fetch_photo_candidates.py. Until then only the catalogue's "
              "own photographs are used (usually one a plant).")
    else:
        print(f"Candidates file holds {len(held)} of them "
              f"({len(candidates)} plants in the file).")
        for r in rows:
            if r not in held:
                print(f"  not in the candidates file: {r['common_name']} ({r['scientific_name']})")
    read = _load(REVIEW, {})
    print(f"Sheets read so far (scripts/model_review.py): "
          f"{sum(1 for r in rows if r['scientific_name'] in read)} of {len(rows)}.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("step", choices=("status", "fetch", "render", "sheets", "all"))
    ap.add_argument("--only", nargs="+", metavar="NAME",
                    help="scientific or common names")
    ap.add_argument("--place", help="a region pack's place (default: the default pack)")
    ap.add_argument("--all-plants", action="store_true",
                    help="the whole catalogue, not the native list")
    args = ap.parse_args(argv)
    rows = plants(args)
    if not rows:
        print("No plants matched.")
        return 1
    if args.step == "status":
        status(rows)
    if args.step in ("fetch", "all"):
        fetch(rows)
    if args.step in ("render", "all"):
        render(rows)
    if args.step in ("sheets", "all"):
        sheets(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
