"""World and records: zones, roads, depots, shelters, inventory, sources, reports, incidents, signals, alerts, audit."""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.common import get_or_404, row, rows
from app.core import state
from app.db import get_db
from app.models import (Alert, AuditLog, Depot, Gazetteer, Incident, InventoryItem, Report, Road, Shelter, Signal, Source,
                        Zone)
from app.services import hazard
from app.ws.manager import emit

router = APIRouter(prefix="/api", tags=["world"])


@router.get("/state")
def sim_state(db: Session = Depends(get_db)):
    return {"clock": state.now(db), "scenario": state.get(db, "scenario"), "flood_extent": hazard.flood_polygons(db),
            "flood_version": state.get(db, "flood_version"), "network_down": [z.code for z in db.scalars(select(Zone).where(Zone.internet_down))]}


@router.get("/zones")
def zones(db: Session = Depends(get_db)):
    return rows(db.scalars(select(Zone).order_by(Zone.id)))


@router.get("/roads")
def roads(db: Session = Depends(get_db)):
    return rows(db.scalars(select(Road).order_by(Road.id)))


@router.get("/gazetteer")
def gazetteer(db: Session = Depends(get_db)):
    return rows(db.scalars(select(Gazetteer).order_by(Gazetteer.id)))


@router.get("/depots")
def depots(db: Session = Depends(get_db)):
    out = []
    for d in db.scalars(select(Depot).order_by(Depot.id)):
        items = db.scalars(select(InventoryItem).where(InventoryItem.location_type == "depot", InventoryItem.location_id == d.id))
        out.append({**row(d), "inventory": rows(items)})
    return out


@router.get("/shelters")
def shelters(db: Session = Depends(get_db)):
    out = []
    for s in db.scalars(select(Shelter).order_by(Shelter.id)):
        items = db.scalars(select(InventoryItem).where(InventoryItem.location_type == "shelter", InventoryItem.location_id == s.id))
        out.append({**row(s), "inventory": rows(items)})
    return out


class ShelterPatch(BaseModel):
    occupancy: int | None = Field(None, ge=0)
    capacity: int | None = Field(None, ge=0)
    status: str | None = Field(None, pattern="^(open|full|inaccessible|unconfirmed|closed)$")
    status_reason: str | None = None


@router.patch("/shelters/{sid}")
def patch_shelter(sid: int, body: ShelterPatch, db: Session = Depends(get_db)):
    s = get_or_404(db, Shelter, sid)
    changes = body.model_dump(exclude_none=True)
    for k, v in changes.items():
        setattr(s, k, v)
    state.audit(db, "Duty officer", "shelter_updated", f"{s.name}: {changes}", actor_type="human", object_type="shelter", object_id=s.id, inputs=changes)
    db.commit()
    emit("shelter", row(s))
    return row(s)


@router.get("/inventory")
def inventory(location_type: str | None = None, db: Session = Depends(get_db)):
    q = select(InventoryItem).order_by(InventoryItem.location_type, InventoryItem.location_id, InventoryItem.resource_type)
    if location_type:
        q = q.where(InventoryItem.location_type == location_type)
    now = state.now(db)
    return [{**row(i), "stale": (now - i.last_updated_at) > 12} for i in db.scalars(q)]


class InventoryPatch(BaseModel):
    quantity: float = Field(ge=0)
    note: str | None = None


@router.patch("/inventory/{iid}")
def patch_inventory(iid: int, body: InventoryPatch, db: Session = Depends(get_db)):
    i = get_or_404(db, InventoryItem, iid)
    before = i.quantity
    i.quantity, i.last_updated_at = body.quantity, state.now(db)
    state.audit(db, "Duty officer", "stock_counted", f"{i.resource_type} at {i.location_type} {i.location_id}: {before} -> {body.quantity}",
                actor_type="human", object_type="inventory", object_id=i.id, inputs={"before": before, "after": body.quantity, "note": body.note})
    db.commit()
    emit("inventory", row(i))
    return row(i)


@router.get("/sources")
def sources(db: Session = Depends(get_db)):
    return rows(db.scalars(select(Source).order_by(Source.id)))


