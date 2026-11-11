"""Plans & approvals, and dispatch tracking with delivery confirmation."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import coordination
from app.api.common import get_or_404, row, rows
from app.db import get_db
from app.graph import pipeline
from app.models import Approval, Dispatch, Plan

router = APIRouter(prefix="/api", tags=["plans & dispatch"])


@router.get("/plans")
def plans(db: Session = Depends(get_db)):
    out = []
    for p in db.scalars(select(Plan).order_by(Plan.version.desc())):
        out.append({**row(p), "approvals": rows(db.scalars(select(Approval).where(Approval.plan_id == p.id)))})
    return out


class NewPlan(BaseModel):
    reason: str = "requested by the duty officer"


@router.post("/plans")
def new_plan(body: NewPlan, db: Session = Depends(get_db)):
    """Ask the Coordination agent for a fresh plan now."""
    p = coordination.build_plan(db, body.reason)
    db.commit()
    return row(p)


class Decision(BaseModel):
    approver_name: str = Field("Duty officer", min_length=2)
    comment: str | None = None


@router.post("/plans/{pid}/approve")
def approve(pid: int, body: Decision, db: Session = Depends(get_db)):
    p = get_or_404(db, Plan, pid)
    try:
        ds = coordination.approve(db, p, body.approver_name, body.comment)
    except ValueError as e:
        raise HTTPException(409, str(e)) from e
    db.commit()
    return {"plan": row(p), "dispatches": rows(ds)}


@router.post("/plans/{pid}/reject")
def reject(pid: int, body: Decision, db: Session = Depends(get_db)):
    p = get_or_404(db, Plan, pid)
    if p.status != "pending_approval":
        raise HTTPException(409, f"plan v{p.version} is {p.status}")
    coordination.reject(db, p, body.approver_name, body.comment)
    db.commit()
    return row(p)


class Edit(Decision):
    remove_lines: list[int] = []
    quantities: dict[str, int] = {}      # "line:resource_type" -> new quantity


@router.post("/plans/{pid}/edit")
def edit(pid: int, body: Edit, db: Session = Depends(get_db)):
    p = get_or_404(db, Plan, pid)
    if p.status != "pending_approval":
        raise HTTPException(409, f"plan v{p.version} is {p.status}")
    new = coordination.edit(db, p, body.approver_name, body.remove_lines, body.quantities, body.comment)
    db.commit()
    return row(new)


@router.get("/dispatches")
def dispatches(db: Session = Depends(get_db)):
    return rows(db.scalars(select(Dispatch).order_by(Dispatch.id.desc())), exclude={"confirmation_phone_hash"})


class DispatchPatch(BaseModel):
    status: str = Field(pattern="^(in_transit|delivered|failed)$")
    note: str | None = None
    who: str = "Field team"


@router.patch("/dispatches/{did}")
def patch_dispatch(did: int, body: DispatchPatch, db: Session = Depends(get_db)):
    """Field-team status updates from the app."""
    d = get_or_404(db, Dispatch, did)
    if body.status == "delivered":
        coordination.mark_delivered(db, d, body.who)
    elif body.status == "failed":
        coordination.fail(db, d, body.note or "reported by field team", body.who)
        pipeline.run(db, "dispatch_failed")
    else:
        d.status = "in_transit"
    db.commit()
    return row(d, {"confirmation_phone_hash"})


class Confirm(BaseModel):
    method: str = Field("field_team", pattern="^(field_team|shelter_checkin|sms_reply)$")
    who: str = "Field team"


@router.post("/dispatches/{did}/confirm")
def confirm(did: int, body: Confirm, db: Session = Depends(get_db)):
    d = get_or_404(db, Dispatch, did)
    try:
        coordination.confirm(db, d, body.method, body.who)
    except ValueError as e:
        raise HTTPException(409, str(e)) from e
    db.commit()
    return row(d, {"confirmation_phone_hash"})


@router.post("/dispatches/tick")
def tick(db: Session = Depends(get_db)):
    """Run delivery tracking now (the scenario clock also does this)."""
    pipeline.run(db, "tick")
    db.commit()
    return {"ok": True}
