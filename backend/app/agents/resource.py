"""Resource Agent — "Do we have enough, and where?"
Supply = depot stock reachable over open roads (+ in transit). Demand = verified needs of incidents + shelter
occupancy × per-person daily standards (Sphere: 15 L water per person per day). Detects current shortages
(demand > reachable supply) and projected ones (burn-rate: "water at Napoklu camp runs out in ~18 h"), proposes
transfers from surplus depots, escalates when there is none, and flags stale stock."""
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import state
from app.models import Depot, Incident, InventoryItem, Shelter, Zone
from app.services import alerts, routing
from app.services import scoring as S
from app.disasters import UNITS

NEED_TO_RESOURCES = {  # what one incident of each need asks for, per person affected (min 1 person)
    "food": {"food_kits": 1.0},
    "water": {"water_litres": 30.0},          # two days at 15 L
    "medical": {"medical_kits": 0.25},
    "shelter": {"blankets": 1.0},
    "rescue": {"boats": 1 / 8},
}
ACTIVE_LEVELS = ("verified", "likely")


def depot_stock(db: Session) -> dict[int, dict[str, InventoryItem]]:
    out: dict[int, dict[str, InventoryItem]] = {}
    for i in db.scalars(select(InventoryItem).where(InventoryItem.location_type == "depot")):
        out.setdefault(i.location_id, {})[i.resource_type] = i
    return out


def shelter_burn(db: Session, s: Shelter) -> list[dict]:
    """Hours left per item at the shelter's current occupancy."""
    out = []
    for i in db.scalars(select(InventoryItem).where(InventoryItem.location_type == "shelter", InventoryItem.location_id == s.id)):
        per_day = state.standards(db).get(i.resource_type, 0) * s.occupancy
        rate = per_day / 24
        hours = (i.quantity / rate) if rate > 0 else None
        out.append({"resource_type": i.resource_type, "quantity": round(i.quantity, 1), "in_transit": i.in_transit, "unit": i.unit,
                    "rate_per_h": round(rate, 2), "hours_left": None if hours is None else round(hours, 1),
                    "per_person_day": state.standards(db).get(i.resource_type, 0)})
    return out


def consume(db: Session, dt_h: float) -> None:
    """Time passes: shelters use stock at the per-person standard."""
    if dt_h <= 0:
        return
    for s in db.scalars(select(Shelter).where(Shelter.status.in_(["open", "full", "unconfirmed", "inaccessible"]))):
        for i in db.scalars(select(InventoryItem).where(InventoryItem.location_type == "shelter", InventoryItem.location_id == s.id)):
            use = state.standards(db).get(i.resource_type, 0) * s.occupancy / 24 * dt_h
            used = min(i.quantity, use)
            i.quantity = round(i.quantity - used, 2)
            i.consumed = round(i.consumed + used, 2)
    db.flush()


def incident_demand(inc: Incident) -> dict[str, float]:
    people = max(1, inc.people_affected or 1)
    d: dict[str, float] = {}
    for need in inc.need_types or []:
        for rt, per in NEED_TO_RESOURCES.get(need, {}).items():
            d[rt] = d.get(rt, 0) + math.ceil(per * people)
    return d


def reachable_depots(db: Session, zone: Zone | None) -> list[tuple[Depot, dict]]:
    out = []
    for d in db.scalars(select(Depot)):
        dz = db.get(Zone, d.zone_id)
        r = routing.route(db, dz.code, zone.code) if zone else None
        if r:
            out.append((d, r))
    return sorted(out, key=lambda x: x[1]["km"])


