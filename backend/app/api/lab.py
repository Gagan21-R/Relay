"""Scenario Lab API: list / filter scenarios, launch (fresh world), reset, stage progress and the final report.
Every launched scenario runs through the real channels, agents and approval workflow; its data is synthetic."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import state
from app.core.roles import Actor, current_actor, require_officer
from app.db import get_db
from app.models import Alert, AuditLog, Dispatch, Incident, Plan, Report, Zone
from app.sim import engine, lab
from app.sim.scenarios import SCENARIOS

router = APIRouter(prefix="/api/lab", tags=["scenario lab"])


def _center(sc: dict) -> list:
    from app.sim import worlds
    w = worlds.get(sc.get("world", "kodagu"))
    return w["center"]


def _summary(sid: str, sc: dict) -> dict:
    return {"id": sid, "name": sc["name"], "disaster": sc.get("disaster", sc["hazard"]), "difficulty": sc.get("difficulty", "intermediate"),
            "state": sc.get("state", "Karnataka"), "region": sc.get("region", []), "description": sc["description"],
            "objectives": sc.get("objectives", []), "expected": sc.get("expected", []), "stages": sc.get("stages", []),
            "language": sc.get("language"), "lab": bool(sc.get("lab")), "colour": sc.get("colour"), "center": _center(sc),
            "events": [{"t": t, "what": why} for t, _, _, why in sc.get("events", [])]}


@router.get("/scenarios")
def scenarios():
    return {"coverage": {**lab.coverage(), "total_with_kodagu": len(SCENARIOS)}, "scenarios": [_summary(k, v) for k, v in SCENARIOS.items()],
            "note": "Synthetic scenarios on real places (approximate coordinates). Reports in regional languages are template-drafted."}


class Launch(BaseModel):
    id: str
    replay_until: float = Field(0.0, ge=0, le=24)
    speed: float = Field(0.0, ge=0, le=600)


@router.post("/launch")
def launch(body: Launch, db: Session = Depends(get_db)):
    if body.id not in SCENARIOS:
        raise HTTPException(404, f"unknown scenario {body.id}")
    out = engine.start_scenario(db, body.id, replay_until=body.replay_until, speed=body.speed, fresh=True)
    db.commit()
    return {**out, "world": state.get(db, "world"), "scenario": state.get(db, "scenario")}


@router.post("/reset")
def reset(db: Session = Depends(get_db)):
    sc = state.get(db, "scenario", {}) or {}
    out = engine.start_scenario(db, sc.get("id", "kodagu_flood"), replay_until=0.0, fresh=True)
    db.commit()
    return out


@router.get("/status")
def status(db: Session = Depends(get_db)):
    sc = state.get(db, "scenario", {}) or {}
    spec = SCENARIOS.get(sc.get("id", "kodagu_flood"), {})
    now = state.now(db)
    stages = spec.get("stages") or [{"name": "Timeline", "from_t": 0.0, "to_t": engine.timeline_info(db)["end_t"], "summary": spec.get("description", "")}]
    current = next((s["name"] for s in stages if s["from_t"] <= now < s["to_t"]), stages[-1]["name"] if now >= stages[-1]["from_t"] else stages[0]["name"])
    return {"scenario": sc, "clock": now, "stages": stages, "current_stage": current, "timeline": engine.timeline_info(db),
            "counts": {"reports": len(db.scalars(select(Report.id)).all()), "incidents": len(db.scalars(select(Incident.id)).all()),
                       "plans": len(db.scalars(select(Plan.id)).all()), "tasks": len(db.scalars(select(Dispatch.id)).all())}}


def _objective_checks(db: Session, sid: str) -> list[dict]:
    script = lab.script(sid)
    out = []
    zones = {z.code: z for z in db.scalars(select(Zone))}
    seen = set()
    for _, _, _, _, _, lb in script:
        key = lb.get("key")
        if not key or key in seen or not key.startswith("S"):
            continue
        seen.add(key)
        z = zones.get(lb["zone"])
        incs = [i for i in db.scalars(select(Incident).where(Incident.zone_id == (z.id if z else -1)))
                if lb["need"] in (i.need_types or []) or i.category == lb["need"]]
        tasks = [d for i in incs for d in db.scalars(select(Dispatch).where(Dispatch.incident_id == i.id))]
        st = ("confirmed" if any(d.status == "confirmed" for d in tasks) else "delivered" if any(d.status == "delivered" for d in tasks)
              else "dispatched" if any(d.status == "dispatched" for d in tasks) else "planned" if any(d.status in ("approved", "assigned") for d in tasks)
              else "detected" if incs else "missed")
        out.append({"objective": f"{lb['need']} at {z.name if z else lb['zone']}", "status": st, "incidents": [i.id for i in incs],
                    "met": st == "confirmed"})
    rumours = [lb for *_, lb in script if lb.get("real") is False]
    if rumours:
        z = zones.get(rumours[0]["zone"])
        rumour_reports = [r for r in db.scalars(select(Report).where(Report.zone_id == (z.id if z else -1))) if r.rumour_signals]
        incs = {db.get(Incident, r.incident_id) for r in rumour_reports if r.incident_id}
        planned = any(db.scalar(select(Dispatch.id).where(Dispatch.incident_id == i.id).limit(1)) for i in incs if i)
        out.append({"objective": "do not act on the rumour", "status": "acted on — check" if planned else "not acted on",
                    "met": not planned, "levels": sorted({i.confidence_level for i in incs if i})})
    return out


@router.get("/report")
def report(db: Session = Depends(get_db)):
    """Final report: decisions, successes, failures and unresolved issues, from the live database."""
    sc = state.get(db, "scenario", {}) or {}
    sid = sc.get("id", "kodagu_flood")
    human = db.scalars(select(AuditLog).where(AuditLog.actor_type == "human").order_by(AuditLog.id)).all()
    tasks = db.scalars(select(Dispatch)).all()
    incs = db.scalars(select(Incident)).all()
    last_plan = db.scalar(select(Plan).order_by(Plan.version.desc()))
    successes = [f"D-{d.id} to {d.to_name} confirmed ({d.confirmation_method})" for d in tasks if d.status == "confirmed"]
    successes += [f"#{i.id} {i.title} marked {i.confidence_level} — not acted on" for i in incs if i.confidence_level in ("false", "disputed")]
    successes += [f"silent zone flagged: {z.name}" for z in db.scalars(select(Zone).where(Zone.blackout_flag))]
    failures = [f"D-{d.id} to {d.to_name} failed: {(d.history or [{}])[-1].get('note', '')}" for d in tasks if d.status == "failed"]
    failures += [f"unmet in plan v{last_plan.version}: {a['to_name']} ({a['why']})" for a in (last_plan.assignments if last_plan else []) if a.get("kind") == "unmet"]
    unresolved = [f"#{i.id} {i.title} (priority {i.priority_score:.0f}, {i.status})" for i in incs
                  if i.status in ("open", "planned") and i.priority_score >= 50 and i.confidence_level not in ("false", "disputed")]
    unresolved += [f"D-{d.id} {d.status} — awaiting {'Duty Officer confirmation' if d.status == 'delivered' else 'next step'}"
                   for d in tasks if d.status in ("approved", "assigned", "dispatched", "delivered")]
    unresolved += [f"alert: {a.message}" for a in db.scalars(select(Alert).where(Alert.resolved.is_(False), Alert.severity == "high"))]
    if last_plan and last_plan.status == "pending_approval":
        unresolved.append(f"plan v{last_plan.version} still waiting for approval")
    return {"scenario": sc, "clock": state.now(db), "synthetic": True,
            "objectives": _objective_checks(db, sid) if SCENARIOS.get(sid, {}).get("lab") else [],
            "decisions": [{"t": a.sim_time, "who": a.actor, "action": a.action, "summary": a.summary} for a in human],
            "successes": successes, "failures": failures, "unresolved": unresolved,
            "numbers": {"reports": len(db.scalars(select(Report.id)).all()), "incidents": len(incs), "plans": len(db.scalars(select(Plan.id)).all()),
                        "tasks": {s: sum(1 for d in tasks if d.status == s) for s in sorted({d.status for d in tasks})}},
            "note": "Computed from the live database. Objective checks use the scenario design; they are a training aid, not an accuracy claim."}


@router.get("/current")
def current(db: Session = Depends(get_db)):
    return {"scenario": state.get(db, "scenario"), "world": state.get(db, "world"), "disaster": state.disaster(db)}



# ---------------- guided run ----------------
class GuideStart(BaseModel):
    scenario: str | None = None


@router.get("/guide")
def guide_info(db: Session = Depends(get_db)):
    from app.sim import guide
    return guide.info(db)


@router.post("/guide/start")
def guide_start(body: GuideStart, db: Session = Depends(get_db)):
    """Launch (or restart) a scenario at T+0 and reset the guided steps."""
    from app.sim import guide
    if body.scenario and body.scenario not in SCENARIOS:
        raise HTTPException(404, f"unknown scenario {body.scenario}")
    out = guide.start(db, body.scenario)
    db.commit()
    return out


@router.post("/guide/step/{n}")
def guide_step(n: int, db: Session = Depends(get_db)):
    from app.sim import guide
    out = guide.run_step(db, n)
    db.commit()
    return out


class GuideAct(BaseModel):
    kind: str = Field(pattern="^(approve_plan|dispatch_all|send_comms|confirm_all|approve_and_dispatch)$")
    plan_id: int | None = None


@router.post("/guide/act/{n}")
def guide_act(n: int, body: GuideAct, db: Session = Depends(get_db), actor: Actor = Depends(current_actor)):
    """The Duty Officer action a waiting step asks for. Only a Duty Officer may do it (403 otherwise)."""
    from app.sim import guide
    require_officer(actor, "act in the guided run")
    out = guide.act(db, n, body.kind, body.plan_id)
    db.commit()
    return out
