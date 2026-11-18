#!/usr/bin/env python3
"""
picks_from_model_review.py — the 3D model references as each native's
photographs (V3.55; docs/plans/V3.55-the-photographs-arrive.md).

    python scripts/picks_from_model_review.py picks.json
    python scripts/fold_photo_picks.py picks.json --write

V3.48 read every candidate photograph of the region's reviewed natives
(``data/fetched/photo_candidates.json``) and kept the good ones as references
for the 3D models, by what each shows (``data/fetched/model_review.json``,
``refs``). The V3.35 picking page's file never reached a session, so the owner
chose those references as the photographs the app and the website show.

This writes them in the picking page's format, for ``fold_photo_picks.py`` to
check and fold: at most six a plant, one of each kind in turn (flower, whole
plant, fruit, winter, leaves, bark) in the order the review kept them, so the
flower leads (V3.35's D2). A tree, shrub or vine the colour review found has no
showy flower leads with the whole plant instead of a catkin. A CC0 photograph's
credit, "no rights reserved", gets the uploader's iNaturalist login, as the
older single photographs had. No network; nothing is written but ``picks.json``.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import native_here, photo_picks  # noqa: E402

FETCHED = ROOT / "data" / "fetched"
#: The review's kinds, in turn, and the slot each is filed under.
KINDS = (("flower", "flower"), ("habit", "habit"), ("fruit", "fruit"),
         ("winter", "winter"), ("leaf", "leaf"), ("bark", "bark_stem"))
WOODY = ("tree", "shrub", "vine")


def _order(row: dict, check: dict) -> tuple:
    if (row.get("plant_type") in WOODY
            and check.get("verdict") == "no_showy_flower"):
        return (KINDS[1], KINDS[0]) + KINDS[2:]
    return KINDS


def _credit(cand: dict) -> str:
    credit = " ".join((cand.get("attribution") or "").split())
    if credit.lower() == "no rights reserved" and cand.get("user"):
        credit += f", uploaded by {cand['user']}"
    return credit


def picks_for(refs: dict, candidates: dict, order: tuple) -> list:
    by_id = {str(c["photo"]): c for group in candidates.values()
             for c in group}
    queues = {kind: [str(p) for p in refs.get(kind) or []]
              for kind, _slot in order}
    picked, seen = [], set()
    while len(picked) < photo_picks.MAX_PICKS and any(queues.values()):
        for kind, slot in order:
            queue = queues[kind]
            while queue and queue[0] in seen:
                queue.pop(0)
            if not queue or len(picked) == photo_picks.MAX_PICKS:
                continue
            pid = queue.pop(0)
            seen.add(pid)
            cand = by_id[pid]
            picked.append({"photo": cand["photo"], "url": cand["url"],
                           "slot": slot, "attribution": _credit(cand),
                           "license": cand["license"],
                           "taken_on": cand.get("taken_on") or ""})
    return picked


def build() -> dict:
    candidates = json.loads((FETCHED / "photo_candidates.json")
                            .read_text(encoding="utf-8"))
    review = json.loads((FETCHED / "model_review.json")
                        .read_text(encoding="utf-8"))
    master = {r["scientific_name"]: r for r in json.loads(
        (ROOT / "data" / "plants_master.json").read_text(encoding="utf-8"))}
    checks = json.loads((ROOT / "data" / "flower_colour_checks.json")
                        .read_text(encoding="utf-8"))["checks"]
    answers = {}
    for sci in sorted(native_here.native_names()):
        if sci not in review or sci not in candidates:
            continue
        picks = picks_for(review[sci]["refs"], candidates[sci]["groups"],
                          _order(master[sci], checks.get(sci, {})))
        if picks:
            answers[sci] = {"picks": picks}
    return {"about": "V3.48's model references as display photographs "
                     "(V3.55, the owner's choice)", "answers": answers}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out", type=Path, help="where to write the picks file")
    args = ap.parse_args(argv)
    payload = build()
    args.out.write_text(json.dumps(payload, indent=1, ensure_ascii=False)
                        + "\n", encoding="utf-8")
    leads = collections.Counter(a["picks"][0]["slot"]
                                for a in payload["answers"].values())
    total = sum(len(a["picks"]) for a in payload["answers"].values())
    print(f"{len(payload['answers'])} plants, {total} photographs; "
          f"leading with {dict(leads)}. Wrote {args.out}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
