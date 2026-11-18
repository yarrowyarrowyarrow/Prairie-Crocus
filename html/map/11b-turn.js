    // ── Turning a placed community (V3.59) ───────────────────────────────────
    //
    // The owner: "I'd like to be able to rotate the communities after (or
    // before?) placing them". Before is Python's (src/community_turn.py: the
    // bar's Turn button and the R key turn the preview). After is here: a
    // right-click on any plant of a placed community offers to turn it 45°
    // either way about its own centre, and the move goes to Python through the
    // same group-move a drag sends, so it is one undo step and saved like one.
    //
    // A community placed in a row or grid is one group of many communities;
    // the turn takes the one clicked (its communityId), not the whole row.

    function turnMenuItems(pd) {
      if (!pd || !(pd.communityId || pd.groupId)) return [];
      var scope = pd.communityId ? 'community' : 'group';
      if (_markersInScope(pd, scope).length < 2) return [];
      return [
        { label: 'Turn community 45° clockwise',
          action: function() { turnPlantGroup(pd, 45); } },
        { label: 'Turn community 45° anticlockwise',
          action: function() { turnPlantGroup(pd, -45); } },
        'sep',
      ];
    }

    // Pure: points [{lat, lng}] turned ``degrees`` clockwise (as seen on the
    // map, north up) about their mean, in metres so the shape keeps its size.
    function turnedPoints(points, degrees) {
      if (!points.length) return [];
      var clat = 0, clng = 0;
      points.forEach(function(p) { clat += p.lat; clng += p.lng; });
      clat /= points.length; clng /= points.length;
      var mLat = 111320, mLng = 111320 * Math.cos(clat * Math.PI / 180) || 1e-9;
      var a = degrees * Math.PI / 180, c = Math.cos(a), s = Math.sin(a);
      return points.map(function(p) {
        var east = (p.lng - clng) * mLng, north = (p.lat - clat) * mLat;
        var e2 = east * c + north * s, n2 = -east * s + north * c;
        return { lat: clat + n2 / mLat, lng: clng + e2 / mLng };
      });
    }

    function turnPlantGroup(pd, degrees) {
      var scope = pd.communityId ? 'community' : 'group';
      var members = _markersInScope(pd, scope);
      if (members.length < 2) return;
      var originals = members.map(function(m) {
        return { markerId: m._pd.markerId, plantId: m._pd.plantId,
                 lat: m._pd.lat, lng: m._pd.lng };
      });
      var turned = turnedPoints(originals, degrees);
      var moved = [];
      members.forEach(function(m, i) {
        var ll = L.latLng(turned[i].lat, turned[i].lng);
        m.setLatLng(ll);
        m._pd.lat = ll.lat; m._pd.lng = ll.lng;
        var lbl = plantLabels[m._pd.markerId];
        if (lbl) lbl.setLatLng(ll);
        moved.push({ markerId: m._pd.markerId, plantId: m._pd.plantId,
                     lat: ll.lat, lng: ll.lng });
      });
      if (typeof _refitSpeciesNumbers === 'function') _refitSpeciesNumbers();
      if (bridge && bridge.onPlantGroupMoved) {
        bridge.onPlantGroupMoved(pd.groupId, JSON.stringify(originals),
                                 JSON.stringify(moved));
      }
    }
