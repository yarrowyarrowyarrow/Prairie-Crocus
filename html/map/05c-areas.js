// html/map/05c-areas.js — an area put down whole: a rectangle or a circle of
// the size typed (V3.75).
//
// Placement › Yard's *Place it as* (src/yard_palette.py) hands the shape tool
// `place` ("rectangle" or "circle") with its size in metres. The area follows
// the cursor as a ghost, R turns a rectangle 15° (Python's
// tree_edit_flow.turn_key asks turnHoveredObject, which asks turnPlacingArea
// first), and a click puts it down as the outline a drawn one would have,
// through finishShape, so the design stores it as it stores any drawn area.
// A classic script like its neighbours, loaded after 05b-yard.js, whose
// _structureCorners it uses.

    var _areaGhost = null, _areaBearing = 0;
    var AREA_TURN_DEG = 15, AREA_CIRCLE_SIDES = 32;

    function _placingArea() {
      return currentMode === 'shape' && !!currentShape &&
        (currentShape.place === 'rectangle' || currentShape.place === 'circle');
    }

    // The outline about (lat, lng): a rectangle `place_length_m` along its
    // bearing (clockwise from north) by `place_width_m`, or a circle
    // `place_across_m` wide.
    function areaOutline(cfg, lat, lng, bearing) {
      if (cfg.place === 'circle') {
        var r = (+cfg.place_across_m || 3) / 2;
        var kx = 111320 * Math.cos(lat * Math.PI / 180), pts = [];
        for (var i = 0; i < AREA_CIRCLE_SIDES; i++) {
          var a = 2 * Math.PI * i / AREA_CIRCLE_SIDES;
          pts.push([lat + r * Math.cos(a) / 111320, lng + r * Math.sin(a) / kx]);
        }
        return pts;
      }
      return _structureCorners(lat, lng, +cfg.place_length_m || 3,
                               +cfg.place_width_m || 2, bearing || 0);
    }

    function _dropAreaGhost() {
      if (_areaGhost) { map.removeLayer(_areaGhost); _areaGhost = null; }
    }

    // The ghost under the cursor while placing (01-core.js's mouse move).
    function updateAreaGhost(latlng) {
      if (!_placingArea()) { _dropAreaGhost(); return; }
      var pts = areaOutline(currentShape, latlng.lat, latlng.lng, _areaBearing);
      var colour = currentShape.stroke_color || '#2e7d32';
      if (_areaGhost) _areaGhost.setLatLngs(pts);
      else _areaGhost = L.polygon(pts, {
        color: colour, weight: 2, dashArray: '4 4', interactive: false,
        fillColor: currentShape.fill_color || colour, fillOpacity: 0.2
      }).addTo(map);
      _areaGhost._at = [latlng.lat, latlng.lng];
    }

    // A click while placing puts the area down there (handleShapeClick asks).
    // Returns whether it did.
    function placeAreaAt(lat, lng) {
      if (!_placingArea()) return false;
      _dropAreaGhost();
      shapePoints = areaOutline(currentShape, lat, lng, _areaBearing);
      finishShape();
      return true;
    }

    // R while placing a rectangle turns it 15°. Returns whether it turned.
    function turnPlacingArea() {
      if (!_placingArea() || currentShape.place !== 'rectangle') return false;
      _areaBearing = (_areaBearing + AREA_TURN_DEG) % 180;
      if (_areaGhost && _areaGhost._at)
        updateAreaGhost(L.latLng(_areaGhost._at[0], _areaGhost._at[1]));
      return true;
    }
