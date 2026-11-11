"""Resources: depot stock (stale flags), shelter burn rates, current and projected shortages, transfer proposals,
and burn-rate projection series for charts."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import resource
from app.api.common import row, rows
from app.core import state
from app.db import get_db
from app.models import Depot, InventoryItem
from app.services import scoring as S

router = APIRouter(prefix="/api/resources", tags=["resources"])


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    a = resource.analyse(db)
    now = state.now(db)
    depots = []
    for d in db.scalars(select(Depot).order_by(Depot.id)):
        items = db.scalars(select(InventoryItem).where(InventoryItem.location_type == "depot", InventoryItem.location_id == d.id))
        depots.append({**row(d), "inventory": [{**row(i), "stale": now - i.last_updated_at > S.STALE_STOCK_H, "age_h": round(now - i.last_updated_at, 1)} for i in items]})
    series = []
    for s in a["shelters"]:
        for b in s["burn"]:
            if b["rate_per_h"] > 0:
                pts = [{"t": round(now + h, 1), "level": max(0.0, round(b["quantity"] - b["rate_per_h"] * h, 1))} for h in range(0, 49, 3)]
                series.append({"shelter": s["name"], "shelter_id": s["id"], "resource_type": b["resource_type"], "unit": b["unit"],
                               "hours_left": b["hours_left"], "points": pts})
    return {**a, "depots": depots, "series": series, "horizon_h": S.SHORTAGE_HORIZON_H, "stale_after_h": S.STALE_STOCK_H}
