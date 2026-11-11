"""All RELAY tables (Section 3 of the build prompt, plus zones/roads/gazetteer/signals/recon/sms/sim state).
Portable across PostgreSQL and SQLite: JSON columns, lat/lng floats (distances by haversine), no PostGIS functions."""
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(32))            # citizen volunteer field_team official_agency ngo sensor social
    name: Mapped[str] = mapped_column(String(200))
    phone_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    phone_masked: Mapped[str | None] = mapped_column(String(32))
    preferred_language: Mapped[str] = mapped_column(String(8), default="en")
    reliability_score: Mapped[float] = mapped_column(Float, default=0.5)
    reports_confirmed: Mapped[int] = mapped_column(Integer, default=0)
    reports_refuted: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Zone(Base):
    __tablename__ = "zones"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    polygon: Mapped[list] = mapped_column(JSON, default=list)                  # [[lat, lng], ...]
    population: Mapped[int] = mapped_column(Integer, default=0)
    tower_status: Mapped[str] = mapped_column(String(16), default="up")       # up | down
    power_status: Mapped[str] = mapped_column(String(16), default="on")       # on | off
    internet_down: Mapped[bool] = mapped_column(Boolean, default=False)
    normal_reports_per_hour: Mapped[float] = mapped_column(Float, default=0.5)
    vulnerability: Mapped[dict] = mapped_column(JSON, default=dict)            # elderly_share, children_share, medical_facilities, remoteness
    last_report_at: Mapped[float | None] = mapped_column(Float)                # simulated hours
    blackout_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    blackout_score: Mapped[float] = mapped_column(Float, default=0.0)
    blackout_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)


class Gazetteer(Base):
    __tablename__ = "gazetteer"
    id: Mapped[int] = mapped_column(primary_key=True)
    canonical: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(24))                              # town village landmark shelter depot river
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("zones.id"))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    aliases: Mapped[list] = mapped_column(JSON, default=list)                  # spellings in several scripts


class Road(Base):
    __tablename__ = "roads"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    a: Mapped[str] = mapped_column(String(32))                                 # zone code at each end
    b: Mapped[str] = mapped_column(String(32))
    points: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="open")            # open | flooded | blocked
    status_source: Mapped[str] = mapped_column(String(120), default="seed")
    updated_at: Mapped[float] = mapped_column(Float, default=0.0)


class Depot(Base):
    __tablename__ = "depots"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    owner: Mapped[str] = mapped_column(String(80), default="District administration")
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)


class Shelter(Base):
    __tablename__ = "shelters"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    capacity: Mapped[int] = mapped_column(Integer)
    occupancy: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="open")            # open full inaccessible unconfirmed closed
    status_reason: Mapped[str | None] = mapped_column(String(240))
    access_road_ids: Mapped[list] = mapped_column(JSON, default=list)           # road codes
    manager_source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))
    last_confirmed_at: Mapped[float] = mapped_column(Float, default=0.0)       # simulated hours


class InventoryItem(Base):
    """Stock at a depot or a shelter. quantity = on hand; in_transit = dispatched toward this place;
    consumed = delivered and used. Stale when not counted for a while."""
    __tablename__ = "inventory"
    id: Mapped[int] = mapped_column(primary_key=True)
    location_type: Mapped[str] = mapped_column(String(16))                     # depot | shelter
    location_id: Mapped[int] = mapped_column(Integer, index=True)
    resource_type: Mapped[str] = mapped_column(String(32))                     # food_kits water_litres medical_kits boats blankets volunteers vehicles
    quantity: Mapped[float] = mapped_column(Float, default=0)
    in_transit: Mapped[float] = mapped_column(Float, default=0)
    consumed: Mapped[float] = mapped_column(Float, default=0)
    unit: Mapped[str] = mapped_column(String(16))
    last_updated_at: Mapped[float] = mapped_column(Float, default=0.0)


