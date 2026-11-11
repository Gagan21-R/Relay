"""Approval precedent memory. Every human decision on a plan line is stored under a signature
(disaster | target kind | need category | confidence level | resource types). When a new line has the same signature
the plan shows the factual counts — "approved 3 of 4 times before" — and nothing more: precedents never change a
priority, quantity, assignment or route, and never approve anything."""
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import state
from app.models import Incident, Precedent


def signature(db: Session, line: dict) -> str:
    cat, conf = line.get("kind", "?"), "forecast"
    if line.get("incident_id"):
        inc = db.get(Incident, line["incident_id"])
        cat, conf = (inc.category, inc.confidence_level) if inc else ("?", "?")
    elif line.get("kind") == "shelter":
        cat = "shelter_resupply"
    res = ",".join(sorted(r["resource_type"] for r in line.get("resources", [])))
    return f"{state.disaster(db)}|{line.get('kind')}|{cat}|{conf}|{res}"


def lookup(db: Session, sig: str) -> dict:
    c = Counter(p.decision for p in db.scalars(select(Precedent).where(Precedent.signature == sig)))
    total = sum(c.values())
    text = (f"similar line: approved {c['approved']} of {total} time(s) before" + (f", removed {c['removed']}" if c["removed"] else "")
            + (f", rejected {c['rejected']}" if c["rejected"] else "")) if total else "no precedent for this kind of line yet"
    return {"signature": sig, "approved": c["approved"], "removed": c["removed"], "rejected": c["rejected"], "total": total, "text": text}


def record(db: Session, plan, decision: str, who: str, removed_lines: list[int] | None = None) -> int:
    n = 0
    for a in plan.assignments:
        if a.get("kind") == "unmet":
            continue
        d = "removed" if removed_lines and a.get("line") in removed_lines else decision
        if decision == "edited" and d != "removed":
            continue
        db.add(Precedent(signature=a.get("precedent", {}).get("signature") or signature(db, a), decision=d, plan_id=plan.id,
                         detail={"line": a.get("line"), "to": a.get("to_name")}, decided_by=who, at_sim=state.now(db)))
        n += 1
    db.flush()
    return n
