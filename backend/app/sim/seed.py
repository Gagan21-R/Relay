"""Seed the Kodagu scenario. `python -m app.sim.seed --reset` drops everything and rebuilds.

The static world (zones, gazetteer, roads, depots, shelters, stock, sources) is loaded first; then the 12-hour timeline
(signals and the ~80 reports) is replayed through the real pipeline by the scenario engine, so the seeded state is
exactly what RELAY would have produced live."""
import argparse
import math

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import state
from app.core.privacy import hash_phone, mask_phone
from app.db import Base, SessionLocal, engine
from app.models import Depot, Gazetteer, InventoryItem, Road, Shelter, Source, Zone
from app.models import tables as T
from app.sim import worlds
from app.ws.manager import mute

TIER_RELIABILITY = {"official_agency": 0.95, "sensor": 0.9, "field_team": 0.85, "ngo": 0.75, "volunteer": 0.7,
                    "citizen": 0.5, "social": 0.35, "anonymous": 0.3}


def _square(lat: float, lng: float, half_deg: float) -> list:
    """Rough zone boundary (an octagon) around the town centre; display and blackout geometry only."""
    k = half_deg
    return [[round(lat + k * math.sin(a), 4), round(lng + k * 1.03 * math.cos(a), 4)] for a in [i * math.pi / 4 for i in range(8)]]


def load_world(db: Session, spec: dict | None = None) -> None:
    """Load a world spec (default Kodagu) into empty tables."""
    from app.disasters import UNITS
    from app.models import Hospital, Volunteer
    W = spec or worlds.kodagu()
    zones = {}
    for code, name, lat, lng, pop, rate, vul, aliases in W["zones"]:
        z = Zone(code=code, name=name, lat=lat, lng=lng, population=pop, normal_reports_per_hour=rate, vulnerability=vul,
                 polygon=_square(lat, lng, 0.03 if pop > 10000 else 0.022))
        db.add(z)
        db.flush()
        zones[code] = z
        db.add(Gazetteer(canonical=name, kind="town" if pop > 8000 else "village", zone_id=z.id, lat=lat, lng=lng, aliases=aliases))
    for name, zc, lat, lng, aliases in W["landmarks"]:
        db.add(Gazetteer(canonical=name, kind="landmark", zone_id=zones[zc].id, lat=lat, lng=lng, aliases=aliases))
    for code, name, a, b, attrs in W["roads"]:
        za, zb = zones[a], zones[b]
        mid = attrs.get("mid") or [(za.lat + zb.lat) / 2, (za.lng + zb.lng) / 2]
        db.add(Road(code=code, name=name, a=a, b=b, points=[[za.lat, za.lng], mid, [zb.lat, zb.lng]],
                    **{k: v for k, v in attrs.items() if k in ("kind", "surface", "allowed_vehicles")}))
    for name, owner, zc, lat, lng, stock, counted_at in W["depots"]:
        d = Depot(name=name, owner=owner, zone_id=zones[zc].id, lat=lat, lng=lng)
        db.add(d)
        db.flush()
        db.add(Gazetteer(canonical=name, kind="depot", zone_id=zones[zc].id, lat=lat, lng=lng, aliases=[name.lower()]))
        for rt, q in stock.items():
            db.add(InventoryItem(location_type="depot", location_id=d.id, resource_type=rt, quantity=q, unit=UNITS.get(rt, ""), last_updated_at=counted_at))
    keys = {}
    for key, typ, name, phone, lang in W["sources"]:
        s = Source(type=typ, name=name, preferred_language=lang, reliability_score=TIER_RELIABILITY[typ],
                   phone_hash=hash_phone(phone) if phone else None, phone_masked=mask_phone(phone) if phone else None)
        db.add(s)
        db.flush()
        keys[key] = s.id
    mgr_for = {zc: keys.get(k) for zc, k in W.get("managers", {}).items()}
    for name, zc, lat, lng, cap, occ, roads, stock in W["shelters"]:
        sh = Shelter(name=name, zone_id=zones[zc].id, lat=lat, lng=lng, capacity=cap, occupancy=occ, access_road_ids=roads,
                     manager_source_id=mgr_for.get(zc), last_confirmed_at=0.0)
        db.add(sh)
        db.flush()
        db.add(Gazetteer(canonical=name, kind="shelter", zone_id=zones[zc].id, lat=lat, lng=lng, aliases=[name.lower()]))
        for rt, q in stock.items():
            db.add(InventoryItem(location_type="shelter", location_id=sh.id, resource_type=rt, quantity=q, unit=UNITS.get(rt, ""), last_updated_at=0.0))
    for name, zc, lat, lng, beds in W.get("hospitals", []):
        db.add(Hospital(name=name, zone_id=zones[zc].id, lat=lat, lng=lng, beds=beds))
        db.add(Gazetteer(canonical=name, kind="hospital", zone_id=zones[zc].id, lat=lat, lng=lng, aliases=[name.lower()]))
    for code, name, zc, skills, vehicle, langs, (assigned, on_time) in W.get("volunteers", []):
        z = zones[zc]
        db.add(Volunteer(code=code, name=f"{name} (synthetic)", zone_id=z.id, lat=z.lat + 0.004, lng=z.lng + 0.004, skills=skills,
                         vehicle=vehicle, languages=langs, assigned_tasks=assigned, on_time_confirmations=on_time,
                         phone_masked=f"+91 98xxxx{code[-3:]}"))
    state.set_now(db, 0.0)
    state.put(db, "source_keys", keys)
    state.put(db, "world", {k: W[k] for k in ("id", "name", "state", "center", "zoom")} | {"languages": W.get("languages", ["en"])})
    state.put(db, "scenario", {"id": "kodagu_flood", "name": "Kodagu monsoon flood", "running": False, "speed": 0})
    db.flush()


def reset_schema() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def seed(reset: bool = False, replay_until: float | None = 12.0, scenario: str = "kodagu_flood") -> dict:
    """Build the world and replay the scenario timeline up to `replay_until` hours (None = world only)."""
    if reset:
        reset_schema()
    else:
        Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Zone)):
            return counts(db)
        mute(True)
        try:
            load_world(db)
            db.commit()
            from app.sim import engine as sim_engine          # the engine needs the pipeline; imported late
            sim_engine.start_scenario(db, scenario, replay_until=replay_until)
            db.commit()
        finally:
            mute(False)
        return counts(db)


def counts(db: Session) -> dict:
    out = {}
    for name in ("Source", "Zone", "Gazetteer", "Road", "Depot", "Shelter", "InventoryItem", "Report", "Incident", "Signal",
                 "Plan", "Dispatch", "Alert", "ReconTask", "SmsMessage", "AuditLog"):
        out[getattr(T, name).__tablename__] = db.scalar(select(func.count()).select_from(getattr(T, name)))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Seed the RELAY Kodagu scenario")
    ap.add_argument("--reset", action="store_true", help="drop all tables first")
    ap.add_argument("--until", type=float, default=12.0, help="replay the timeline up to this many hours")
    a = ap.parse_args()
    for table, n in seed(reset=a.reset, replay_until=a.until).items():
        print(f"{table:16s} {n}")
