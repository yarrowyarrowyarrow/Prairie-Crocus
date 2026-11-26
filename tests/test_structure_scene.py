"""
tests/test_structure_scene.py — a placed structure in 3D as the map draws it
(V3.70, F288 part 1; the V3.69 review).

The review found every rectangular structure turned a quarter turn between the
map and the 3D (the tester's raised bed), its width never sent, the shed's and
the bee hotel's roofs upside down, and a pond and a native lawn patch that
ignored winter. These hold each fix:

* the catalogue, the manifest and the Blender builder agree on each model's
  authored size and width;
* a rectangle's scene entry carries the map's width and bearing, read as the map
  reads them, and a Fence / Wall is a fence line;
* each kind has a Size range that holds its default;
* both roofs are gables, read off the shipped GLB files;
* in the real viewer (headless Chromium) a raised bed lies north-south at the
  map's length and width, and January ices a pond and snows on a lawn patch.
"""

import ast
import json
import math
import os
import re
import struct
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import render_yard                                            # noqa: E402
from src.db.structures import (                               # noqa: E402
    STRUCTURES, get_structure, size_range, size_words)
from src import scene_structures as SS                        # noqa: E402
from src.scene_contract import build_scene                    # noqa: E402
from tests.test_scene3d_render import fail_on_viewer_errors   # noqa: E402

_MODELS = os.path.join(ROOT, "html", "assets", "models")
_LAT, _LNG = 53.52, -113.52
_KY = 111320.0
_KX = 111320.0 * math.cos(math.radians(_LAT))


def _ll(east, north):
    return [_LNG + east / _KX, _LAT + north / _KY]


def _structure(sid, east=0.0, north=0.0, size_m=None, definition=None):
    sd = dict(definition if definition is not None else get_structure(sid))
    if size_m is not None:
        sd["size_m"] = float(size_m)
    return {"type": "Feature",
            "geometry": {"type": "Point", "coordinates": _ll(east, north)},
            "properties": {"element_type": "structure", "struct_id": sid,
                           "size_m": sd.get("size_m"), "struct_def": sd}}


def _project(*features):
    return {"type": "FeatureCollection", "properties": {
        "site_config": {"latitude": _LAT, "longitude": _LNG}},
        "features": list(features)}


def _manifest():
    with open(os.path.join(_MODELS, "manifest.json"), encoding="utf-8") as fh:
        return json.load(fh)["structures"]


def _builder_widths():
    """``STRUCTURE_WIDTHS`` from the Blender builder, read without Blender."""
    path = os.path.join(ROOT, "scripts", "blender", "assetlib", "structures.py")
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in tree.body:
        if (isinstance(node, ast.Assign)
                and getattr(node.targets[0], "id", "") == "STRUCTURE_WIDTHS"):
            return ast.literal_eval(node.value)
    raise AssertionError("STRUCTURE_WIDTHS is not in the builder")


def _glb_positions(path, node_name):
    """The POSITION values of one named node's mesh in a GLB (glTF: y up)."""
    with open(path, "rb") as fh:
        data = fh.read()
    off, chunks = 12, {}
    while off < len(data):
        n, kind = struct.unpack_from("<II", data, off)
        chunks[kind] = data[off + 8: off + 8 + n]
        off += 8 + n
    gltf, binary = json.loads(chunks[0x4E4F534A]), chunks[0x004E4942]
    node = next(n for n in gltf["nodes"] if n.get("name") == node_name)
    prim = gltf["meshes"][node["mesh"]]["primitives"][0]
    acc = gltf["accessors"][prim["attributes"]["POSITION"]]
    view = gltf["bufferViews"][acc["bufferView"]]
    base = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = view.get("byteStride") or 12
    return [struct.unpack_from("<fff", binary, base + k * stride)
            for k in range(acc["count"])]


