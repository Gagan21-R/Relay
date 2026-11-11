"""Hazard state from signals: the current flood extent, which roads it cuts, river and rainfall status per zone."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import geo, state
from app.models import Road, Signal, Zone


def flood_polygons(db: Session) -> list:
    """Satellite extent (latest version) plus any polygons added by what-if events."""
    return list(state.get(db, "flood_extent", [])) + list(state.get(db, "extra_flood", []))


def apply_flood_to_roads(db: Session, source: str) -> list[str]:
    """Mark roads whose interior is under water as flooded (field 'blocked' reports are left alone). Returns changed codes."""
    polys = flood_polygons(db)
    changed = []
    for r in db.scalars(select(Road)):
        under = any(geo.in_any(p[0], p[1], polys) for p in geo.road_samples(r.points))
        if under and r.status == "open":
            r.status, r.status_source, r.updated_at = "flooded", source, state.now(db)
            changed.append(r.code)
        elif not under and r.status == "flooded":
            r.status, r.status_source, r.updated_at = "open", source, state.now(db)
            changed.append(r.code)
    db.flush()
    return changed


def zone_hazard(db: Session, zone: Zone) -> dict:
    """What the sensors say about one zone: inside the flood extent, river above danger, rainfall category."""
    polys = flood_polygons(db)
    inside = geo.in_any(zone.lat, zone.lng, polys) or any(geo.in_any(p[0], p[1], polys) for p in zone.polygon)
    river = db.scalars(select(Signal).where(Signal.type == "river", Signal.zone_id == zone.id).order_by(Signal.observed_at.desc())).first()
    rain = db.scalars(select(Signal).where(Signal.type == "rainfall", Signal.zone_id == zone.id).order_by(Signal.observed_at.desc())).first()
    quake = db.scalars(select(Signal).where(Signal.type == "quake").order_by(Signal.observed_at.desc())).first()
    above = bool(river and river.value.get("level_m", 0) >= river.value.get("danger_m", 99))
    return {
        "in_flood_extent": inside,
        "river_above_danger": above,
        "river": river.value if river else None,
        "rain_mm_24h": rain.value.get("mm_24h") if rain else None,
        "heavy_rain": bool(rain and rain.value.get("mm_24h", 0) >= 115),
        "quake_mag": quake.value.get("magnitude") if quake else None,
    }


def apply_signal(db: Session, sig: Signal) -> list[str]:
    """Side effects of a newly arrived signal on the world. Returns a list of plain-language changes."""
    out = []
    z = db.get(Zone, sig.zone_id) if sig.zone_id else None
    if sig.type == "flood_extent":
        state.put(db, "flood_extent", sig.value.get("polygons", []))
        state.put(db, "flood_version", sig.value.get("version"))
        roads = apply_flood_to_roads(db, f"satellite flood extent v{sig.value.get('version')}")
        out.append(f"Flood extent v{sig.value.get('version')} received; roads now flooded: {', '.join(roads) or 'none new'}")
    elif sig.type == "tower_outage" and z:
        z.tower_status = "down" if sig.value.get("towers_down", 0) >= max(1, sig.value.get("towers_total", 1)) else "partial"
        out.append(f"{z.name}: {sig.value.get('towers_down')}/{sig.value.get('towers_total')} mobile towers down")
    elif sig.type == "power_outage" and z:
        z.power_status = "off"
        out.append(f"{z.name}: power off")
    elif sig.type == "river" and z:
        v = sig.value
        out.append(f"{v.get('station')}: {v.get('level_m')} m (danger {v.get('danger_m')} m)")
    elif sig.type == "rainfall" and z:
        out.append(f"{z.name}: {sig.value.get('mm_24h')} mm rain in 24 h")
    elif sig.type == "dam":
        out.append(f"{sig.value.get('dam')} dam bulletin: {sig.value.get('bulletin')}")
    elif sig.type == "quake":
        out.append(f"Earthquake M{sig.value.get('magnitude')} at {sig.value.get('place')}")
    db.flush()
    return out
