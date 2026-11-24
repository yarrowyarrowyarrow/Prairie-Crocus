"""
tests/test_shrub_apart.py — the region's shrubs can be told apart (V3.63, F268).

The V3.62 re-read found a dozen of the 34 native shrubs were one green oval in
July: one green, one surface, one outline, and fruit hidden behind the leaves
or gone before the snow. V3.63 read each shrub's leaf colour, leaf surface,
crown outline and how long it holds its fruit off its photographs, and draws
them. What can go wrong quietly, each with a test here:

  * a shrub loses its colour or surface and falls back to the shared green;
  * the crown words in Python and in the viewer drift apart, so a crown the
    catalogue calls a vase is drawn as the form's own outline, or nothing;
  * the crown is left out of the body's cache key, so two crowns share one body;
  * fruit held into winter is not held, or is held past its month, or held
    across the new year the wrong way;
  * a shrub's fruit goes back to the points behind the leaves;
  * a fruit colour the photographs corrected is reseeded back to red.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from src import data_quality, native_here, shrub_habit  # noqa: E402
from src.scene_contract import _foliage_color, _fruit_window  # noqa: E402

_JS = os.path.join(_ROOT, "html", "scene3d")


def _js(name: str) -> str:
    with open(os.path.join(_JS, name), encoding="utf-8") as fh:
        return fh.read()


def _natives() -> list:
    with open(os.path.join(_ROOT, "data", "plants_master.json"), encoding="utf-8") as fh:
        rows = json.load(fh)
    names = native_here.native_names()
    return [r for r in rows if r["scientific_name"] in names and r.get("plant_type") == "shrub"]


class TheCatalogue(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.shrubs = _natives()

    def test_there_are_the_34(self):
        self.assertEqual(len(self.shrubs), 34)

    def test_every_native_shrub_has_its_own_leaf_colour_and_surface(self):
        for r in self.shrubs:
            self.assertRegex(r.get("leaf_color") or "", r"^#[0-9a-f]{6}$", r["common_name"])
            self.assertIn(r.get("leaf_surface"), data_quality.LEAF_SURFACES, r["common_name"])

    def test_the_greens_differ(self):
        """The fault was one green for 26 of 34; no colour now holds more than four."""
        from collections import Counter
        most = Counter(_foliage_color(r) for r in self.shrubs).most_common(1)[0][1]
        self.assertLessEqual(most, 4)

    def test_every_native_shrub_has_a_crown_in_a_shrubs_words(self):
        for r in self.shrubs:
            self.assertIn(r.get("crown_shape"), data_quality.SHRUB_CROWN_SHAPES, r["common_name"])
            self.assertIsNotNone(r.get("crown_clear"), r["common_name"])

    def test_held_fruit_is_fruit_and_after_its_season(self):
        for r in self.shrubs:
            held = r.get("fruit_held_until")
            if held is None:
                continue
            self.assertTrue(r.get("fruit_color"), r["common_name"])
            w = _fruit_window(r)
            self.assertTrue(w["fruit_start"], r["common_name"])
            self.assertNotIn(held, range(w["fruit_start"], w["fruit_end"] + 1), r["common_name"])

    def test_the_winter_fruit_the_photographs_show(self):
        held = {r["common_name"] for r in self.shrubs if r.get("fruit_held_until")}
        for name in ("Common Snowberry", "Highbush Cranberry", "Prickly Wild Rose",
                     "Silver Buffaloberry", "Silverberry"):
            self.assertIn(name, held)

    def test_the_black_currants_are_black(self):
        """Drawn red until V3.63; every photograph shows black. The fruit
        seeder owns the correction, so a re-run does not undo it."""
        import seed_fruit_morphology as sfm
        by = {r["common_name"]: r for r in self.shrubs}
        for name, sci in (("Wild Black Currant", "Ribes americanum"),
                          ("Bristly Black Currant", "Ribes lacustre"),
                          ("Bracted Honeysuckle", "Lonicera involucrata")):
            self.assertEqual(by[name]["fruit_color"], "#1c1a22")
            self.assertEqual(sfm.FRUIT_COLOR_FIX[sci], "#1c1a22")

    def test_the_fruit_seeder_and_the_catalogue_agree(self):
        import seed_fruit_morphology as sfm
        with open(os.path.join(_ROOT, "data", "plants_master.json"), encoding="utf-8") as fh:
            rows = json.load(fh)
        applied, missing, recoloured = sfm.apply(rows, check=True)
        self.assertEqual(recoloured, 0, "a fruit colour fix is not in the catalogue")


class TheBlock(unittest.TestCase):

    def _shrub(self, **over):
        p = {"plant_type": "shrub", "branching": "multi_stem", "woody_stems": 12,
             "leaf_shape": "ovate", "leaf_size_cm": 5.0, "leaf_arrangement": "alternate",
             "leaf_data_source": "photo", "height_m": 3, "canopy_m": 3}
        p.update(over)
        return p

    def test_a_read_crown_rides_in_the_block(self):
        d = shrub_habit.drawn_block(self._shrub(crown_shape="vase", crown_clear=0.1), "clump")
        self.assertEqual((d["crown"], d["clear"]), ("vase", 0.1))

    def test_no_crown_or_a_trees_word_draws_the_forms_outline(self):
        for shape in ("", "conical", "spire"):
            d = shrub_habit.drawn_block(self._shrub(crown_shape=shape, crown_clear=0.3), "clump")
            self.assertEqual((d["crown"], d["clear"]), ("", 0.0), shape)

    def test_the_scene_carries_the_held_month(self):
        w = _fruit_window({"fruit_period": "September-October", "fruit_held_until": 3})
        self.assertEqual(w, {"fruit_start": 9, "fruit_end": 10, "fruit_held_until": 3})
        self.assertEqual(_fruit_window({"fruit_held_until": 3})["fruit_held_until"], 0)


class TheViewerAgrees(unittest.TestCase):

    def test_the_crowns_are_the_same_words(self):
        words = re.search(r"const WOODY_CROWNS = \[([^\]]*)\]", _js("03d-woody.js")).group(1)
        self.assertEqual(tuple(re.findall(r"'(\w+)'", words)), shrub_habit.CROWNS)

    def test_every_crown_has_its_outline_bias_and_stems(self):
        woody = _js("03d-woody.js")
        env = woody[woody.index("function _wdCrownEnvelope"):]
        env = env[:env.index("\n}\n")]
        for crown in shrub_habit.CROWNS:
            self.assertIn(f"case '{crown}'", env, crown)
            for table in ("_WD_CROWN_BIAS", "_WD_CROWN_STEM"):
                body = re.search(table + r" = \{(.*?)\};", woody, re.S).group(1)
                self.assertRegex(body, rf"\b{crown}:", f"{table} {crown}")

    def test_the_crown_is_in_the_bodys_key(self):
        key = _js("03d-woody.js")
        key = key[key.index("function woodyKeyFor"):]
        key = key[:key.index("\n}\n")]
        self.assertIn("d.crown", key)
        self.assertIn("d.clear", key)

    def test_a_shrubs_fruit_goes_to_the_cards(self):
        fruit = _js("11-fruit.js")
        self.assertIn("woodyFruitApplies(p)) { carded.push(p); continue; }", fruit)
        self.assertIn("buildWoodyFruit(carded, month, terrain)", fruit)
        order = re.findall(r"'scene3d/([\w-]+\.js)'", _js("chunks.js"))
        self.assertLess(order.index("15c-woodybloom.js"), order.index("15d-woodyfruit.js"))
        self.assertLess(order.index("11-fruit.js"), order.index("15d-woodyfruit.js"))

    def test_the_fruit_estimates_are_named(self):
        head = _js("15d-woodyfruit.js")[:3200]
        for word in ("WOODY_FRUIT_SIZE", "WOODY_FRUIT_PER_M2", "WOODY_FRUIT_HELD",
                     "WOODY_FRUIT_WINTER", "estimate"):
            self.assertIn(word, head)

    def test_no_month_is_compared_in_the_chunk(self):
        """The season is the scene's (01d-season.js, V3.46); the fruit's own
        months come from the catalogue, never typed here."""
        self.assertIsNone(re.search(r"month\s*[<>=!]=?\s*\d", _js("15d-woodyfruit.js")))


@unittest.skipUnless(shutil.which("node") or shutil.which("nodejs"), "needs node")
class TheFruitMonths(unittest.TestCase):
    """fruitInSeason, run in node: in season, held after it, across the new year."""

    def _ask(self, p, months):
        src = _js("15d-woodyfruit.js")
        fn = src[src.index("function fruitInSeason"):]
        fn = fn[:fn.index("\n}\n") + 2]
        prog = fn + f"\nconst p = {json.dumps(p)};\nconsole.log(JSON.stringify({json.dumps(months)}.map(m => fruitInSeason(p, m))));"
        node = shutil.which("node") or shutil.which("nodejs")
        out = subprocess.run([node, "-e", prog], capture_output=True, text=True, encoding="utf-8", check=True)
        return json.loads(out.stdout)

    def test_a_snowberry_holds_into_march(self):
        got = self._ask({"fruit_start": 9, "fruit_end": 10, "fruit_held_until": 3},
                        list(range(1, 13)))
        self.assertEqual(got, ["held", "held", "held", None, None, None, None, None,
                               "on", "on", "held", "held"])

    def test_without_a_held_month_it_goes_with_its_season(self):
        got = self._ask({"fruit_start": 7, "fruit_end": 8}, [6, 7, 8, 9, 12])
        self.assertEqual(got, [None, "on", "on", None, None])

    def test_held_to_the_month_after_ends_there(self):
        got = self._ask({"fruit_start": 8, "fruit_end": 9, "fruit_held_until": 11}, [9, 10, 11, 12])
        self.assertEqual(got, ["on", "held", "held", None])

    def test_no_fruit_season_no_fruit(self):
        self.assertEqual(self._ask({"fruit_held_until": 3}, [1, 3]), [None, None])


if __name__ == "__main__":
    unittest.main()
