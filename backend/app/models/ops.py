"""Operational tables added in the enhancement round: hospitals, volunteers, road observations, outgoing public
communications and approval precedents."""
from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Hospital(Base):
    __tablename__ = "hospitals"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    beds: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="open")            # open | overloaded | inaccessible


class Volunteer(Base):
    """A registered volunteer. Reliability = (on_time_confirmations + 1) / (assigned_tasks + 2) (Laplace smoothing),
    kept separate from source (reporter) reliability and from approval precedents."""
    __tablename__ = "volunteers"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True)                 # V-001
    name: Mapped[str] = mapped_column(String(120))
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("zones.id"))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    skills: Mapped[list] = mapped_column(JSON, default=list)                   # rescue boat medical driving logistics translation
    vehicle: Mapped[str | None] = mapped_column(String(16))                    # truck 4x4 boat two_wheeler None
    languages: Mapped[list] = mapped_column(JSON, default=list)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    assigned_tasks: Mapped[int] = mapped_column(Integer, default=0)
    on_time_confirmations: Mapped[int] = mapped_column(Integer, default=0)
    phone_masked: Mapped[str | None] = mapped_column(String(32))

    @property
    def reliability(self) -> float:
        return (self.on_time_confirmations + 1) / (self.assigned_tasks + 2)


class RoadReport(Base):
    """One observation of a road's condition, with its source and freshness. Unverified reports can close a road
    for planning (caution) but can never make a route 'safe'."""
    __tablename__ = "road_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    road_id: Mapped[int] = mapped_column(ForeignKey("roads.id"), index=True)
    status: Mapped[str] = mapped_column(String(16))                            # open | flooded | blocked | damaged
    source: Mapped[str] = mapped_column(String(160))
    source_type: Mapped[str] = mapped_column(String(24))                       # official sensor field_team volunteer citizen social satellite
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[str | None] = mapped_column(String(120))
    reported_at: Mapped[float] = mapped_column(Float, default=0.0)
    note: Mapped[str | None] = mapped_column(String(240))


class Communication(Base):
    """An outgoing area-wise public update drafted from a reusable template. Never sent without human approval."""
    __tablename__ = "communications"
    id: Mapped[int] = mapped_column(primary_key=True)
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("zones.id"))
    template_id: Mapped[str] = mapped_column(String(40))
    language: Mapped[str] = mapped_column(String(8))
    facts: Mapped[dict] = mapped_column(JSON, default=dict)
    text: Mapped[str] = mapped_column(Text)
    english_text: Mapped[str] = mapped_column(Text)
    translation_status: Mapped[str] = mapped_column(String(32))                # source | drafted-unreviewed | english-fallback
    fact_check: Mapped[dict] = mapped_column(JSON, default=dict)               # {ok, missing: [...]}
    status: Mapped[str] = mapped_column(String(16), default="draft")           # draft approved sent rejected
    approved_by: Mapped[str | None] = mapped_column(String(120))
    recipients: Mapped[int] = mapped_column(Integer, default=0)
    created_at_sim: Mapped[float] = mapped_column(Float, default=0.0)
    sent_at_sim: Mapped[float | None] = mapped_column(Float)


class Precedent(Base):
    """Approval precedent memory: how a person decided a plan line with the same signature before."""
    __tablename__ = "precedents"
    id: Mapped[int] = mapped_column(primary_key=True)
    signature: Mapped[str] = mapped_column(String(160), index=True)            # disaster|kind|category|confidence|resources
    decision: Mapped[str] = mapped_column(String(16))                          # approved rejected removed
    plan_id: Mapped[int | None] = mapped_column(Integer)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    decided_by: Mapped[str] = mapped_column(String(120))
    at_sim: Mapped[float] = mapped_column(Float, default=0.0)
