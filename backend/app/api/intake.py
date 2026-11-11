"""Intake endpoints for every channel: web, SMS (Twilio-style webhook), voice (IVR), field app, radio console, feeds."""
import time
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.common import row
from app.channels import ingest, voice
from app.channels.adapters import ADAPTERS
from app.channels.sms import parse_inbound
from app.channels.sms_flow import handle_inbound
from app.core import state
from app.db import get_db
from app.models import Report, SmsMessage, Source, Zone
from app.ws.manager import emit

router = APIRouter(prefix="/api/intake", tags=["intake"])


def _report_out(db: Session, r: Report) -> dict:
    out = row(r)
    emit("report", out)
    return out


class WebReport(BaseModel):
    text: str = Field(min_length=2, max_length=2000)
    name: str | None = None
    phone: str | None = None
    lat: float | None = None
    lng: float | None = None


@router.post("/web")
def intake_web(body: WebReport, db: Session = Depends(get_db)):
    src = ingest.resolve_source(db, body.phone or body.name or "web-anonymous", "web")
    r = ingest.submit(db, channel="web", source=src, text=body.text, lat=body.lat, lng=body.lng)
    db.commit()
    return {"report": _report_out(db, r), "blocked": r.status == "blocked"}


@router.post("/sms")
async def intake_sms(request: Request, db: Session = Depends(get_db)):
    """Twilio / Exotel / MSG91-style webhook (form-encoded From, Body) or JSON {from, body} from the simulator."""
    if request.headers.get("content-type", "").startswith("application/json"):
        payload = await request.json()
    else:
        payload = dict(await request.form())
    msg = parse_inbound(payload)
    if not msg["from"] or not msg["body"]:
        raise HTTPException(422, "SMS needs a sender (From) and a body (Body)")
    out = handle_inbound(db, msg["from"], msg["body"])
    db.commit()
    r = out.get("report")
    return {"kind": out["kind"], "report": _report_out(db, r) if r else None,
            "dispatch": out.get("dispatch"),
            "replies": [{"body": m.body, "language": m.language, "kind": m.kind} for m in out.get("replies", [])]}


@router.get("/sms/thread")
def sms_thread(phone: str, db: Session = Depends(get_db)):
    """Conversation for one phone (the Phone Simulator shows this)."""
    from app.core.privacy import hash_phone
    msgs = db.scalars(select(SmsMessage).where(SmsMessage.phone_hash == hash_phone(phone)).order_by(SmsMessage.id))
    return [{"id": m.id, "direction": m.direction, "body": m.body, "kind": m.kind, "language": m.language, "t": m.created_at_sim} for m in msgs]


@router.get("/sms/outbox")
def sms_outbox(limit: int = 100, db: Session = Depends(get_db)):
    msgs = db.scalars(select(SmsMessage).order_by(SmsMessage.id.desc()).limit(limit))
    return [{**row(m)} for m in msgs]


# ---- voice (IVR, Twilio TwiML) ----
@router.post("/voice")
async def intake_voice(request: Request, db: Session = Depends(get_db)):
    form = dict(await request.form()) if not request.headers.get("content-type", "").startswith("application/json") else await request.json()
    lang = request.query_params.get("lang")
    if form.get("RecordingUrl") or form.get("TranscriptionText"):
        text, _ = voice.transcribe(None, lang or "en", form.get("TranscriptionText"))
        out = handle_inbound(db, form.get("From", "+910000000000"), text or "[voice message, no transcript]", channel="voice",
                             audio_url=form.get("RecordingUrl"))
        db.commit()
        return Response(voice.done_twiml(lang or "en"), media_type="application/xml")
    if form.get("Digits"):
        lang = voice.lang_for_digit(str(form["Digits"]))
        return Response(voice.record_twiml(lang, f"/api/intake/voice?lang={lang}"), media_type="application/xml")
    return Response(voice.menu_twiml("/api/intake/voice"), media_type="application/xml")


