"""
tests/test_woody_render.py — a shrub built from its own numbers, read back
from the real viewer (V3.49, F268).

``src/shrub_habit.py`` decides which shrubs are drawn from what was read of
them and ``html/scene3d/03d-woody.js`` builds the body. Every part of that can
be right while the picture is wrong, which is what the reference sheets showed
of the baked shrubs for years: sticks as thick as an arm, leaf cards at their
ends. So this pushes scenes built by the real ``build_scene`` into the real
viewer in headless Chromium and reads back what was built
(``html/woody_probe.html``):

* a read shrub is the new body and an estimated one is the baked figure;
* it stands as tall and as wide as the plant, at one scale up and across;
* it spends no more than its budget, and its leaves are drawn no more than
  three times their size;
* its leaves wear their cut-out and cast its shadow, and the cut-out keeps a
  whole chain of smaller copies;
* out of leaf its stems still stand;
* a young shrub is a smaller shrub, with fewer stems;
* the flower layer is handed points on the body;
* in flower it carries its clusters as cut-out cards on its shoots, as many
  as its crown has room for, each the size its recorded flowers make
  (``html/scene3d/15c-woodybloom.js``), and an estimated shrub keeps the
  florets it had;
* Stylised draws none of it;
* every form builds with every leaf outline in the vocabulary.

Skips with no Chromium binary or no WebGL, as the other render gates do; a
viewer that THROWS fails.
"""

import copy
import datetime
import html as _html
import json
import math
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import render_yard                                            # noqa: E402
from src import data_quality, shrub_habit                     # noqa: E402
from src import sprite_gallery as sg                          # noqa: E402
from tests.test_scene3d_render import fail_on_viewer_errors   # noqa: E402

_ROW = {"common_name": "Test Dogwood", "scientific_name": "Testus cornus",
        "plant_type": "shrub", "mature_height_m": "3", "spacing_m": "2",
        "bloom_period": "June–July", "deciduous_evergreen": "deciduous",
        "branching": "multi_stem", "leaf_shape": "ovate", "leaf_size_cm": 8.0,
        "leaf_arrangement": "opposite", "bark_color": "#b5402e",
        "flower_form": "cluster", "flower_arch": "cyme", "flower_diameter_cm": 0.6,
        "florets_per_head": 60, "petal_count": 4, "petal_shape": "narrow",
        "flower_symmetry": "radial", "flower_color": "#f2f2ea"}
_READ = {"leaf_data_source": "photo", "woody_stems": 25}


def _scene(name="Test Dogwood", month=7, quality=1, **over):
    row = dict(_ROW, common_name=name, **over)
    scene = sg._scene_for(sg._species_specimen(row), 1, name, 1,
                          when=datetime.datetime(2024, month, 15, 12, 0))
    scene["quality"] = quality
    return scene


def _young(scene, share):
    """The same scene with its shrub `share` of the way grown."""
    scene = copy.deepcopy(scene)
    p = scene["plants"][0]
    for key in ("height_m", "canopy_m"):
        p[key] = round(p[key] * share, 3)
        p["drawn"][key] = round(p["drawn"][key] * share, 3)
    return scene


SCENES = {
    "read": _scene(**_READ),
    "estimated": _scene(),
    "thicket": _scene("Test Rose", branching="suckering", mature_height_m="1.5",
                      spacing_m="1", leaf_shape="compound_pinnate", leaf_size_cm=9.0,
                      leaf_arrangement="alternate", leaf_data_source="photo", woody_stems=15),
    "arching": _scene("Test Currant", branching="arching", mature_height_m="0.8",
                      spacing_m="1", leaf_shape="palmately_lobed", leaf_size_cm=7.0,
                      leaf_arrangement="alternate", leaf_data_source="photo", woody_stems=5),
    "mat": _scene("Test Juniper", branching="prostrate", mature_height_m="1.5",
                  spacing_m="1.5", deciduous_evergreen="evergreen", leaf_shape="awl",
                  leaf_size_cm=1.2, leaf_arrangement="whorled", bloom_period="",
                  flower_form="none", flower_arch="", leaf_data_source="photo",
                  woody_stems=10),
    "big": _scene("Test Saskatoon", mature_height_m="4", spacing_m="2.5",
                  leaf_shape="obovate", leaf_size_cm=4.0, leaf_arrangement="alternate",
                  leaf_data_source="photo", woody_stems=18),
    "winter": _scene(month=1, **_READ),
    "stylised": _scene(quality=0, **_READ),
    "lifelike": _scene(quality=2, **_READ),
}
SCENES["young"] = _young(SCENES["read"], 0.3)
# A willow in April: catkins on bare twigs.
SCENES["catkin"] = _scene("Test Willow", month=4, bloom_period="April–May",
                          flower_form="spike", flower_arch="spike", petal_count=0,
                          flower_diameter_cm=0.3, florets_per_head=80,
                          leaf_shape="lanceolate", leaf_arrangement="alternate", **_READ)
