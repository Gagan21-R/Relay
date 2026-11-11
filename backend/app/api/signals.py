"""Non-human signal feeds, blackout zones and reconnaissance, rumour corrections and the public corrections view."""
import time
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import blackout, rumour
from app.api.common import get_or_404, row, rows
from app.channels import ingest, voice
from app.core import state
from app.core.config import get_settings
from app.db import get_db
from app.graph import pipeline
from app.models import Alert, Incident, ReconTask, Signal, Source, Zone
from app.services import hazard
from app.ws.manager import emit

router = APIRouter(prefix="/api", tags=["signals, blackout & rumours"])
SIGNAL_TYPES = {"rainfall", "river", "dam", "quake", "flood_extent", "tower_outage", "power_outage", "census"}


class SignalIn(BaseModel):
    zone_code: str | None = None
    value: dict
    source: str = "manual entry"


@router.post("/signals/{typ}")
def add_signal(typ: str, body: SignalIn, db: Session = Depends(get_db)):
    """Rainfall (IMD), river gauge (CWC), dam bulletin, earthquake, satellite flood extent (polygons), tower/power outage."""
    if typ not in SIGNAL_TYPES:
        raise HTTPException(404, f"unknown signal type {typ}; use one of {sorted(SIGNAL_TYPES)}")
    z = db.scalar(select(Zone).where(Zone.code == body.zone_code)) if body.zone_code else None
    if typ == "census" and z:
        z.population = int(body.value.get("population", z.population))
    if typ == "tower_outage" and z and body.value.get("towers_down", 1) == 0:
        z.tower_status = "up"
    if typ == "power_outage" and z and body.value.get("restored"):
        z.power_status = "on"
    sig = Signal(type=typ, zone_id=z.id if z else None, value=body.value, source=body.source, observed_at=state.now(db))
    db.add(sig)
    db.flush()
    restored = typ == "tower_outage" and body.value.get("towers_down", 1) == 0
    changes = [f"{z.name}: towers restored"] if restored and z else hazard.apply_signal(db, sig)
    state.audit(db, body.source, f"signal_{typ}", "; ".join(changes) or typ, actor_type="system", object_type="signal", object_id=sig.id)
    out = pipeline.run(db, "signal")
    db.commit()
    emit("signal", {"id": sig.id, "type": typ, "zone": body.zone_code, "value": body.value, "changes": changes})
    return {"signal": row(sig), "changes": changes, "plan_id": out.get("plan_id")}


@router.get("/zones/blackout")
def blackout_zones(db: Session = Depends(get_db)):
    """Every zone with its blackout risk breakdown, silent zones ranked first (population × hazard × hours silent)."""
    zones = db.scalars(select(Zone)).all()
    recon = {t.zone_id: t for t in db.scalars(select(ReconTask).order_by(ReconTask.id))}
    out = []
    for z in zones:
        r = blackout.risk(db, z)
        out.append({**row(z), "risk": r, "recon": row(recon[z.id]) if z.id in recon else None})
    out.sort(key=lambda x: (not x["blackout_flag"], -x["risk"]["rank_value"] if x["blackout_flag"] else -x["risk"]["score"]))
    return out


@router.get("/recon")
def recon_tasks(db: Session = Depends(get_db)):
    return rows(db.scalars(select(ReconTask).order_by(ReconTask.id.desc())))


class Who(BaseModel):
    who: str = "Duty officer"


@router.post("/recon/{rid}/approve")
def approve_recon(rid: int, body: Who, db: Session = Depends(get_db)):
    t = get_or_404(db, ReconTask, rid)
    try:
        blackout.approve_recon(db, t, body.who)
    except ValueError as e:
        raise HTTPException(409, str(e)) from e
    db.commit()
    return row(t)


