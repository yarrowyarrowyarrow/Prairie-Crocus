"""scripts/model_review.py (V3.48): the record of what each reference sheet
showed. Offline; reads the committed review and candidates files."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import model_review as mv  # noqa: E402
from src import photo_picks  # noqa: E402

MANIFEST = {"Monarda fistulosa": {"photos": [
    {"url": "https://inaturalist-open-data.s3.amazonaws.com/photos/111/medium.jpg"},
    {"url": "https://inaturalist-open-data.s3.amazonaws.com/photos/222/medium.jpg"},
    {"url": "https://inaturalist-open-data.s3.amazonaws.com/photos/333/medium.jpg"}]}}
KNOWN = {"monarda fistulosa": "Monarda fistulosa", "wild bergamot": "Monarda fistulosa"}


class Folding(unittest.TestCase):

    def test_sheet_numbers_become_photograph_ids(self):
        recs, errors = mv.fold({"Wild Bergamot": {
            "refs": {"habit": [3], "flower": [1, 2]}, "score": 6,
            "faults": ["flower_colour"], "note": " Lilac, not pink. "}},
            MANIFEST, KNOWN)
        self.assertEqual(errors, [])
        rec = recs["Monarda fistulosa"]
        self.assertEqual(rec["refs"], {"habit": ["333"], "flower": ["111", "222"]})
        self.assertEqual(rec["note"], "Lilac, not pink.")
        self.assertEqual(rec["read_in"], mv.PASS)

    def test_a_low_score_with_no_fault_is_refused(self):
        """V3.66's re-read wrote seven 'as before' readings under 7 with no
        fault; the suite caught it after the fact, the tool now refuses it."""
        _, errors = mv.fold({"Monarda fistulosa": {"score": 5, "faults": []}},
                            MANIFEST, KNOWN)
        self.assertTrue(any("needs at least one fault" in e for e in errors), errors)
        _, errors = mv.fold({"Monarda fistulosa": {"score": 7, "faults": []}},
                            MANIFEST, KNOWN)
        self.assertEqual(errors, [])

    def test_a_bad_note_is_named(self):
        for note, word in (
                ({"refs": {"habit": [4]}, "score": 5}, "no photograph 4"),
                ({"refs": {"petal": [1]}, "score": 5}, "petal"),
                ({"faults": ["ugly"], "score": 5}, "ugly"),
                ({"score": 11}, "score"),
                ({}, "score")):
            _, errors = mv.fold({"Monarda fistulosa": note}, MANIFEST, KNOWN)
            self.assertTrue(any(word in e for e in errors), (note, errors))
        _, errors = mv.fold({"Not a plant": {"score": 5}}, MANIFEST, KNOWN)
        self.assertIn("not a plant in the catalogue", errors[0])


class TheRecord(unittest.TestCase):
    """The committed review: every plant is in the catalogue, every fault is a
    word the file knows, and every reference is a photograph the candidates
    file holds for that plant (so its credit can be found)."""

    @classmethod
    def setUpClass(cls):
        cls.review = mv.load()
        cls.rows = {r["scientific_name"] for r in
                    json.loads(mv.MASTER.read_text(encoding="utf-8"))}
        cands = json.loads((ROOT / "data" / "fetched" / "photo_candidates.json")
                           .read_text(encoding="utf-8"))
        cls.ids = {sci: {str(photo_picks.photo_id(p["url"]))
                         for group in (e.get("groups") or {}).values() for p in group}
                   for sci, e in cands.items()}

    def test_there_is_a_record(self):
        self.assertTrue(self.review)

    def test_every_record_is_well_formed(self):
        for sci, rec in self.review.items():
            self.assertIn(sci, self.rows)
            self.assertIsInstance(rec["score"], int, sci)
            self.assertTrue(0 <= rec["score"] <= 10, sci)
            for f in rec["faults"]:
                self.assertIn(f, mv.FAULTS, sci)
            for kind, ids in rec["refs"].items():
                self.assertIn(kind, mv.KINDS, sci)
                for pid in ids:
                    self.assertIn(pid, self.ids.get(sci, set()), (sci, kind))

    def test_a_low_score_says_why(self):
        for sci, rec in self.review.items():
            if rec["score"] < 7:
                self.assertTrue(rec["faults"] and rec["note"], sci)


if __name__ == "__main__":
    unittest.main()
