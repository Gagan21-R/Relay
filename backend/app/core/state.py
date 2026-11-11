"""Simulation state (clock, speed, network) in the sim_state table, and the audit log helper that also pushes a
live event. Everything RELAY does is timestamped in simulated hours since the event started (T+h)."""
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog, SimState
from app.ws.manager import emit


def get(db: Session, key: str, default: Any = None) -> Any:
    row = db.get(SimState, key)
    return row.value.get("v", default) if row else default


def put(db: Session, key: str, value: Any) -> None:
    row = db.get(SimState, key)
    if row:
        row.value = {"v": value}
    else:
        db.add(SimState(key=key, value={"v": value}))
    db.flush()


def now(db: Session) -> float:
    """Simulated hours since the event started."""
    return float(get(db, "clock", 0.0))


def set_now(db: Session, t: float) -> None:
    put(db, "clock", round(float(t), 3))


def audit(db: Session, actor: str, action: str, summary: str, *, actor_type: str = "agent", object_type: str | None = None,
          object_id: int | None = None, inputs: dict | None = None, outputs: dict | None = None, push: bool = True) -> AuditLog:
    row = AuditLog(actor=actor, actor_type=actor_type, action=action, object_type=object_type, object_id=object_id,
                   summary=summary, inputs=inputs or {}, outputs=outputs or {}, sim_time=now(db))
    db.add(row)
    db.flush()
    if push:
        emit("audit", {"id": row.id, "actor": actor, "actor_type": actor_type, "action": action, "summary": summary,
                       "object_type": object_type, "object_id": object_id, "sim_time": row.sim_time})
    return row


def disaster(db: Session) -> str:
    """The active disaster category (set by the selector or by the loaded scenario)."""
    return (get(db, "scenario", {}) or {}).get("disaster") or get(db, "disaster", "flood") or "flood"


def standards(db: Session) -> dict:
    from app.disasters import profile
    return profile(disaster(db))["per_person_day"]
