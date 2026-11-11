"""Entry point for every report, whatever the channel. Resolves the source (masking/hashing phone numbers) and hands
the report to the pipeline."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import state
from app.core.privacy import hash_phone, mask_phone
from app.models import Report, Source
from app.sim.seed_sources import source_key_map

SOCIAL_CHANNELS = {"social_feed", "news_feed"}


def next_ref(db: Session) -> str:
    n = (db.scalar(select(func.max(Report.id))) or 0) + 1001
    return f"R-{n}"


def resolve_source(db: Session, who: str | None, channel: str, language: str | None = None) -> Source:
    """`who` is a seeded source key, a phone number, or a social handle."""
    keys = source_key_map(db)
    if who and who in keys:
        return db.get(Source, keys[who])
    if who and who.startswith("+"):
        h = hash_phone(who)
        s = db.scalar(select(Source).where(Source.phone_hash == h))
        if s:
            return s
        s = Source(type="citizen", name=f"Citizen {mask_phone(who)}", phone_hash=h, phone_masked=mask_phone(who),
                   preferred_language=language or "en", reliability_score=0.5)
    else:
        handle = who or "anonymous"
        s = db.scalar(select(Source).where(Source.name == handle))
        if s:
            return s
        typ = "social" if channel in SOCIAL_CHANNELS or handle.startswith("@") else "anonymous"
        s = Source(type=typ, name=handle, preferred_language=language or "en", reliability_score=0.35 if typ == "social" else 0.3)
    db.add(s)
    db.flush()
    return s


def store_raw(db: Session, *, channel: str, source: Source, text: str, received_at: float, media: dict | None = None,
              adapter: str | None = None, audio_url: str | None = None) -> Report:
    r = Report(ref=next_ref(db), source_id=source.id, channel=channel, adapter=adapter or channel, raw_text=text,
               received_at=received_at, media_urls=(media or {}).get("urls", []), media_meta=(media or {}).get("meta", {}),
               audio_url=audio_url, status="received")
    db.add(r)
    db.flush()
    return r


def from_timeline(db: Session, *, channel: str, who: str, text: str, received_at: float, media: dict | None = None) -> Report:
    """Scenario replay: a report arrives through its channel's adapter (SMS and voice go through the SMS flow so
    auto-replies and clarification questions are sent exactly as in a live deployment)."""
    if channel in ("sms", "voice"):
        from app.channels.sms_flow import handle_inbound
        return handle_inbound(db, who, text, received_at=received_at, channel=channel)["report"]
    src = resolve_source(db, who, channel)
    return submit(db, channel=channel, source=src, text=text, received_at=received_at, media=media)


def submit(db: Session, *, channel: str, source: Source, text: str, received_at: float | None = None, media: dict | None = None,
           adapter: str | None = None, lat: float | None = None, lng: float | None = None, event_time: float | None = None,
           audio_url: str | None = None) -> Report:
    """Store a report and run the agent graph on it."""
    from app.graph import pipeline
    r = store_raw(db, channel=channel, source=source, text=text, received_at=state.now(db) if received_at is None else received_at,
                  media=media, adapter=adapter, audio_url=audio_url)
    r.lat, r.lng, r.reported_event_time = lat, lng, event_time
    db.flush()
    pipeline.run(db, "report_received", report_ids=[r.id])
    db.refresh(r)
    return r
