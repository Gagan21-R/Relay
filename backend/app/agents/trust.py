"""Trust & Evidence Agent — "Is it true, and have we seen it before?"
1. Cross-lingual duplicate clustering: a report joins an incident only if embedding similarity >= threshold AND
   distance <= X m AND time difference <= Y h (all configurable in services/scoring.py). Embeddings are computed on a
   language-neutral form (English translation + canonical place + need types) in mock mode, or on the raw text with
   Gemini multilingual embeddings, so a Kannada SMS and an English post about the same school meet.
2. Forwards / copies of the same text count as ONE source.
3. Explainable confidence: weighted components + penalties, stored with the incident (confidence_breakdown).
4. Life-safety reports are never discarded: low confidence sends them to the Fast Verify queue.
5. Source reliability updates when a person confirms or refutes an incident."""
from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.common import row
from app.core import geo, state
from app.core.config import get_settings
from app.i18n import lexicon as L
from app.models import Incident, Report, Signal, Source, Zone
from app.services import hazard
from app.services import scoring as S
from app.services.llm import cosine, get_embedder
from app.ws.manager import emit

CATEGORY_ORDER = ["rescue", "medical", "water", "food", "shelter", "infrastructure", "missing_contact", "other"]
ACTIONABLE = {"rescue", "medical", "water", "food", "shelter", "infrastructure", "missing_contact"}


# ---------- embeddings ----------
def neutral_text(r: Report) -> str:
    """Language-neutral form used for similarity: translation + canonical place + needs."""
    needs = " ".join(n for n in (r.need_types or []) if n != "other")
    return f"{r.translated_text_en or r.raw_text} | {r.location_text or ''} | {needs}".lower()


@lru_cache(maxsize=4096)
def _embed(text: str) -> tuple:
    return tuple(get_embedder().embed([text])[0])


def similarity(a: Report, b: Report) -> float:
    if not get_settings().mock:  # real multilingual embeddings compare the original texts directly
        return cosine(list(_embed(a.raw_text)), list(_embed(b.raw_text)))
    return cosine(list(_embed(neutral_text(a))), list(_embed(neutral_text(b))))


def raw_similarity(a: Report, b: Report) -> float:
    """Same-text test for forwards and copies (a translation of the same event is NOT a copy)."""
    return cosine(list(_embed(a.raw_text.lower().replace("rt ", "", 1))), list(_embed(b.raw_text.lower().replace("rt ", "", 1))))


def sim_threshold() -> float:
    return S.CLUSTER["similarity_threshold"] if get_settings().mock else S.CLUSTER["similarity_threshold_gemini"]


def _contains(text: str, phrases: list[str]) -> list[str]:
    low = text.lower()
    return [p for p in phrases if p.lower() in low]


def is_refutation(r: Report) -> bool:
    return bool(_contains(r.raw_text + " " + (r.translated_text_en or ""), L.REFUTE))


# ---------- clustering ----------
def match_score(r: Report, other: Report) -> dict:
    """The three tests for 'same incident', with the numbers used. Shared by clustering and the same-report analyser."""
    sim = round(similarity(r, other), 3)
    dist = geo.haversine_m(r.lat, r.lng, other.lat, other.lng) if None not in (r.lat, r.lng, other.lat, other.lng) else None
    dt = abs(r.received_at - other.received_at)
    shared_needs = sorted(set(r.need_types or []) & set(other.need_types or []) - {"other"})
    th = sim_threshold() if dist is not None else S.CLUSTER["no_location_similarity"]
    tests = {
        "similarity": {"value": sim, "threshold": th, "pass": sim >= th},
        "distance_m": {"value": None if dist is None else round(dist), "threshold": S.CLUSTER["max_distance_m"],
                       "pass": dist is not None and dist <= S.CLUSTER["max_distance_m"] or (dist is None and r.zone_id is None and sim >= th)},
        "time_h": {"value": round(dt, 2), "threshold": S.CLUSTER["time_window_h"],
                   "pass": dt <= (24.0 if _contains(r.raw_text, L.RESOLVED) else S.CLUSTER["time_window_h"])},
    }
    compat, cwhy = needs_compatible(r, other)
    tests["needs"] = {"value": cwhy, "pass": compat}
    same = all(t["pass"] for t in tests.values())
    return {"same": same, "tests": tests, "shared_needs": shared_needs,
            "copy_of_same_text": raw_similarity(r, other) >= S.CLUSTER["forward_similarity"]}


