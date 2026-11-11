"""Blackout Detection — "Which areas have gone silent?"  Silence is a signal.
Risk per zone = hazard + population + silence + infrastructure loss + missing-contact reports + vulnerability, each
with its points and reason (zones.blackout_breakdown). Above the threshold: a blackout alert, a ranked list of silent
zones (population × hazard × hours silent), and a reconnaissance task with an estimate of likely needs and supplies to
pre-position, which goes through human approval. A report from inside the zone (satellite phone, field app,
drone) completes the task, resolves the alert and the zone returns to the normal pipeline.
Also produces the shelter/road triggers for Monitoring & Replanning."""
import math

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.common import row
from app.core import state
from app.models import Depot, InventoryItem, ReconTask, Report, Shelter, Zone
from app.services import alerts, hazard, routing
from app.services import scoring as S
from app.disasters import UNITS
from app.ws.manager import emit

AFFECTED_SHARE = 0.6           # share of a silent zone's population assumed to need help on the first visit
MIN_SILENT_H = 6.0             # a zone with any report from inside in the last 6 h is not silent
CARRY = {  # what one recon trip can carry, by method
    "field_team_satphone": {"water_litres": 2000, "food_kits": 300, "medical_kits": 30, "blankets": 200},
    "helicopter": {"water_litres": 800, "food_kits": 150, "medical_kits": 20, "blankets": 80},
    "drone": {"medical_kits": 2},
}


# ---------------- risk score ----------------
def risk(db: Session, z: Zone) -> dict:
    W = S.BLACKOUT_WEIGHTS
    now = state.now(db)
    hz = hazard.zone_hazard(db, z)
    if hz["in_flood_extent"]:
        h, hwhy = 1.0, "inside the current satellite flood extent"
    elif hz["quake_mag"] and hz["quake_mag"] >= 5:
        h, hwhy = 0.8, f"earthquake M{hz['quake_mag']}"
    elif hz["river_above_danger"]:
        h, hwhy = 0.7, "river above danger mark"
    elif hz["heavy_rain"]:
        h, hwhy = 0.5, f"heavy rain {hz['rain_mm_24h']} mm/24 h"
    else:
        h, hwhy = 0.0, "no hazard signal"
    pop = min(1.0, z.population / 10000)
    silent_h = now - (z.last_report_at if z.last_report_at is not None else 0.0)
    expected = z.normal_reports_per_hour * silent_h
    sil = 0.0 if silent_h < MIN_SILENT_H else min(1.0, expected / 3)
    inside = db.scalar(select(func.count()).select_from(Report).where(Report.zone_id == z.id, Report.missing_contact.is_(False), Report.status != "blocked")) or 0
    infra = (0.5 if z.tower_status == "down" else 0.25 if z.tower_status == "partial" else 0) + (0.5 if z.power_status == "off" else 0)
    missing = db.scalar(select(func.count()).select_from(Report).where(Report.zone_id == z.id, Report.missing_contact.is_(True))) or 0
    v = z.vulnerability or {}
    vul = min(1.0, 2 * v.get("elderly_share", 0) + 0.6 * v.get("remoteness", 0))
    comp = {
        "hazard": (h, hwhy),
        "population": (pop, f"{z.population:,} people (census)"),
        "silence": (sil, f"{silent_h:.1f} h without a report from inside ({inside} ever); about {expected:.1f} expected at its normal rate"),
        "infrastructure": (infra, f"towers {z.tower_status}, power {z.power_status}"),
        "missing_contact": (min(1.0, missing / 2), f"{missing} relative/neighbour report(s): cannot reach people here"),
        "vulnerability": (vul, f"elderly {v.get('elderly_share', 0):.0%}, remoteness {v.get('remoteness', 0):.0%}"),
    }
    total = sum(W[k] * val for k, (val, _) in comp.items())
    return {"score": round(total, 3), "hours_silent": round(silent_h, 1), "hazard": h,
            "rank_value": round(z.population * max(h, 0.1) * silent_h),
            "components": {k: {"value": round(val, 2), "weight": W[k], "points": round(W[k] * val, 3), "why": why} for k, (val, why) in comp.items()}}


# ---------------- recon ----------------
def _estimate(db: Session, z: Zone, h: float) -> dict:
    affected = round(z.population * AFFECTED_SHARE)
    needs = {rt: math.ceil(affected * per) for rt, per in state.standards(db).items() if per > 0}
    needs["blankets"] = math.ceil(affected * 0.3 * (1 if h >= 0.7 else 0.5))
    return {"affected_estimate": affected, "basis": f"{z.population:,} people × {AFFECTED_SHARE:.0%} × one day at per-person standards", "needs_one_day": needs}


