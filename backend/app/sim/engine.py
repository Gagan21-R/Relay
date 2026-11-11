"""Digital twin / scenario engine. A scenario is a timeline of signals and reports; `advance_to(t)` releases every
event up to simulated hour t through the same channels and agents a live deployment would use."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.channels import ingest
from app.core import state
from app.models import Signal, Zone
from app.services import hazard
from app.sim import kodagu_reports as KR
from app.sim import kodagu_world as KW
from app.ws.manager import emit


def timeline(scenario: str = "kodagu_flood") -> list[tuple]:
    """(t, kind, payload) sorted by time. kind: signal | report."""
    ev = [(t, "signal", (typ, zc, val, src)) for t, typ, zc, val, src in KW.SIGNALS]
    ev += [(r[0], "report", r) for r in KR.REPORTS]
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
        from app.models import Shelter
        name, occ = payload
        sh = db.scalar(select(Shelter).where(Shelter.name.like(f"{name}%")))
        if sh:
            sh.last_confirmed_at, sh.occupancy = t, occ
            if sh.status == "unconfirmed":
                sh.status = "open"
            state.audit(db, f"{sh.name} manager", "shelter_checkin", f"{sh.name}: {occ}/{sh.capacity}", actor_type="human",
                        object_type="shelter", object_id=sh.id, push=False)
    else:
        _, channel, who, text = payload[:4]
        media = KR.MEDIA.get(text)
        ingest.from_timeline(db, channel=channel, who=who, text=text, received_at=t, media=media)


def advance_to(db: Session, t: float) -> int:
    """Release every pending timeline event with time <= t, then move the clock to t. Returns events released."""
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
    emit("sim", {"clock": state.now(db), "released": n})
    return n


def start_scenario(db: Session, scenario: str = "kodagu_flood", replay_until: float | None = 0.0) -> dict:
    state.put(db, "scenario", {"id": scenario, "name": "Kodagu monsoon flood", "running": False, "speed": 0})
    state.put(db, "timeline_cursor", 0)
    state.set_now(db, 0.0)
    state.put(db, "flood_extent", [])
    n = advance_to(db, replay_until) if replay_until is not None else 0
    return {"scenario": scenario, "released": n, "clock": state.now(db)}