class TheModelsAndTheCatalogueAgree(unittest.TestCase):

    def test_each_model_is_authored_at_the_catalogue_size_and_width(self):
        manifest, widths = _manifest(), _builder_widths()
        for s in STRUCTURES:
            entry = manifest[s["id"]]
            self.assertEqual(entry["size_m"], s["size_m"], s["id"])
            if s.get("shape") == "rectangle":
                self.assertEqual(entry.get("width_m"), s["width_m"], s["id"])
                self.assertEqual(widths.get(s["id"]), s["width_m"], s["id"])
            else:
                self.assertNotIn("width_m", entry, s["id"])
                self.assertNotIn(s["id"], widths)

    def test_a_bigger_shed_is_not_a_taller_one(self):
        self.assertEqual(_manifest()["shed"]["scale_mode"], "footprint")


class TheSceneDrawsWhatTheMapDraws(unittest.TestCase):

    def test_a_rectangle_carries_the_maps_width_and_bearing(self):
        for s in STRUCTURES:
            if s["id"] in SS.AS_LINE:
                continue
            sc = build_scene(_project(_structure(s["id"])), year=0)
            rec = sc["structures"][0]
            if s.get("shape") == "rectangle":
                self.assertEqual(rec["width_m"], s["width_m"], s["id"])
                self.assertEqual(rec["bearing_deg"], SS.MAP_BEARING_DEG)
            else:
                self.assertNotIn("bearing_deg", rec, s["id"])

    def test_the_size_box_sets_the_length_and_the_width_stays(self):
        sc = build_scene(_project(_structure("raised_bed", size_m=6.0)), year=0)
        rec = sc["structures"][0]
        self.assertEqual((rec["size_m"], rec["width_m"]), (6.0, 1.2))

    def test_a_definition_with_no_shape_is_read_as_the_map_reads_it(self):
        """``placeStructureOnMap``: no shape is a rectangle, no width a
        square."""
        f = _structure("pond", definition={"id": "pond", "size_m": 4.0})
        rec = SS.record(f["properties"], 0.0, 0.0)
        self.assertEqual((rec["width_m"], rec["bearing_deg"]), (4.0, 0.0))

    def test_a_fence_is_a_fence_line_along_the_maps_rectangle(self):
        sc = build_scene(_project(_structure("fence", 0, 0, size_m=12.0)),
                         year=0)
        self.assertEqual(sc["structures"], [])
        fences = [ln for ln in sc["lines"] if ln["kind"] == "fence"]
        self.assertEqual(len(fences), 1)
        (x0, y0), (x1, y1) = fences[0]["points"]
        self.assertAlmostEqual(x0, x1, places=2)          # north-south
        self.assertAlmostEqual(abs(y1 - y0), 12.0, places=1)


class TheSizeBoxPerKind(unittest.TestCase):

    def test_every_kind_has_a_range_holding_its_default(self):
        for s in STRUCTURES:
            lo, hi = size_range(s["id"])
            self.assertLess(lo, hi, s["id"])
            self.assertTrue(lo <= s["size_m"] <= hi, s["id"])

    def test_the_box_says_what_it_measures(self):
        self.assertEqual(size_words(get_structure("raised_bed")), "Length (m):")
        self.assertEqual(size_words(get_structure("pond")), "Across (m):")


class TheRoofsAreGables(unittest.TestCase):
    """Until V3.70 both roofs' boards were tilted with their outer edges up:
    a V, splayed open like a carton (``_roof_tilt``)."""

    def _check(self, name, body):
        path = os.path.join(_MODELS, f"struct_{name}.glb")
        roof = _glb_positions(path, "roof")
        across = max(abs(p[2]) for p in roof)
        ridge = max(p[1] for p in roof if abs(p[2]) < 0.15 * across)
        eaves = max(p[1] for p in roof if abs(p[2]) > 0.85 * across)
        top = max(p[1] for p in _glb_positions(path, body))
        self.assertGreater(ridge, eaves + 0.1, name)
        self.assertLess(top, ridge, f"{name}: the gable end pokes through")

    def test_the_shed(self):
        self._check("shed", "walls")

    def test_the_bee_hotel(self):
        self._check("bee_hotel", "house")