def _plan_recon(db: Session, z: Zone, r: dict) -> ReconTask:
    roads_open = any(x for x in (routing.route(db, d_z.code, z.code) for d_z in db.scalars(select(Zone).where(Zone.id.in_(select(Depot.zone_id))))))
    method = "field_team_satphone" if roads_open else ("helicopter" if z.population >= 1000 else "drone")
    # ask the Resource agent what the team should carry (it owns stock and per-person standards)
    from app.agents import bus
    replies = bus.ask(db, "blackout", "resource", "recon_supplies",
                      f"{z.name} has been silent for {r['hours_silent']} h ({z.population:,} people, risk {r['score']:.2f}). "
                      f"I am proposing a {method.replace('_', ' ')} recon: what should it carry, and from where?",
                      {"zone_id": z.id, "method": method, "hazard": r["hazard"]}, conversation=f"recon:{z.code}:{state.now(db):.1f}")
    offer = next((m.content for m in replies if m.performative == "propose"), None) or {}
    est, pre = offer.get("estimate", _estimate(db, z, r["hazard"])), offer.get("prepositioned", [])
    depot = db.get(Depot, offer["depot_id"]) if offer.get("depot_id") else db.scalars(select(Depot)).first()
    best = (depot, (offer.get("route") or {}).get("km", 999), offer.get("route"))
    label = {"field_team_satphone": "field team with satellite phone", "helicopter": "helicopter", "drone": "drone"}[method]
    t = ReconTask(zone_id=z.id, method=method, team=f"{label} from {depot.name}", risk_score=r["score"], risk_breakdown=r,
                  estimated_needs=est, prepositioned=pre, from_depot_id=depot.id, created_at_sim=state.now(db),
                  rationale=(f"{z.name} is silent for {r['hours_silent']} h with risk {r['score']:.2f}: "
                             + "; ".join(c["why"] for c in r["components"].values() if c["value"] > 0)
                             + f". Send a {label}" + (f" (route {best[2]['km']} km)" if best[2] else " (no open road)")
                             + " carrying supplies so the first visit can deliver, not just assess."))
    db.add(t)
    db.flush()
    carried = ", ".join(f"{p['quantity']} {p['resource_type']}" for p in pre)
    from app.agents import bus
    bus.send(db, "blackout", "duty_officer", "propose", "recon",
             f"{z.name} ({z.population:,} people) is silent. I propose a {label} from {depot.name} carrying {carried or 'no supplies'}. Approve?",
             {"recon_id": t.id, "zone": z.code}, conversation=f"recon:{z.code}:{state.now(db):.1f}")
    state.audit(db, "blackout", "recon_proposed", f"{z.name}: {label}, pre-position {carried}", object_type="recon", object_id=t.id)
    emit("recon", row(t))
    return t


def approve_recon(db: Session, t: ReconTask, who: str) -> ReconTask:
    if t.status != "pending_approval":
        raise ValueError(f"recon task is {t.status}")
    t.status, t.approved_by = "in_progress", who
    for p in t.prepositioned:
        i = db.scalar(select(InventoryItem).where(InventoryItem.location_type == "depot", InventoryItem.location_id == t.from_depot_id,
                                                  InventoryItem.resource_type == p["resource_type"]))
        if i:
            i.quantity = max(0, i.quantity - p["quantity"])
            i.in_transit += p["quantity"]
    state.audit(db, who, "recon_approved", f"recon to zone {t.zone_id} approved ({t.team})", actor_type="human", object_type="recon", object_id=t.id)
    emit("recon", row(t))
    return t


def _complete_if_heard(db: Session, z: Zone) -> None:
    """A report from inside a flagged zone ends the blackout: the zone is back on the normal pipeline."""
    since = (z.blackout_breakdown or {}).get("flagged_at", 0)
    heard = db.scalars(select(Report).where(Report.zone_id == z.id, Report.missing_contact.is_(False), Report.status != "blocked",
                                            Report.received_at >= since)).all()
    if not heard:
        return
    z.blackout_flag = False
    for t in db.scalars(select(ReconTask).where(ReconTask.zone_id == z.id, ReconTask.status.in_(["pending_approval", "in_progress"]))):
        t.status = "completed" if t.status == "in_progress" else "cancelled"
        t.completed_at_sim = state.now(db)
        t.report_ids = [r.id for r in heard]
        for p in t.prepositioned if t.status == "completed" else []:
            i = db.scalar(select(InventoryItem).where(InventoryItem.location_type == "depot", InventoryItem.location_id == t.from_depot_id,
                                                      InventoryItem.resource_type == p["resource_type"]))
            if i:
                i.in_transit = max(0, i.in_transit - p["quantity"])
                i.consumed += p["quantity"]
        emit("recon", row(t))
    alerts.resolve(db, f"blackout:{z.code}", f"contact restored: {heard[0].ref} via {heard[0].channel}", actor="blackout")
    state.audit(db, "blackout", "blackout_resolved", f"{z.name}: contact restored by {heard[0].ref} ({heard[0].channel}); now normal incidents",
                object_type="zone", object_id=z.id)


