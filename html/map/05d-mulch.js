// html/map/05d-mulch.js — the rings of mulch under plants (V3.76).
//
// Python decides which plants have a ring and how big it is
// (src/mulch_rings.py) and hands the whole list here a moment after any
// change and after every full redraw (src/mulch_rings_flow.py), so this only
// draws: brown discs in a pane under the plants' canvas, taking no clicks.
// A ring under a plant standing in a drawn bed or mulch area is not drawn
// (shown: false), the ground being mulched already. A plant's right-click
// menu (03-plants.js asks mulchMenuItems) gives or takes away its ring, or
// its group's.

    var _mulchLayer = null, _mulchRings = [];

    function setMulchRings(list) {
      _mulchRings = list || [];
      if (typeof map === 'undefined' || !map) return;
      if (!map.getPane('mulchPane')) {
        var pane = map.createPane('mulchPane');
        pane.style.zIndex = 390;               // under the overlays and plants
        pane.style.pointerEvents = 'none';
      }
      if (_mulchLayer) map.removeLayer(_mulchLayer);
      _mulchLayer = L.layerGroup();
      var renderer = L.svg({ pane: 'mulchPane' });
      _mulchRings.forEach(function(r) {
        if (!r.shown) return;
        L.circle([r.lat, r.lng], {
          radius: r.r, pane: 'mulchPane', renderer: renderer, interactive: false,
          color: '#5d4330', weight: 1, fillColor: '#8b6a47', fillOpacity: 0.8
        }).addTo(_mulchLayer);
      });
      _mulchLayer.addTo(map);
    }

    function _hasMulch(lat, lng) {
      return _mulchRings.some(function(r) {
        return Math.abs(r.lat - lat) < 1e-7 && Math.abs(r.lng - lng) < 1e-7;
      });
    }

    // A plant's right-click items: its own ring, and its group's.
    function mulchMenuItems(pd) {
      if (!pd || !pd.plantId) return [];
      var on = _hasMulch(pd.lat, pd.lng);
      function send(groupId) {
        if (bridge && bridge.onMulchRingToggled)
          bridge.onMulchRingToggled(pd.plantId, pd.lat, pd.lng, groupId || '', !on);
      }
      var items = [{ label: on ? 'Take its mulch ring away' : 'Add a mulch ring',
                     action: function() { send(''); } }];
      var n = (pd.groupId && typeof _groupSize === 'function') ? _groupSize(pd.groupId) : 0;
      if (n >= 2)
        items.push({ label: (on ? 'Take the mulch rings away from all ' : 'Add mulch rings to all ')
                            + n + ' in its group',
                     action: function() { send(pd.groupId); } });
      return items;
    }
