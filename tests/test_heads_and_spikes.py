"""
tests/test_heads_and_spikes.py — leaf colours, daisy heads and dense spikes
(V3.64, F268).

What can go wrong quietly, each with a test here:

  * a native loses its leaf colour and falls back to its type's one green;
  * a colour read alone is written as if the leaves and habit had been read,
    so an unread water plant is drawn in a body of its own (P9), or a read
    plant's citation is overwritten by a sitting that read only its colour;
  * a head is drawn smaller than it was, or larger than its stated limit, or
    faces straight up again;
  * a dense spike goes back to florets on a string, or a loose raceme or a
    shrub's cluster is taken for one;
  * the chunk loads after something that calls it at build time.
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

from src import native_here  # noqa: E402

_JS = os.path.join(_ROOT, "html", "scene3d")


def _js(name):
    with open(os.path.join(_JS, name), encoding="utf-8") as fh:
        return fh.read()


def _fn(src, name):
    s = src[src.index("function " + name):]
    return s[:s.index("\n}\n") + 2]


class TheCatalogue(unittest.TestCase):

    def test_every_native_has_a_leaf_colour(self):
        with open(os.path.join(_ROOT, "data", "plants_master.json"), encoding="utf-8") as fh:
            rows = json.load(fh)
        names = native_here.native_names()
        bare = [r["common_name"] for r in rows
                if r["scientific_name"] in names and not r.get("leaf_color")]
        self.assertEqual(bare, [])

    def test_the_grey_plants_are_grey(self):
        """The fault was one green for the sageworts, pussytoes and silverweed."""
        import colorsys
        with open(os.path.join(_ROOT, "data", "plants_master.json"), encoding="utf-8") as fh:
            rows = {r["common_name"]: r for r in json.load(fh)}
        for name in ("Prairie Sagewort", "Prairie Sage", "Littleleaf Pussytoes", "Silverweed"):
            c = rows[name]["leaf_color"]
            r, g, b = (int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))
            self.assertLess(colorsys.rgb_to_hsv(r, g, b)[1], 0.25, name)


class TheReadingTool(unittest.TestCase):

    def setUp(self):
        import leaf_readings
        self.lr = leaf_readings
        self.rows = [{"scientific_name": "Testus aqua", "common_name": "Test Water Plant",
                      "plant_type": "aquatic"},
                     {"scientific_name": "Testus read", "common_name": "Test Read",
                      "plant_type": "wildflower", "leaf_data_source": "photo",
                      "leaf_data_citation": "iNaturalist photographs 1 (read V3.48)"}]
        self.review = {"Testus aqua": {"refs": {"leaf": ["9"]}},
                       "Testus read": {"refs": {"leaf": ["8"]}}}

    def test_a_colour_alone_needs_no_habit(self):
        batch = {"Testus aqua": {"leaf_color": "#5f7a3a"}}
        self.assertEqual(self.lr.problems(batch, {r["scientific_name"]: r for r in self.rows},
                                          self.review), [])

    def test_a_colour_alone_leaves_the_leaf_pair_as_it_was(self):
        self.lr.apply({"Testus aqua": {"leaf_color": "#5F7A3A"},
                       "Testus read": {"leaf_color": "#6a9a4a"}}, self.rows, self.review)
        aqua, read = self.rows
        self.assertEqual(aqua["leaf_color"], "#5f7a3a")
        self.assertNotIn("leaf_data_source", aqua, "an unread plant was marked read")
        self.assertEqual(read["leaf_data_citation"], "iNaturalist photographs 1 (read V3.48)")


class TheViewerAgrees(unittest.TestCase):

    def test_the_chunk_loads_and_the_florets_use_it(self):
        order = re.findall(r"'scene3d/([\w-]+\.js)'", _js("chunks.js"))
        self.assertIn("15e-heads.js", order)
        florets = _js("15-florets.js")
        self.assertIn("headSpray(p, b.arch", florets)
        self.assertNotIn("function _inflorescence", florets, "defined twice")
        self.assertIn("function _inflorescence", _js("15e-heads.js"))

    def test_a_dense_wildflower_cluster_goes_to_the_cards(self):
        self.assertIn("denseClusterApplies(p)", _js("15c-woodybloom.js"))

    def test_the_estimates_are_named(self):
        head = _js("15e-heads.js")[:3200]
        for word in ("HEAD_MIN_M", "HEAD_GAIN_MAX", "HEAD_TILT", "HEADS_PER_CLUSTER",
                     "DENSE_FLORETS", "estimate"):
            self.assertIn(word, head)


@unittest.skipUnless(shutil.which("node") or shutil.which("nodejs"), "needs node")
class TheRulesInNode(unittest.TestCase):

    def _run(self, expr):
        src = _js("15e-heads.js")
        consts = "\n".join(l for l in src.splitlines()
                           if re.match(r"const (HEAD_|HEADS_|DENSE_)", l))
        prog = "\n".join([
            "let STYLISED = false;",
            "function woodyBloomGain(p) { return (p.plant_type === 'shrub' || p.plant_type === 'tree')"
            " ? Math.max(1, Math.min(2.5, 1 + ((p.height_m || 1) - 1.5) / 3)) : 1; }",
            consts, _fn(src, "bloomGain"), _fn(src, "headSpray"),
            _fn(src, "denseClusterApplies"),
            _fn(src, "headsPerCluster"),
            "let s = 7; const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);",
            f"console.log(JSON.stringify({expr}));"])
        node = shutil.which("node") or shutil.which("nodejs")
        out = subprocess.run([node, "-e", prog], capture_output=True, text=True,
                             encoding="utf-8", check=True)
        return json.loads(out.stdout)

    def test_a_small_head_is_drawn_larger_within_its_limit(self):
        got = self._run("[1, 2, 2.5, 5, 0.5].map(d => bloomGain({plant_type: 'wildflower', "
                        "flower_diameter_cm: d}, 'head'))")
        # HEAD_MIN_M 4 cm since V3.67 (3 cm before), at most 1.8 times.
        self.assertEqual(got[0], 1.8)                     # 1 cm: the limit
        self.assertAlmostEqual(got[1], 1.8)               # 2 cm: the limit
        self.assertAlmostEqual(got[2], 1.6)               # 2.5 cm drawn 4 cm
        self.assertEqual(got[3], 1)                       # 5 cm: as it is
        self.assertEqual(got[4], 1.8)

    def test_a_cluster_and_a_shrub_keep_their_own_gain(self):
        got = self._run("[bloomGain({plant_type: 'wildflower', flower_diameter_cm: 0.5}, 'raceme'),"
                        " bloomGain({plant_type: 'shrub', height_m: 4.5, flower_diameter_cm: 1}, 'head')]")
        self.assertEqual(got[0], 1)
        self.assertAlmostEqual(got[1], 2.0)

    def test_a_branched_asters_cluster_is_a_spray_facing_out(self):
        got = self._run("headSpray({stem_branching: 'branched_throughout'}, 'head', 1, 0.8, 0, 0, 0, 0.03, rnd)")
        self.assertEqual(len(got), 6)                     # 4 until V3.67
        for h in got:
            self.assertGreaterEqual(h["tilt"], 0.5)
            self.assertLessEqual(h["tilt"], 0.95)
        # The first head stands at the anchor, facing out along +x (bearing pi/2).
        self.assertEqual((got[0]["x"], got[0]["y"]), (1, 0.8))
        self.assertAlmostEqual(got[0]["spin"], 1.5708, delta=0.41)

    def test_a_count_already_of_heads_is_not_multiplied(self):
        """V3.67's first build gave a coneflower's 24 counted heads five each:
        120 heads on a 45 cm plant. The heads are capped by its footprint."""
        got = self._run("[headsPerCluster({stem_branching: 'branched_above', canopy_m: 0.45}, 0.05, 24),"
                        " headsPerCluster({stem_branching: 'branched_above', canopy_m: 0.9}, 0.04, 24),"
                        " headsPerCluster({stem_branching: 'branched_above'}, 0.04)]")
        self.assertEqual(got, [2, 5, 5])

    def test_an_unbranched_stem_and_a_cluster_carry_one(self):
        got = self._run("[headSpray({stem_branching: 'unbranched'}, 'head', 0, 1, 0, 0, 0, 0.03, rnd).length,"
                        " headSpray({stem_branching: 'branched_above'}, 'raceme', 0, 1, 0, 0, 0, 0.1, rnd)]")
        self.assertEqual(got[0], 1)
        self.assertEqual(len(got[1]), 1)
        self.assertIsNone(got[1][0]["tilt"], "a cluster keeps its own florets' nod")

    def test_which_clusters_are_dense(self):
        got = self._run("[" + ",".join([
            "denseClusterApplies({plant_type: 'wildflower', flower_arch: 'panicle', florets_per_head: 160})",
            "denseClusterApplies({plant_type: 'wildflower', flower_arch: 'raceme', florets_per_head: 8})",
            "denseClusterApplies({plant_type: 'wildflower', flower_arch: 'head', florets_per_head: 90})",
            "denseClusterApplies({plant_type: 'shrub', flower_arch: 'raceme', florets_per_head: 30})",
            "denseClusterApplies({plant_type: 'grass', flower_arch: 'panicle', florets_per_head: 60,"
            " inflorescence_form: 'open_panicle'})",
            "denseClusterApplies({plant_type: 'wildflower', flower_arch: 'corymb', florets_per_head: 60})"]) + "]")
        self.assertEqual(got, [True, False, False, False, False, True])

    def test_a_cluster_with_no_tip_to_carry_it_keeps_its_florets(self):
        """A water plant's body has no stem tips: before V3.64's fix its
        flowers vanished (broad-leaved water-plantain, water arum)."""
        bloom = _js("15c-woodybloom.js")
        self.assertIn("back.push(p); continue;", bloom)
        self.assertIn("buildFlorets(back, month, terrain)", bloom)


if __name__ == "__main__":
    unittest.main()