def scan(db: Session) -> list[dict]:
    out = []
    for z in db.scalars(select(Zone)):
        if z.blackout_flag:
            _complete_if_heard(db, z)
        r = risk(db, z)
        prev = z.blackout_breakdown or {}
        z.blackout_score = r["score"]
        flagged = r["score"] >= S.BLACKOUT_THRESHOLD and r["components"]["silence"]["value"] > 0
        z.blackout_breakdown = {**r, "flagged_at": prev.get("flagged_at") if z.blackout_flag else (state.now(db) if flagged else None)}
        if flagged and not z.blackout_flag:
            z.blackout_flag = True
            alerts.raise_alert(db, type="blackout", severity="critical", key=f"blackout:{z.code}", actor="blackout",
                               message=f"{z.name} has gone silent: {r['hours_silent']} h without reports, risk {r['score']:.2f}. Reconnaissance proposed.",
                               related={"zone_id": z.id}, details=r)
            if not db.scalar(select(ReconTask.id).where(ReconTask.zone_id == z.id, ReconTask.status.in_(["pending_approval", "in_progress"]))):
                _plan_recon(db, z, r)
        out.append({"zone": z.code, **r, "flag": z.blackout_flag})
        emit("zone", {"code": z.code, "blackout_flag": z.blackout_flag, "blackout_score": z.blackout_score})
    db.flush()
    return out


# ---------------- monitoring triggers (shelters and roads) ----------------
def shelter_and_road_triggers(db: Session) -> list[dict]:
    now = state.now(db)
    triggers = []
    for s in db.scalars(select(Shelter)):
        acc = routing.shelter_access(db, s)
        if not acc["accessible"] and s.status != "inaccessible":
            s.status, s.status_reason = "inaccessible", acc["why"]
            alerts.raise_alert(db, type="shelter_inaccessible", severity="critical", key=f"inaccessible:{s.id}", actor="monitor",
                               message=f"{s.name} is inaccessible: {acc['why']}", related={"shelter_id": s.id}, details=acc)
            emit("shelter", row(s))
        elif acc["accessible"] and s.status == "inaccessible":
            s.status, s.status_reason = "open", None
            alerts.resolve(db, f"inaccessible:{s.id}", "an access road reopened", actor="monitor")
        if s.status == "inaccessible":
            triggers.append({"key": f"inaccessible:{s.id}:{','.join(acc['closed_roads'])}", "why": f"{s.name} inaccessible ({acc['why']})"})
        if s.status == "open" and s.capacity and s.occupancy >= s.capacity:
            s.status = "full"
        if s.status == "full":
            triggers.append({"key": f"full:{s.id}", "why": f"{s.name} is full ({s.occupancy}/{s.capacity})"})
            alerts.raise_alert(db, type="shelter_inaccessible", severity="medium", key=f"full:{s.id}", actor="monitor",
                               message=f"{s.name} is full: route new arrivals elsewhere", related={"shelter_id": s.id})
        if s.status == "open" and now - s.last_confirmed_at > S.SHELTER_CHECKIN_STALE_H:
            s.status, s.status_reason = "unconfirmed", f"no check-in for {now - s.last_confirmed_at:.1f} h"
            alerts.raise_alert(db, type="shelter_inaccessible", severity="medium", key=f"unconfirmed:shelter:{s.id}", actor="monitor",
                               message=f"{s.name} missed check-ins ({now - s.last_confirmed_at:.1f} h): status unconfirmed, call the manager",
                               related={"shelter_id": s.id})
            triggers.append({"key": f"unconfirmed:{s.id}", "why": f"{s.name} unconfirmed (missed check-ins)"})
        elif s.status != "unconfirmed":
            alerts.resolve(db, f"unconfirmed:shelter:{s.id}", "checked in", actor="monitor")
    db.flush()
    return triggers


def run(db: Session, st: dict) -> dict:
    zs = scan(db)
    flagged = [z for z in zs if z["flag"]]
    return {"summary": f"{len(flagged)} silent zone(s): {', '.join(z['zone'] for z in flagged) or 'none'}"}