@router.get("/reports")
def reports(limit: int = Query(200, le=1000), incident_id: int | None = None, channel: str | None = None,
            language: str | None = None, db: Session = Depends(get_db)):
    q = select(Report).order_by(Report.received_at.desc(), Report.id.desc()).limit(limit)
    if incident_id:
        q = q.where(Report.incident_id == incident_id)
    if channel:
        q = q.where(Report.channel == channel)
    if language:
        q = q.where(Report.original_language == language)
    srcs = {s.id: s for s in db.scalars(select(Source))}
    out = []
    for r in db.scalars(q):
        s = srcs.get(r.source_id)
        out.append({**row(r), "source": {"type": s.type, "name": s.name, "phone_masked": s.phone_masked, "reliability": s.reliability_score} if s else None})
    return out


@router.get("/reports/{rid}")
def report(rid: int, db: Session = Depends(get_db)):
    r = get_or_404(db, Report, rid)
    s = db.get(Source, r.source_id) if r.source_id else None
    return {**row(r), "source": row(s) if s else None}


@router.get("/incidents")
def incidents(db: Session = Depends(get_db)):
    return rows(db.scalars(select(Incident).order_by(Incident.priority_score.desc(), Incident.id)))


@router.get("/signals")
def signals(type: str | None = None, db: Session = Depends(get_db)):
    q = select(Signal).order_by(Signal.observed_at.desc())
    if type:
        q = q.where(Signal.type == type)
    return rows(db.scalars(q))


@router.get("/alerts")
def alerts(open_only: bool = False, db: Session = Depends(get_db)):
    q = select(Alert).order_by(Alert.resolved, Alert.id.desc())
    if open_only:
        q = q.where(Alert.resolved.is_(False))
    return rows(db.scalars(q))


@router.post("/alerts/{aid}/ack")
def ack_alert(aid: int, db: Session = Depends(get_db)):
    a = get_or_404(db, Alert, aid)
    a.acknowledged = True
    state.audit(db, "Duty officer", "alert_acknowledged", a.message, actor_type="human", object_type="alert", object_id=a.id)
    db.commit()
    emit("alert", row(a))
    return row(a)


@router.get("/audit")
def audit(actor_type: str | None = None, action: str | None = None, limit: int = Query(300, le=2000), db: Session = Depends(get_db)):
    q = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    if actor_type:
        q = q.where(AuditLog.actor_type == actor_type)
    if action:
        q = q.where(AuditLog.action == action)
    return rows(db.scalars(q))


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    """Headline numbers for the ticker and the landing page."""
    from sqlalchemy import func
    from app.models import Dispatch, Plan
    reports = db.scalars(select(Report)).all()
    incs = db.scalars(select(Incident)).all()
    levels: dict[str, int] = {}
    for i in incs:
        levels[i.confidence_level] = levels.get(i.confidence_level, 0) + 1
    return {
        "clock": state.now(db),
        "reports": len(reports),
        "languages": len({r.original_language for r in reports if r.original_language}),
        "offline_channel_reports": sum(1 for r in reports if r.channel in ("sms", "voice", "radio_entry")),
        "blocked_reports": sum(1 for r in reports if r.status == "blocked"),
        "incidents": len(incs),
        "levels": levels,
        "fast_verify": sum(1 for i in incs if i.fast_verify),
        "people_affected": sum(i.people_affected for i in incs if i.confidence_level not in ("false",)),
        "alerts_open": db.scalar(select(func.count()).select_from(Alert).where(Alert.resolved.is_(False))),
        "plans_pending": db.scalar(select(func.count()).select_from(Plan).where(Plan.status == "pending_approval")),
        "dispatches_active": db.scalar(select(func.count()).select_from(Dispatch).where(Dispatch.status.in_(["dispatched", "in_transit", "delivered"]))),
        "zones_down": [z.name for z in db.scalars(select(Zone).where(Zone.internet_down))],
        "blackout_zones": [z.name for z in db.scalars(select(Zone).where(Zone.blackout_flag))],
    }