def core_needs(r: Report) -> set[str]:
    """Actionable needs; 'infrastructure' only counts when it is the report's only need (a blocked road mentioned in
    passing should not glue a rescue report to a road report)."""
    n = set(r.need_types or []) & ACTIONABLE
    return n - {"infrastructure"} if len(n) > 1 else n


def is_claim(r: Report) -> bool:
    return bool(r.rumour_signals)


def needs_compatible(a: Report, b: Report) -> tuple[bool, str]:
    if is_claim(a) and is_claim(b):
        return True, "both are spreading claims"
    if is_claim(a) != is_claim(b) and not (core_needs(a) and core_needs(b)):
        return False, "a spreading claim and a first-hand report"
    shared = core_needs(a) & core_needs(b)
    if shared:
        return True, f"shared need: {', '.join(sorted(shared))}"
    return False, f"different needs ({', '.join(sorted(core_needs(a))) or 'none'} vs {', '.join(sorted(core_needs(b))) or 'none'})"


def _actionable(r: Report) -> bool:
    return bool(set(r.need_types or []) & ACTIONABLE) or r.life_safety or bool(r.rumour_signals)


def cluster(db: Session, r: Report) -> Incident | None:
    if r.status == "blocked":
        return None
    refutes = is_refutation(r)
    if not _actionable(r) and not refutes:
        r.cluster_evidence = {"decision": "situational information", "why": "no actionable need, life-safety signal or claim"}
        return None
    window = S.CLUSTER["time_window_h"]
    if _contains(r.raw_text, L.RESOLVED):     # "all 12 safe": an update on an older incident, so look further back
        window = 24.0
    cands = db.scalars(select(Incident).where(Incident.last_report_at >= r.received_at - window, Incident.status != "resolved"))
    best, best_ev = None, None
    for inc in cands:
        members = db.scalars(select(Report).where(Report.incident_id == inc.id, Report.id != r.id)).all()
        for m in members:
            ev = match_score(r, m)
            if ev["same"] and (best_ev is None or ev["tests"]["similarity"]["value"] > best_ev["tests"]["similarity"]["value"]):
                best, best_ev = inc, {**ev, "matched_report": m.ref}
    if best is None and refutes:
        # a correction joins the claim it corrects if it is about the same place, even with lower text similarity
        scored = []
        for inc in db.scalars(select(Incident).where(Incident.last_report_at >= r.received_at - window)):
            if inc.zone_id and inc.zone_id == r.zone_id and _claims(db, inc):
                ms = db.scalars(select(Report).where(Report.incident_id == inc.id)).all()
                scored.append((max(similarity(r, m) for m in ms), inc))
        if scored:
            sim, best = max(scored, key=lambda x: x[0])
            best_ev = {"same": True, "reason": f"a correction about a claim in the same zone (similarity {sim:.2f})"}
    if best is None:
        if refutes and not _actionable(r):
            r.cluster_evidence = {"decision": "correction with no matching claim", "why": "kept as situational information"}
            return None
        best = Incident(title="", category="other", lat=r.lat, lng=r.lng, area_name=r.location_text, zone_id=r.zone_id,
                        first_report_at=r.received_at, last_report_at=r.received_at)
        db.add(best)
        db.flush()
        best_ev = {"decision": "new incident", "why": "no open incident passed all three tests (similarity, distance, time)"}
    else:
        best_ev = {"decision": "joined incident", **best_ev}
    r.incident_id = best.id
    r.cluster_evidence = best_ev
    best.last_report_at = max(best.last_report_at, r.received_at)
    if best.lat is None and r.lat is not None:
        best.lat, best.lng, best.area_name, best.zone_id = r.lat, r.lng, r.location_text, r.zone_id
    db.flush()
    return best


