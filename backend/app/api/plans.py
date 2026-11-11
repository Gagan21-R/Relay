"""Plans & approvals, and the task lifecycle: created -> approved -> assigned -> dispatched -> delivered -> confirmed.
Every action names its actor (X-Role / X-Actor headers); the coordination agent enforces who may do what
(403 Forbidden) and which transitions are valid (409 Conflict)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import coordination
from app.api.common import get_or_404, row, rows
from app.core.roles import Actor, current_actor
from app.db import get_db
from app.graph import pipeline
from app.models import Approval, Dispatch, Plan, Volunteer
from app.services import volunteers

router = APIRouter(prefix="/api", tags=["plans & tasks"])
HIDE = {"confirmation_phone_hash"}


def _d(db: Session, d: Dispatch) -> dict:
    v = db.get(Volunteer, d.volunteer_id) if d.volunteer_id else None
    return {**row(d, HIDE), "volunteer": {"code": v.code, "name": v.name, "reliability": volunteers.reliability(v)} if v else None}


@router.get("/plans")
def plans(db: Session = Depends(get_db)):
    out = []
    for p in db.scalars(select(Plan).order_by(Plan.version.desc())):
        out.append({**row(p), "approvals": rows(db.scalars(select(Approval).where(Approval.plan_id == p.id)))})
    return out


class NewPlan(BaseModel):
    reason: str = "requested by the duty officer"


@router.post("/plans")
def new_plan(body: NewPlan, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    """Ask the Coordination agent for a fresh plan now."""
    coordination._officer(actor, "request a plan")
    p = coordination.build_plan(db, body.reason)
    db.commit()
    return row(p)


class Decision(BaseModel):
    approver_name: str | None = Field(None, description="ignored when X-Actor is sent; kept for old clients")
    comment: str | None = None
    assign_recommended: bool = True


def _who(actor: Actor, body: Decision) -> Actor:
    return Actor(actor.role, body.approver_name) if body.approver_name and actor.name == "Duty Officer" else actor


@router.post("/plans/{pid}/approve")
def approve(pid: int, body: Decision, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    p = get_or_404(db, Plan, pid)
    ds = coordination.approve(db, p, _who(actor, body), body.comment, body.assign_recommended)
    db.commit()
    return {"plan": row(p), "dispatches": [_d(db, d) for d in ds]}


@router.post("/plans/{pid}/reject")
def reject(pid: int, body: Decision, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    p = get_or_404(db, Plan, pid)
    coordination.reject(db, p, _who(actor, body), body.comment)
    db.commit()
    return row(p)


class Edit(Decision):
    remove_lines: list[int] = []
    quantities: dict[str, int] = {}      # "line:resource_type" -> new quantity


@router.post("/plans/{pid}/edit")
def edit(pid: int, body: Edit, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    p = get_or_404(db, Plan, pid)
    new = coordination.edit(db, p, _who(actor, body), body.remove_lines, body.quantities, body.comment)
    db.commit()
    return row(new)


class DispatchAll(BaseModel):
    verify_routes: bool = Field(False, description="the officer confirms they checked each route; required for unverified routes")


@router.post("/plans/{pid}/dispatch-all")
def dispatch_all(pid: int, body: DispatchAll, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    """Duty Officer shortcut: verify (when asked) and dispatch every assigned task of an approved plan. Each task still
    goes through the same checks; failures are reported per task."""
    coordination._officer(actor, "dispatch a whole plan")
    get_or_404(db, Plan, pid)
    done, skipped = [], []
    for d in db.scalars(select(Dispatch).where(Dispatch.plan_id == pid, Dispatch.status == "assigned").order_by(Dispatch.id)):
        try:
            if body.verify_routes and not (d.route_info or {}).get("verified"):
                coordination.verify_route(db, d, actor)
            coordination.dispatch(db, d, actor)
            done.append(d.id)
        except coordination.InvalidTransition as e:
            skipped.append({"dispatch_id": d.id, "why": str(e)})
    db.commit()
    return {"dispatched": done, "skipped": skipped}


@router.get("/dispatches")
def dispatches(db: Session = Depends(get_db)):
    return [_d(db, d) for d in db.scalars(select(Dispatch).order_by(Dispatch.id.desc()))]


@router.get("/dispatches/{did}/volunteers")
def volunteer_ranking(did: int, db: Session = Depends(get_db)):
    """The deterministic ranking tool for this task (skills, availability, reliability, distance; ties by ID)."""
    d = get_or_404(db, Dispatch, did)
    return volunteers.rank(db, (d.route_info or {}).get("need", "food"), d.to_lat, d.to_lng, d.vehicle)


class Assign(BaseModel):
    volunteer_code: str | None = None


@router.post("/dispatches/{did}/assign")
def assign(did: int, body: Assign, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    d = coordination.assign(db, get_or_404(db, Dispatch, did), actor, body.volunteer_code)
    db.commit()
    return _d(db, d)


class Note(BaseModel):
    note: str | None = None


@router.post("/dispatches/{did}/verify-route")
def verify_route(did: int, body: Note, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    d = coordination.verify_route(db, get_or_404(db, Dispatch, did), actor, body.note)
    db.commit()
    return _d(db, d)


@router.post("/dispatches/{did}/dispatch")
def do_dispatch(did: int, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    d = coordination.dispatch(db, get_or_404(db, Dispatch, did), actor)
    db.commit()
    return _d(db, d)


@router.post("/dispatches/{did}/deliver")
def deliver(did: int, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    d = coordination.mark_delivered(db, get_or_404(db, Dispatch, did), actor)
    db.commit()
    return _d(db, d)


class Confirm(BaseModel):
    method: str = Field("officer_review", pattern="^(officer_review|field_team|shelter_checkin|sms_reply|phone_call)$")
    note: str | None = None


@router.post("/dispatches/{did}/confirm")
def confirm(did: int, body: Confirm, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    d = coordination.confirm(db, get_or_404(db, Dispatch, did), actor, body.method, body.note)
    db.commit()
    return _d(db, d)


class Fail(BaseModel):
    reason: str = Field("reported by field team", min_length=3)


@router.post("/dispatches/{did}/fail")
def fail(did: int, body: Fail, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    d = coordination.fail(db, get_or_404(db, Dispatch, did), body.reason, actor)
    pipeline.run(db, "dispatch_failed")
    db.commit()
    return _d(db, d)


class DispatchPatch(BaseModel):
    status: str = Field(pattern="^(delivered|failed)$")
    note: str | None = None


@router.patch("/dispatches/{did}")
def patch_dispatch(did: int, body: DispatchPatch, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    """Older field-app style status update; goes through the same lifecycle checks."""
    d = get_or_404(db, Dispatch, did)
    if body.status == "delivered":
        coordination.mark_delivered(db, d, actor)
    else:
        coordination.fail(db, d, body.note or "reported by field team", actor)
        pipeline.run(db, "dispatch_failed")
    db.commit()
    return _d(db, d)


@router.post("/dispatches/tick")
def tick(db: Session = Depends(get_db)):
    """Run delivery tracking now (the scenario clock also does this)."""
    pipeline.run(db, "tick")
    db.commit()
    return {"ok": True}
