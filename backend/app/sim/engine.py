"""Digital twin / scenario engine. A scenario is a timeline of signals, shelter check-ins and reports; `advance_to(t)`
releases every event up to simulated hour t through the same channels and agents a live deployment would use.
A background clock plays the timeline at a chosen speed; what-if events change the world at any moment."""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.channels import ingest
from app.core import geo, state
from app.db import Base
from app.models import Depot, InventoryItem, Road, Shelter, Signal, Zone
from app.services import hazard
from app.sim import kodagu_reports as KR
from app.sim import kodagu_world as KW
from app.sim.scenarios import SCENARIOS, reports_for
from app.ws.manager import emit


def timeline(scenario: str = "kodagu_flood") -> list[tuple]:
    """(t, kind, payload) sorted by time. kind: signal | checkin | report."""
    sc = SCENARIOS.get(scenario, SCENARIOS["kodagu_flood"])
    ev = [(t, "signal", (typ, zc, val, src)) for t, typ, zc, val, src in sc["signals"]]
    ev += [(r[0], "report", r) for r in reports_for(scenario)]
    ev += [(t, "checkin", (name, occ)) for t, name, occ in KW.CHECKINS]
    return sorted(ev, key=lambda e: (e[0], {"signal": 0, "checkin": 1}.get(e[1], 2)))


def _pass_time(db: Session, t: float) -> None:
    """Move the clock to t; shelters consume stock for the elapsed time."""
    from app.agents import resource
    dt = t - state.now(db)
    if dt > 0:
        resource.consume(db, dt)
        state.set_now(db, t)


def _release(db: Session, event: tuple) -> None:
    t, kind, payload = event
    _pass_time(db, t)
    if kind == "signal":
        typ, zc, val, src = payload
        z = db.scalar(select(Zone).where(Zone.code == zc)) if zc else None
        sig = Signal(type=typ, zone_id=z.id if z else None, value=val, source=src, observed_at=t)
        db.add(sig)
        db.flush()
        changes = hazard.apply_signal(db, sig)
        emit("signal", {"id": sig.id, "type": typ, "zone": zc, "value": val, "changes": changes, "t": t})
    elif kind == "checkin":
        name, occ = payload
        sh = db.scalar(select(Shelter).where(Shelter.name.like(f"{name}%")))
        if sh and sh.status not in ("inaccessible", "closed"):
            sh.last_confirmed_at, sh.occupancy = t, occ
            if sh.status == "unconfirmed":
                sh.status = "open"
            state.audit(db, f"{sh.name} manager", "shelter_checkin", f"{sh.name}: {occ}/{sh.capacity}", actor_type="human",
                        object_type="shelter", object_id=sh.id, push=False)
    else:
        _, channel, who, text = payload[:4]
        silenced = set(state.get(db, "silenced_zones", []))
        if silenced and payload[4]["zone"] in silenced and channel != "radio_entry":
            return  # a silenced village sends nothing (what-if event)
        ingest.from_timeline(db, channel=channel, who=who, text=text, received_at=t, media=KR.MEDIA.get(text))


def advance_to(db: Session, t: float) -> int:
    """Release every pending timeline event with time <= t, then move the clock to t and run a monitoring tick."""
    sc = state.get(db, "scenario", {}) or {}
    events = timeline(sc.get("id", "kodagu_flood"))
    cursor = int(state.get(db, "timeline_cursor", 0))
    n = 0
    while cursor < len(events) and events[cursor][0] <= t + 1e-9:
        _release(db, events[cursor])
        cursor += 1
        n += 1
        state.put(db, "timeline_cursor", cursor)
    _pass_time(db, t)
    from app.graph import pipeline
    pipeline.run(db, "tick")
    db.flush()
    emit("sim", {"clock": state.now(db), "released": n, "remaining": len(events) - cursor})
    return n


def reset_world(db: Session) -> None:
    """Empty every table and reload the static world (used to start a scenario from scratch)."""
    from app.sim.seed import load_world
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(delete(table))
    db.flush()
    load_world(db)
    from app.channels.sms import get_sms_provider
    outbox = getattr(get_sms_provider(), "outbox", None)
    if outbox is not None:
        outbox.clear()


def start_scenario(db: Session, scenario: str = "kodagu_flood", replay_until: float | None = 0.0, speed: float = 0.0,
                   fresh: bool = False) -> dict:
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario}")
    if fresh:
        reset_world(db)
    sc = SCENARIOS[scenario]
    state.put(db, "scenario", {"id": scenario, "name": sc["name"], "hazard": sc["hazard"], "running": speed > 0, "speed": speed})
    state.put(db, "timeline_cursor", 0)
    state.put(db, "flood_extent", [])
    state.put(db, "extra_flood", [])
    state.put(db, "silenced_zones", [])
    state.put(db, "handled_triggers", [])
    state.set_now(db, 0.0)
    n = advance_to(db, replay_until) if replay_until is not None else 0
    state.audit(db, "Simulation", "scenario_started", f"{sc['name']} (replayed to T+{state.now(db):.1f} h)", actor_type="system")
    emit("refresh", {"scenario": scenario})
    return {"scenario": scenario, "name": sc["name"], "released": n, "clock": state.now(db)}