def _claims(db: Session, inc: Incident) -> bool:
    return any(m.rumour_signals for m in db.scalars(select(Report).where(Report.incident_id == inc.id)))


# ---------- independence: forwards count once ----------
def independent_sources(reports: list[Report], sources: dict[int, Source]) -> list[dict]:
    """Group reports into independent sources: same source id, or a forward/near-copy of an earlier report's text."""
    groups: list[dict] = []
    for r in sorted(reports, key=lambda x: x.received_at):
        if is_refutation(r):
            continue
        src = sources.get(r.source_id)
        joined = None
        for g in groups:
            if r.source_id in g["source_ids"]:
                joined = g
                break
            if any(s["signal"] == "forward_chain" for s in r.rumour_signals or []) and g["forward_chain"]:
                joined = g
                break
            if any(raw_similarity(r, x) >= S.CLUSTER["forward_similarity"] for x in g["reports"]):
                joined = g
                break
        if joined:
            joined["reports"].append(r)
            joined["source_ids"].add(r.source_id)
            joined["copies"] += 1
        else:
            groups.append({"reports": [r], "source_ids": {r.source_id}, "copies": 0,
                           "forward_chain": any(s["signal"] == "forward_chain" for s in r.rumour_signals or []),
                           "type": src.type if src else "anonymous", "reliability": src.reliability_score if src else 0.3,
                           "name": src.name if src else "unknown"})
    return groups


