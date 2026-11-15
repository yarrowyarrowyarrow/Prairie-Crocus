"""Flowers and fruit sit on the plant, petals and blades pass light, and low
plants are not baked dark (V3.48, docs/plans/V3.48-models-against-photographs.md).

Static: these read the viewer's and the generator's source. What the changes
look like is in the before and after sheets scripts/model_references.py draws."""

import os
import re
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_JS = os.path.join(_ROOT, "html", "scene3d")


def _read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as f:
        return f.read()


class OnThePlant(unittest.TestCase):

    def test_the_chunk_is_loaded(self):
        files = re.findall(r"'scene3d/([\w-]+\.js)'", _read(_JS, "chunks.js"))
        self.assertIn("15b-anchors.js", files)
        self.assertTrue(os.path.exists(os.path.join(_JS, "15b-anchors.js")))

    def test_flowers_and_fruit_ask_where_the_body_is(self):
        """Without the call a bloom goes back to a random spot in the air over
        the plant, which is what 83 of 250 sheets showed."""
        self.assertIn("bloomAnchors(p, heads, month)", _read(_JS, "15-florets.js"))
        self.assertIn("bloomAnchors(p, n, month)", _read(_JS, "11-fruit.js"))

    def test_the_bodies_say_where_they_are(self):
        quality = _read(_JS, "04-quality.js")
        self.assertIn("noteBloomBody(p, arch,", quality, "herbs do not note their body")
        self.assertIn("bloomBodiesReset()", quality, "a scene push keeps the last scene's bodies")
        self.assertIn("window.vineHostOf", _read(_JS, "22-vines.js"),
                      "a shrub's crown cannot be found")

    def test_a_herbs_anchors_are_its_tips_and_a_crowns_are_its_outside(self):
        src = _read(_JS, "15b-anchors.js")
        for name in ("_stemTips", "_crownPoints", "bloomAnchors", "woodyBloomCount",
                     "woodyBloomGain"):
            self.assertIn(f"function {name}(", src)
        # A tip is high on the plant: lower points are leaves.
        cut = float(re.search(r"y < top \* ([\d.]+)\) continue", src).group(1))
        self.assertGreaterEqual(cut, 0.6)
        # Larger than life, within a stated bound, and only on woody plants.
        gain = re.search(r"Math\.min\(([\d.]+), 1 \+", src)
        self.assertLessEqual(float(gain.group(1)), 3.0)
        self.assertIn("return 1;", src[src.index("function woodyBloomGain"):])

    def test_no_month_is_compared_here(self):
        """The season is 01d-season.js's to say (V3.46): this chunk only passes
        the month to leafless()."""
        src = _read(_JS, "15b-anchors.js")
        self.assertIsNone(re.search(r"month\s*[<>=!]=?\s*\d", src))


class Light(unittest.TestCase):

    def test_a_petal_passes_light(self):
        src = _read(_JS, "15-florets.js")
        share = float(re.search(r"const PETAL_TRANSLUCENCY = ([\d.]+);", src).group(1))
        self.assertTrue(0.5 <= share < 1.0, share)
        self.assertIn("applyLeafLight(shader, PETAL_TRANSLUCENCY)", src)

    def test_low_plants_are_baked_with_the_low_rule(self):
        src = _read(_ROOT, "scripts", "blender", "assetlib", "build_all.py")
        self.assertEqual(src.count("**LOW_AO)"), 2, "herbs and layers both")
        args = re.search(r"LOW_AO = dict\((.+?)\)", src).group(1)
        got = dict(kv.split("=") for kv in args.replace(" ", "").split(","))
        self.assertEqual(float(got["floor_z"]), 0.0)
        self.assertGreaterEqual(float(got["gradient_floor"]), 0.8)
        self.assertLessEqual(float(got["max_dist"]), 0.2)


if __name__ == "__main__":
    unittest.main()