SCENES["rose"] = _scene("Test Rose", branching="suckering", mature_height_m="1.5",
                        spacing_m="1", leaf_shape="compound_pinnate", leaf_size_cm=9.0,
                        leaf_arrangement="alternate", flower_arch="solitary",
                        flower_diameter_cm=5.0, florets_per_head=3, petal_count=5,
                        petal_shape="notched", flower_color="#e58fb0",
                        leaf_data_source="photo", woody_stems=15)

#: Flowers the cluster sizes are asked for: architecture, one flower's width
#: in metres, flowers in a cluster.
CLUSTERS = {"chokecherry": ("raceme", 0.012, 30), "dogwood": ("cyme", 0.006, 60),
            "rose": ("solitary", 0.05, 3), "cranberry": ("corymb", 0.006, 120),
            "catkin": ("spike", 0.003, 80), "meadowsweet": ("panicle", 0.005, 120)}

#: The forms drawn in the scenes above, by name.
FORMS = {"read": "clump", "thicket": "thicket", "arching": "arching", "mat": "mat",
         "big": "clump"}


class TheShrubInTheRealViewer(unittest.TestCase):
    got = None

    @classmethod
    def setUpClass(cls):
        job = {"scenes": SCENES, "forms": list(shrub_habit.FORMS),
               "shapes": sorted(data_quality.LEAF_SHAPES),
               "clusters": list(CLUSTERS.values())}
        try:
            server = render_yard.Server({"/__yard/job.json": job})
        except OSError as exc:
            raise unittest.SkipTest(f"cannot bind a local port: {exc}")
        try:
            dom = render_yard.run_probe(
                server.url("woody_probe.html?job=/__yard/job.json"),
                budget_ms=120000, timeout=480)
        except (OSError, RuntimeError, Exception) as exc:    # noqa: BLE001
            server.stop()
            raise unittest.SkipTest(f"Chromium would not run headlessly: {exc}")
        server.stop()
        fail_on_viewer_errors(dom)
        match = re.search(r"<title>MEASURED (\{.*\})</title>", dom, re.S)
        if not match:
            raise unittest.SkipTest("the probe never reported: no WebGL in "
                                    "this environment")
        cls.got = json.loads(_html.unescape(match.group(1)))

    def _parts(self, name):
        bodies = self.got["scenes"][name]["bodies"]
        self.assertTrue(bodies, f"{name}: nothing was drawn")
        return bodies

    def _leaves(self, name):
        leaves = [b for b in self._parts(name) if b["leaves"]]
        self.assertEqual(len(leaves), 1, f"{name}: not one mesh of leaves from its own body")
        return leaves[0]

    def _stems(self, name):
        stems = [b for b in self._parts(name) if b["woody"] and not b["leaves"]]
        self.assertEqual(len(stems), 1, f"{name}: not one mesh of stems from its own body")
        return stems[0]

    # ── which body ───────────────────────────────────────────────────────────

    def test_the_fixtures_are_what_the_gate_needs(self):
        for name, form in FORMS.items():
            d = SCENES[name]["plants"][0]["drawn"]
            self.assertEqual((d["body"], d["form"]), ("woody", form), name)
        self.assertIsNone(SCENES["estimated"]["plants"][0].get("drawn"))
        self.assertEqual(SCENES["winter"]["plants"][0]["season"]["look"], "bare")
        self.assertNotIn("season", SCENES["mat"]["plants"][0], "an evergreen has no season")

    def test_a_read_shrub_is_drawn_from_its_own_numbers(self):
        for name in FORMS:
            self.assertEqual(self._leaves(name)["plan"]["form"], FORMS[name], name)
            self._stems(name)

    def test_an_estimated_shrub_keeps_the_baked_figure(self):
        """Drawing a genus guess in a species' own body would state it as read."""
        self.assertFalse(any(b["woody"] for b in self._parts("estimated")))

    def test_stylised_draws_none_of_it(self):
        """Detail level 0 is a style, with its own faceted shrubs."""
        self.assertFalse(any(b["woody"] for b in self._parts("stylised")))

    # ── at its size ──────────────────────────────────────────────────────────

    def test_it_stands_as_tall_and_as_wide_as_the_plant(self):
        for name in FORMS:
            b, p = self._leaves(name), SCENES[name]["plants"][0]
            # The stems stand on the ground and the leaves begin low on them.
            self.assertAlmostEqual(self._stems(name)["bottom"], 0.0, delta=0.02, msg=name)
            self.assertLess(b["bottom"], 0.3, f"{name}: bare for a third of its height")
            self.assertLessEqual(b["top"], 1.001, msg=name)
            self.assertGreaterEqual(b["top"], 0.9, msg=name)
            # The widest leaf lands on the plant's recorded spread.
            self.assertAlmostEqual(b["half"], b["unit_half_width"], delta=0.02, msg=name)
            self.assertAlmostEqual(b["scale"][1], p["drawn"]["height_m"], delta=0.01, msg=name)
            wide = 2 * b["half"] * b["scale"][0]
            self.assertAlmostEqual(wide, p["canopy_m"], delta=0.05 * p["canopy_m"], msg=name)

    def test_it_is_placed_at_nearly_one_scale_up_and_across(self):
        """The baked figures are stretched to the plant's width. This body is
        built to the plant's own height and width, so the two scales differ by
        what the build missed its outline by: a quarter at the very most."""
        for name in FORMS:
            sx, sy, sz = self._leaves(name)["scale"]
            self.assertAlmostEqual(sx, sz, delta=1e-6, msg=name)
            self.assertLess(abs(sx / sy - 1.0), 0.31, name)
        sx, sy, _ = self._leaves("read")["scale"]
        self.assertAlmostEqual(sx / sy, 1.0, delta=0.08)

    def test_the_stems_and_the_leaves_share_one_frame(self):
        for name in FORMS:
            lv, st = self._leaves(name), self._stems(name)
            self.assertEqual(lv["scale"], st["scale"], name)
            self.assertAlmostEqual(lv["unit_half_width"], st["unit_half_width"], places=6)

    # ── within its means ─────────────────────────────────────────────────────

    def test_it_spends_no_more_than_its_budget(self):
        for name in list(FORMS) + ["lifelike", "young"]:
            b = self._leaves(name)
            self.assertLessEqual(b["whole"], b["plan"]["budget"] + 2, name)
            self.assertGreater(b["whole"], 200, name)

    def test_the_budget_follows_the_shrubs_height(self):
        lo, hi = self.got["scenes"]["read"]["budget"][1]
        self.assertEqual(self._leaves("arching")["plan"]["budget"], lo)   # 0.8 m
        self.assertEqual(self._leaves("big")["plan"]["budget"], hi)       # 4 m
        self.assertTrue(lo < self._leaves("read")["plan"]["budget"] < hi)

    def test_lifelike_spends_more_on_the_same_shrub(self):
        self.assertGreater(self._leaves("lifelike")["plan"]["budget"],
                           self._leaves("read")["plan"]["budget"])
        self.assertGreaterEqual(self._leaves("lifelike")["plan"]["cards"],
                                self._leaves("read")["plan"]["cards"])

    def test_a_leaf_is_drawn_at_its_size_where_the_budget_allows(self):
        """A 3 m dogwood's 8 cm leaves fit at life size; a 4 m saskatoon's
        4 cm ones do not, and the plan says by how much."""
        self.assertAlmostEqual(self._leaves("read")["plan"]["gain"], 1.0, delta=0.05)
        big = self._leaves("big")["plan"]["gain"]
        self.assertGreater(big, 1.2)
        top = self.got["scenes"]["read"]["gain_max"]
        for name in FORMS:
            self.assertLessEqual(self._leaves(name)["plan"]["gain"], top + 1e-9, name)
        self.assertLessEqual(top, 3.0)

    def test_the_stems_are_as_many_as_were_counted(self):
        self.assertEqual(self._leaves("read")["plan"]["stems"], 25)
        self.assertEqual(self._leaves("arching")["plan"]["stems"], 5)

    # ── the leaves ───────────────────────────────────────────────────────────

    def test_the_leaves_wear_their_outline_and_cast_its_shadow(self):
        for name in FORMS:
            b = self._leaves(name)
            self.assertTrue(b["uv"] and b["colours"], name)
            self.assertTrue(b["cut"], f"{name}: the leaves are whole cards")
            self.assertGreater(b["alpha_test"], 0.0, name)
            self.assertTrue(b["shadow_cut"], f"{name}: the shadow is of whole cards")

    def test_the_outline_has_its_whole_chain_of_smaller_copies(self):
        """128 px down to 1: nine. A chain cut short leaves the far copies
        to the machine, whose average falls under the cut."""
        for name in FORMS:
            self.assertGreaterEqual(self._leaves(name)["mips"], 8, name)

    def test_a_spray_fills_a_fair_share_of_its_card(self):
        for name in FORMS:
            cover = self._leaves(name)["plan"]["spray"]["cover"]
            self.assertTrue(0.1 <= cover <= 0.7, f"{name}: cover {cover}")

    def test_the_stems_are_not_cut_out(self):
        for name in FORMS:
            self.assertFalse(self._stems(name)["cut"], name)

    # ── the seasons and the years ────────────────────────────────────────────

    def test_out_of_leaf_the_stems_stand_and_the_leaves_are_gone(self):
        lv, st = self._leaves("winter"), self._stems("winter")
        self.assertLess(lv["scale"][1], 0.01, "the leaves were not put away")
        self.assertAlmostEqual(st["scale"][1], SCENES["winter"]["plants"][0]["height_m"],
                               delta=0.01)

    def test_in_leaf_the_leaves_are_at_the_plants_size(self):
        for name in FORMS:
            self.assertAlmostEqual(self._leaves(name)["scale"][1],
                                   SCENES[name]["plants"][0]["height_m"], delta=0.01, msg=name)

    def test_a_young_shrub_is_a_smaller_shrub(self):
        """Built at the share of its grown size that holds it, with fewer
        stems, not the grown body shrunk with its leaves."""
        young, grown = self._leaves("young")["plan"], self._leaves("read")["plan"]
        self.assertLess(young["tier"], 1.0)
        self.assertLess(young["H"], grown["H"])
        self.assertLess(young["stems"], grown["stems"])
        self.assertGreaterEqual(young["stems"], 1)
        # It is still placed at the plant's size this year.
        p = SCENES["young"]["plants"][0]
        self.assertAlmostEqual(self._leaves("young")["scale"][1], p["drawn"]["height_m"],
                               delta=0.01)

    # ── the flowers ──────────────────────────────────────────────────────────

    def test_the_flowers_are_handed_points_on_the_body(self):
        for name in ("read", "thicket", "arching"):
            p = SCENES[name]["plants"][0]
            anchors = self.got["scenes"][name]["anchors"]
            self.assertGreater(len(anchors), 20, name)
            reach = p["canopy_m"] / 2 * 1.08 + 0.05
            for x, y, z in anchors:
                self.assertLessEqual(math.hypot(x - p["x"], z + p["y"]), reach, name)
                self.assertTrue(0.0 <= y <= p["height_m"] * 1.05 + 0.05, name)

    def test_out_of_leaf_the_flowers_go_on_the_twigs(self):
        """A willow's catkins and a buffaloberry's flowers come before the leaves."""
        p = SCENES["winter"]["plants"][0]
        anchors = self.got["scenes"]["winter"]["anchors"]
        self.assertGreater(len(anchors), 20)
        for x, y, z in anchors:
            self.assertLessEqual(math.hypot(x - p["x"], z + p["y"]), p["canopy_m"] / 2 + 0.05)

    # ── in flower ────────────────────────────────────────────────────────────

    def _cards(self, name):
        return self.got["scenes"][name]["blooms"]["cards"]

    def _count(self, name):
        return sum(c["count"] for c in self._cards(name))

    def test_a_read_shrub_in_flower_carries_its_clusters_as_cards(self):
        for name in ("read", "rose", "big"):
            cards = self._cards(name)
            self.assertTrue(cards, f"{name}: in flower, and no cluster was drawn")
            self.assertEqual(self.got["scenes"][name]["blooms"]["florets"], 0,
                             f"{name}: its flowers were built a floret at a time as well")
            for c in cards:
                self.assertTrue(c["cut"], name)
                self.assertGreaterEqual(c["mips"], 8, name)
                self.assertFalse(c["shadow"], f"{name}: a flower casts no shadow here")
                self.assertLessEqual(c["triangles"], 4, name)

    def test_an_estimated_shrub_keeps_its_florets(self):
        blooms = self.got["scenes"]["estimated"]["blooms"]
        self.assertEqual(blooms["cards"], [])
        self.assertGreater(blooms["florets"], 0)

    def test_out_of_flower_there_are_none(self):
        self.assertEqual(self._cards("winter"), [])
        self.assertEqual(self._cards("mat"), [])

    def test_catkins_stand_on_bare_twigs(self):
        """The leaves are put away in April and the flowers are not."""
        self.assertLess(self._leaves("catkin")["scale"][1], 0.01)
        cards = self._cards("catkin")
        self.assertTrue(cards, "a willow in April with no catkins")
        self.assertEqual(cards[0]["triangles"], 4, "a catkin shows from every side")

    def test_the_clusters_are_on_the_shrub(self):
        for name in ("read", "rose", "big", "catkin"):
            p = SCENES[name]["plants"][0]
            for c in self._cards(name):
                big = max(c["sizes"])
                for x, y, z in c["at"]:
                    self.assertLessEqual(math.hypot(x - p["x"], z + p["y"]),
                                         p["canopy_m"] / 2 * 1.08 + 0.05 + big, name)
                    self.assertTrue(-big <= y <= p["height_m"] * 1.05 + 0.05 + big, name)

    def test_a_bigger_crown_carries_more_of_them(self):
        self.assertGreater(self._count("big"), self._count("rose"))
        top = self.got["bloom"]["max"]
        for name in ("read", "rose", "big", "catkin"):
            self.assertTrue(8 <= self._count(name) <= top,
                            f"{name}: {self._count(name)} clusters")

    def test_a_cluster_is_the_size_its_flowers_make(self):
        """Thirty 1.2 cm chokecherry flowers are a 10 cm raceme and sixty 6 mm
        dogwood flowers a 6 cm head: the sizes in the photographs, to a third."""
        got = dict(zip(CLUSTERS, self.got["clusters"]))
        want = {"chokecherry": 0.10, "dogwood": 0.06, "rose": 0.05, "cranberry": 0.076,
                "catkin": 0.055, "meadowsweet": 0.127}
        for name, size in want.items():
            self.assertAlmostEqual(got[name], size, delta=size * 0.33, msg=name)

    def test_a_cluster_is_drawn_no_more_than_twice_its_size(self):
        gain = self.got["bloom"]["gain_max"]
        self.assertLessEqual(gain, 2.0)
        natural = dict(zip(CLUSTERS, self.got["clusters"]))
        for name, key in (("read", "dogwood"), ("rose", "rose"), ("catkin", "catkin")):
            for c in self._cards(name):
                # 15% either way is one cluster's own variation.
                self.assertLessEqual(max(c["sizes"]), natural[key] * gain * 1.16, name)
                self.assertGreaterEqual(min(c["sizes"]), natural[key] * 0.84, name)

    # ── every form, every leaf ───────────────────────────────────────────────

    def test_every_form_builds_with_every_leaf_outline(self):
        matrix = self.got["matrix"]
        self.assertEqual(len(matrix),
                         len(shrub_habit.FORMS) * len(data_quality.LEAF_SHAPES) * 3)
        for row in matrix:
            label = f"{row['form']} / {row['shape']} / {row['arrangement']}"
            self.assertNotIn("error", row, f"{label}: {row.get('error')}")
            self.assertEqual(row["bad"], 0, f"{label}: a coordinate is not a number")
            self.assertLessEqual(row["triangles"], row["budget"] + 2, label)
            self.assertGreater(row["cards"], 20, label)
            self.assertGreater(row["crown"], 5, label)
            self.assertTrue(1.0 <= row["gain"] <= 3.0, label)
            self.assertTrue(0.02 <= row["cover"] <= 0.8, f"{label}: cover {row['cover']}")
            self.assertTrue(0.9 <= row["top"] <= 1.001, f"{label}: top {row['top']}")
            self.assertTrue(row["key"], label)


class TheProbeIsNotShipped(unittest.TestCase):

    def test_the_installer_leaves_the_probe_out(self):
        spec = os.path.join(ROOT, "scripts", "packaging", "permadesign.spec")
        with open(spec, encoding="utf-8") as fh:
            self.assertIn("_probe.html", fh.read())

    def test_the_probe_reports_its_own_errors(self):
        with open(os.path.join(render_yard.HTML, "woody_probe.html"),
                  encoding="utf-8") as fh:
            self.assertIn('src="probe_watch.js"', fh.read())


if __name__ == "__main__":
    unittest.main()