# ---------- confidence ----------
def score(db: Session, inc: Incident) -> Incident:
    reports = db.scalars(select(Report).where(Report.incident_id == inc.id)).all()
    sources = {s.id: s for s in db.scalars(select(Source).where(Source.id.in_([r.source_id for r in reports])))}
    groups = independent_sources(reports, sources)
    supporting = [r for r in reports if not is_refutation(r)]
    refuting = [r for r in reports if is_refutation(r)]
    W, P = S.CONFIDENCE_WEIGHTS, S.PENALTIES
    comp: dict[str, dict] = {}

    n = len(groups)
    comp["corroboration"] = {"value": {0: 0.0, 1: 0.2, 2: 0.6, 3: 0.85}.get(n, 1.0),
                             "why": f"{n} independent source(s)" + (f"; {sum(g['copies'] for g in groups)} forward/copy merged" if any(g["copies"] for g in groups) else "")}
    best = max(groups, key=lambda g: g["reliability"], default=None)
    comp["reliability"] = {"value": round(best["reliability"], 2) if best else 0.0,
                           "why": f"best source: {best['name']} ({best['type']}, {best['reliability']:.2f})" if best else "no supporting source"}

    z = db.get(Zone, inc.zone_id) if inc.zone_id else None
    hz = hazard.zone_hazard(db, z) if z else None
    point_in = hz is not None and inc.lat is not None and geo.in_any(inc.lat, inc.lng, hazard.flood_polygons(db))
    if hz is None:
        cons, cwhy = 0.3, "no location to check against sensors"
    elif point_in or hz["in_flood_extent"]:
        cons, cwhy = 1.0, "inside the current satellite flood extent"
    elif hz["river_above_danger"]:
        cons, cwhy = 0.8, f"river above danger mark ({hz['river']['station']})"
    elif hz["heavy_rain"]:
        cons, cwhy = 0.6, f"heavy rain: {hz['rain_mm_24h']} mm in 24 h"
    else:
        cons, cwhy = 0.3, "no sensor signal for this zone yet"
    official_contradiction = None
    if any("dam" in (r.translated_text_en or r.raw_text).lower() or "ಅಣೆಕಟ್ಟು" in r.raw_text or "बांध" in r.raw_text for r in supporting):
        dam = db.scalars(select(Signal).where(Signal.type == "dam").order_by(Signal.observed_at.desc())).first()
        if dam and dam.value.get("structure") == "safe":
            cons, cwhy = 0.0, f"{dam.value.get('dam')} dam bulletin says the structure is safe"
            official_contradiction = f"official dam bulletin ({dam.source})"
    comp["sensor_consistency"] = {"value": cons, "why": cwhy}

    strong = [g for g in groups if g["type"] in ("field_team", "official_agency", "sensor")]
    medium = [g for g in groups if g["type"] in ("volunteer", "ngo")]
    comp["official_or_field"] = {"value": 1.0 if strong else 0.5 if medium else 0.0,
                                 "why": f"supported by {strong[0]['name']}" if strong else f"supported by {medium[0]['name']}" if medium else "no field team or official report yet"}
    geo_ok = max((r.geocode_confidence for r in supporting), default=0)
    plaus = 0.5 * geo_ok + 0.25 * (1.0 if all(r.received_at >= 0 for r in supporting) else 0) + 0.25 * (1.0 if inc.zone_id else 0)
    comp["plausibility"] = {"value": round(plaus, 2), "why": f"place found in gazetteer ({geo_ok:.0%}); time after event start; zone {'known' if inc.zone_id else 'unknown'}"}
    spec = max(((0.35 if r.people_count else 0) + (0.35 if r.location_text else 0) + (0.3 if set(r.need_types or []) & ACTIONABLE else 0)) for r in supporting) if supporting else 0
    comp["specificity"] = {"value": round(spec, 2), "why": "people count, place and concrete need" if spec >= 0.99 else "some details missing"}
    media = [r.media_meta for r in supporting if r.media_meta]
    if not media:
        mval, mwhy = 0.5, "no media (neutral)"
    elif any(str(m.get("taken_at", ""))[:4].isdigit() and int(str(m["taken_at"])[:4]) < 2026 for m in media):
        mval, mwhy = 0.0, "photo EXIF date is from before this event"
    else:
        mval, mwhy = 1.0, "photo EXIF time and GPS consistent (reverse-image search: not connected)"
    comp["media"] = {"value": mval, "why": mwhy}

    positive = sum(W[k] * comp[k]["value"] for k in W)
    penalties = []
    credible_refuters = []
    for r in refuting:
        s = sources.get(r.source_id)
        if s and s.reliability_score >= S.CREDIBLE_CONTRADICTOR:
            credible_refuters.append((r, s))
    if official_contradiction:
        credible_refuters.append((None, None))
    if credible_refuters:
        pen = min(P["contradiction_max"], P["contradiction"] * len(credible_refuters))
        who = ", ".join(s.name for _, s in credible_refuters if s) or ""
        penalties.append({"name": "contradiction", "value": -pen, "why": f"contradicted by {', '.join(x for x in [who, official_contradiction] if x)}"})
    signals = {s["signal"] for r in supporting for s in (r.rumour_signals or [])}
    for sig in ("forward_chain", "sensational_claim", "old_media"):
        if sig in signals:
            penalties.append({"name": sig, "value": -P[sig], "why": {"forward_chain": "spread as a forward ('share to all')",
                                                                    "sensational_claim": "catastrophic claim without detail",
                                                                    "old_media": "recycled photo"}[sig]})
    total = max(0.0, min(1.0, positive + sum(p["value"] for p in penalties)))

    if inc.official_status == "confirmed":
        level, lwhy = "verified", "confirmed by a person"
    elif inc.official_status == "refuted":
        level, lwhy = "false", "refuted by a person"
    elif credible_refuters:
        strong_ref = official_contradiction or any(s.type in ("official_agency", "field_team", "volunteer") for _, s in credible_refuters if s)
        level = "false" if strong_ref and total < 0.3 and signals & {"forward_chain", "sensational_claim", "old_media"} else "disputed"
        lwhy = "credible contradiction" + (" + rumour signals, low score" if level == "false" else "")
    else:
        level = next(name for th, name in S.LEVELS if total >= th)
        lwhy = f"score {total:.2f}"

    inc.confidence_score = round(total, 3)
    inc.confidence_level = level
    inc.confidence_breakdown = {"components": {k: {**v, "weight": W[k], "points": round(W[k] * v["value"], 3)} for k, v in comp.items()},
                                "penalties": penalties, "total": round(total, 3), "level": level, "level_reason": lwhy,
                                "independent_sources": [{"name": g["name"], "type": g["type"], "reports": [x.ref for x in g["reports"]],
                                                         "copies_merged": g["copies"]} for g in groups],
                                "contradicting_reports": [r.ref for r, _ in credible_refuters if r]}
    # incident summary fields
    needs = [n for r in supporting for n in (r.need_types or []) if n != "other"]
    cat = next((c for c in CATEGORY_ORDER if c in needs), "other")
    inc.category = {"missing_contact": "other"}.get(cat, cat)
    inc.need_types = sorted(set(needs)) or ["other"]
    inc.people_affected = max((r.people_count or 0 for r in supporting), default=0)
    inc.vulnerable_groups = sorted({v for r in supporting for v in (r.vulnerable_groups or [])})
    inc.life_safety = any(r.life_safety for r in supporting)
    place = inc.area_name or (z.name if z else "location unknown")
    label = "Missing contact" if cat == "missing_contact" else cat.capitalize()
    inc.title = f"{label} · {place}" + (f" · {inc.people_affected} people" if inc.people_affected else "")
    inc.fast_verify = inc.life_safety and level in ("unverified", "disputed") and inc.official_status is None
    inc.updated_at = inc.updated_at
    db.flush()
    return inc


