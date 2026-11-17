// html/scene3d/01e-light.js — light that follows the sun (V3.53, F265; 3D-6 of
// docs/plans/V3.43-the-3d-preview-reviewed.md, the owner's decision D6).
//
// Until V3.53 the viewer lit every scene with one sun, one hemisphere light whose
// ground colour was a fixed dark green, and a fixed exposure. Three faults
// followed, each measured on the review lot (docs/plans/V3.53-light.md):
//
//  * The light coming up off the ground was a seventh of what the viewer's own
//    sun and sky put on the lawn it draws (F187). Everything facing away from
//    the sun (a wall's shaded side, a trunk, the underside of a crown, an
//    animal's belly) was lit by that dark green alone.
//  * The exposure never moved, so as the sun went down the picture went to
//    murk: an August evening read as dusk, an October afternoon nearly so.
//  * The sun's shadow map was a square around the stage's origin sized from the
//    stage (±25 m at least), not the yard: 75 m of map for a 15 m lot, centred
//    wherever the origin happened to be.
//
// Here, decided once per sun position (``applyLight``, from 01-core.js's
// updateAtmosphere and setNight) and once per scene (``fitShadowToYard``, from
// permaSetScene):
//
//  * The ground's light is the ground's albedo times what falls on it: the sun
//    on the share of the ground it reaches, plus the sky. Snow, dormant grass
//    and green grass each reflect their own share. This is how a real ground
//    lights what stands on it, with the viewer's own light units, so it follows
//    the sun's height and the season by itself.
//  * The sky's light warms with the horizon as the sun goes down.
//  * The exposure is the noon exposure times the square root of how much less
//    light falls on the ground than at noon, within a cap: an evening stays an
//    evening, darker and warmer than noon, but legible. A camera's automatic
//    exposure does about this, and only partly corrects, on purpose.
//  * The shadow map is fitted to what casts and receives in the yard: the
//    design's own extent and every building and plant in the scene, in the
//    sun's own view. The map's size in pixels is unchanged, so no per-frame
//    cost is added; each pixel covers less ground.
//
// **Every number below is an estimate nobody measured on a site**, stated here
// the way V3.45's fence heights are. Nothing here reads the plant data.

const LIGHT = {
  // Reflectance of the ground, linear RGB. Grass about 0.2, dormant grass
  // about 0.22, old snow about 0.75. Grass's own green was drawn first
  // (0.16, 0.22, 0.10) and put an olive cast on every wall turned from the sun
  // (V3.53's first sheet); a lawn is a mix of blades, thatch and soil, so it
  // is kept only faintly green.
  albedo: {
    green: new THREE.Color().setRGB(0.18, 0.21, 0.14, THREE.LinearSRGBColorSpace),
    dormant: new THREE.Color().setRGB(0.23, 0.21, 0.16, THREE.LinearSRGBColorSpace),
    snow: new THREE.Color().setRGB(0.72, 0.75, 0.80, THREE.LinearSRGBColorSpace),
  },
  // The share of the ground near a thing that the sun reaches: things stand
  // among other things, and the ground beside a wall or under a crown is
  // partly in shade. An estimate.
  sunOnGround: 0.7,
  // Exposure: the noon value, how strongly it follows the light, and its cap.
  noonExposure: 1.15, follow: 0.5, maxExposure: 1.85,
  nightExposure: 1.45,
  // The sky's light: how far toward the horizon's colour it goes at low sun.
  warmSky: 0.45,
  // The shadow map: a margin round what is fitted, and the most ground it
  // covers before it falls back to the stage.
  shadowPadM: 1.5, shadowMaxM: 140,
};
const _NOON_SKY = new THREE.Color(0xdfeefc);
const _lightTmp = new THREE.Color(), _lightTmp2 = new THREE.Color();

// The light that falls on level ground (linear RGB, the viewer's units): the
// sun on the share of the ground it reaches, plus the sky.
function sunUp() {
  return sun.position.clone().sub(sun.target.position).normalize().y;
}
function groundLight(out) {
  const up = Math.max(0, sunUp());
  out.copy(sun.color).multiplyScalar(sun.intensity * up * LIGHT.sunOnGround);
  return out.add(_lightTmp2.copy(hemi.color).multiplyScalar(hemi.intensity));
}
function groundAlbedo() {
  const g = typeof seasonGround === 'function' ? seasonGround(lastMonth) : 'green';
  return g === 'snow' ? LIGHT.albedo.snow
    : (g === 'dormant' || g === 'waking') ? LIGHT.albedo.dormant : LIGHT.albedo.green;
}
const _luma = (c) => 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;
// The light at noon on midsummer's day, from 01-core.js's own noon values: what
// the exposure follows.
const NOON_LIGHT = 2.4 * Math.sin(60 * Math.PI / 180) * LIGHT.sunOnGround
  + 0.9 * _luma(_NOON_SKY);

