#!/usr/bin/env python3
"""
scripts/fold_animal_photos.py — fold the animal photographs the owner's PC
fetched into ``data/fauna_master.json`` (F270, V3.55).

Reads ``data/fetched/animal_photos.json`` (written by
``scripts/fetch_animal_photos.py``) and **refuses the whole file on one bad
row**, as ``fold_photo_picks.py`` does: an animal the catalogue does not hold,
a licence that may not ship (a bee's CC0 or CC BY only, the data gate's rule),
a credit missing where the licence asks for one, or an image that is not on
iNaturalist's photo hosts. Then it writes each photo onto the animal that has
none (``--force`` replaces one it has).

    python scripts/fold_animal_photos.py            # check only
    python scripts/fold_animal_photos.py --write    # check, then write

After ``--write``, bump ``src/db/plants.py:_SCHEMA_VERSION`` so installs
reseed, and run ``python -m src.cli validate-data``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from fetch_inaturalist_images import accept_for, license_ok  # noqa: E402

FAUNA = os.path.join(_ROOT, "data", "fauna_master.json")
IN = os.path.join(_ROOT, "data", "fetched", "animal_photos.json")
#: Where iNaturalist serves its photographs.
HOSTS = ("inaturalist-open-data.s3.amazonaws.com", "static.inaturalist.org")


def problems(photos: dict, fauna: list) -> list:
    """Every reason the file may not be folded, as sentences; empty when it
    may."""
    by_name = {f["scientific_name"]: f for f in fauna}
    out = []
    for sci, row in sorted(photos.items()):
        animal = by_name.get(sci)
        if animal is None:
            out.append(f"{sci}: not in the catalogue")
            continue
        code = (row.get("license") or "").lower()
        if not license_ok(code, accept_for(animal.get("taxon"))):
            out.append(f"{sci}: licence {code!r} may not ship for a "
                       f"{animal.get('taxon')}")
        if code != "cc0" and not (row.get("attribution") or "").strip():
            out.append(f"{sci}: {code} needs a credit")
        host = urllib.parse.urlparse(row.get("url") or "").hostname or ""
        if host not in HOSTS:
            out.append(f"{sci}: image host {host!r} is not iNaturalist's")
    return out


def fold(photos: dict, fauna: list, force: bool = False) -> int:
    """Write the photos onto the animals; return how many changed."""
    changed = 0
    for f in fauna:
        row = photos.get(f["scientific_name"])
        if row is None or (f.get("image_url") and not force):
            continue
        f["image_url"] = row["url"]
        f["image_attribution"] = row.get("attribution", "")
        f["image_license"] = row["license"]
        changed += 1
    return changed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="replace a photograph an animal already has")
    args = ap.parse_args(argv)
    with open(IN, encoding="utf-8") as fh:
        photos = json.load(fh).get("photos") or {}
    with open(FAUNA, encoding="utf-8") as fh:
        fauna = json.load(fh)
    bad = problems(photos, fauna)
    if bad:
        print("Refused, nothing written:")
        for line in bad:
            print("  " + line)
        return 1
    n = fold(photos, fauna, args.force)
    if not args.write:
        print(f"{len(photos)} photos checked; {n} would be written. "
              f"Add --write to write them.")
        return 0
    with open(FAUNA, "w", encoding="utf-8") as fh:
        json.dump(fauna, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(f"{n} animals given a photograph. Bump _SCHEMA_VERSION.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
