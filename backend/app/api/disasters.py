"""Disaster categories, the active disaster (selector) and GDACS alerts."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core import state
from app.db import get_db
from app.disasters import DISASTERS
from app.graph import pipeline
from app.services import gdacs
from app.ws.manager import emit

router = APIRouter(prefix="/api", tags=["disasters"])


@router.get("/disasters")
def disasters(db: Session = Depends(get_db)):
    active = state.disaster(db)
    return {"active": active, "items": [{"code": k, **{x: v[x] for x in ("name", "gdacs", "overlay", "life_threat", "per_person_day", "fleet", "recommendations")},
                                          "indicators_sample": v["indicators"][:8]} for k, v in DISASTERS.items()]}


class Active(BaseModel):
    code: str


@router.post("/disasters/active")
def set_active(body: Active, db: Session = Depends(get_db)):
    """The selector: changes severity factors, resource standards, overlays and recommendations; agents re-run."""
    if body.code not in DISASTERS:
        raise HTTPException(404, f"unknown disaster {body.code}")
    state.put(db, "disaster", body.code)
    sc = state.get(db, "scenario", {}) or {}
    state.put(db, "scenario", {**sc, "disaster": body.code})
    state.audit(db, "Duty officer", "disaster_selected", DISASTERS[body.code]["name"], actor_type="human")
    pipeline.run(db, "disaster_changed", incident_ids=[])
    from app.agents import triage
    triage.run(db, {})
    db.commit()
    emit("refresh", {"disaster": body.code})
    return {"active": body.code}


@router.get("/live/gdacs")
def live_gdacs(force: bool = False):
    return gdacs.alerts(force)