class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(240))
    category: Mapped[str] = mapped_column(String(24))                          # rescue medical food water shelter infrastructure other
    need_types: Mapped[list] = mapped_column(JSON, default=list)
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)
    area_name: Mapped[str | None] = mapped_column(String(120))
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("zones.id"))
    confidence_level: Mapped[str] = mapped_column(String(16), default="unverified")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    priority_score: Mapped[float] = mapped_column(Float, default=0.0)
    priority_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    people_affected: Mapped[int] = mapped_column(Integer, default=0)
    vulnerable_groups: Mapped[list] = mapped_column(JSON, default=list)
    life_safety: Mapped[bool] = mapped_column(Boolean, default=False)
    fast_verify: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_note: Mapped[str | None] = mapped_column(Text)
    official_status: Mapped[str | None] = mapped_column(String(16))           # confirmed | refuted (by a person)
    status: Mapped[str] = mapped_column(String(16), default="open")            # open planned in_progress resolved
    first_report_at: Mapped[float] = mapped_column(Float, default=0.0)        # simulated hours
    last_report_at: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    ref: Mapped[str] = mapped_column(String(16), unique=True)                 # R-1042
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))
    channel: Mapped[str] = mapped_column(String(24))                           # web sms voice field_app social_feed news_feed official_feed radio_entry
    adapter: Mapped[str | None] = mapped_column(String(32))
    raw_text: Mapped[str] = mapped_column(Text)
    original_language: Mapped[str | None] = mapped_column(String(8))
    language_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    script: Mapped[str | None] = mapped_column(String(16))                     # native romanized mixed
    translated_text_en: Mapped[str | None] = mapped_column(Text)
    translation_method: Mapped[str | None] = mapped_column(String(32))
    translation_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    audio_url: Mapped[str | None] = mapped_column(String(300))
    media_urls: Mapped[list] = mapped_column(JSON, default=list)
    media_meta: Mapped[dict] = mapped_column(JSON, default=dict)               # EXIF-like: taken_at, gps
    received_at: Mapped[float] = mapped_column(Float, default=0.0)            # simulated hours since event start
    reported_event_time: Mapped[float | None] = mapped_column(Float)
    location_text: Mapped[str | None] = mapped_column(String(200))
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("zones.id"))
    geocode_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    geocode_method: Mapped[str | None] = mapped_column(String(32))
    need_types: Mapped[list] = mapped_column(JSON, default=list)
    people_count: Mapped[int | None] = mapped_column(Integer)
    vulnerable_groups: Mapped[list] = mapped_column(JSON, default=list)
    urgency_hint: Mapped[str | None] = mapped_column(String(16))               # critical high medium low
    life_safety: Mapped[bool] = mapped_column(Boolean, default=False)
    rumour_signals: Mapped[list] = mapped_column(JSON, default=list)
    missing_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    extraction_method: Mapped[str | None] = mapped_column(String(32))
    extraction: Mapped[dict] = mapped_column(JSON, default=dict)               # full structured record + evidence spans
    needs_clarification: Mapped[list] = mapped_column(JSON, default=list)      # missing fields asked by SMS
    incident_id: Mapped[int | None] = mapped_column(ForeignKey("incidents.id"))
    cluster_evidence: Mapped[dict] = mapped_column(JSON, default=dict)         # why it joined (or started) its incident
    forward_of_report_id: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="received")        # received clarifying processed blocked
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_by_agent: Mapped[str] = mapped_column(String(32), default="coordination")
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="pending_approval")  # draft pending_approval approved rejected superseded
    kind: Mapped[str] = mapped_column(String(16), default="relief")            # relief | recon
    trigger: Mapped[str | None] = mapped_column(String(240))
    rationale: Mapped[str] = mapped_column(Text, default="")
    assignments: Mapped[list] = mapped_column(JSON, default=list)
    created_at_sim: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Dispatch(Base):
    __tablename__ = "dispatches"
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    incident_id: Mapped[int | None] = mapped_column(ForeignKey("incidents.id"))
    from_depot_id: Mapped[int] = mapped_column(ForeignKey("depots.id"))
    to_type: Mapped[str] = mapped_column(String(16))                           # shelter | incident | zone
    to_id: Mapped[int | None] = mapped_column(Integer)
    to_lat: Mapped[float] = mapped_column(Float)
    to_lng: Mapped[float] = mapped_column(Float)
    to_name: Mapped[str] = mapped_column(String(160))
    resource_lines: Mapped[list] = mapped_column(JSON, default=list)           # [{resource_type, quantity, unit}]
    assigned_team: Mapped[str] = mapped_column(String(120))
    route: Mapped[list] = mapped_column(JSON, default=list)                    # [[lat, lng], ...]
    status: Mapped[str] = mapped_column(String(16), default="pending")         # pending dispatched in_transit delivered confirmed failed
    dispatched_at: Mapped[float | None] = mapped_column(Float)
    eta: Mapped[float | None] = mapped_column(Float)                           # simulated hours
    delivered_at: Mapped[float | None] = mapped_column(Float)
    confirmation_method: Mapped[str | None] = mapped_column(String(32))       # field_team sms_reply shelter_checkin
    confirmation_phone_hash: Mapped[str | None] = mapped_column(String(64))
    confirmation_language: Mapped[str | None] = mapped_column(String(8))
    confirmed_at: Mapped[float | None] = mapped_column(Float)
    overdue: Mapped[bool] = mapped_column(Boolean, default=False)


