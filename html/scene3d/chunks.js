// html/scene3d/chunks.js — the 3D viewer's chunks, in load order (V3.39).
//
// Moved out of scene3d.html, which was at its 400-line ceiling: the guard's
// own note said the next chunk needed this list out of the page first. A
// classic script, loaded before the page's module, which reads it; each
// chunk's onload loads the next, so the global-scope declarations accumulate
// in this order. Load ORDER is dependency order (see any chunk's header).
window.SCENE3D_CHUNKS = [
  'scene3d/01-core.js',
  // Surfaces + plantMaterial: before 02-plants because everything downstream
  // of it builds geometry that wants a material.
  'scene3d/01b-surface.js',
  'scene3d/01c-leaves.js',   // V2.94: leaves let light through (F186)
  // V3.46: the season as the scene decided it (F263): one place colours a
  // plant body, says whether leaves are down and whether snow lies.
  'scene3d/01d-season.js',
  // V3.53: light that follows the sun: the ground's bounce, the exposure, and
  // the shadow map over the yard (F265, F187). After 01d-season.js, whose
  // ground it reflects.
  'scene3d/01e-light.js',
  'scene3d/02-plants.js',
  // V3.45: what the ground is, the lines on it, the street and the houses
  // (F262). After 02-plants.js for terrainHeightAt and the ground's textures.
  'scene3d/02c-site.js',
  'scene3d/03-herbs.js',
  'scene3d/03b-trees.js',   // V2.92: the procedural trees, split from 03-herbs
  // V3.48: a wildflower built from its own leaf, arrangement and stem count
  // where those were read (F268). After 03-herbs.js for its leaf outlines.
  'scene3d/03c-leafy.js',
  // V3.49: a shrub built from its own stem count and leaf where those were
  // read (F268), and the shrub layer, moved out of 04-quality.js. After
  // 03c-leafy.js for its leaf outlines and tubes.
  'scene3d/03d-woody.js',
  // V3.50: a tree built from its own crown where that was read (F268): its
  // trunks, bare bole, limbs and outline, on 03d-woody.js's shoots.
  // V3.66: a leafy wildflower's stems carry cut-out leafy shoots, as a shrub's
  // do, as many as cover its outline (F268). Called by 03c-leafy.js at build.
  'scene3d/03g-stemleaves.js',
  // V3.67b: the leafy body's rosettes and tufts, split from 03c-leafy.js (at
  // its ceiling), with an umbrella of one divided leaf and a fern's fronds.
  'scene3d/03h-leafyforms.js',
  'scene3d/03e-crowns.js',
  // V3.51: a grass, sedge or rush built from its own blades and seed head
  // where those were read (F268). After 03c-leafy.js for its blades and tubes.
  'scene3d/03f-tufts.js',
  'scene3d/04-quality.js',
  'scene3d/05-flowers.js',
  'scene3d/06-fly.js',
  'scene3d/07-wildlife.js',
  'scene3d/08-modes.js',
  'scene3d/09-models.js',
  'scene3d/10-inspect.js',
  'scene3d/11-fruit.js',
  'scene3d/12-seedheads.js',
  'scene3d/13-stylised.js',
  'scene3d/14-layers.js',
  'scene3d/15-florets.js',
  // V3.48: flowers and fruit on the stems and crowns that were drawn.
  'scene3d/15b-anchors.js',
  // V3.49: a shrub's flower clusters as cut-out cards on its shoots, where
  // the body is one of 03d-woody.js's (F268).
  'scene3d/15c-woodybloom.js',
  // V3.63: a shrub's or tree's fruit as cut-out bunches on its shoots, and
  // held on the bare twigs into the winter where that was read (F268).
  'scene3d/15d-woodyfruit.js',
  // V3.64: a daisy you can see and a spike drawn as a spike: a head's least
  // size and its facing, and a wildflower's dense clusters as cards (F268).
  'scene3d/15e-heads.js',
  // V3.67b: a flower that hangs, as a bell or a swept-back dart, where its
  // head_attitude was read nodding (F268). Called by 05-flowers.js at build.
  'scene3d/15f-nodding.js',
  // V2.43: click-to-plant in the reference sandboxes, and the QWebChannel
  // the viewer never had. Last on purpose — its pointer handlers must
  // register after 10-inspect.js's so both see the same click.
  'scene3d/16-editing.js',
  // V2.44: the tween registry and the plant / pull / catch animations.
  // 16-editing.js only calls into these at click time, long after every
  // chunk has loaded, so it does not need to load first.
  'scene3d/17-anim.js',
  'scene3d/18-flight.js',   // V2.45: real wingbeats (src/flight_model.py)
  // V2.46: the roster / labels / spotlight, split out of 07-wildlife.js when
  // life-size scaling and creature collision took it past its ceiling.
  'scene3d/19-roster.js',
  // V2.46b: the walker's body and his net, split out of 08-modes.js when the
  // held net took it past its ceiling. Nothing here is called from the
  // animation loop — see the load-order note in the file.
  'scene3d/20-walker.js',
  // V2.46d: the procedural creature bodies, split out of 07-wildlife.js when
  // the bird flight attitude took it past its ceiling. Nothing here is called
  // from the animation loop — see 08-modes.js:_loopFault.
  'scene3d/21-critters.js',
  // V2.89: vines on the tree or shrub beside them (F179). Called from
  // buildPlants after the trees and shrubs have noted where they stand.
  'scene3d/22-vines.js',
  // V3.50: a vine's own leafy shoots where its leaves were read (F268).
  'scene3d/22b-vineleaves.js',
  // V2.90: the pond (F175) — floating leaves on a pond's water, submerged
  // plants showing what reaches the surface, broad leaves on stalks.
  'scene3d/23-pond.js',
  // V3.67b: the water plants by their own parts (F268): feathery shoots and
  // threads on the water, flowering stalks out of it, duckweed chains, a
  // buckbean's leaflets, a water-plantain's panicle, a calla's spathe.
  'scene3d/23b-pondforms.js',
  'scene3d/24-succulents.js',   // V2.93: cacti, yucca and roseroot (F177)
  // V3.39: what a card says, its links and the trail back (F255). After
  // 16-editing.js, whose bridge Plant one calls, and after 10-inspect.js,
  // whose showCard draws through it.
  'scene3d/25-cards.js',
  // V3.43: the frame-rate readout (Ctrl+Shift+F). It wraps the render call
  // only while it is showing, and nothing calls into it.
  // V3.46: where the plan's losses are and which plants (F263), from
  // scene.timeline_notes: a button under the line, a list, rings on the ground.
  'scene3d/25b-timeline.js',
  'scene3d/26-perf.js',
  // V3.44: the named viewpoints (from the street, the house, above) and the
  // moment in words (F261). 08-modes.js, where the camera presets live, was
  // at its ceiling; its two callers in earlier chunks are typeof-guarded.
  'scene3d/27-views.js',
];