def timeline_info(db: Session) -> dict:
    sc = state.get(db, "scenario", {}) or {}
    events = timeline(sc.get("id", "kodagu_flood"))
    cursor = int(state.get(db, "timeline_cursor", 0))
    return {"total": len(events), "released": cursor, "end_t": events[-1][0] if events else 0,
            "next": [{"t": e[0], "kind": e[1], "what": e[2][3][:80] if e[1] == "report" else str(e[2][0])} for e in events[cursor:cursor + 5]]}


# ---------------- what-if events ----------------
def what_if(db: Session, typ: str, p: dict) -> list[str]:
    from app.channels.adapters import ADAPTERS
    from app.channels.sms_flow import handle_inbound
    out = []
    now = state.now(db)
    if typ in ("close_road", "reopen_road"):
        r = db.scalar(select(Road).where(Road.code == p["road"]))
        if not r:
            raise ValueError("unknown road")
        r.status, r.status_source, r.updated_at = ("blocked", "what-if: closed by operator", now) if typ == "close_road" else ("open", "what-if: reopened", now)
        out.append(f"{r.name} {r.status}")
    elif typ == "flood_shelter":
        s = db.get(Shelter, int(p["shelter_id"]))
        polys = list(state.get(db, "extra_flood", []))
        for code in s.access_road_ids:
            r = db.scalar(select(Road).where(Road.code == code))
            pt = geo.lerp_point(r.points[0], r.points[-1], 0.3)
            polys.append(geo.circle(pt[0], pt[1], 2500))
        polys.append(geo.circle(s.lat, s.lng, 600))
        state.put(db, "extra_flood", polys)
        roads = hazard.apply_flood_to_roads(db, "what-if: flood over shelter access")
        out.append(f"flood covers {s.name} and its access roads ({', '.join(roads) or 'no road change'})")
    elif typ == "drop_inventory":
        d = db.get(Depot, int(p["depot_id"]))
        frac = float(p.get("fraction", 0.5))
        for i in db.scalars(select(InventoryItem).where(InventoryItem.location_type == "depot", InventoryItem.location_id == d.id)):
            if not p.get("resource_type") or i.resource_type == p["resource_type"]:
                i.quantity = round(i.quantity * (1 - frac))
        out.append(f"{d.name}: stock dropped by {int(frac * 100)}%")
    elif typ in ("cut_internet", "restore_internet"):
        z = db.scalar(select(Zone).where(Zone.code == p["zone"]))
        z.internet_down = typ == "cut_internet"
        emit("network", {"zone": z.code, "name": z.name, "internet_down": z.internet_down})
        out.append(f"internet {'DOWN' if z.internet_down else 'restored'} in {z.name}")
    elif typ == "spike_reports":
        n = int(p.get("count", 6))
        names = ["citizen_sms", "regional_social", "news", "field_team"]
        for k in range(n):
            a = ADAPTERS[names[k % len(names)]]
            for it in a.pull(1):
                if a.channel == "sms":
                    handle_inbound(db, it.who, it.text)
                else:
                    ingest.submit(db, channel=a.channel, source=ingest.resolve_source(db, it.who, a.channel), text=it.text, adapter=a.name)
        out.append(f"{n} extra reports injected")
    elif typ == "silence_village":
        z = db.scalar(select(Zone).where(Zone.code == p["zone"]))
        z.tower_status, z.power_status = "down", "off"
        z.last_report_at = min(z.last_report_at if z.last_report_at is not None else now, now - 8)
        state.put(db, "silenced_zones", sorted(set(state.get(db, "silenced_zones", [])) | {z.code}))
        if p.get("with_hazard", True):
            state.put(db, "extra_flood", [*state.get(db, "extra_flood", []), geo.circle(z.lat, z.lng, 1800)])
        out.append(f"{z.name} silenced: towers down, power off, no reports")
    else:
        raise ValueError(f"unknown what-if event {typ}")
    state.audit(db, "Simulation", f"whatif_{typ}", "; ".join(out), actor_type="system", inputs=p)
    from app.graph import pipeline
    res = pipeline.run(db, "scenario_event")
    db.flush()
    emit("sim", {"clock": now, "event": typ, "changes": out})
    return out + ([f"new plan proposed (plan id {res['plan_id']})"] if res.get("plan_id") else [])
