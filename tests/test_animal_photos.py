"""
tests/test_animal_photos.py — the animal photographs fetched on the owner's
PC and folded in a session (F270, V3.55): which animals are asked for, which
photo is taken, and what the fold refuses. No network.
"""

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import fetch_animal_photos as fetch  # noqa: E402
import fold_animal_photos as fold  # noqa: E402


def _animal(sci, name, taxon="lepidoptera", url=""):
    return {"scientific_name": sci, "common_name": name, "taxon": taxon,
            "image_url": url, "image_attribution": "", "image_license": ""}


class WhichAnimals(unittest.TestCase):

    def test_named_single_species_without_a_photo_most_recorded_first(self):
        fauna = [_animal("Danaus plexippus", "Monarch"),
                 _animal("Andrena spp.", "Mining Bees", "bee"),
                 _animal("Bombus x", "Bombus x", "bee"),
                 _animal("Papilio canadensis", "Canadian Tiger Swallowtail"),
                 _animal("Vanessa cardui", "Painted Lady", url="http://x")]
        near = {"Papilio canadensis": {"near": 500},
                "Danaus plexippus": {"near": 20}}
        self.assertEqual([f["common_name"] for f in fetch.wanted(fauna, near)],
                         ["Canadian Tiger Swallowtail", "Monarch"])
        self.assertIn("Painted Lady", [f["common_name"] for f in
                                       fetch.wanted(fauna, near, force=True)])

    def test_an_observation_photo_that_may_ship_at_medium_size(self):
        results = [{"id": 1, "photos": [{"license_code": "cc-by-nc",
                                         "url": "https://s/1/square.jpg"}]},
                   {"id": 2, "photos": [{"license_code": "cc-by-sa",
                                         "url": "https://s/2/square.jpg",
                                         "attribution": "(c) A"}]}]
        row = fetch.from_observations(results, {"cc0", "cc-by", "cc-by-sa"})
        self.assertEqual(row["url"], "https://s/2/medium.jpg")
        self.assertEqual(row["license"], "cc-by-sa")
        self.assertTrue(row["page"].endswith("/observations/2"))
        # A bee's photo is CC0 or CC BY only (the data gate's rule).
        self.assertIsNone(fetch.from_observations(results, {"cc0", "cc-by"}))


class TheFold(unittest.TestCase):

    _URL = "https://inaturalist-open-data.s3.amazonaws.com/photos/1/medium.jpg"

    def test_one_bad_row_refuses_the_file(self):
        fauna = [_animal("Danaus plexippus", "Monarch"),
                 _animal("Bombus terricola", "Yellow-banded Bumble Bee", "bee")]
        good = {"Danaus plexippus": {"url": self._URL, "license": "cc-by",
                                     "attribution": "(c) A"}}
        self.assertEqual(fold.problems(good, fauna), [])
        for bad in (
                {"Nope nope": {"url": self._URL, "license": "cc0"}},
                {"Bombus terricola": {"url": self._URL, "license": "cc-by-sa",
                                      "attribution": "(c) A"}},
                {"Danaus plexippus": {"url": self._URL, "license": "cc-by"}},
                {"Danaus plexippus": {"url": "https://example.com/a.jpg",
                                      "license": "cc0"}}):
            self.assertTrue(fold.problems(bad, fauna), bad)

    def test_it_fills_only_what_has_no_photo_unless_told(self):
        fauna = [_animal("Danaus plexippus", "Monarch"),
                 _animal("Vanessa cardui", "Painted Lady", url="http://old")]
        photos = {n: {"url": self._URL, "license": "cc0", "attribution": ""}
                  for n in ("Danaus plexippus", "Vanessa cardui")}
        self.assertEqual(fold.fold(photos, fauna), 1)
        self.assertEqual(fauna[0]["image_url"], self._URL)
        self.assertEqual(fauna[1]["image_url"], "http://old")
        self.assertEqual(fold.fold(photos, fauna, force=True), 2)


if __name__ == "__main__":
    unittest.main()
