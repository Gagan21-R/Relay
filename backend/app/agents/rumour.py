"""Rumour Control — "What do people need to know is false?"
When an incident is false, an officer publishes a correction: pre-translated in every supported language with the
place name in that language's script, sent by SMS to people who reported from the area (in their own language) and
shown on the public corrections page."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import state
from app.i18n.languages import LANGUAGES, script_of_char
from app.i18n.templates import rumour_text
from app.models import Gazetteer, Incident, Report, Source
from app.services import alerts


def rumour_kind(db: Session, inc: Incident) -> str:
    text = " ".join((r.translated_text_en or r.raw_text).lower() for r in db.scalars(select(Report).where(Report.incident_id == inc.id)))
    sig = {s["signal"] for r in db.scalars(select(Report).where(Report.incident_id == inc.id)) for s in (r.rumour_signals or [])}
    if "dam" in text:
        return "dam_burst"
    if "old_media" in sig or "photo" in text:
        return "old_photo"
    if "camp" in text and ("closed" in text or "don't go" in text):
        return "camp_closed"
    return "generic"


def place_in(db: Session, inc: Incident, lang: str, kind: str) -> str:
    """The place name as people write it in that language (from the gazetteer), else English."""
    canon = {"dam_burst": "Harangi dam", "old_photo": "Madikeri bus stand"}.get(kind)
    names = []
    if canon:
        names = [g for g in db.scalars(select(Gazetteer).where(Gazetteer.canonical == canon))]
    if not names and inc.zone_id:
        names = list(db.scalars(select(Gazetteer).where(Gazetteer.zone_id == inc.zone_id, Gazetteer.kind.in_(["town", "village"]))))
    for g in names:
        for a in g.aliases or []:
            if lang != "en" and a and any(script_of_char(c) == lang or (lang == "mr" and script_of_char(c) == "hi") for c in a):
                return a.replace(" ಅಣೆಕಟ್ಟು", "").replace(" बांध", "")
    base = names[0].canonical if names else (inc.area_name or "this place")
    return base.replace(" dam", "")


def publish(db: Session, inc: Incident, who: str, override_en: str | None = None) -> dict:
    from app.channels.sms_flow import send
    if inc.confidence_level != "false" and inc.official_status != "refuted":
        raise ValueError("only incidents marked false can be corrected publicly")
    kind = rumour_kind(db, inc)
    translations = {lang: rumour_text(kind, lang, place_in(db, inc, lang, kind)) for lang in LANGUAGES}
    if override_en:
        translations["en"] = override_en
    a, _ = alerts.raise_alert(db, type="rumour", severity="high", key=f"rumour:{inc.id}", actor=who,
                              message=translations["en"], translations=translations, related={"incident_id": inc.id},
                              details={"kind": kind, "published_by": who, "public": True})
    # SMS to everyone who reported in the area, in their own language (forwarders included: they spread it)
    zone_reports = db.scalars(select(Report).where((Report.incident_id == inc.id) | (Report.zone_id == inc.zone_id))).all()
    phones = {}
    for r in zone_reports:
        s = db.get(Source, r.source_id) if r.source_id else None
        if s and s.phone_hash:
            phones[s.phone_hash] = s.preferred_language if s.preferred_language in translations else "en"
    sent = [send(db, h, translations[lang], "rumour_correction", lang).id for h, lang in phones.items()]
    state.audit(db, who, "rumour_correction_published", f"#{inc.id} ({kind}) in {len(translations)} languages, {len(sent)} SMS",
                actor_type="human", object_type="alert", object_id=a.id, outputs={"languages": list(translations), "sms": len(sent)})
    return {"alert_id": a.id, "kind": kind, "translations": translations, "sms_sent": len(sent)}