#: The headless probe: the real viewer in an iframe, one scene pushed, and the
#: drawn structures measured. Served from memory beside html/.
_PROBE = """<!doctype html><html><head><meta charset="utf-8"></head><body>
<iframe id="v" src="scene3d.html" style="width:640px;height:400px;border:0"></iframe>
<script src="probe_watch.js"></script>
<script>
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function until(test, ms) {
  for (let t = 0; t < ms; t += 100) { if (test()) return true; await sleep(100); }
  return false;
}
function viewer() { return document.getElementById('v').contentWindow; }
function measure(w) {
  const out = {};
  w.eval('designGroup').traverse((o) => {
    if (!o.userData || !o.userData.structId) return;
    const b = new w.THREE.Box3().setFromObject(o);
    const rec = { ew: +(b.max.x - b.min.x).toFixed(3),
                  ns: +(b.max.z - b.min.z).toFixed(3), parts: {} };
    o.traverse((m) => { if (m.isMesh && m.material && m.material.color)
      rec.parts[m.name] = m.material.color.getHex(); });
    out[o.userData.structId] = rec;
  });
  return out;
}
(async function () {
  try {
    await until(() => { const w = viewer();
      return w && typeof w.permaShowView === 'function'; }, 60000);
    const w = viewer(), job = await (await fetch('/__s/job.json')).json();
    const res = {};
    for (const name of Object.keys(job)) {
      w.permaSetScene(job[name]);
      await until(() => w.permaModelsReady(), 60000);
      await sleep(300);
      res[name] = measure(w);
    }
    document.title = 'MEASURED ' + JSON.stringify(res);
  } catch (e) {
    document.getElementById('probe-errors').textContent += 'probe: ' + e + '\\n';
    document.title = 'FAILED';
  }
})();
</script><pre id="probe-errors"></pre></body></html>"""


@unittest.skipIf(render_yard.find_chromium() is None,
                 "no Chromium binary (set CHROME= to run this gate)")
class InTheRealViewer(unittest.TestCase):
    got = None

    @classmethod
    def setUpClass(cls):
        from datetime import datetime
        yard = _project(_structure("raised_bed", 0, 0, size_m=6.0),
                        _structure("native_bee_log", 8, 0),
                        _structure("shed", 16, 0),
                        _structure("pond", 0, 16),
                        _structure("native_lawn_patch", 16, 16))
        job = {"july": build_scene(yard, year=0,
                                   when=datetime(2025, 7, 21, 14)),
               "january": build_scene(yard, year=0,
                                      when=datetime(2025, 1, 21, 12))}
        try:
            server = render_yard.Server({"/__s/job.json": job,
                                         "/structure_probe.html":
                                         _PROBE.encode("utf-8")})
        except OSError as exc:
            raise unittest.SkipTest(f"cannot bind a local port: {exc}")
        try:
            dom = render_yard.run_probe(server.url("structure_probe.html"),
                                        budget_ms=120000, timeout=300)
        except Exception as exc:                          # noqa: BLE001
            server.stop()
            raise unittest.SkipTest(f"Chromium would not run headlessly: {exc}")
        server.stop()
        fail_on_viewer_errors(dom)
        match = re.search(r"<title>MEASURED (\{.*\})</title>", dom, re.S)
        if not match:
            raise unittest.SkipTest("the probe never reported: no WebGL here")
        import html as _html
        cls.got = json.loads(_html.unescape(match.group(1)))

    def test_a_raised_bed_lies_as_the_map_draws_it(self):
        bed = self.got["july"]["raised_bed"]
        self.assertAlmostEqual(bed["ns"], 6.0, delta=0.15)   # its length
        self.assertAlmostEqual(bed["ew"], 1.2, delta=0.1)    # its width

    def test_a_bee_log_and_a_shed_turn_too(self):
        log, shed = self.got["july"]["native_bee_log"], self.got["july"]["shed"]
        self.assertGreater(log["ns"], 2 * log["ew"])
        self.assertGreater(shed["ns"], shed["ew"])

    def test_january_ices_the_pond_and_snows_on_the_lawn_patch(self):
        jul, jan = self.got["july"], self.got["january"]
        self.assertEqual(jan["pond"]["parts"]["water"], 0xcbd9e4)
        self.assertNotEqual(jul["pond"]["parts"]["water"], 0xcbd9e4)
        self.assertEqual(jan["native_lawn_patch"]["parts"]["turf"], 0xeef2f5)
        self.assertNotEqual(jul["native_lawn_patch"]["parts"]["turf"], 0xeef2f5)


if __name__ == "__main__":
    unittest.main()