// Called (through relight) once the sun or the moon is placed and 01-core.js
// has set its colour and strength and the sky's.
function applyLight(altDeg, night) {
  if (!night) {
    const t = Math.pow(Math.max(0, Math.min(1, altDeg / 30)), 0.65);  // 1 = high
    hemi.color.copy(_NOON_SKY).lerp(skyU.uHorizon.value, LIGHT.warmSky * (1 - t));
  }
  const fall = groundLight(_lightTmp);
  hemi.groundColor.copy(fall).multiply(groundAlbedo())
    .multiplyScalar(1 / Math.max(0.05, hemi.intensity));
  renderer.toneMappingExposure = night ? LIGHT.nightExposure : Math.min(
    LIGHT.maxExposure, Math.max(LIGHT.noonExposure, LIGHT.noonExposure
      * Math.pow(NOON_LIGHT / Math.max(0.05, _luma(fall)), LIGHT.follow)));
}
// The season changes the ground under a sun that has not moved: permaSetScene
// asks again once the scene says what the ground is doing.
function relight() {
  const alt = Math.asin(Math.max(-1, Math.min(1, sunUp()))) * 180 / Math.PI;
  applyLight(alt, sceneNight);
}

// The sun's shadow map over what casts and receives in the yard (``sc.focus``,
// its buildings and its plants), in the sun's own view. Returns false (and the
// caller keeps 01-core.js's square over the stage) for a scene with no focus,
// a walk or the sprite gallery, or one too big for the map.
const _shadowEye = new THREE.OrthographicCamera();
function fitShadowToYard(sc) {
  const f = sc && sc.focus;
  if (!f) return false;
  const tH = (x, y) => terrainHeightAt(x, y, sc.terrain);
  const pts = [];
  for (const [x, y] of [[f.min_x, f.min_y], [f.max_x, f.min_y],
                        [f.max_x, f.max_y], [f.min_x, f.max_y]]) {
    pts.push([x, tH(x, y), y]);
  }
  for (const b of sc.buildings || []) {
    for (const [x, y] of b.ring || []) pts.push([x, tH(x, y) + (b.height_m || 0), y]);
  }
  for (const p of sc.plants || []) {
    if (p.gone) continue;
    const r = (p.canopy_m || 0) / 2, h = tH(p.x, p.y) + (p.height_m || 0);
    pts.push([p.x - r, h, p.y - r], [p.x + r, h, p.y + r],
             [p.x - r, h, p.y + r], [p.x + r, h, p.y - r]);
  }
  const cx = (f.min_x + f.max_x) / 2, cy = (f.min_y + f.max_y) / 2;
  const target = new THREE.Vector3(cx, tH(cx, cy), -cy);
  const dir = sun.position.clone().sub(sun.target.position).normalize();
  sun.target.position.copy(target);
  sun.position.copy(target).addScaledVector(dir, 300);
  sun.target.updateMatrixWorld();
  _shadowEye.position.copy(sun.position);
  _shadowEye.lookAt(target);
  _shadowEye.updateMatrixWorld();
  const inv = _shadowEye.matrixWorldInverse, v = new THREE.Vector3();
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  let z0 = Infinity, z1 = -Infinity;
  for (const [x, h, y] of pts) {
    v.set(x, h, -y).applyMatrix4(inv);
    x0 = Math.min(x0, v.x); x1 = Math.max(x1, v.x);
    y0 = Math.min(y0, v.y); y1 = Math.max(y1, v.y);
    z0 = Math.min(z0, -v.z); z1 = Math.max(z1, -v.z);
  }
  const pad = LIGHT.shadowPadM;
  if (!isFinite(x0) || x1 - x0 > LIGHT.shadowMaxM || y1 - y0 > LIGHT.shadowMaxM) {
    return false;
  }
  const cam = sun.shadow.camera;
  cam.left = x0 - pad; cam.right = x1 + pad;
  cam.bottom = y0 - pad; cam.top = y1 + pad;
  cam.near = Math.max(1, z0 - 50); cam.far = z1 + 50;
  cam.updateProjectionMatrix();
  return true;
}
