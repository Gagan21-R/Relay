"""Outgoing area-wise public communication: draft from a reusable template in each language the area speaks, check
that every fact (place, shelter, road, numbers) survived, fall back to English where no drafted template exists, and
send (mock SMS) only after a Duty Officer approves. The LLM may draft a translation outside mock mode, but its output
is used only if it passes the same fact check; it never decides what is sent or to whom."""
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.common import row
from app.core import state
from app.i18n.languages import LANGUAGES
from app.i18n.public_templates import PUBLIC
from app.models import Communication, Source, Zone
from app.services.llm import get_llm
from app.ws.manager import emit


def fact_check(text: str, facts: dict) -> dict:
    """Every fact value must appear verbatim; every number in the facts must appear as digits."""
    missing = [k for k, v in facts.items() if str(v).strip() and str(v) not in text]
    nums = set(re.findall(r"\d+", " ".join(str(v) for v in facts.values())))
    lost = sorted(n for n in nums if n not in re.findall(r"\d+", text))
    return {"ok": not missing and not lost, "missing_fields": missing, "missing_numbers": lost}


def area_languages(db: Session, zone: Zone | None) -> list[str]:
    langs = set((state.get(db, "world", {}) or {}).get("languages", ["en"]))
    q = select(Source.preferred_language).where(Source.type.in_(["citizen", "volunteer"]))
    if zone:
        from app.models import Report
        q = q.where(Source.id.in_(select(Report.source_id).where(Report.zone_id == zone.id)))
    langs |= {l for l in db.scalars(q) if l}
    return sorted(langs | {"en"}, key=lambda l: (l != "en", LANGUAGES.get(l, {}).get("priority", 9), l))


def _render(template_id: str, lang: str, facts: dict) -> tuple[str, str]:
    t = PUBLIC[template_id]
    if lang == "en":
        return t["en"].format(**facts), "source"
    if lang in t:
        return t[lang].format(**facts), "drafted-unreviewed"
    english = t["en"].format(**facts)
    out = get_llm().generate_text(
        f"Translate this public safety SMS into {LANGUAGES.get(lang, {}).get('name', lang)}. Keep every place name, road name, "
        f"shelter name and number exactly as written, in Latin script. Reply with the translation only.\n\n{english}")
    if out and fact_check(out, facts)["ok"]:
        return out.strip(), "machine-translated-unreviewed"
    return english, "english-fallback"


def draft(db: Session, template_id: str, facts: dict, zone_id: int | None, languages: list[str] | None, who: str) -> list[Communication]:
    if template_id not in PUBLIC:
        raise ValueError(f"unknown template {template_id}")
    need = PUBLIC[template_id]["fields"]
    gaps = [f for f in need if not str(facts.get(f, "")).strip()]
    if gaps:
        raise ValueError(f"missing facts: {', '.join(gaps)}")
    facts = {k: str(facts[k]).strip() for k in need}
    zone = db.get(Zone, zone_id) if zone_id else None
    langs = languages or area_languages(db, zone)
    out = []
    english = PUBLIC[template_id]["en"].format(**facts)
    for lang in langs:
        text, status = _render(template_id, lang, facts)
        c = Communication(zone_id=zone.id if zone else None, template_id=template_id, language=lang, facts=facts, text=text,
                          english_text=english, translation_status=status, fact_check=fact_check(text, facts), status="draft",
                          created_at_sim=state.now(db))
        db.add(c)
        out.append(c)
    db.flush()
    state.audit(db, who, "communication_drafted", f"{template_id} for {zone.name if zone else 'all areas'} in {', '.join(langs)}",
                actor_type="human", object_type="communication", object_id=out[0].id if out else None,
                outputs={"languages": langs, "fallbacks": [c.language for c in out if c.translation_status == "english-fallback"]})
    for c in out:
        emit("communication", row(c))
    return out


def approve(db: Session, c: Communication, who: str) -> Communication:
    if c.status != "draft":
        raise ValueError(f"communication {c.id} is {c.status}, not a draft")
    if not c.fact_check.get("ok"):
        raise ValueError(f"fact check failed: {c.fact_check}")
    c.status, c.approved_by = "approved", who
    state.audit(db, who, "communication_approved", f"#{c.id} {c.template_id} ({c.language}, {c.translation_status})", actor_type="human",
                object_type="communication", object_id=c.id)
    emit("communication", row(c))
    return c


def reject(db: Session, c: Communication, who: str) -> Communication:
    c.status = "rejected"
    state.audit(db, who, "communication_rejected", f"#{c.id}", actor_type="human", object_type="communication", object_id=c.id)
    emit("communication", row(c))
    return c


def send(db: Session, c: Communication, who: str) -> Communication:
    """Mock send to every phone in the area whose language matches (English fallback goes to speakers of languages
    that have no template). Requires prior approval."""
    from app.channels.sms_flow import send as sms_send
    from app.models import Report
    if c.status != "approved":
        raise ValueError(f"communication {c.id} is {c.status}: approve it first")
    q = select(Source).where(Source.phone_hash.is_not(None), Source.type.in_(["citizen", "volunteer"]))
    if c.zone_id:
        q = q.where(Source.id.in_(select(Report.source_id).where(Report.zone_id == c.zone_id)))
    covered = set(PUBLIC[c.template_id]) - {"fields"}
    n = 0
    for s in db.scalars(q):
        lang = s.preferred_language or "en"
        if lang == c.language or (c.language == "en" and lang not in covered):
            sms_send(db, s.phone_hash, c.text, "public_update", c.language)
            n += 1
    c.status, c.recipients, c.sent_at_sim = "sent", n, state.now(db)
    state.audit(db, who, "communication_sent", f"#{c.id} {c.template_id} ({c.language}) to {n} phone(s) [mock SMS]", actor_type="human",
                object_type="communication", object_id=c.id)
    emit("communication", row(c))
    return c
