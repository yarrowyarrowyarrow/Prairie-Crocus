"""
tests/test_stem_leaves.py — a leafy wildflower's stems carry leafy-shoot
cards (V3.66, F268).

What can go wrong quietly, each with a test here:

  * the chunk is not loaded, or loads after something that calls it;
  * a stem of one or two leaves (a sarsaparilla's single umbrella) is
    filled with leaves it does not have;
  * a card reaches above the plant, so the body is scaled to the card's tip
    and the plant shrinks (the first build did that, by 17%);
  * a divided leaf is counted as solid, so a milk-vetch is taken to be
    covered already and gets none;
  * Stylised draws them.
"""

import os
import re
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_JS = os.path.join(_ROOT, "html", "scene3d")


def _js(name):
    with open(os.path.join(_JS, name), encoding="utf-8") as fh:
        return fh.read()


class TheChunk(unittest.TestCase):

    def test_it_loads_before_the_layers_and_after_the_shrubs(self):
        order = re.findall(r"'scene3d/([\w-]+\.js)'", _js("chunks.js"))
        self.assertIn("03g-stemleaves.js", order)
        self.assertLess(order.index("03d-woody.js"), order.index("03g-stemleaves.js"))
        self.assertLess(order.index("03g-stemleaves.js"), order.index("04-quality.js"))

    def test_the_leafy_body_calls_it_for_stems_and_colonies(self):
        leafy = _js("03c-leafy.js")
        self.assertIn("leafyStemCards(C, P, rng)", leafy)
        self.assertIn("noteStemPath(P, at, top, y0, y1, hi, a)", leafy)
        self.assertIn("noteBranchPath(P, p0, end, ba)", leafy)

    def test_the_estimates_are_named(self):
        src = _js("03g-stemleaves.js")
        head = src[:src.index("function leafyStemCards")]
        for word in ("HERB_COVER", "HERB_CARD_BUDGET", "HERB_GAIN_MAX", "estimate"):
            self.assertIn(word, head)

    def test_a_stem_of_one_or_two_leaves_gets_none(self):
        src = _js("03g-stemleaves.js")
        self.assertIn("P.nodes < HERB_CARD_MIN_NODES", src)
        self.assertRegex(src, r"HERB_CARD_MIN_NODES = 3;")

    def test_stylised_draws_none(self):
        self.assertIn("if (STYLISED ||", _js("03g-stemleaves.js"))

    def test_a_card_stays_under_the_stem_top(self):
        self.assertIn("const lim = pa.top * 0.96", _js("03g-stemleaves.js"))

    def test_an_open_top_and_narrow_leaves_are_not_filled_solid(self):
        """V3.67: the asters, harebell and blazingstar read as solid columns."""
        src = _js("03g-stemleaves.js")
        self.assertIn("HERB_NARROW_FLOOR", src)
        self.assertIn("FORKS.branched_above[FORKS.branched_above.length - 1]", src)  # none above the last fork
        self.assertIn("pa.small ? HERB_BRANCH_CARD", src)    # a branch's, smaller
        self.assertIn("BRANCH_OPEN", _js("03c-leafy.js"))

    def test_a_divided_leaf_counts_what_it_fills(self):
        src = _js("03g-stemleaves.js")
        self.assertIn("compound_pinnate: 0.35", src)
        self.assertIn("_HERB_LEAF_FILL[P.shape]", src)


if __name__ == "__main__":
    unittest.main()
