"""Triage Agent — "Who needs help first?"
Priority out of 100 = life threat + people + vulnerable groups + waiting time + confidence + access difficulty, each
with its points and reason stored in priority_breakdown. Unverified life-safety incidents keep a real share of the
confidence points: they are checked fast, never pushed to the bottom."""
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.common import row
from app.core import geo, state
from app.models import Incident, Road, Zone
from app.services import hazard
from app.services import scoring as S
from app.ws.manager import emit

CONF_FACTOR = {"verified": 1.0, "likely": 0.8, "unverified": 0.5, "disputed": 0.2, "false": 0.0}


def access_difficulty(db: Session, inc: Incident) -> tuple[float, str]:
    z = db.get(Zone, inc.zone_id) if inc.zone_id else None
    if not z:
        return 0.5, "location unknown: assume hard to reach"
    roads = db.scalars(select(Road).where((Road.a == z.code) | (Road.b == z.code))).all()
    closed = [r for r in roads if r.status != "open"]
    if roads and len(closed) == len(roads):
        return 1.0, f"every road into {z.name} is closed"
    if closed:
        return 0.7, f"{len(closed)} of {len(roads)} roads into {z.name} closed"
    if inc.lat is not None and geo.in_any(inc.lat, inc.lng, hazard.flood_polygons(db)):
        return 0.6, "inside the flood extent: boats or detours likely"
    if z.tower_status != "up":
        return 0.5, "mobile towers down: hard to coordinate on site"
    return 0.2, "roads open"


def prioritise(db: Session, inc: Incident) -> Incident:
    W = S.PRIORITY_WEIGHTS
    if inc.confidence_level == "false" or inc.status == "resolved":
        inc.priority_score = 0.0
        inc.priority_breakdown = {"components": {}, "total": 0.0, "note": "false or resolved: no priority"}
        return inc
    now = state.now(db)
    from app.disasters import profile
    lt = profile(state.disaster(db))["life_threat"].get(inc.category, S.LIFE_THREAT_BY_CATEGORY.get(inc.category, 0.1))
    if inc.life_safety:
        lt = max(lt, 0.9)
    people = inc.people_affected or 0
    pv = min(1.0, math.log10(people + 1) / math.log10(500)) if people else 0.15
    vul = min(1.0, 0.35 * len(inc.vulnerable_groups or []))
    wait = max(0.0, now - inc.first_report_at) if inc.status == "open" else 0.0
    wv = min(1.0, wait / 6.0)
    cf = CONF_FACTOR.get(inc.confidence_level, 0.5)
    if inc.life_safety and inc.confidence_level == "unverified":
        cf = 0.6
    ad, adwhy = access_difficulty(db, inc)
    comp = {
        "life_threat": (lt, f"{inc.category} in a {state.disaster(db)}{' with a life-safety signal' if inc.life_safety else ''}"),
        "people": (pv, f"{people} people (log scale, 500 = full)" if people else "people count unknown"),
        "vulnerable": (vul, ", ".join(inc.vulnerable_groups or []) or "none reported"),
        "waiting_time": (wv, f"waiting {wait:.1f} h since first report" if inc.status == "open" else f"status {inc.status}"),
        "confidence": (cf, f"{inc.confidence_level}" + (" (life-safety keeps weight)" if inc.life_safety and inc.confidence_level == "unverified" else "")),
        "access_difficulty": (ad, adwhy),
    }
    total = sum(W[k] * v for k, (v, _) in comp.items())
    inc.priority_score = round(total, 1)
    inc.priority_breakdown = {"components": {k: {"value": round(v, 2), "weight": W[k], "points": round(W[k] * v, 1), "why": why}
                                             for k, (v, why) in comp.items()}, "total": round(total, 1)}
    return inc


def run(db: Session, st: dict) -> dict:
    ids = st.get("incident_ids") or []
    incs = [db.get(Incident, i) for i in ids] if ids else db.scalars(select(Incident).where(Incident.status != "resolved")).all()
    for inc in incs:
        if inc is None:
            continue
        prioritise(db, inc)
        emit("incident", row(inc))
    db.flush()
    ranked = db.scalars(select(Incident).where(Incident.status != "resolved").order_by(Incident.priority_score.desc()).limit(3)).all()
    if ids:
        from app.agents import bus
        changed = [db.get(Incident, i) for i in ids if db.get(Incident, i)]
        bus.send(db, "triage", "monitor", "inform", "priorities",
                 "Re-ranked " + ", ".join(f"#{i.id} {i.title} → {i.priority_score:.0f}/100" for i in changed[:3])
                 + ". Top now: " + "; ".join(f"#{i.id} {i.priority_score:.0f}" for i in ranked) + ". Watch for anything that needs a plan.",
                 {"incident_ids": [i.id for i in changed], "top": [i.id for i in ranked]}, conversation=f"priorities:{state.now(db):.2f}")
    return {"summary": "top: " + "; ".join(f"#{i.id} {i.priority_score:.0f}" for i in ranked)}
