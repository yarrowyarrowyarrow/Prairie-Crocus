// html/map/05b-yard.js — the Yard palette's lines, and objects moved and turned (V3.72).
//
// A classic script like its neighbours, loaded straight after 05-features.js,
// which was at its ceiling: the line drawing moved here whole (it had been
// 05-features.js's "Hedgerow drawing (S2)"), with two changes. A saved line is
// drawn without telling Python it was drawn, and keeps its id: until V3.72 every
// open added a copy of each hedge and fence to the design. And a wall and a
// swale have their own looks.
//
// Objects (a bee hotel, a brush pile, a compost bin…) are placed by
// placeStructureOnMap; here they are dragged when no tool is on, and turned 45°
// from their right-click menu or by R with the pointer over them. A turn is
// stored as bearing_deg on the feature (src/yard_object_flow.py), and a
// rectangle is drawn turned (_structureCorners), as src/yard_kinds.footprint_ring
// and the 3D read it.

    // ── Lines: hedges, fences, walls, swales (S2) ─────────────────────────────
    function handleHedgerowClick(lat, lng) {
      hedgerowPoints.push([lat, lng]);

      // Draw vertex marker
      L.circleMarker([lat, lng], {
        radius: 4,
        color: currentHedgerow ? currentHedgerow.color : '#4caf50',
        fillColor: currentHedgerow ? currentHedgerow.color : '#4caf50',
        fillOpacity: 1
      }).addTo(drawnItems);

      refreshHedgerowPolyline();
    }

    function refreshHedgerowPolyline() {
      if (hedgerowPreview) { map.removeLayer(hedgerowPreview); hedgerowPreview = null; }
      if (hedgerowPoints.length >= 2) {
        var color = currentHedgerow ? currentHedgerow.color : '#4caf50';
        hedgerowPreview = L.polyline(hedgerowPoints, {
          color: color, weight: 3, opacity: 0.7, dashArray: '6 4'
        }).addTo(map);
      }
    }

    function updateHedgerowPreview(latlng) {
      if (hedgerowPreview) { map.removeLayer(hedgerowPreview); }
      var color = currentHedgerow ? currentHedgerow.color : '#4caf50';
      var pts = hedgerowPoints.concat([[latlng.lat, latlng.lng]]);
      hedgerowPreview = L.polyline(pts, {
        color: color, weight: 3, opacity: 0.5, dashArray: '4 4'
      }).addTo(map);
    }

    function finishHedgerow() {
      if (hedgerowPoints.length < 2) return;
      if (hedgerowPreview) { map.removeLayer(hedgerowPreview); hedgerowPreview = null; }
      drawnItems.clearLayers();

      var cfg = currentHedgerow || {};
      // A saved line keeps the id the design knows it by (V3.72), so a
      // right-click on it after a reopen removes it, not a copy.
      var id = cfg.hedge_id ||
        ('hedge_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5));
      if (hedgerowLayers[id]) { map.removeLayer(hedgerowLayers[id]); delete hedgerowLayers[id]; }
      var color   = cfg.color    || '#4caf50';
      var widthM  = cfg.width_m  || 1.5;
      var spacing = cfg.spacing_m || 1.0;
      var style   = cfg.style    || 'hedge';
      var species = cfg.species  || '';
      var group   = L.layerGroup().addTo(map);

      // Style definitions
      var styleMap = {
        'hedge':       { weight: 6, opacity: 0.6, dashArray: null,    fillDots: true },
        'fence':       { weight: 3, opacity: 0.8, dashArray: '8 6',  fillDots: false },
        'living_fence':{ weight: 5, opacity: 0.6, dashArray: '12 4', fillDots: true },
        'windbreak':   { weight: 8, opacity: 0.5, dashArray: null,    fillDots: true },
        'wall':        { weight: 5, opacity: 0.85, dashArray: null,   fillDots: false },
        'swale':       { weight: 9, opacity: 0.45, dashArray: '2 6', fillDots: false }
      };
      var s = styleMap[style] || styleMap['hedge'];

      // Main polyline
      var mainLine = L.polyline(hedgerowPoints, {
        color: color,
        weight: s.weight,
        opacity: s.opacity,
        dashArray: s.dashArray,
        lineCap: 'round',
        lineJoin: 'round'
      }).addTo(group);

      // The line's length, for every style. Until V3.11 it was measured only
      // where plants are dotted along it, so a fence (no dots) threw on the
      // tooltip below and was never kept, saved or sent to Python.
      var totalLen = 0, segments = [];
      for (var i = 1; i < hedgerowPoints.length; i++) {
        var from = L.latLng(hedgerowPoints[i-1]);
        var to   = L.latLng(hedgerowPoints[i]);
        var segLen = from.distanceTo(to);
        segments.push({ from: from, to: to, len: segLen });
        totalLen += segLen;
      }
      // A hedge, living fence or windbreak planted with real plants (V3.74)
      // draws no dots: its plants are on the map. One drawn with plants
      // chosen is planted by Python as soon as it is finished.
      var living = cfg.living !== undefined ? !!cfg.living
        : (style === 'hedge' || style === 'living_fence' || style === 'windbreak');
      var planted = (+cfg.plants > 0) || !!(cfg.plant_ids && cfg.plant_ids.length);
      var numPlants = planted ? (+cfg.plants || 0)
        : (s.fillDots ? Math.floor(totalLen / spacing) + 1 : 0);

      // Plant markers along the line
      if (s.fillDots && !planted) {
        var distAlong = 0;
        var segIdx = 0;
        var segDist = 0;
        for (var p = 0; p < numPlants; p++) {
          var target = p * spacing;
          while (segIdx < segments.length - 1 && segDist + segments[segIdx].len < target) {
            segDist += segments[segIdx].len;
            segIdx++;
          }
          var seg = segments[segIdx];
          var frac = seg.len > 0 ? (target - segDist) / seg.len : 0;
          frac = Math.max(0, Math.min(1, frac));
          var ptLat = seg.from.lat + (seg.to.lat - seg.from.lat) * frac;
          var ptLng = seg.from.lng + (seg.to.lng - seg.from.lng) * frac;

          var dotColor = style === 'living_fence' ?
            (p % 2 === 0 ? color : shiftColor(color, 30)) : color;
          L.circleMarker([ptLat, ptLng], {
            radius: 3.5,
            color: dotColor,
            fillColor: dotColor,
            fillOpacity: 0.8,
            weight: 1
          }).addTo(group);
        }
      }

      // Label at midpoint
      var midIdx = Math.floor(hedgerowPoints.length / 2);
      var styleWords = style.replace(/_/g, ' ').replace(/\b\w/g, function(c) { return c.toUpperCase(); });
      var FENCE_WORDS = { rail: 'Rail fence', board: 'Board fence', chain_link: 'Chain link fence' };
      if (style === 'fence' && FENCE_WORDS[cfg.fence_kind]) styleWords = FENCE_WORDS[cfg.fence_kind];
      var labelText = species || styleWords;
      var labelIcon = L.divIcon({
        className: 'hedgerow-label',
        html: escH(labelText),
        iconSize: [0, 0],
        iconAnchor: [0, 12]
      });
      L.marker(hedgerowPoints[midIdx], { icon: labelIcon, interactive: false }).addTo(group);

      // Tooltip
      var tooltipText = '<b>' + escH(styleWords) + '</b>';
      if (species) tooltipText += '<br>' + escH(species);
      tooltipText += '<br><span style="color:#b0bec5;font-size:12px">' +
        (numPlants ? (planted ? '' : '~') + Number(numPlants) + ' plants · ' : '') +
        totalLen.toFixed(1) + 'm<br>Right-click for more</span>';
      mainLine.bindTooltip(tooltipText, { className: 'plant-marker-label' });

      // Store metadata
      mainLine._hedge = {
        id: id,
        points: hedgerowPoints.slice(),
        style: style,
        color: color,
        widthM: widthM,
        spacingM: spacing,
        species: species,
        lengthM: totalLen,
        numPlants: numPlants
      };

      // Right-click: plant it (a living line, V3.74) or remove it, with
      // what Remove takes said. It removed on a right-click until V3.74.
      var linePoints = hedgerowPoints.slice();
      var lineWords = styleWords.toLowerCase();
      function removeLine() {
        map.removeLayer(group);
        delete hedgerowLayers[id];
        if (bridge) bridge.onHedgerowRemoved(id, JSON.stringify(linePoints));
      }
      mainLine.on('contextmenu', function(e) {
        L.DomEvent.stop(e);
        var oe = e.originalEvent;
        if (typeof showContextMenu !== 'function') { removeLine(); return; }
        var items = [];
        if (living) {
          items.push({ label: (planted ? 'Change its plants…'
                                       : 'Plant this ' + lineWords + '…'),
                       action: function() {
                         if (bridge && bridge.onHedgePlantRequested)
                           bridge.onHedgePlantRequested(id);
                       } });
          items.push('sep');
        }
        items.push({ label: '🗑 Remove the ' + lineWords +
                     (planted && numPlants ? ' and its ' + Number(numPlants) +
                      ' plants' : ''), action: removeLine });
        showContextMenu(oe.clientX, oe.clientY, items);
      });

      hedgerowLayers[id] = group;

      // Notify Python of a line just drawn, never of a saved one being drawn
      // again (V3.72): that told Python a line had been drawn, so every open
      // added a copy of each hedge and fence and asked to be saved.
      if (bridge && !cfg._suppressBridge)
        bridge.onHedgerowComplete(id, JSON.stringify(hedgerowPoints.slice()), species, style, totalLen, numPlants);

      hedgerowPoints = [];
      setMode('none');
    }

    // Undo helper — remove a hedgerow group by its id. Returns true on hit.
    function undoHedgerowById(hedgeId) {
      var group = hedgerowLayers[hedgeId];
      if (!group) return false;
      try { map.removeLayer(group); } catch (e) {}
      delete hedgerowLayers[hedgeId];
      return true;
    }

    // Load a hedgerow from saved project
    function loadHedgerow(hedgeDef) {
      hedgerowPoints = hedgeDef.points || [];
      currentHedgerow = Object.assign({}, hedgeDef, { _suppressBridge: true });
      if (hedgerowPoints.length >= 2) {
        finishHedgerow();
      }
      hedgerowPoints = [];
      currentHedgerow = null;
    }

    // ── Objects: drawn turned, dragged, and turned 45° (V3.72) ──────────────
    // The corners of a rectangle sizeM along its bearing (clockwise from north)
    // by widthM across, about (lat, lng): src/yard_kinds.footprint_ring's.
    function _structureCorners(lat, lng, sizeM, widthM, bearingDeg) {
      var b = (bearingDeg || 0) * Math.PI / 180, cb = Math.cos(b), sb = Math.sin(b);
      var hn = sizeM / 2, he = widthM / 2;
      var kx = 111320 * Math.cos(lat * Math.PI / 180);
      return [[-he, -hn], [he, -hn], [he, hn], [-he, hn]].map(function(p) {
        var e = p[0] * cb + p[1] * sb, n = -p[0] * sb + p[1] * cb;
        return [lat + n / 111320, lng + e / kx];
      });
    }

    var _hoverObject = null;              // the object under the pointer, for R

    function _redrawObject(st) {
      if (st.layer.setLatLng) st.layer.setLatLng([st.lat, st.lng]);
      else if (st.layer.setLatLngs)
        st.layer.setLatLngs(_structureCorners(st.lat, st.lng, st.sizeM,
                                              st.widthM, st.bearing));
      if (st.label && st.label.setLatLng) st.label.setLatLng([st.lat, st.lng]);
      st.group._pdStruct.lat = st.lat; st.group._pdStruct.lng = st.lng;
    }

    // Turn an object 45° clockwise and tell Python (one undo step there).
    function turnObject(st, degrees) {
      st.bearing = ((st.bearing || 0) + (degrees || 45)) % 360;
      _redrawObject(st);
      if (bridge && bridge.onStructureTurned)
        bridge.onStructureTurned(st.id, st.structId, st.lat, st.lng, st.bearing);
    }

    // R on the map: the object under the pointer, if no tool is on. Returns
    // whether one was turned (the window turns a community being placed first).
    function turnHoveredObject() {
      if (!_hoverObject || currentMode !== 'none') return false;
      turnObject(_hoverObject, 45);
      return true;
    }

    // Make a placed object movable and turnable. Its right-click menu has
    // Turn 45° and Remove; it used to remove on a right-click.
    function makeObjectEditable(group, layer, label, id, structDef, lat, lng,
                                sizeM, widthM, name, remove) {
      var st = { id: id, structId: structDef.id, lat: lat, lng: lng,
                 sizeM: sizeM, widthM: widthM, bearing: +structDef.bearing_deg || 0,
                 layer: layer, label: label, group: group, name: name };
      group._pdObject = st;
      var el = layer.getElement && layer.getElement();
      if (el) el.style.cursor = 'move';
      layer.on('mouseover', function() { _hoverObject = st; });
      layer.on('mouseout', function() { if (_hoverObject === st) _hoverObject = null; });
      layer.on('contextmenu', function(e) {
        L.DomEvent.stop(e);
        var oe = e.originalEvent;
        if (typeof showContextMenu !== 'function') { remove(); return; }
        showContextMenu(oe.clientX, oe.clientY, [
          { label: '↻ Turn 45°', action: function() { turnObject(st, 45); } },
          'sep',
          { label: '🗑 Remove ' + name, action: remove },
        ]);
      });
      var dragging = false, moved = false, base = null;
      function onMove(e) {
        moved = true;
        st.lat = e.latlng.lat; st.lng = e.latlng.lng;
        _redrawObject(st);
      }
      function onUp() {
        if (!dragging) return;
        dragging = false;
        map.off('mousemove', onMove); map.off('mouseup', onUp);
        try { map.dragging.enable(); } catch (_) {}
        if (moved && bridge && bridge.onExistingFeatureMoved)
          bridge.onExistingFeatureMoved(st.id, st.structId, base[0], base[1],
                                        st.lat, st.lng);
      }
      layer.on('mousedown', function(e) {
        if (currentMode !== 'none' && currentMode !== 'select') return;
        var oe = e.originalEvent;
        if (oe && oe.button !== undefined && oe.button !== 0) return;
        if (oe && (oe.shiftKey || oe.ctrlKey || oe.metaKey)) return;
        L.DomEvent.stop(e);
        dragging = true; moved = false; base = [st.lat, st.lng];
        try { map.dragging.disable(); } catch (_) {}
        map.on('mousemove', onMove); map.on('mouseup', onUp);
      });
      return st;
    }