def run(db: Session, st: dict) -> dict:
    touched: dict[int, Incident] = {}
    for rid in st.get("report_ids", []):
        r = db.get(Report, rid)
        if r.zone_id and not r.missing_contact and r.status != "blocked":
            z = db.get(Zone, r.zone_id)
            z.last_report_at = max(z.last_report_at or 0, r.received_at)
        old = r.incident_id
        if old:  # re-run after a clarification: re-cluster from scratch
            r.incident_id = None
            db.flush()
            if db.get(Incident, old):
                touched[old] = db.get(Incident, old)
        inc = cluster(db, r)
        if inc:
            touched[inc.id] = inc
    for inc in touched.values():
        if db.scalar(select(Report.id).where(Report.incident_id == inc.id).limit(1)) is None:
            db.delete(inc)
            continue
        score(db, inc)
        emit("incident", row(inc))
    db.flush()
    ids = [i for i in touched if db.get(Incident, i)]
    if ids:
        state.audit(db, "trust", "incidents_scored",
                    "; ".join(f"#{i.id} {i.confidence_level} {i.confidence_score:.2f}" for i in touched.values() if db.get(Incident, i.id)),
                    outputs={"incident_ids": ids}, push=False)
    return {"incident_ids": ids, "summary": f"{len(ids)} incident(s) clustered and scored"}


# ---------- people's decisions ----------
def verify(db: Session, inc: Incident, decision: str, who: str, note: str | None) -> Incident:
    """A person confirms or refutes an incident; every source's track record is updated."""
    inc.official_status = "confirmed" if decision == "confirm" else "refuted"
    inc.verification_note = note
    reports = db.scalars(select(Report).where(Report.incident_id == inc.id)).all()
    for r in reports:
        s = db.get(Source, r.source_id) if r.source_id else None
        if not s:
            continue
        supported = not is_refutation(r)
        right = supported == (decision == "confirm")
        if right:
            s.reports_confirmed += 1
        else:
            s.reports_refuted += 1
        from app.sim.seed import TIER_RELIABILITY
        prior, k = TIER_RELIABILITY.get(s.type, 0.5), S.RELIABILITY_PRIOR_WEIGHT
        s.reliability_score = round((prior * k + s.reports_confirmed) / (k + s.reports_confirmed + s.reports_refuted), 3)
    score(db, inc)
    state.audit(db, who, f"incident_{inc.official_status}", f"#{inc.id} {inc.title}: {note or ''}", actor_type="human",
                object_type="incident", object_id=inc.id)
    emit("incident", row(inc))
    return inc
