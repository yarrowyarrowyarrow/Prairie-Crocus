"""scripts/model_references.py (V3.47, V3.48): which plants, which photographs,
which months, the cameras and the sheet's grid. Offline: nothing is downloaded
or rendered here."""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import model_references as mr  # noqa: E402
from src import native_here  # noqa: E402


def _args(**kw):
    base = {"only": None, "place": None, "all_plants": False}
    base.update(kw)
    return SimpleNamespace(**base)


class WhichPlants(unittest.TestCase):

    def test_default_is_the_regions_native_list(self):
        rows = mr.plants(_args())
        self.assertEqual({r["scientific_name"] for r in rows},
                         set(native_here.native_names()))

    def test_only_takes_either_name(self):
        rows = mr.plants(_args(only=["wild bergamot", "Populus tremuloides"]))
        self.assertEqual(sorted(r["scientific_name"] for r in rows),
                         ["Monarda fistulosa", "Populus tremuloides"])

    def test_every_native_has_a_scene_built_from_its_row(self):
        """The render builds each scene from the catalogue as it stands (V3.48),
        so no plant waits on html/sprite_gallery_scenes.json being rebuilt."""
        for i, row in enumerate(mr.plants(_args())):
            scene = mr.scene_for(row, i, 7)
            self.assertTrue(scene.get("plants"), row["scientific_name"])
            self.assertEqual(scene["month"], 7)


class WhichMonths(unittest.TestCase):
    """A plant is drawn when it has something to show (V3.48)."""

    def test_a_wildflower_is_drawn_in_the_middle_of_its_flowering(self):
        self.assertEqual(mr.months({"plant_type": "wildflower",
                                    "bloom_period": "April-May"}), {"main": 4})
        self.assertEqual(mr.months({"plant_type": "wildflower",
                                    "bloom_period": "June-August"}), {"main": 7})

    def test_a_woody_plant_is_drawn_in_leaf_and_again_in_flower(self):
        got = mr.months({"plant_type": "shrub", "bloom_period": "May",
                         "fruit_period": "August", "fruit_color": "#801020"})
        self.assertEqual(got, {"main": 7, "flower": 5, "fruit": 8})

    def test_no_second_picture_when_july_already_shows_it(self):
        got = mr.months({"plant_type": "shrub", "bloom_period": "June-August",
                         "fruit_period": "July-August", "fruit_color": "#801020"})
        self.assertEqual(got, {"main": 7})

    def test_fruit_only_where_a_colour_is_recorded(self):
        got = mr.months({"plant_type": "tree", "bloom_period": "July",
                         "fruit_period": "September"})
        self.assertEqual(got, {"main": 7})

    def test_nothing_recorded_is_july(self):
        self.assertEqual(mr.months({"plant_type": "grass"}), {"main": 7})


class WhichPhotographs(unittest.TestCase):
    ROW = {"scientific_name": "Monarda fistulosa", "common_name": "Wild Bergamot",
           "image_url": "https://example.org/now.jpg"}

    def test_candidates_win_in_the_sheets_order_without_repeats(self):
        cands = {"Monarda fistulosa": {"groups": {
            "fruit": [{"url": "u3"}], "flower": [{"url": "u1"}, {"url": "u2"}],
            "now": [{"url": "u1"}]}}}
        photos, source = mr.photos_for(self.ROW, cands, {})
        self.assertEqual(source, "candidates")
        self.assertEqual([p["url"] for p in photos], ["u1", "u2", "u3"])
        self.assertEqual([p["group"] for p in photos], ["flower", "flower", "fruit"])

    def test_without_candidates_the_catalogues_photos_are_used(self):
        shipped = {"Monarda fistulosa": [{"url": "s1", "attribution": "x"}]}
        photos, source = mr.photos_for(self.ROW, {}, shipped)
        self.assertEqual(source, "shipped")
        self.assertEqual([p["url"] for p in photos], ["s1", "https://example.org/now.jpg"])


class Cameras(unittest.TestCase):

    def test_framed_on_the_plants_size(self):
        small = mr.views({"height_m": 0.5, "canopy_m": 0.4})
        tree = mr.views({"height_m": 20, "canopy_m": 8})
        self.assertLess(small["side"]["at"][2], 1.0)
        self.assertGreater(tree["side"]["at"][2], 20)
        self.assertEqual(tree["side"]["looks_at"], [0, 10.0, 0])

    def test_a_low_plant_is_looked_down_on_and_a_tree_is_not(self):
        """Seen level from half its own height a knee-high plant shows the
        undersides of its flowers; a tree is seen level."""
        small = mr.views({"height_m": 0.5, "canopy_m": 0.4})["side"]
        tree = mr.views({"height_m": 20, "canopy_m": 8})["side"]
        self.assertGreater(small["at"][1], small["looks_at"][1] + 0.15)
        self.assertEqual(tree["at"][1], tree["looks_at"][1])


class TheSheet(unittest.TestCase):

    def test_photographs_go_round_the_models(self):
        cells = mr._cells(8)
        self.assertNotIn((0, 0), cells)          # the side view's block
        self.assertNotIn((1, 1), cells)
        self.assertNotIn((2, 0), cells)          # the view from above
        self.assertEqual(cells[0], (3, 0))
        self.assertEqual(len(set(cells)), 8)
        self.assertEqual(mr._cells(3, extras=2)[0], (5, 0))

    def test_the_header_says_what_the_model_was_drawn_from(self):
        words = mr.recorded({"growth_form": "clump", "leaf_shape": "lanceolate",
                             "leaf_size_cm": 8.0, "flower_arch": "head",
                             "petal_count": 5, "flowering_stems": 28})
        for bit in ("body: clump", "lanceolate 8.0 cm", "head", "x5", "28 stems"):
            self.assertIn(bit, words)
        self.assertIn("not recorded", mr.recorded({}))


if __name__ == "__main__":
    unittest.main()
