#!/usr/bin/env python3
"""
leaf_readings.py — read a plant's leaves and habit off its reference
photographs, and write what was read into the catalogue (V3.48, F268).

    python scripts/leaf_readings.py status
    python scripts/leaf_readings.py strips                 # the pictures to read from
    python scripts/leaf_readings.py strips --only "Yarrow" --per 2
    python scripts/leaf_readings.py add batch.json         # record readings
    python scripts/leaf_readings.py add batch.json --dry-run
    python scripts/leaf_readings.py status --group shrubs  # the shrubs (V3.49)
    python scripts/leaf_readings.py strips --group shrubs

Until V3.48 every leaf and habit number in the catalogue was the seeder's
estimate for the genus: an 8 cm leaf on every aster, three stems on everything.
The 3D viewer draws a wildflower from those numbers at their real size once
they are read (``src/herb_habit.py``), so reading them is what moves a plant
off the shared baked figure and onto its own.

``strips`` puts the photographs ``scripts/model_review.py`` picked as good
references for the whole plant, the leaf and the flower in one row a plant,
under what the catalogue records now and what the review said. Run
``scripts/model_references.py fetch`` first; the strips go beside the sheets in
``data/fetched/model_refs/reading/`` (ignored by git).

``add`` takes a JSON object, scientific name to the fields read::

    {"Achillea borealis": {"growth_form": "erect", "leaf_shape": "bipinnate",
                           "leaf_size_cm": 9, "leaf_arrangement": "alternate",
                           "basal_rosette": 1, "stem_branching": "unbranched",
                           "flowering_stems": 10, "stem_leaf_nodes": 8}}

It refuses the whole batch on one bad value (a word outside the vocabulary, a
number outside its range, an unknown plant or field), then writes each row with
``leaf_data_source = "photo"`` and a citation naming the photographs read: the
review's picks for that plant, by iNaturalist photograph id. Where a reading
also gives flower numbers (``FLOWER_READ``), the flower pair is marked the same
way. ``flowering_stems`` is the flower clusters on a grown plant, not its
stems; the viewer divides by how a stem forks.

A shrub (``--group shrubs``, V3.49) is read the same way and drawn by
``src/shrub_habit.py``. Its habit is the woody one (``branching``:
``multi_stem``, ``suckering``, ``arching``, ``prostrate``) and it needs one
number a wildflower does not, ``woody_stems``: the stems a grown plant sends
up from the ground, easiest to count on a winter photograph, which is why a
shrub's strip shows one::

    {"Cornus sericea": {"branching": "multi_stem", "woody_stems": 25,
                        "leaf_shape": "ovate", "leaf_size_cm": 8,
                        "leaf_arrangement": "opposite"}}

Only form, size and count are read. Nothing about what a plant is used for
belongs here (P12), and a flower's colour is the owner's answer (V3.34): this
tool refuses ``flower_color``.

A changed row needs a schema bump to reach an installed copy.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src import data_quality as dq  # noqa: E402
from src import herb_habit, native_here, photo_picks, shrub_habit, tree_habit  # noqa: E402

MASTER = ROOT / "data" / "plants_master.json"
REVIEW = ROOT / "data" / "fetched" / "model_review.json"
REFS = ROOT / "data" / "fetched" / "model_refs"
READ_IN = "V3.50"

#: A word from a vocabulary.
WORDS = {
    "growth_form": dq.GROWTH_FORMS,
    "leaf_shape": dq.LEAF_SHAPES,
    "leaf_arrangement": dq.LEAF_ARRANGEMENTS,
    "leaf_surface": dq.LEAF_SURFACES,
    "branching": dq.BRANCHING_HABITS,
    "crown_shape": dq.CROWN_SHAPES,
    "limb_habit": dq.LIMB_HABITS,
    "stem_branching": dq.STEM_BRANCHINGS,
    "flower_arch": dq.FLOWER_ARCHITECTURES,
    "petal_shape": dq.PETAL_SHAPES,
    "flower_symmetry": dq.FLOWER_SYMMETRIES,
}
#: A number, with the range a reading may fall in.
NUMBERS = {
    "leaf_size_cm": (0.2, 80.0),
    "stem_leaf_nodes": (1, 80),
    "flowering_stems": (1, 300),
    "woody_stems": (1, 60),
    "crown_clear": (0.0, 0.8),
    "mature_height_m": (0.02, 30.0),
    "petal_count": (0, 60),
    "florets_per_head": (1, 2000),
    "flower_diameter_cm": (0.1, 20.0),
    "flower_height_frac": (0.3, 1.3),
}
WHOLE = ("stem_leaf_nodes", "flowering_stems", "woody_stems", "petal_count",
         "florets_per_head")
FLAGS = ("basal_rosette",)
FIELDS = tuple(WORDS) + tuple(NUMBERS) + FLAGS
#: A reading that gives any of these read the flower too.
FLOWER_READ = ("flower_arch", "petal_shape", "flower_symmetry", "petal_count",
               "florets_per_head", "flower_diameter_cm", "flower_height_frac")
#: What a reading must give for the viewer to draw the plant from it: a
#: wildflower's habit, or a shrub's woody habit and its stems.
NEEDED = ("growth_form", "leaf_shape", "leaf_size_cm", "leaf_arrangement")
NEEDED_WOODY = ("branching", "woody_stems", "leaf_shape", "leaf_size_cm",
                "leaf_arrangement")
#: A tree, and the crown it is drawn from (V3.50); a vine, its leaves.
NEEDED_TREE = ("woody_stems", "crown_shape", "crown_clear", "limb_habit",
               "leaf_shape", "leaf_size_cm", "leaf_arrangement")
NEEDED_VINE = ("leaf_shape", "leaf_size_cm", "leaf_arrangement")
#: The plants a sitting reads: which types, the module that says whether one
#: is drawn from its numbers, and the photographs a strip shows of each.
GROUPS = {
    "herbs": {"types": herb_habit.TYPES, "habit": herb_habit,
              "words": "wildflowers, herbs and groundcovers",
              "kinds": (("habit", 3), ("leaf", 3), ("flower", 2))},
    "shrubs": {"types": shrub_habit.TYPES, "habit": shrub_habit,
               "words": "shrubs",
               "kinds": (("habit", 3), ("winter", 1), ("leaf", 2), ("flower", 1),
                         ("fruit", 1))},
    "trees": {"types": tree_habit.TYPES, "habit": tree_habit, "words": "trees and vines",
              "kinds": (("habit", 3), ("winter", 1), ("leaf", 2), ("flower", 1),
                        ("fruit", 1))},
}


def needed(row: dict) -> tuple:
    kind = row.get("plant_type")
    if kind == "tree":
        return NEEDED_TREE
    if kind == "vine":
        return NEEDED_VINE
    return NEEDED_WOODY if kind in shrub_habit.TYPES else NEEDED


def _load(path: Path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def citation(sci: str, review: dict) -> str:
    """The photographs a reading of ``sci`` was made from: the review's picks
    for the whole plant (in leaf and in winter), the leaf and the flower, by
    photograph id."""
    refs = (review.get(sci) or {}).get("refs") or {}
    ids = []
    for kind in ("habit", "winter", "leaf", "flower"):
        for pid in refs.get(kind, []):
            if str(pid) not in ids:
                ids.append(str(pid))
    if not ids:
        return ""
    return f"iNaturalist photographs {', '.join(ids[:8])} (read {READ_IN})"


def problems(batch: dict, rows: dict, review: dict) -> list:
    """Why ``batch`` cannot be recorded, as sentences; empty when it can."""
    out = []
    for sci, reading in batch.items():
        row = rows.get(sci)
        if row is None:
            out.append(f"{sci}: not in the catalogue")
            continue
        if not isinstance(reading, dict) or not reading:
            out.append(f"{sci}: nothing read")
            continue
        for field, value in reading.items():
            if field not in FIELDS:
                out.append(f"{sci}: {field} is not a field this tool reads")
            elif field in WORDS and value not in WORDS[field]:
                out.append(f"{sci}: {field} {value!r} is not in the vocabulary")
            elif field in NUMBERS:
                lo, hi = NUMBERS[field]
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    out.append(f"{sci}: {field} must be a number")
                elif not lo <= value <= hi:
                    out.append(f"{sci}: {field} {value} is outside {lo} to {hi}")
                elif field in WHOLE and value != int(value):
                    out.append(f"{sci}: {field} must be a whole number")
            elif field in FLAGS and value not in (0, 1):
                out.append(f"{sci}: {field} must be 0 or 1")
        merged = {**row, **reading}
        # A rayless head (a thistle, pussytoes, pearly everlasting, Joe-Pye)
        # records no rays: its white "petals" are bracts. And a count is per
        # flower or per head's rays, never the florets in a head.
        if (reading.get("petal_count") or 0) > 0 and merged.get("petal_shape") == "tubular":
            out.append(f"{sci}: petal_count on a rayless head (petal_shape tubular) "
                       f"must stay 0")
        for field in needed(row):
            if not merged.get(field):
                out.append(f"{sci}: {field} is not recorded and was not read")
        if not citation(sci, review):
            out.append(f"{sci}: the review picked no photographs to cite "
                       f"(scripts/model_review.py)")
    return out


def apply(batch: dict, rows: list, review: dict) -> int:
    """Write ``batch`` into ``rows`` (the catalogue's list), with where each
    reading came from. Returns how many rows changed."""
    by = {r["scientific_name"]: r for r in rows}
    changed = 0
    for sci, reading in batch.items():
        row, before = by[sci], dict(by[sci])
        for field, value in reading.items():
            if field == "mature_height_m":
                # The catalogue keeps a height as text ("0.15", "1").
                value = f"{float(value):g}"
            elif field in NUMBERS and field not in WHOLE:
                value = float(value)
            elif field in WHOLE or field in FLAGS:
                value = int(value)
            row[field] = value
        cite = citation(sci, review)
        row["leaf_data_source"] = "photo"
        row["leaf_data_citation"] = cite
        if any(f in reading for f in FLOWER_READ):
            row["flower_data_source"] = "photo"
            row["flower_data_citation"] = cite
        changed += row != before
    return changed


# ── which plants ────────────────────────────────────────────────────────────

def plants(only=None, types=herb_habit.TYPES) -> list:
    """The region's natives of ``types``, or the plants named in ``only``."""
    rows = _load(MASTER, [])
    if only:
        want = {n.lower() for n in only}
        return [r for r in rows if r["scientific_name"].lower() in want
                or r["common_name"].lower() in want]
    names = native_here.native_names()
    return [r for r in rows if r["scientific_name"] in names
            and r.get("plant_type") in types]


def status(group: str = "herbs") -> None:
    g = GROUPS[group]
    rows = plants(types=g["types"])
    read = [r for r in rows if herb_habit.is_read(r)]
    drawn = [r for r in read if g["habit"].form_for(r)]
    print(f"{len(rows)} native {g['words']}.")
    print(f"Leaves and habit read off photographs: {len(read)}.")
    print(f"Drawn from their own numbers (src/{g['habit'].__name__.split('.')[-1]}.py): "
          f"{len(drawn)}.")
    for r in read:
        if r not in drawn:
            print(f"  read, but its habit is not one the new body draws: "
                  f"{r['common_name']} ({r.get('growth_form') or r.get('branching')})")
    left = [r for r in rows if r not in read]
    if left:
        print(f"Not read yet: {len(left)}.")
        for r in left[:400]:
            print(f"  {r['common_name']} ({r['scientific_name']})")


# ── the strips ──────────────────────────────────────────────────────────────

TILE, PAD, HEAD, CAP = 250, 6, 74, 16
KINDS = (("habit", 3), ("leaf", 3), ("flower", 2))


def _recorded(row: dict) -> str:
    woody = row.get("plant_type") in shrub_habit.TYPES
    bits = [f"{row.get('plant_type')}", f"height {row.get('mature_height_m')} m",
            f"spacing {row.get('spacing_m')} m",
            f"habit {row.get('branching') or '-'}, {row.get('woody_stems') or '-'} "
            f"stems from the ground" if woody
            else f"habit {row.get('growth_form') or '-'}",
            f"leaf {row.get('leaf_shape') or '-'} {row.get('leaf_size_cm') or '-'} cm "
            f"{row.get('leaf_arrangement') or '-'}",
            f"{row.get('stem_branching') or 'branching -'}",
            f"rosette {row.get('basal_rosette')}",
            f"clusters {row.get('flowering_stems')}",
            f"stem leaves {row.get('stem_leaf_nodes') or '-'}",
            f"flower {row.get('flower_arch') or '-'} {row.get('flower_diameter_cm') or '-'} cm "
            f"x{row.get('florets_per_head') or '-'} petals {row.get('petal_count')}"]
    return "   ".join(bits)


def strips(rows: list, per: int = 3, kinds: tuple = KINDS) -> list:
    """One picture for every ``per`` plants: its recorded numbers, what the
    review said, and the photographs picked for the whole plant, the leaf and
    the flower (``kinds``: which, and how many of each)."""
    from PIL import Image, ImageDraw
    import model_references as mr
    manifest = _load(REFS / "manifest.json", {})
    review = _load(REVIEW, {})
    out_dir = REFS / "reading"
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = sum(n for _, n in kinds)
    width = PAD + cols * (TILE + PAD)
    band = HEAD + TILE + CAP + PAD
    written = []
    for start in range(0, len(rows), per):
        chunk = rows[start:start + per]
        im = Image.new("RGB", (width, band * len(chunk)), "#16201a")
        d = ImageDraw.Draw(im)
        for k, row in enumerate(chunk):
            sci, y = row["scientific_name"], k * band
            rec = review.get(sci) or {}
            d.text((PAD, y + 2), f"{row['common_name']}  ({sci})", fill="#eaf1e6",
                   font=mr._font(20))
            d.text((PAD, y + 27), _recorded(row), fill="#c9b98a", font=mr._font(12))
            for j, line in enumerate(mr._wrap(d, rec.get("note", ""), mr._font(12),
                                              width - 2 * PAD)[:2]):
                d.text((PAD, y + 43 + j * 14), line, fill="#9fb096", font=mr._font(12))
            by_id = {str(photo_picks.photo_id(p["url"]) or ""): p
                     for p in (manifest.get(sci) or {}).get("photos", [])}
            shown, col = set(), 0
            for kind, n in kinds:
                picks = [pid for pid in (rec.get("refs") or {}).get(kind, [])
                         if str(pid) in by_id and str(pid) not in shown][:n]
                for pid in picks:
                    shown.add(str(pid))
                    x = PAD + col * (TILE + PAD)
                    try:
                        pic = mr._fit(Image.open(REFS / by_id[str(pid)]["file"]), TILE, TILE)
                        im.paste(pic, (x + (TILE - pic.width) // 2,
                                       y + HEAD + (TILE - pic.height) // 2))
                    except OSError:
                        d.rectangle([x, y + HEAD, x + TILE, y + HEAD + TILE], fill="#402020")
                    d.text((x, y + HEAD + TILE + 1), kind, fill="#d6e8cd", font=mr._font(12))
                    col += 1
        path = out_dir / f"strip_{start // per + 1:03d}.jpg"
        im.save(path, quality=84)
        written.append(path)
    print(f"Wrote {len(written)} strips of {len(rows)} plants to {out_dir}")
    return written


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("step", choices=("status", "strips", "add"))
    ap.add_argument("batch", nargs="?", help="add: the JSON file of readings")
    ap.add_argument("--only", nargs="+", metavar="NAME")
    ap.add_argument("--unread", action="store_true",
                    help="strips: only plants not read yet")
    ap.add_argument("--per", type=int, default=3, help="strips: plants a picture")
    ap.add_argument("--group", choices=tuple(GROUPS), default="herbs",
                    help="status, strips: which plants (default: herbs)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if args.step == "status":
        status(args.group)
        return 0
    if args.step == "strips":
        g = GROUPS[args.group]
        rows = plants(args.only, g["types"])
        if args.unread:
            rows = [r for r in rows if not herb_habit.is_read(r)]
        strips(rows, args.per, g["kinds"])
        return 0
    if not args.batch:
        ap.error("add needs a JSON file")
    batch = _load(Path(args.batch), None)
    if not isinstance(batch, dict):
        print("The batch must be a JSON object: scientific name to the fields read.")
        return 1
    rows = _load(MASTER, [])
    review = _load(REVIEW, {})
    bad = problems(batch, {r["scientific_name"]: r for r in rows}, review)
    if bad:
        print(f"Nothing written: {len(bad)} problem(s).")
        for line in bad:
            print("  " + line)
        return 1
    n = apply(batch, rows, review)
    if args.dry_run:
        print(f"{n} of {len(batch)} rows would change. Nothing written.")
        return 0
    with open(MASTER, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)   # the catalogue's own shape
        f.write("\n")
    print(f"{n} of {len(batch)} rows changed in {MASTER.relative_to(ROOT)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
