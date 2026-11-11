"""Inbound SMS logic: delivery-confirmation replies, clarification replies merged into the same report, or a new
report with an auto-reply (and at most one clarification question) in the sender's language. Unicode throughout."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.channels import ingest
from app.channels.sms import get_sms_provider
from app.core import state
from app.core.privacy import hash_phone, mask_phone
from app.i18n.templates import render
from app.models import Report, SmsMessage, Source
from app.ws.manager import emit

CLARIFY_WINDOW_H = 3.0
_REPLY_TO: dict[str, str] = {}     # phone hash -> number, in memory only (never stored); real providers reply by conversation


def log_sms(db: Session, direction: str, phone: str | None, body: str, kind: str, *, phone_hash: str | None = None,
            language: str | None = None, report_id: int | None = None, dispatch_id: int | None = None,
            provider_ref: str | None = None) -> SmsMessage:
    m = SmsMessage(direction=direction, phone_hash=phone_hash or hash_phone(phone or ""), phone_masked=mask_phone(phone) if phone else "",
                   body=body, language=language, kind=kind, report_id=report_id, dispatch_id=dispatch_id,
                   provider_ref=provider_ref, created_at_sim=state.now(db))
    if not m.phone_masked:
        src = db.scalar(select(Source).where(Source.phone_hash == m.phone_hash))
        m.phone_masked = src.phone_masked if src else "XXXX"
    db.add(m)
    db.flush()
    emit("sms", {"id": m.id, "direction": direction, "phone": m.phone_masked, "phone_key": m.phone_hash[:12], "body": body,
                 "language": language, "kind": kind, "report_id": report_id, "dispatch_id": dispatch_id, "t": m.created_at_sim})
    return m


def send(db: Session, phone_hash: str, body: str, kind: str, language: str, **kw) -> SmsMessage:
    to = _REPLY_TO.get(phone_hash)
    out = get_sms_provider().send(to or "masked", body)
    return log_sms(db, "out", to, body, kind, phone_hash=phone_hash, language=language, provider_ref=out.ref, **kw)


def _pending_clarification(db: Session, src: Source) -> Report | None:
    r = db.scalar(select(Report).where(Report.source_id == src.id, Report.status == "clarifying").order_by(Report.id.desc()))
    if r and state.now(db) - r.received_at <= CLARIFY_WINDOW_H:
        return r
    return None


def handle_inbound(db: Session, phone: str, body: str, *, received_at: float | None = None, channel: str = "sms",
                   audio_url: str | None = None, run_pipeline=None) -> dict:
    """Returns {kind, report, replies}. `run_pipeline(db, report_ids)` runs the agents (injected to avoid a cycle)."""
    from app.graph import pipeline
    run_pipeline = run_pipeline or (lambda d, ids: pipeline.run(d, "report_received", report_ids=ids))
    h = hash_phone(phone) if phone.startswith("+") or phone[:1].isdigit() else None
    if h:
        _REPLY_TO[h] = phone
    src = ingest.resolve_source(db, phone, channel)
    h = h or src.phone_hash or hash_phone(src.name)
    log_sms(db, "in", phone if phone.startswith("+") else None, body, "inbound", phone_hash=h)

    # 1. a reply to a delivery confirmation request (YES / NO in any language)
    from app.agents import coordination
    handled = coordination.handle_confirmation_reply(db, h, body)
    if handled:
        return {"kind": "confirmation_reply", **handled}

    # 2. a reply to our clarification question: merge into the same report and re-run the agents
    pending = _pending_clarification(db, src) if channel == "sms" else None
    if pending:
        asked = list(pending.needs_clarification)
        pending.raw_text = f"{pending.raw_text}\n↳ {body}"
        pending.status = "processed"
        db.flush()
        run_pipeline(db, [pending.id])
        lang = pending.original_language or src.preferred_language
        got = [k for k in asked if k not in (pending.needs_clarification or [])]
        what = ", ".join(got) or "your reply"
        reply = send(db, h, render("clarified", lang, ref=pending.ref, what=what), "clarified", lang, report_id=pending.id)
        state.audit(db, "intake", "clarification_merged", f"{pending.ref}: reply merged ({what})", object_type="report", object_id=pending.id)
        return {"kind": "clarification_reply", "report": pending, "replies": [reply]}

    # 3. a new report
    r = ingest.store_raw(db, channel=channel, source=src, text=body, received_at=received_at if received_at is not None else state.now(db),
                         audio_url=audio_url)
    run_pipeline(db, [r.id])
    db.refresh(r)
    lang = r.original_language or src.preferred_language or "en"
    replies = []
    if r.status != "blocked":
        replies.append(send(db, h, render("ack", lang, ref=r.ref), "ack", lang, report_id=r.id))
        if r.needs_clarification:
            kind = "clarify_location" if "location" in r.needs_clarification else "clarify_need"
            replies.append(send(db, h, render(kind, lang, ref=r.ref), "clarification", lang, report_id=r.id))
            r.status = "clarifying"
            state.audit(db, "intake", "clarification_sent", f"{r.ref}: asked for {', '.join(r.needs_clarification)} in {lang}",
                        object_type="report", object_id=r.id)
    db.flush()
    return {"kind": "report", "report": r, "replies": replies}
