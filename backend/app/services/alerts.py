"""Alerts are raised with a stable key so the same condition never produces duplicates, and resolved when it clears."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.common import row
from app.core import state
from app.models import Alert
from app.ws.manager import emit


def raise_alert(db: Session, *, type: str, severity: str, message: str, key: str, related: dict | None = None,
                details: dict | None = None, translations: dict | None = None, actor: str = "monitor") -> tuple[Alert, bool]:
    """Returns (alert, created). An open alert with the same key is updated in place."""
    a = db.scalar(select(Alert).where(Alert.key == key, Alert.resolved.is_(False)))
    created = a is None
    if created:
        a = Alert(type=type, severity=severity, message=message, key=key, related=related or {}, details=details or {},
                  translations=translations or {}, created_at_sim=state.now(db))
        db.add(a)
        db.flush()
        state.audit(db, actor, f"alert_{type}", message, object_type="alert", object_id=a.id, outputs={"severity": severity, **(related or {})})
    else:
        a.message, a.severity, a.details = message, severity, details or a.details
        if related:
            a.related = related
        if translations:
            a.translations = translations
        db.flush()
    emit("alert", row(a))
    return a, created


def resolve(db: Session, key: str, reason: str, actor: str = "monitor") -> Alert | None:
    a = db.scalar(select(Alert).where(Alert.key == key, Alert.resolved.is_(False)))
    if a:
        a.resolved = True
        a.details = {**(a.details or {}), "resolved_because": reason, "resolved_at": state.now(db)}
        db.flush()
        state.audit(db, actor, "alert_resolved", f"{a.message} — {reason}", object_type="alert", object_id=a.id)
        emit("alert", row(a))
    return a


def open_keys(db: Session, prefix: str) -> list[str]:
    return [a.key for a in db.scalars(select(Alert).where(Alert.key.like(prefix + "%"), Alert.resolved.is_(False)))]
