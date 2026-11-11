"""Simulation controls: network status per zone (more what-if events and the scenario engine arrive in phase 10)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import state
from app.db import get_db
from app.models import Zone
from app.sim.samples import PHONES, SAMPLES
from app.ws.manager import emit

router = APIRouter(prefix="/api/sim", tags=["simulation"])


class NetworkChange(BaseModel):
    zone_code: str
    internet_down: bool


@router.post("/network")
def network(body: NetworkChange, db: Session = Depends(get_db)):
    """Internet DOWN in a zone: web, social and field-app reports from inside it stop; SMS, voice and radio continue."""
    z = db.scalar(select(Zone).where(Zone.code == body.zone_code))
    if not z:
        raise HTTPException(404, f"zone {body.zone_code} not found")
    z.internet_down = body.internet_down
    state.audit(db, "Simulation", "network_changed", f"Internet {'DOWN' if body.internet_down else 'restored'} in {z.name}",
                actor_type="system", object_type="zone", object_id=z.id)
    db.commit()
    emit("network", {"zone": z.code, "name": z.name, "internet_down": z.internet_down})
    return {"zone": z.code, "internet_down": z.internet_down}


@router.get("/samples")
def samples():
    return {"messages": SAMPLES, "phones": PHONES}