class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    approver_name: Mapped[str] = mapped_column(String(120))
    decision: Mapped[str] = mapped_column(String(16))                          # approved rejected edited
    comment: Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(32))                              # shortage blackout shelter_inaccessible rumour delivery_overdue escalation replan
    severity: Mapped[str] = mapped_column(String(16))                          # critical high medium low
    message: Mapped[str] = mapped_column(Text)
    translations: Mapped[dict] = mapped_column(JSON, default=dict)
    related: Mapped[dict] = mapped_column(JSON, default=dict)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    key: Mapped[str | None] = mapped_column(String(120), index=True)          # de-duplication key for open alerts
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at_sim: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Signal(Base):
    """Non-human signals: rainfall, river gauge, dam bulletins, quakes, flood extent polygons, tower/power outages."""
    __tablename__ = "signals"
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(24))                              # rainfall river dam quake flood_extent tower_outage power_outage census drone
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("zones.id"))
    value: Mapped[dict] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(String(80))
    observed_at: Mapped[float] = mapped_column(Float, default=0.0)


class ReconTask(Base):
    __tablename__ = "recon_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending_approval")  # pending_approval approved in_progress completed rejected
    method: Mapped[str] = mapped_column(String(32))                            # drone helicopter field_team_satphone
    team: Mapped[str] = mapped_column(String(120))
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    estimated_needs: Mapped[dict] = mapped_column(JSON, default=dict)
    prepositioned: Mapped[list] = mapped_column(JSON, default=list)
    from_depot_id: Mapped[int | None] = mapped_column(ForeignKey("depots.id"))
    rationale: Mapped[str] = mapped_column(Text, default="")
    approved_by: Mapped[str | None] = mapped_column(String(120))
    images: Mapped[list] = mapped_column(JSON, default=list)
    report_ids: Mapped[list] = mapped_column(JSON, default=list)
    created_at_sim: Mapped[float] = mapped_column(Float, default=0.0)
    completed_at_sim: Mapped[float | None] = mapped_column(Float)


class SmsMessage(Base):
    """Every SMS in or out (the Phone Simulator reads this). Phones only as hash + masked."""
    __tablename__ = "sms_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    direction: Mapped[str] = mapped_column(String(4))                          # in | out
    phone_hash: Mapped[str] = mapped_column(String(64), index=True)
    phone_masked: Mapped[str] = mapped_column(String(32))
    body: Mapped[str] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(8))
    kind: Mapped[str] = mapped_column(String(32))                              # report ack clarification clarification_reply confirmation_request confirmation_reply rumour_correction
    report_id: Mapped[int | None] = mapped_column(Integer)
    dispatch_id: Mapped[int | None] = mapped_column(Integer)
    provider_ref: Mapped[str | None] = mapped_column(String(64))
    created_at_sim: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(80))                             # agent name or person
    actor_type: Mapped[str] = mapped_column(String(16))                        # agent | human | system
    action: Mapped[str] = mapped_column(String(80))
    object_type: Mapped[str | None] = mapped_column(String(32))
    object_id: Mapped[int | None] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(Text, default="")
    inputs: Mapped[dict] = mapped_column(JSON, default=dict)
    outputs: Mapped[dict] = mapped_column(JSON, default=dict)
    sim_time: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SimState(Base):
    __tablename__ = "sim_state"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
