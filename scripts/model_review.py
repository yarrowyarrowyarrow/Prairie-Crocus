#!/usr/bin/env python3
"""
model_review.py — what each plant's reference sheet showed (V3.48;
docs/plans/V3.48-models-against-photographs.md).

``scripts/model_references.py`` puts a plant's 3D model beside its reference
photographs. This records what a reader of that sheet decided: which
photographs are the good references for the plant's habit, flower, leaves and
fruit, how well the model stands for the plant, and what is wrong with it.

    python scripts/model_review.py add < notes.json     # fold a batch in
    python scripts/model_review.py summary               # faults, counted
    python scripts/model_review.py todo                  # plants not yet read
    python scripts/model_review.py show "Monarda fistulosa"
    python scripts/model_review.py compare               # this pass against the last

A plant read again in a later pass keeps what the earlier pass said under
``earlier`` (V3.62), so a re-read can be measured against it, and keeps its
reference photographs when the new batch names none.

A batch names photographs by their number on the sheet::

    {"Gaillardia aristata": {
        "refs": {"habit": [4, 9], "flower": [1, 7], "leaf": [4, 11], "fruit": [10]},
        "score": 3, "faults": ["flower_colour", "stem_leaves"],
        "note": "Rays are yellow with a red base; the model's are orange."}}

``add`` turns each number into the photograph's own iNaturalist id (read from
the sheet's ``manifest.json``), because a sheet's numbering changes when a
download fails and the id does not. The record is kept in
``data/fetched/model_review.json``, which is committed (the photographs and
sheets are not) and never shipped.

The score answers the sprite audit's question, 0 to 10: would someone who
knows this plant recognise it, and tell it from its neighbours? 7 and up means
the model is doing its job.

The notes say what a plant looks like: its form and its colours. Nothing about
what a plant is used for belongs here (design principle P12).
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src import photo_picks  # noqa: E402

REVIEW = ROOT / "data" / "fetched" / "model_review.json"
MANIFEST = ROOT / "data" / "fetched" / "model_refs" / "manifest.json"
MASTER = ROOT / "data" / "plants_master.json"
PASS = "V3.65"

#: The passes in order, oldest first.
PASSES = ("V3.48", "V3.62", "V3.64", "V3.65")

#: What a photograph can be the reference for.
KINDS = ("habit", "flower", "leaf", "fruit", "winter", "bark")

#: What can be wrong with a model, and what each word means here.
FAULTS = {
    # the body
    "habit": "the wrong kind of body (a rosette for a leafy-stemmed plant, "
             "a tuft for a creeping mat, one stem for a clump)",
    "stem_leaves": "leaves missing from the stems, or drawn on stems that are bare",
    "sparse": "far fewer stems, leaves or branches than the plant carries",
    "dense": "a solid mass where the plant is open",
    "proportion": "height against width is off, or a part is out of scale",
    "leaf_shape": "the leaf's outline or division is wrong",
    "leaf_size": "leaves too big or too small for the plant",
    "leaf_colour": "the green is wrong (too dark, too yellow, not grey, not blue)",
    "leaf_place": "leaves arranged wrongly (opposite, whorled, basal, in tiers)",
    "stems": "stems wrong: thickness, colour, straightness or forking",
    # flowers
    "flower_colour": "the bloom's colour is wrong",
    "flower_centre": "the centre (disc, eye, cone) is missing or the wrong colour",
    "flower_size": "one flower or head is too big or too small",
    "flower_shape": "one flower is the wrong shape (petal count, outline, symmetry)",
    "flower_arch": "the cluster is the wrong architecture (a spike drawn as a plate)",
    "flower_count": "too few or too many flowers for a plant in bloom",
    "flower_place": "flowers at the wrong height or place on the plant",
    "no_flower": "in flower in July and none drawn, or drawn out of season",
    # after flowering
    "seed_head": "a grass, sedge or rush seed head is missing or the wrong form",
    "fruit": "fruit is missing, the wrong shape, size or colour",
    # woody plants
    "crown": "the crown's outline or branching is wrong",
    "bark": "bark or twig colour or texture is wrong",
    "trunk": "trunk count, girth or lean is wrong",
    # the record
    "data": "a recorded number looks wrong (height, spread, bloom months)",
    "photos": "the photographs are too few or too poor to judge the model by",
}


def _load(path: Path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def load() -> dict:
    return _load(REVIEW, {})


def names() -> dict:
    """Common and scientific name, lower-cased, to the scientific name."""
    out = {}
    for row in _load(MASTER, []):
        out[row["scientific_name"].lower()] = row["scientific_name"]
        out[row["common_name"].lower()] = row["scientific_name"]
    return out


def photo_ids(entry: dict) -> list:
    """The photograph ids of a manifest entry, in the order the sheet numbers them."""
    return [str(photo_picks.photo_id(p["url"]) or "") for p in entry.get("photos", [])]


def fold(batch: dict, manifest: dict, known: dict) -> tuple:
    """``(records, errors)`` for a batch of notes. Nothing is kept from a batch
    with an error in it: a half-folded batch is harder to trust than none."""
    out, errors = {}, []
    for name, note in batch.items():
        sci = known.get(str(name).lower())
        if not sci:
            errors.append(f"{name}: not a plant in the catalogue")
            continue
        entry = manifest.get(sci)
        if entry is None:
            errors.append(f"{sci}: no sheet (run model_references.py fetch)")
            continue
        ids = photo_ids(entry)
        refs = {}
        for kind, numbers in (note.get("refs") or {}).items():
            if kind not in KINDS:
                errors.append(f"{sci}: '{kind}' is not one of {', '.join(KINDS)}")
                continue
            picked = []
            for n in numbers:
                if not isinstance(n, int) or not 1 <= n <= len(ids) or not ids[n - 1]:
                    errors.append(f"{sci}: no photograph {n} on its sheet "
                                  f"({len(ids)} photographs)")
                    continue
                picked.append(ids[n - 1])
            if picked:
                refs[kind] = picked
        faults = list(note.get("faults") or [])
        for f in faults:
            if f not in FAULTS:
                errors.append(f"{sci}: '{f}' is not a fault this file knows")
        score = note.get("score")
        if not isinstance(score, int) or not 0 <= score <= 10:
            errors.append(f"{sci}: a score from 0 to 10 is needed")
        out[sci] = {"refs": refs, "score": score, "faults": faults,
                    "note": str(note.get("note") or "").strip(), "read_in": PASS}
        if note.get("fixed"):
            out[sci]["fixed"] = str(note["fixed"])
    return out, errors


def verdict(record: dict) -> str:
    """One line for the sheet's corner."""
    if not record:
        return ""
    return f"{record.get('score')}/10  " + " ".join(record.get("faults") or [])