@router.post("/recon/{rid}/reject")
def reject_recon(rid: int, body: Who, db: Session = Depends(get_db)):
    t = get_or_404(db, ReconTask, rid)
    t.status = "rejected"
    state.audit(db, body.who, "recon_rejected", f"recon {rid} rejected", actor_type="human", object_type="recon", object_id=rid)
    db.commit()
    return row(t)


class ReconReport(BaseModel):
    message: str = Field(min_length=3)
    callsign: str = "Recon team"
    kind: str = Field("satphone", pattern="^(satphone|police_wireless|ham|field_app)$")


@router.post("/recon/{rid}/report")
def recon_report(rid: int, body: ReconReport, db: Session = Depends(get_db)):
    """The recon team reports from inside the silent zone: the report enters the normal pipeline and ends the blackout."""
    t = get_or_404(db, ReconTask, rid)
    z = db.get(Zone, t.zone_id)
    name = f"{body.callsign} ({body.kind})"
    src = db.scalar(select(Source).where(Source.name == name))
    if not src:
        src = Source(type="field_team", name=name, reliability_score=0.85, preferred_language="en")
        db.add(src)
        db.flush()
    channel = "field_app" if body.kind == "field_app" else "radio_entry"
    r = ingest.submit(db, channel=channel, source=src, text=body.message, lat=z.lat, lng=z.lng, adapter=f"recon:{rid}")
    db.commit()
    db.refresh(t)
    return {"report": row(r), "recon": row(t), "zone": row(z)}


@router.post("/recon/{rid}/image")
async def recon_image(rid: int, image: UploadFile = File(...), note: str | None = Form(None), db: Session = Depends(get_db)):
    """Drone / aerial image. EXPERIMENTAL: with a Gemini key the image is checked for rooftop SOS/HELP signs and people;
    in mock mode it is stored for a person to review."""
    t = get_or_404(db, ReconTask, rid)
    data = await image.read()
    url = voice.save_audio(data, f"drone-{int(time.time())}-{uuid.uuid4().hex[:6]}-{image.filename or 'img.jpg'}")
    finding = {"method": "stored for human review (mock mode: no automated detection)", "sos_detected": None}
    if not get_settings().mock:  # pragma: no cover - needs a key
        try:
            from google import genai
            from google.genai import types
            c = genai.Client(api_key=get_settings().gemini_api_key)
            res = c.models.generate_content(model=get_settings().gemini_model, contents=[
                "Disaster aerial image. Answer in JSON: {sos_detected: bool, people_visible: int, notes: str}. Look for SOS/HELP painted on roofs, waving people, stranded people.",
                types.Part.from_bytes(data=data, mime_type=image.content_type or "image/jpeg")], config={"response_mime_type": "application/json"})
            import json
            finding = {"method": "gemini vision (experimental)", **json.loads(res.text)}
        except Exception:  # noqa: BLE001
            pass
    t.images = [*(t.images or []), {"url": url, "note": note, "finding": finding, "t": state.now(db)}]
    state.audit(db, "Recon team", "drone_image", f"image for recon {rid}: {finding['method']}", actor_type="human", object_type="recon", object_id=rid)
    db.commit()
    emit("recon", row(t))
    return row(t)


class RumourBody(BaseModel):
    incident_id: int
    who: str = "Duty officer"
    message_en: str | None = None


@router.post("/alerts/rumour")
def publish_rumour(body: RumourBody, db: Session = Depends(get_db)):
    inc = get_or_404(db, Incident, body.incident_id)
    try:
        out = rumour.publish(db, inc, body.who, body.message_en)
    except ValueError as e:
        raise HTTPException(409, str(e)) from e
    db.commit()
    return out


@router.get("/public/corrections")
def public_corrections(db: Session = Depends(get_db)):
    """The public view: official rumour corrections in every language (no internal data)."""
    out = []
    for a in db.scalars(select(Alert).where(Alert.type == "rumour").order_by(Alert.id.desc())):
        out.append({"id": a.id, "message": a.message, "translations": a.translations, "t": a.created_at_sim})
    return out
