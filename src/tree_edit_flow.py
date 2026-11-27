"""
tree_edit_flow.py — persist drag / scroll-resize of existing tree & building
marks (V2.26), and the move and turn of a placed object (V3.72).

Free functions taking ``main`` (kept off MainWindow/the map controller, both at
their guard ceilings; wired from ``app.py`` via lambdas). Existing on-site
features — detected trees, and anything placed with Mark tree / Mark building —
are ``existing_tree`` / ``existing_building`` Point features (shade casters, not
design plants). The map now lets the user drag them to the real spot and
scroll-resize the crown to match the photo; these handlers write the new
position / canopy radius back onto the feature so it survives save, reload,
shade and the 3D view.

Each edit is one undo step (a persistence checkpoint). The marker has already
moved/resized on the map, so there's nothing to redraw — we only persist.
"""

from __future__ import annotations

from contextlib import nullcontext

_EXISTING = ("existing_tree", "existing_building")
#: What the map lets a person drag: an existing tree or building, and since
#: V3.72 a placed object (a bee hotel, a brush pile…).
_MOVABLE = _EXISTING + ("structure",)


def _checkpoint(main, label: str):
    persistence = getattr(main, "_persistence", None)
    return (persistence.checkpoint(label) if persistence is not None
            else nullcontext())


def _find(main, struct_id: str, lat: float, lng: float):
    """The existing-feature or object Point matching ``struct_id`` at
    ≈(lat, lng), or ``None``. Position is the identity (struct_id is shared
    by every tree)."""
    from src.yard_kinds import struct_id_of
    for f in main._project.get("features", []):
        props = f.get("properties") or {}
        if props.get("element_type") not in _MOVABLE:
            continue
        if (props.get("struct_id") or struct_id_of(props)) != struct_id:
            continue
        coords = (f.get("geometry") or {}).get("coordinates") or []
        if len(coords) >= 2 and abs(coords[1] - lat) < 1e-6 \
                and abs(coords[0] - lng) < 1e-6:
            return f
    return None


def on_existing_feature_moved(main, marker_id: str, struct_id: str,
                              old_lat: float, old_lng: float,
                              new_lat: float, new_lng: float) -> None:
    """Write a dragged existing tree/building's new position onto its feature."""
    feat = _find(main, struct_id, old_lat, old_lng)
    if feat is None:
        return
    with _checkpoint(main, "move existing feature"):
        # A wall object dragged goes onto the wall nearest where it was let
        # go (V3.76), the map's marker with it.
        new_lat, new_lng = onto_wall(main, feat["properties"], new_lat,
                                     new_lng)
        feat["geometry"]["coordinates"] = [new_lng, new_lat]
    main._mark_modified()


def onto_wall(main, props: dict, lat: float, lng: float) -> tuple:
    """A door, a downspout or a spigot (``on_wall``) onto the nearest
    building's wall (``src/wall_objects.py``): ``props`` gain its bearing and
    facing, and the map's marker is drawn again where it stands. Anything
    else, and a click far from every wall, stays where it was put."""
    from src import map_js, wall_objects
    sd = props.get("struct_def") or {}
    if not wall_objects.is_wall_object(sd):
        return lat, lng
    s_lat, s_lng = wall_objects.place(main._project, props, lat, lng)
    if (s_lat, s_lng) != (lat, lng) or props.get("bearing_deg"):
        sid = props.get("struct_id") or sd.get("id", "")
        main.map_widget.run_js(map_js.undo_structure_at(sid, lat, lng))
        main.map_widget.load_structure(dict(sd), s_lat, s_lng)
    return s_lat, s_lng


def on_structure_turned(main, marker_id: str, struct_id: str, lat: float,
                        lng: float, bearing_deg: float) -> None:
    """Store a turned object's bearing (V3.72), which the map, the planner's
    footprint and the 3D all read. One undo step."""
    feat = _find(main, struct_id, lat, lng)
    if feat is None or feat["properties"].get("element_type") != "structure":
        return
    with _checkpoint(main, "turn"):
        feat["properties"]["bearing_deg"] = round(float(bearing_deg) % 360.0,
                                                  1)
    main._mark_modified()


def turn_key(main) -> bool:
    """R on the map: the community being placed, else the object under the
    pointer (the page turns it and reports back)."""
    from src import community_turn
    if community_turn.turn_pending(main):
        return True
    main.map_widget.turn_hovered_object()
    return False


def on_existing_feature_foliage(main, marker_id: str, struct_id: str,
                                lat: float, lng: float, foliage: str) -> None:
    """Set a tree's foliage (conifer/deciduous) from the map's right-click
    switch — drives the 2D crown colour, 3D shape, and winter-shade weighting.
    Only trees carry foliage; a building mark is ignored."""
    if foliage not in ("evergreen", "deciduous"):
        return
    feat = _find(main, struct_id, lat, lng)
    if feat is None or feat["properties"].get("element_type") != "existing_tree":
        return
    with _checkpoint(main, "set tree foliage"):
        feat["properties"]["tree_foliage"] = foliage
    main._mark_modified()


def on_existing_feature_resized(main, marker_id: str, struct_id: str,
                                lat: float, lng: float,
                                new_diameter_m: float) -> None:
    """Write a scroll-resized existing feature's new crown size (diameter →
    ``canopy_radius_m``, the value shade + keep-out read) onto its feature."""
    feat = _find(main, struct_id, lat, lng)
    if feat is None:
        return
    radius = max(0.5, float(new_diameter_m) / 2.0)
    with _checkpoint(main, "resize existing feature"):
        props = feat["properties"]
        props["canopy_radius_m"] = radius
        props["size_m"] = float(new_diameter_m)
    main._mark_modified()