def add(text: str) -> int:
    batch = json.loads(text)
    records, errors = fold(batch, _load(MANIFEST, {}), names())
    if errors:
        print("Nothing kept:")
        for e in errors:
            print("  " + e)
        return 1
    review = load()
    for sci, rec in records.items():
        old = review.get(sci)
        if old:
            if not rec["refs"]:
                rec["refs"] = old.get("refs") or {}
            earlier = list(old.get("earlier") or [])
            if old.get("read_in") != rec["read_in"]:
                earlier.append({k: old[k] for k in ("read_in", "score", "faults", "note")
                                if k in old})
            if earlier:
                rec["earlier"] = earlier
        review[sci] = rec
    REVIEW.parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEW, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(review.items())), f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"Kept {len(records)}; {len(review)} plants read in all.")
    return 0


def summary() -> None:
    review = load()
    rows = {r["scientific_name"]: r for r in _load(MASTER, [])}
    faults = collections.Counter()
    by_type = collections.defaultdict(list)
    for sci, rec in review.items():
        for f in rec.get("faults") or []:
            faults[f] += 1
        by_type[(rows.get(sci) or {}).get("plant_type", "?")].append(rec.get("score") or 0)
    print(f"{len(review)} plants read.")
    print("\nScore by plant type (mean, and how many score 7 or more):")
    for t, scores in sorted(by_type.items()):
        good = sum(1 for s in scores if s >= 7)
        print(f"  {t:12s} {sum(scores) / len(scores):4.1f}   {good} of {len(scores)}")
    print("\nFaults, by how many plants share them:")
    for f, n in faults.most_common():
        print(f"  {n:4d}  {f:14s} {FAULTS[f]}")