def analyse(db: Session) -> dict:
    """Full picture used by the Resources page, the Coordination agent and the alerts."""
    now = state.now(db)
    stocks = depot_stock(db)
    depots = {d.id: d for d in db.scalars(select(Depot))}
    # demand from incidents that are worth acting on (plus unverified life-safety: a team check needs kit)
    demand_by_type: dict[str, float] = {}
    inc_demand = []
    for inc in db.scalars(select(Incident).where(Incident.status.in_(["open", "planned"]))):
        if inc.confidence_level in ACTIVE_LEVELS or (inc.life_safety and inc.confidence_level == "unverified"):
            d = incident_demand(inc)
            if d:
                inc_demand.append({"incident_id": inc.id, "title": inc.title, "demand": d})
                for k, v in d.items():
                    demand_by_type[k] = demand_by_type.get(k, 0) + v
    shelters = []
    projected = []
    for s in db.scalars(select(Shelter)):
        burn = shelter_burn(db, s)
        access = routing.shelter_access(db, s)
        shelters.append({"id": s.id, "name": s.name, "occupancy": s.occupancy, "capacity": s.capacity, "status": s.status, "burn": burn, "access": access})
        for b in burn:
            if b["hours_left"] is not None and b["hours_left"] < S.SHORTAGE_HORIZON_H:
                need48 = max(0.0, b["rate_per_h"] * 48 - b["quantity"] - b["in_transit"])
                projected.append({"shelter_id": s.id, "shelter": s.name, "zone_id": s.zone_id, "resource_type": b["resource_type"],
                                  "hours_left": b["hours_left"], "rate_per_h": b["rate_per_h"], "quantity": b["quantity"],
                                  "in_transit": b["in_transit"], "needed_for_48h": math.ceil(need48), "unit": b["unit"]})
    # supply that can actually reach (any open route from the depot), stale stock excluded and flagged
    supply_by_type: dict[str, float] = {}
    stale = []
    for did, items in stocks.items():
        for rt, i in items.items():
            if now - i.last_updated_at > S.STALE_STOCK_H:
                stale.append({"depot": depots[did].name, "depot_id": did, "inventory_id": i.id, "resource_type": rt, "quantity": i.quantity,
                              "last_updated_at": i.last_updated_at, "age_h": round(now - i.last_updated_at, 1)})
                continue
            supply_by_type[rt] = supply_by_type.get(rt, 0) + i.quantity
    shelter_need = {}
    for p in projected:
        shelter_need[p["resource_type"]] = shelter_need.get(p["resource_type"], 0) + p["needed_for_48h"]
    current = []
    for rt in sorted(set(demand_by_type) | set(shelter_need)):
        need = demand_by_type.get(rt, 0) + shelter_need.get(rt, 0)
        have = supply_by_type.get(rt, 0)
        if need > have:
            current.append({"resource_type": rt, "demand": round(need), "supply": round(have), "gap": round(need - have), "unit": UNITS.get(rt, "")})
    # transfer proposals for projected shelter shortages
    transfers = []
    for p in projected:
        z = db.get(Zone, p["zone_id"])
        options = []
        for d, r in reachable_depots(db, z):
            i = stocks.get(d.id, {}).get(p["resource_type"])
            fresh = i is not None and now - i.last_updated_at <= S.STALE_STOCK_H
            if i and fresh and i.quantity >= p["needed_for_48h"] > 0:
                options.append({"depot_id": d.id, "depot": d.name, "available": i.quantity, "km": r["km"], "eta_h": r["eta_h"], "route": r["zones"]})
        transfers.append({**p, "proposal": options[0] if options else None, "alternatives": options[1:3],
                          "why": (f"nearest reachable depot with fresh stock: {options[0]['depot']} ({options[0]['km']} km, ETA {options[0]['eta_h']} h)"
                                  if options else "no reachable depot holds enough fresh stock: escalate")})
    return {"clock": now, "demand_by_type": demand_by_type, "supply_by_type": supply_by_type, "incident_demand": inc_demand,
            "shelters": shelters, "projected": projected, "current": current, "transfers": transfers, "stale": stale,
            "standards_per_person_day": state.standards(db), "disaster": state.disaster(db)}


def run(db: Session, st: dict) -> dict:
    a = analyse(db)
    live_keys = set()
    for t in a["transfers"]:
        key = f"shortage:projected:{t['shelter_id']}:{t['resource_type']}"
        live_keys.add(key)
        label = t["resource_type"].replace("_", " ")
        msg = f"{label.capitalize()} at {t['shelter']} runs out in ~{t['hours_left']:.0f} h ({t['quantity']:.0f} {t['unit']} left, using {t['rate_per_h']:.0f}/h)"
        alerts.raise_alert(db, type="shortage", severity="high" if t["hours_left"] < 12 else "medium", message=msg, key=key, actor="resource",
                           related={"shelter_id": t["shelter_id"]}, details={"forecast": t, "proposal": t["proposal"], "why": t["why"]})
        if not t["proposal"]:
            ekey = f"escalation:{t['shelter_id']}:{t['resource_type']}"
            live_keys.add(ekey)
            alerts.raise_alert(db, type="escalation", severity="critical", key=ekey, actor="resource",
                               message=f"No reachable depot can cover {label} for {t['shelter']}: request state/NGO supply", related={"shelter_id": t["shelter_id"]})
    for c in a["current"]:
        key = f"shortage:current:{c['resource_type']}"
        live_keys.add(key)
        alerts.raise_alert(db, type="shortage", severity="high", key=key, actor="resource",
                           message=f"{c['resource_type'].replace('_', ' ').capitalize()}: demand {c['demand']} > reachable supply {c['supply']} {c['unit']}",
                           details=c)
    by_depot: dict[int, list] = {}
    for s_ in a["stale"]:
        by_depot.setdefault(s_["depot_id"], []).append(s_)
    for did, rows_ in by_depot.items():
        key = f"stale:depot:{did}"
        live_keys.add(key)
        alerts.raise_alert(db, type="stale_stock", severity="low", key=key, actor="resource",
                           message=f"Stock at {rows_[0]['depot']} not counted for {rows_[0]['age_h']} h ({len(rows_)} items): excluded from supply until recounted",
                           related={"depot_id": did}, details={"items": rows_})
    for prefix in ("shortage:", "escalation:", "stale:"):
        for k in alerts.open_keys(db, prefix):
            if k not in live_keys:
                alerts.resolve(db, k, "condition cleared", actor="resource")
    return {"shortages": [{"key": k} for k in live_keys if k.startswith("shortage")],
            "summary": f"{len(a['projected'])} projected, {len(a['current'])} current shortage(s), {len(a['stale'])} stale stock row(s)"}
