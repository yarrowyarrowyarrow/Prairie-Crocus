#!/usr/bin/env python3
"""
scripts/fetch_animal_photos.py — a photograph for each animal a homeowner may
be shown, from iNaturalist, openly licensed (F270, V3.55; docs/plans/
V3.55-the-year-and-who-it-feeds.md).

**Runs on the owner's PC**: no cloud session reaches iNaturalist's API.

Design › Through the year names the animals recorded eating a design's plants
and recorded near the yard; 58 of the 1,144 catalogue animals carry a
photograph. This finds one for each animal that could be named and has none:
an English name, one species (no *spp.*), most recorded near the region pack's
place first.

For each it asks iNaturalist for the species, reads its own photo set first
(``fetch_inaturalist_images``, whose licence rules this uses unchanged: CC0,
CC BY and CC BY-SA, **a bee CC0 or CC BY only**), and when none of those may
ship, the most-liked research-grade observations whose photo may. V3.34 found
that the species' own set is where the old fetch fell short, not the licences:
observations are where the open photographs are.

It writes ``data/fetched/animal_photos.json``, which is committed and folded
into ``data/fauna_master.json`` in a session by ``scripts/fold_animal_photos.py``.
Resumable: an animal already in the file is not asked again (``--force`` asks
again). About one request a second, as iNaturalist asks.

Windows (PowerShell), from the repo root:

    python .\\scripts\\fetch_animal_photos.py --probe
    python .\\scripts\\fetch_animal_photos.py

``--probe`` asks about one animal (the Monarch) and prints what came back,
without writing anything: run it first, because this script was written
without seeing a live answer. ``--limit 20`` stops after twenty animals.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from fetch_inaturalist_images import (  # noqa: E402
    accept_for, license_ok, open_candidates, taxon_candidates,
)

FAUNA = os.path.join(_ROOT, "data", "fauna_master.json")
RECORDS = os.path.join(_ROOT, "data", "regions", "edmonton",
                       "animal_records.json")
OUT = os.path.join(_ROOT, "data", "fetched", "animal_photos.json")
API = "https://api.inaturalist.org/v1"
#: How many observations to read when the species' own photos may not ship.
OBSERVATIONS = 10


# ── Which animals (no network) ──────────────────────────────────────────────

def wanted(fauna: list, near: dict, force: bool = False) -> list:
    """The animals to look for, most recorded near the place first: those that
    could be named (an English name, one species) and, unless ``force``, have
    no photograph yet."""
    from src.through_the_year import one_species
    rows = []
    for f in fauna:
        if not one_species(f):
            continue
        if f.get("image_url") and not force:
            continue
        rows.append(f)
    rows.sort(key=lambda f: (-(near.get(f["scientific_name"]) or {}).get(
        "near", 0), f["common_name"].lower()))
    return rows


def from_observations(results: list, accept) -> "dict | None":
    """The first observation photo whose licence may ship: ``{url,
    attribution, license, page}``, the medium-size image."""
    for obs in results or []:
        for ph in obs.get("photos") or []:
            code = (ph.get("license_code") or "").strip().lower()
            if not license_ok(code, accept):
                continue
            url = (ph.get("url") or "").replace("/square.", "/medium.")
            if not url:
                continue
            return {"url": url,
                    "attribution": (ph.get("attribution") or "").strip(),
                    "license": code,
                    "page": f"https://www.inaturalist.org/observations/"
                            f"{obs.get('id')}"}
    return None


# ── Network ─────────────────────────────────────────────────────────────────

def _get(path: str, params: dict) -> dict:
    from src.http_utils import user_agent
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": user_agent(), "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def find(animal: dict, sleep: float) -> "dict | None":
    """One photograph for ``animal``, or None."""
    accept = accept_for(animal.get("taxon"))
    sci = animal["scientific_name"]
    found = _get("taxa", {"q": sci, "rank": "species", "per_page": 5})
    taxon = next((t for t in found.get("results") or []
                  if (t.get("name") or "").lower() == sci.lower()), None)
    time.sleep(sleep)
    if taxon is None:
        return None
    detail = _get(f"taxa/{int(taxon['id'])}", {}).get("results") or [taxon]
    time.sleep(sleep)
    pick = next(open_candidates(taxon_candidates(detail[0]), accept), None)
    if pick:
        url, attribution, code = pick
        return {"url": url, "attribution": attribution, "license": code,
                "page": f"https://www.inaturalist.org/taxa/{taxon['id']}",
                "taxon_id": taxon["id"]}
    obs = _get("observations", {
        "taxon_id": taxon["id"], "quality_grade": "research",
        "photo_license": ",".join(sorted(accept)), "order_by": "votes",
        "per_page": OBSERVATIONS})
    time.sleep(sleep)
    row = from_observations(obs.get("results"), accept)
    if row:
        row["taxon_id"] = taxon["id"]
    return row


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--probe", action="store_true",
                    help="ask about the Monarch and print it; write nothing")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true",
                    help="ask again about animals already found")
    ap.add_argument("--sleep", type=float, default=1.0)
    args = ap.parse_args(argv)

    with open(FAUNA, encoding="utf-8") as fh:
        fauna = json.load(fh)
    if args.probe:
        monarch = next(f for f in fauna
                       if f["scientific_name"] == "Danaus plexippus")
        print(json.dumps(find(monarch, args.sleep), indent=2))
        return 0
    try:
        with open(RECORDS, encoding="utf-8") as fh:
            near = json.load(fh).get("animals") or {}
    except FileNotFoundError:
        near = {}
    try:
        with open(OUT, encoding="utf-8") as fh:
            done = json.load(fh)
    except FileNotFoundError:
        done = {"_about": "Photographs for animals, from iNaturalist, openly "
                          "licensed. Written by scripts/fetch_animal_photos.py "
                          "on the owner's PC; folded by "
                          "scripts/fold_animal_photos.py.",
                "photos": {}, "none": []}
    todo = [f for f in wanted(fauna, near, args.force)
            if args.force or (f["scientific_name"] not in done["photos"]
                              and f["scientific_name"] not in done["none"])]
    if args.limit:
        todo = todo[:args.limit]
    print(f"{len(todo)} animals to look for")
    for i, animal in enumerate(todo, 1):
        sci = animal["scientific_name"]
        try:
            row = find(animal, args.sleep)
        except Exception as exc:                           # noqa: BLE001
            print(f"  {sci}: {exc}; stopping here, run again to carry on")
            break
        if row:
            done["photos"][sci] = row
        elif sci not in done["none"]:
            done["none"].append(sci)
        print(f"  {i}/{len(todo)} {animal['common_name']}: "
              f"{row['license'] if row else 'none that may ship'}")
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(done, fh, indent=1, sort_keys=True)
    print(f"{len(done['photos'])} found, {len(done['none'])} with none that "
          f"may ship. Commit {os.path.relpath(OUT, _ROOT)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