def compare() -> None:
    """This pass's scores against each plant's last earlier reading."""
    review = load()
    rows = {r["scientific_name"]: r for r in _load(MASTER, [])}
    now = {s: r for s, r in review.items() if r.get("read_in") == PASS}
    print(f"{len(now)} of {len(review)} plants read in {PASS}.")
    by_type = collections.defaultdict(list)
    moved = []
    for sci, rec in now.items():
        before = (rec.get("earlier") or [{}])[-1]
        b, a = before.get("score"), rec.get("score")
        t = (rows.get(sci) or {}).get("plant_type", "?")
        by_type[t].append((b, a))
        if b is not None:
            moved.append((a - b, a, b, sci, (rows.get(sci) or {}).get("common_name", "")))
    print("\nBy plant type: mean before, mean now, 7 or more before and now")
    for t, pairs in sorted(by_type.items()):
        bs = [b for b, _ in pairs if b is not None]
        as_ = [a for _, a in pairs]
        print(f"  {t:12s} {sum(bs) / max(1, len(bs)):4.1f} -> {sum(as_) / len(as_):4.1f}"
              f"   {sum(1 for b in bs if b >= 7):3d} -> {sum(1 for a in as_ if a >= 7):3d}"
              f"  of {len(pairs)}")
    moved.sort()
    print("\nFell or stood still, lowest now first:")
    for d, a, b, sci, cn in sorted((m for m in moved if m[0] <= 0), key=lambda m: m[1])[:25]:
        print(f"  {b:2d} -> {a:2d}  {cn} ({sci})")
    print("\nRose most:")
    for d, a, b, sci, cn in sorted(moved, reverse=True)[:15]:
        print(f"  {b:2d} -> {a:2d}  {cn} ({sci})")
    faults = collections.Counter(f for r in now.values() for f in r.get("faults") or [])
    before = collections.Counter(f for r in now.values()
                                 for f in ((r.get("earlier") or [{}])[-1].get("faults") or []))
    print("\nFaults on the plants read in this pass, now and before:")
    for f, n in faults.most_common():
        print(f"  {n:4d}  (was {before.get(f, 0):3d})  {f}")


def todo() -> None:
    review = load()
    manifest = _load(MANIFEST, {})
    left = [s for s in manifest if (review.get(s) or {}).get("read_in") != PASS]
    print(f"{len(left)} of {len(manifest)} sheets not read in {PASS} yet.")
    for s in left:
        print(f"  {s}  ({manifest[s].get('common_name', '')})")


def show(name: str) -> int:
    sci = names().get(name.lower())
    rec = load().get(sci or "")
    if not rec:
        print(f"Nothing recorded for {name}.")
        return 1
    print(json.dumps({sci: rec}, indent=1, ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("step", choices=("add", "summary", "todo", "show", "faults", "compare"))
    ap.add_argument("name", nargs="?")
    args = ap.parse_args(argv)
    if args.step == "add":
        return add(sys.stdin.read())
    if args.step == "summary":
        summary()
    if args.step == "compare":
        compare()
    if args.step == "todo":
        todo()
    if args.step == "show":
        return show(args.name or "")
    if args.step == "faults":
        for f, words in FAULTS.items():
            print(f"{f:14s} {words}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
