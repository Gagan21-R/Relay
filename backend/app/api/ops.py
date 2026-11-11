"""Operations APIs added in the enhancement round: hospitals, volunteers, road observations and verification,
route planning, outgoing public communications, and language coverage."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.common import get_or_404, row, rows
from app.core.roles import Actor, current_actor, require_officer
from app.db import get_db
from app.graph import pipeline
from app.i18n.languages import LANGUAGES
from app.i18n.public_templates import PUBLIC
from app.models import Communication, Hospital, Road, RoadReport, Volunteer, Zone
from app.services import comms, routing, volunteers

router = APIRouter(prefix="/api", tags=["operations"])


@router.get("/hospitals")
def hospitals(db: Session = Depends(get_db)):
    return rows(db.scalars(select(Hospital)))


@router.get("/volunteers")
def volunteer_list(db: Session = Depends(get_db)):
    busy = volunteers.busy_ids(db)
    return [{**row(v), "reliability": volunteers.reliability(v), "busy": v.id in busy,
             "reliability_formula": f"({v.on_time_confirmations}+1)/({v.assigned_tasks}+2)"} for v in db.scalars(select(Volunteer).order_by(Volunteer.code))]


class Rank(BaseModel):
    need: str = "rescue"
    lat: float
    lng: float
    vehicle: str | None = None


@router.post("/volunteers/rank")
def rank(body: Rank, db: Session = Depends(get_db)):
    return volunteers.rank(db, body.need, body.lat, body.lng, body.vehicle)


class Availability(BaseModel):
    available: bool


@router.patch("/volunteers/{code}")
def set_availability(code: str, body: Availability, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    v = db.scalar(select(Volunteer).where(Volunteer.code == code))
    if not v:
        raise HTTPException(404, "unknown volunteer")
    if not (actor.is_officer or (actor.role == "volunteer" and actor.name == code)):
        raise HTTPException(403, "only a Duty Officer or the volunteer themself can change availability")
    v.available = body.available
    db.commit()
    return row(v)


# ---------------- roads ----------------
@router.get("/roads/conditions")
def road_conditions(db: Session = Depends(get_db)):
    return [{**routing.road_condition(db, r), "points": r.points} for r in db.scalars(select(Road))]


@router.get("/road-reports")
def road_reports(db: Session = Depends(get_db)):
    out = []
    for rr in db.scalars(select(RoadReport).order_by(RoadReport.id.desc()).limit(200)):
        r = db.get(Road, rr.road_id)
        out.append({**row(rr), "road": r.code if r else None, "road_name": r.name if r else None})
    return out


class RoadObs(BaseModel):
    status: str = Field(pattern="^(open|flooded|blocked|damaged)$")
    source: str = Field(min_length=2)
    source_type: str = Field("citizen", pattern="^(official|sensor|field_team|volunteer|citizen|social|satellite|operator)$")
    note: str | None = None


@router.post("/roads/{code}/report")
def report_road(code: str, body: RoadObs, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    """Any channel can report a road; closures apply at once (caution), unverified 'open' never reopens a road."""
    r = db.scalar(select(Road).where(Road.code == code))
    if not r:
        raise HTTPException(404, "unknown road")
    if body.source_type in ("official", "operator") and not actor.is_officer:
        raise HTTPException(403, "only a Duty Officer can file an official/operator road status")
    rr = routing.report_road(db, r, body.status, body.source, body.source_type, note=body.note)
    res = pipeline.run(db, "road_report")
    db.commit()
    return {"report": row(rr), "road": routing.road_condition(db, r), "plan_id": res.get("plan_id")}


class Verify(BaseModel):
    confirmed: bool


@router.post("/road-reports/{rid}/verify")
def verify_road_report(rid: int, body: Verify, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    require_officer(actor, "verify a road report")
    rr = get_or_404(db, RoadReport, rid)
    r = db.get(Road, rr.road_id)
    routing.verify_report(db, rr, actor.name, body.confirmed)
    res = pipeline.run(db, "road_verified")
    db.commit()
    return {"road": routing.road_condition(db, r), "plan_id": res.get("plan_id")}


@router.get("/routes")
def route(from_zone: str, to_zone: str, vehicle: str | None = None, db: Session = Depends(get_db)):
    r = routing.plan_route(db, from_zone, to_zone, [vehicle] if vehicle else None)
    if not r:
        raise HTTPException(404, f"no usable route from {from_zone} to {to_zone}" + (f" for a {vehicle}" if vehicle else ""))
    return r


# ---------------- outgoing communication ----------------
@router.get("/communications/templates")
def templates():
    return {"templates": {k: {"fields": v["fields"], "english": v["en"], "languages": sorted(l for l in v if l != "fields")}
                          for k, v in PUBLIC.items()},
            "languages": [{"code": k, "name": v["name"], "support": v.get("support"), "templates": v.get("templates")} for k, v in LANGUAGES.items()],
            "note": "Regional templates are machine-drafted and not validated by native speakers. Languages without one receive English."}


@router.get("/communications")
def communications(db: Session = Depends(get_db)):
    out = []
    for c in db.scalars(select(Communication).order_by(Communication.id.desc()).limit(200)):
        z = db.get(Zone, c.zone_id) if c.zone_id else None
        out.append({**row(c), "zone": z.name if z else "all areas", "language_name": LANGUAGES.get(c.language, {}).get("name", c.language)})
    return out


class Draft(BaseModel):
    template_id: str
    facts: dict[str, str]
    zone_id: int | None = None
    languages: list[str] | None = None


@router.post("/communications/draft")
def draft(body: Draft, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    require_officer(actor, "draft a public message")
    try:
        cs = comms.draft(db, body.template_id, body.facts, body.zone_id, body.languages, actor.name)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    db.commit()
    return rows(cs)


def _act(db: Session, cid: int, actor: Actor, fn, what: str):
    require_officer(actor, what)
    c = get_or_404(db, Communication, cid)
    try:
        fn(db, c, actor.name)
    except ValueError as e:
        raise HTTPException(409, str(e)) from e
    db.commit()
    return row(c)


@router.post("/communications/{cid}/approve")
def approve_comm(cid: int, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    return _act(db, cid, actor, comms.approve, "approve a public message")


@router.post("/communications/{cid}/reject")
def reject_comm(cid: int, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    return _act(db, cid, actor, comms.reject, "reject a public message")


@router.post("/communications/{cid}/send")
def send_comm(cid: int, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    return _act(db, cid, actor, comms.send, "send a public message")


# ---------------- agent conversations ----------------
@router.get("/agents/messages")
def agent_messages(limit: int = 300, agent: str | None = None, topic: str | None = None, conversation: str | None = None,
                   db: Session = Depends(get_db)):
    """Messages between agents (newest first). Filter by agent (sender or recipient), topic or conversation."""
    from app.agents.bus import _row
    from app.models import AgentMessage
    q = select(AgentMessage).order_by(AgentMessage.id.desc())
    if agent:
        q = q.where((AgentMessage.sender == agent) | (AgentMessage.recipient == agent))
    if topic:
        q = q.where(AgentMessage.topic == topic)
    if conversation:
        q = q.where(AgentMessage.conversation == conversation)
    return [_row(m) for m in db.scalars(q.limit(min(limit, 2000)))]


@router.get("/agents/summary")
def agent_summary(db: Session = Depends(get_db)):
    """Who talks to whom, how often, about what — the edges of the live agent network."""
    from collections import Counter

    from app.models import AgentMessage
    edges = Counter((m.sender, m.recipient, m.topic) for m in db.scalars(select(AgentMessage)))
    return {"edges": [{"from": a, "to": b, "topic": t, "count": n} for (a, b, t), n in edges.most_common()],
            "total": sum(edges.values())}
