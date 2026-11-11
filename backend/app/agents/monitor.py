"""Monitoring & Replanning — "Has something changed?"
Watches for triggers and asks the Coordination agent for a revised plan (always re-routed through human approval).
A trigger fires once: its key is remembered so the same condition does not produce a new plan on every tick."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import coordination
from app.core import state
from app.models import Alert, Incident, Plan

HIGH_PRIORITY = 60.0


def _in_pending_plan(db: Session) -> set[int]:
    ids = set()
    for p in db.scalars(select(Plan).where(Plan.status == "pending_approval")):
        ids |= {a.get("incident_id") for a in p.assignments if a.get("incident_id")}
    return ids


def collect(db: Session, st: dict) -> list[dict]:
    triggers = []
    # delivery progress, overdue, failures (time-based)
    triggers += coordination.track(db)
    # new shortages
    for a in db.scalars(select(Alert).where(Alert.type == "shortage", Alert.resolved.is_(False))):
        triggers.append({"key": a.key, "why": a.message})
    # new high-priority verified/likely incidents not covered by a plan or dispatch
    planned = _in_pending_plan(db) | coordination._covered_incidents(db)
    for inc in db.scalars(select(Incident).where(Incident.status == "open", Incident.priority_score >= HIGH_PRIORITY,
                                                 Incident.confidence_level.in_(["verified", "likely"]))):
        if inc.id not in planned:
            triggers.append({"key": f"incident:{inc.id}", "why": f"new high-priority incident #{inc.id} {inc.title}"})
    # Phase 8 adds: shelters inaccessible/full/unconfirmed, flooded access roads, blackout zones
    from app.agents import blackout
    triggers += blackout.shelter_and_road_triggers(db) if hasattr(blackout, "shelter_and_road_triggers") else []
    return triggers


def run(db: Session, st: dict) -> dict:
    seen = set(state.get(db, "handled_triggers", []))
    fresh = [t for t in collect(db, st) if t["key"] not in seen]
    if fresh:
        state.put(db, "handled_triggers", sorted(seen | {t["key"] for t in fresh}))
        state.audit(db, "monitor", "replan_requested", "; ".join(t["why"] for t in fresh[:4]), outputs={"triggers": [t["key"] for t in fresh]}, push=False)
    return {"triggers": fresh, "summary": f"{len(fresh)} new trigger(s)"}
