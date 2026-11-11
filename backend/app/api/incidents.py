"""Incidents with their full evidence trail, the Fast Verify queue, human verification, and the same-report analyser."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import intake, trust
from app.api.common import get_or_404, row, rows
from app.core import state
from app.db import get_db
from app.models import AuditLog, Incident, Report, Signal, Source, Zone
from app.services import hazard

router = APIRouter(prefix="/api", tags=["incidents"])


@router.get("/incidents/{iid}")
def incident(iid: int, db: Session = Depends(get_db)):
    inc = get_or_404(db, Incident, iid)
    reports = db.scalars(select(Report).where(Report.incident_id == iid).order_by(Report.received_at)).all()
    srcs = {s.id: s for s in db.scalars(select(Source).where(Source.id.in_([r.source_id for r in reports])))}
    z = db.get(Zone, inc.zone_id) if inc.zone_id else None
    signals = db.scalars(select(Signal).where(Signal.zone_id == inc.zone_id).order_by(Signal.observed_at.desc())).all() if z else []
    trail = db.scalars(select(AuditLog).where(
        ((AuditLog.object_type == "incident") & (AuditLog.object_id == iid)) |
        ((AuditLog.object_type == "report") & (AuditLog.object_id.in_([r.id for r in reports])))).order_by(AuditLog.id)).all()
    return {
        **row(inc),
        "zone": row(z) if z else None,
        "hazard": hazard.zone_hazard(db, z) if z else None,
        "reports": [{**row(r), "refutes": trust.is_refutation(r),
                     "source": {"type": srcs[r.source_id].type, "name": srcs[r.source_id].name, "reliability": srcs[r.source_id].reliability_score,
                                "phone_masked": srcs[r.source_id].phone_masked} if r.source_id in srcs else None} for r in reports],
        "signals": rows(signals[:8]),
        "audit": rows(trail[-30:]),
    }


@router.get("/fast-verify")
def fast_verify(db: Session = Depends(get_db)):
    """Low-confidence life-safety incidents. Never discarded: each needs a callback or the nearest team to check."""
    out = []
    for inc in db.scalars(select(Incident).where(Incident.fast_verify.is_(True)).order_by(Incident.priority_score.desc())):
        reps = db.scalars(select(Report).where(Report.incident_id == inc.id).order_by(Report.received_at)).all()
        callable_ = [db.get(Source, r.source_id) for r in reps if r.source_id]
        out.append({**row(inc), "reports": [{"ref": r.ref, "raw_text": r.raw_text, "translated_text_en": r.translated_text_en,
                                              "original_language": r.original_language, "channel": r.channel} for r in reps],
                    "callback": [{"name": s.name, "phone_masked": s.phone_masked, "language": s.preferred_language} for s in callable_ if s and s.phone_masked],
                    "waiting_h": round(state.now(db) - inc.first_report_at, 1)})
    return out


class VerifyBody(BaseModel):
    decision: str = Field(pattern="^(confirm|refute)$")
    note: str | None = None
    who: str = "Duty officer"


@router.post("/incidents/{iid}/verify")
def verify(iid: int, body: VerifyBody, db: Session = Depends(get_db)):
    inc = trust.verify(db, get_or_404(db, Incident, iid), body.decision, body.who, body.note)
    from app.graph import pipeline
    pipeline.run(db, "incident_verified", incident_ids=[iid])
    db.commit()
    return row(inc)


class CompareBody(BaseModel):
    texts: list[str] = Field(min_length=2, max_length=6)
    hours_apart: list[float] | None = None


@router.post("/trust/compare")
def compare(body: CompareBody, db: Session = Depends(get_db)):
    """Same-report analyser: are these reports (any language) about the same incident? Shows every test and number.
    Runs the real Intake + Trust logic inside a savepoint that is rolled back, so nothing is stored."""
    sp = db.begin_nested()
    try:
        reps = []
        for i, t in enumerate(body.texts):
            r = Report(ref=f"CMP-{i + 1}", channel="web", raw_text=t, received_at=(body.hours_apart or [0] * len(body.texts))[i] if body.hours_apart else 0.0)
            db.add(r)
            db.flush()
            intake.process(db, r)
            reps.append(r)
        pairs = []
        for i in range(len(reps)):
            for j in range(i + 1, len(reps)):
                m = trust.match_score(reps[i], reps[j])
                pairs.append({"a": i, "b": j, **m})
        items = [{"text": r.raw_text, "language": r.original_language, "script": r.script, "translation": r.translated_text_en,
                  "translation_method": r.translation_method, "location": r.location_text, "need_types": r.need_types,
                  "people": r.people_count, "rumour_signals": r.rumour_signals, "life_safety": r.life_safety} for r in reps]
    finally:
        sp.rollback()
    groups = list(range(len(items)))
    for p in pairs:
        if p["same"]:
            a, b = groups[p["a"]], groups[p["b"]]
            groups = [a if g == b else g for g in groups]
    return {"items": items, "pairs": pairs, "groups": groups, "incidents": len(set(groups)),
            "verdict": "same incident" if len(set(groups)) == 1 else f"{len(set(groups))} different incidents"}


@router.post("/incidents/{iid}/status")
def set_status(iid: int, status: str, db: Session = Depends(get_db)):
    if status not in ("open", "planned", "in_progress", "resolved"):
        raise HTTPException(422, "status must be open, planned, in_progress or resolved")
    inc = get_or_404(db, Incident, iid)
    inc.status = status
    state.audit(db, "Duty officer", "incident_status", f"#{iid} -> {status}", actor_type="human", object_type="incident", object_id=iid)
    db.commit()
    return row(inc)
