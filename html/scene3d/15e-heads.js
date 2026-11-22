// Part of the Site & Pattern 3D viewer. Loaded as an ordered CLASSIC
// script by the bootstrap in scene3d.html — it shares the global scope
// with its siblings (THREE and friends are globals set by the
// bootstrap). Do not add ES `import`/`export` here.
//
// Design principle P5 — see docs/DESIGN_PHILOSOPHY.md
//
// A daisy you can see, and a spike drawn as a spike (V3.64, F268).
//
// The V3.62 re-read found two flower faults on most of the wildflowers:
//
// * heads too small to read (`flower_size` on 49 plants, `flower_count` on 14):
//   every aster, the fleabanes, the hawkweed, the sunflowers. A head was drawn
//   at its true width, nearly face-up and one to a stem tip, so from a yard
//   away a 2 cm aster was a coloured dot seen edge on, and a plant that carries
//   a hundred heads carried twelve;
// * dense spikes drawn as loose strings (`flower_arch` on 36): goldenrods,
//   milk-vetches, hedysarums, licorice, prairie clover, owl clover, bedstraw.
//   A spike of forty florets was forty florets spaced along a line.
//
// So:
// * a head is drawn at least HEAD_MIN_M across, never more than HEAD_GAIN_MAX
//   times its width; it faces out from the plant and up (HEAD_TILT), the way
//   a composite turns to the light; and on a plant whose stems branch, each
//   flower cluster the catalogue counts is a small spray of heads
//   (HEADS_PER_CLUSTER), which is what a cluster of an aster is;
// * a dense cluster on a wildflower is carried as one cut-out card on its stem
//   tip, the card a shrub's flower cluster has been since V3.49
//   (15c-woodybloom.js): a column of flowers for a spike or a raceme, a cone
//   for a goldenrod's panicle, a flat top for a yarrow's or an everlasting's
//   corymb (denseClusterApplies). A plant with no stem tip to carry it (a
//   water plant's own body) keeps its florets.
//
// Every number above is a stated estimate: nothing records how far out a head
// turns, how many heads a cluster holds, or how small a head may be drawn.
// `_inflorescence` moved here from 15-florets.js, which was at its ceiling.

// A head (or a solitary flower) is drawn at least this wide, and no more than
// this many times its own width.
const HEAD_MIN_M = 0.03;
const HEAD_GAIN_MAX = 1.8;
// How far a head nods from face-up, toward the outside of the plant: from, to.
const HEAD_TILT = [0.5, 0.95];
// Heads in one counted cluster, by how the stems branch.
const HEADS_PER_CLUSTER = { unbranched: 1, branched_above: 3, branched_throughout: 4 };
// A cluster is dense, and drawn as one card, from this many florets.
const DENSE_FLORETS = 15;
const DENSE_ARCHES = { spike: 1, raceme: 1, panicle: 1, corymb: 1 };

// How much larger than life a flower is drawn: a tree's or shrub's by its crown
// (15b-anchors.js), a wildflower's head by HEAD_MIN_M.
function bloomGain(p, arch) {
  const woody = woodyBloomGain(p);
  if (woody !== 1 || (arch !== 'head' && arch !== 'solitary')) return woody;
  const d = Math.max(0.0015, (p.flower_diameter_cm || 2) / 100);
  return Math.max(1, Math.min(HEAD_GAIN_MAX, HEAD_MIN_M / d));
}

// `reach` is the unit frame the placements are scaled into (the whole cluster);
// `floret` is the size each drawn floret is scaled to (15-florets.js).
function _inflorescence(p, arch, drawn, h) {
  const dia = bloomGain(p, arch) * Math.max(0.15, Math.min(20, p.flower_diameter_cm || 2)) / 100;
  // A head and a solitary flower are drawn at their true diameter, or at
  // HEAD_MIN_M where that is a dot from a yard away (V3.64).
  if (arch === 'head' || arch === 'solitary') return { reach: dia, floret: dia };
  // The cluster's size comes from the REAL floret count, not from how many are
  // drawn, and never exceeds a share of the plant it is on.
  const n = Math.max(1, p.florets_per_head || drawn);
  const natural = Math.max(dia * 2.2, dia * Math.sqrt(n) * (_ARCH_REACH[arch] || 2.0));
  const reach = Math.max(dia, Math.min(natural, 0.55, _REACH_OF_HEIGHT * h));
  // Each drawn floret stands in for n / drawn real ones, so it covers the area
  // they would: a goldenrod draws 20 florets at 1.7 cm over a 26 cm plume.
  const floret = Math.max(dia, Math.min(reach * 0.5,
                                        dia * Math.sqrt(n / Math.max(1, drawn))));
  return { reach, floret };
}

// Where the heads of one counted cluster sit, round its anchor at (x, y, z):
// [{x, y, z, spin, tilt}], the first at the anchor. A head faces out from the
// plant's middle (cx, cz) and up; `size` is a head's drawn width.
function headSpray(p, arch, x, y, z, cx, cz, size, rnd) {
  const out = [], heads = arch === 'head' ? (HEADS_PER_CLUSTER[p.stem_branching] || 1) : 1;
  const face = (hx, hz) => {
    const dx = hx - cx, dz = hz - cz;
    return Math.hypot(dx, dz) > 0.02 ? Math.atan2(dx, dz) : rnd() * 6.283;
  };
  for (let k = 0; k < heads; k++) {
    const a = k * 2.39996 + rnd(), r = k ? size * (1.1 + 0.5 * rnd()) : 0;
    const hx = x + Math.cos(a) * r, hz = z + Math.sin(a) * r;
    const flat = arch === 'head' || arch === 'solitary';
    out.push({ x: hx, y: y - (k ? size * (0.3 + 0.5 * rnd()) : 0), z: hz,
               spin: flat ? face(hx, hz) + (rnd() - 0.5) * 0.8 : null,
               tilt: flat ? HEAD_TILT[0] + (HEAD_TILT[1] - HEAD_TILT[0]) * rnd() : null });
  }
  return out;
}

// A wildflower whose clusters are dense enough to read as one shape: carried as
// a card (15c-woodybloom.js) and not as florets.
function denseClusterApplies(p) {
  if (STYLISED || !p.flower_arch || p.inflorescence_form) return false;
  if (p.plant_type === 'tree' || p.plant_type === 'shrub' || p.plant_type === 'vine') return false;
  return !!DENSE_ARCHES[p.flower_arch] && (p.florets_per_head || 0) >= DENSE_FLORETS;
}

window.bloomGain = bloomGain;
window.headSpray = headSpray;
window.denseClusterApplies = denseClusterApplies;
