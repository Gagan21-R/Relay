"""Deterministic volunteer assignment tool (no LLM). Ranks every eligible volunteer for a task by
  skills (0.40) + reliability (0.30) + distance (0.30) + vehicle fit bonus (0.10 when their vehicle suits the route)
reliability = (on_time_confirmations + 1) / (assigned_tasks + 2)   (Laplace-smoothed; a new volunteer starts at 0.5)
distance score = max(0, 1 - km / 50).  Ties are broken by volunteer ID (code), so the same inputs always give the same
ranking. Volunteer reliability is kept separate from source (reporter) reliability and from approval precedents."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import geo
from app.models import Dispatch, Volunteer

WEIGHTS = {"skills": 0.40, "reliability": 0.30, "distance": 0.30}
VEHICLE_BONUS = 0.10
MAX_KM = 50.0
SKILLS_FOR = {
    "rescue": ["rescue", "boat", "swimming"], "medical": ["medical", "first_aid"], "water": ["logistics", "driving"],
    "food": ["logistics", "driving"], "shelter": ["logistics", "driving"], "infrastructure": ["driving", "logistics"],
    "missing_contact": ["driving", "translation"], "recon": ["driving", "rescue"],
}
ACTIVE = ("assigned", "dispatched")


def reliability(v: Volunteer) -> float:
    return round((v.on_time_confirmations + 1) / (v.assigned_tasks + 2), 4)


def busy_ids(db: Session) -> set[int]:
    return {d.volunteer_id for d in db.scalars(select(Dispatch).where(Dispatch.status.in_(ACTIVE))) if d.volunteer_id}


def rank(db: Session, need: str, lat: float, lng: float, vehicle: str | None = None, exclude: set[int] | None = None) -> dict:
    wanted = SKILLS_FOR.get(need, ["logistics"])
    busy = busy_ids(db) | set(exclude or ())
    ranked, ineligible = [], []
    for v in db.scalars(select(Volunteer).order_by(Volunteer.code)):
        if not v.available:
            ineligible.append({"code": v.code, "name": v.name, "why": "marked unavailable"})
            continue
        if v.id in busy:
            ineligible.append({"code": v.code, "name": v.name, "why": "already on an active task"})
            continue
        skills = set(v.skills or [])
        match = sorted(skills & set(wanted))
        s_skill = len(match) / len(wanted)
        rel = reliability(v)
        km = geo.haversine_m(v.lat, v.lng, lat, lng) / 1000
        s_dist = max(0.0, 1 - km / MAX_KM)
        fit = bool(vehicle and v.vehicle == vehicle)
        total = WEIGHTS["skills"] * s_skill + WEIGHTS["reliability"] * rel + WEIGHTS["distance"] * s_dist + (VEHICLE_BONUS if fit else 0)
        reasons = [f"skills {', '.join(match) if match else 'none'} of {', '.join(wanted)} ({s_skill:.2f})",
                   f"reliability ({v.on_time_confirmations}+1)/({v.assigned_tasks}+2) = {rel:.2f}",
                   f"{km:.1f} km away ({s_dist:.2f})"]
        if vehicle:
            reasons.append(f"has a {v.vehicle} (+{VEHICLE_BONUS})" if fit else f"vehicle {v.vehicle or 'none'}; route needs {vehicle}")
        ranked.append({"volunteer_id": v.id, "code": v.code, "name": v.name, "score": round(total, 4),
                       "components": {"skills": round(s_skill, 3), "reliability": rel, "distance": round(s_dist, 3), "vehicle_fit": fit},
                       "km": round(km, 1), "vehicle": v.vehicle, "languages": v.languages, "reasons": reasons})
    ranked.sort(key=lambda r: (-r["score"], r["code"]))
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
    return {"need": need, "vehicle": vehicle, "weights": {**WEIGHTS, "vehicle_bonus": VEHICLE_BONUS}, "ranked": ranked,
            "ineligible": ineligible, "tie_break": "volunteer ID (code), ascending"}