@router.post("/voice/simulate")
async def voice_simulate(phone: str = Form(...), language: str = Form("kn"), transcript: str | None = Form(None),
                         audio: UploadFile | None = File(None), db: Session = Depends(get_db)):
    """Phone Simulator: a recorded or uploaded clip plus (in mock mode) the browser's transcript."""
    data = await audio.read() if audio else None
    url = voice.save_audio(data, f"call-{int(time.time())}-{uuid.uuid4().hex[:6]}.webm") if data else None
    text, method = voice.transcribe(data, language, transcript)
    if not text:
        raise HTTPException(422, "No transcript: record with speech recognition on, type a transcript, or set a Gemini key.")
    out = handle_inbound(db, phone, text, channel="voice", audio_url=url)
    r = out["report"]
    r.extraction = {**(r.extraction or {}), "transcription": method}
    db.commit()
    return {"report": _report_out(db, r), "transcription": method,
            "replies": [{"body": m.body, "language": m.language, "kind": m.kind} for m in out.get("replies", [])]}


# ---- field app (offline queue sync) ----
class FieldReport(BaseModel):
    client_id: str = Field(min_length=4, max_length=64)        # idempotency key from the device queue
    text: str = Field(min_length=2, max_length=2000)
    team: str = "Field team"
    lat: float | None = None
    lng: float | None = None
    captured_sim_time: float | None = None
    captured_at: str | None = None
    queued_offline: bool = False


@router.post("/field")
def intake_field(body: FieldReport, db: Session = Depends(get_db)):
    dup = db.scalar(select(Report).where(Report.adapter == f"field:{body.client_id}"))
    if dup:
        return {"report": row(dup), "duplicate": True}
    src = ingest.resolve_source(db, body.team, "field_app")
    if src.type == "anonymous":
        src.type, src.reliability_score = "field_team", 0.85
    r = ingest.submit(db, channel="field_app", source=src, text=body.text, lat=body.lat, lng=body.lng,
                      adapter=f"field:{body.client_id}", event_time=body.captured_sim_time)
    r.extraction = {**(r.extraction or {}), "captured_at": body.captured_at, "queued_offline": body.queued_offline}
    db.commit()
    return {"report": _report_out(db, r), "duplicate": False}


# ---- radio / operator console ----
RADIO_TIERS = {"satphone": ("field_team", 0.85), "police_wireless": ("official_agency", 0.9), "forest_radio": ("official_agency", 0.85),
               "railway_radio": ("official_agency", 0.85), "ham": ("volunteer", 0.7)}


class RadioEntry(BaseModel):
    operator: str = "Control room operator"
    kind: str = Field("satphone", pattern="^(satphone|police_wireless|forest_radio|railway_radio|ham)$")
    callsign: str = Field(min_length=1, max_length=80)
    zone_code: str | None = None
    message: str = Field(min_length=2, max_length=2000)


@router.post("/radio")
def intake_radio(body: RadioEntry, db: Session = Depends(get_db)):
    typ, rel = RADIO_TIERS[body.kind]
    name = f"{body.callsign} ({body.kind.replace('_', ' ')})"
    src = db.scalar(select(Source).where(Source.name == name))
    if not src:
        src = Source(type=typ, name=name, reliability_score=rel, preferred_language="en")
        db.add(src)
        db.flush()
    z = db.scalar(select(Zone).where(Zone.code == body.zone_code)) if body.zone_code else None
    r = ingest.submit(db, channel="radio_entry", source=src, text=body.message, adapter=body.kind,
                      lat=z.lat if z else None, lng=z.lng if z else None)
    r.extraction = {**(r.extraction or {}), "operator": body.operator, "operator_zone": body.zone_code}
    state.audit(db, body.operator, "radio_entry", f"{name}: {body.message[:80]}", actor_type="human", object_type="report", object_id=r.id)
    db.commit()
    return {"report": _report_out(db, r)}


# ---- feed adapters ----
@router.get("/feeds")
def feeds():
    return [{"name": a.name, "channel": a.channel, "description": a.description} for a in ADAPTERS.values()]


@router.post("/feed/{adapter}")
def intake_feed(adapter: str, n: int = 1, db: Session = Depends(get_db)):
    a = ADAPTERS.get(adapter)
    if not a:
        raise HTTPException(404, f"Unknown adapter {adapter}. Available: {', '.join(ADAPTERS)}")
    out = []
    for it in a.pull(max(1, min(n, 10))):
        if a.channel == "sms":
            r = handle_inbound(db, it.who, it.text)["report"]
        else:
            src = ingest.resolve_source(db, it.who, a.channel)
            r = ingest.submit(db, channel=a.channel, source=src, text=it.text, adapter=adapter)
        out.append(r)
    db.commit()
    return {"adapter": adapter, "reports": [_report_out(db, r) for r in out]}
