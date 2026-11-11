"""Coordination Agent — "Who goes where, with what, and did it arrive?"
1. Greedy allocation plan: shelter shortages first (they are forecast and certain), then incidents by priority. Each
   line takes the nearest depot that is reachable over open roads and still has stock and a free vehicle after the
   lines before it; quantities are reserved inside the plan so nothing is promised twice.
2. Every line carries a plain-language reason and its evidence (report refs, confidence, forecast).
3. Plans go to a person (pending_approval). Nothing is dispatched without approval; approve / edit / reject.
4. Approval creates dispatches: depot stock is decremented and tracked in transit; teams and vehicles are taken.
5. Closed loop: delivered -> confirmation request SMS in the recipient's language; YES/NO reply, field-team update or
   shelter check-in confirms; stock moves from in-transit to consumed; overdue and unconfirmed deliveries escalate."""
import math

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.common import row
from app.core import state
from app.i18n import lexicon as L
from app.i18n.templates import render
from app.models import Approval, Depot, Dispatch, Incident, InventoryItem, Plan, Report, Shelter, Source, Zone
from app.services import alerts, routing
from app.services import scoring as S
from app.sim.kodagu_world import UNITS
from app.ws.manager import emit

PLANNABLE = ("verified", "likely")
CREW = {"rescue": 4, "medical": 3, "default": 2}


# ---------------- planning ----------------
def _depot_pool(db: Session) -> dict[int, dict[str, float]]:
    """Fresh stock per depot (stale rows excluded), as a mutable reservation pool for one plan."""
    now = state.now(db)
    pool: dict[int, dict[str, float]] = {}
    for i in db.scalars(select(InventoryItem).where(InventoryItem.location_type == "depot")):
        if now - i.last_updated_at <= S.STALE_STOCK_H:
            pool.setdefault(i.location_id, {})[i.resource_type] = i.quantity
    return pool


def _covered_incidents(db: Session) -> set[int]:
    """Incidents already served by an active dispatch."""
    return {d.incident_id for d in db.scalars(select(Dispatch).where(Dispatch.status.in_(["pending", "dispatched", "in_transit", "delivered", "confirmed"]))) if d.incident_id}


def _covered_shelters(db: Session) -> set[tuple[int, str]]:
    out = set()
    for d in db.scalars(select(Dispatch).where(Dispatch.to_type == "shelter", Dispatch.status.in_(["dispatched", "in_transit", "delivered"]))):
        for line in d.resource_lines:
            out.add((d.to_id, line["resource_type"]))
    return out


def _pick_depot(db: Session, pool: dict, zone: Zone, wants: dict[str, float], crew: int) -> tuple[Depot | None, dict | None, str]:
    tried = []
    for d in db.scalars(select(Depot)):
        dz = db.get(Zone, d.zone_id)
        r = routing.route(db, dz.code, zone.code)
        if not r:
            tried.append(f"{d.name}: no open road")
            continue
        p = pool.get(d.id, {})
        if p.get("vehicles", 0) < 1 or p.get("volunteers", 0) < crew:
            tried.append(f"{d.name}: no free vehicle/crew")
            continue
        if not any(p.get(k, 0) > 0 for k in wants):
            tried.append(f"{d.name}: no stock of {', '.join(wants)}")
            continue
        tried.append((r["km"], d, r))
    options = sorted([t for t in tried if isinstance(t, tuple)], key=lambda t: t[0])
    if not options:
        return None, None, "; ".join(t for t in tried if isinstance(t, str))
    _, d, r = options[0]
    return d, r, f"nearest reachable depot with stock and a free team ({r['km']} km)"


def _take(pool: dict, depot_id: int, wants: dict[str, float]) -> tuple[list[dict], dict]:
    lines, short = [], {}
    p = pool.setdefault(depot_id, {})
    for rt, q in wants.items():
        have = p.get(rt, 0)
        give = min(have, q)
        if rt in ("boats",):
            give = math.floor(give)
        if give > 0:
            p[rt] = have - give
            lines.append({"resource_type": rt, "quantity": round(give), "unit": UNITS.get(rt, "")})
        if give < q:
            short[rt] = round(q - give)
    return lines, short


def build_plan(db: Session, trigger: str) -> Plan:
    from app.agents import resource
    analysis = resource.analyse(db)
    pool = _depot_pool(db)
    covered_inc, covered_sh = _covered_incidents(db), _covered_shelters(db)
    assignments, unmet = [], []
    n = 0

    def add(target: dict, wants: dict, crew: int, zone: Zone, why: str, evidence: dict, priority: float):
        nonlocal n
        d, r, how = _pick_depot(db, pool, zone, wants, crew)
        if not d:
            unmet.append({**target, "wants": wants, "why": f"no depot can serve it: {how}", "evidence": evidence})
            return
        lines, short = _take(pool, d.id, wants)
        pool[d.id]["vehicles"] -= 1
        pool[d.id]["volunteers"] -= crew
        n += 1
        end = [target["lat"], target["lng"]]
        assignments.append({
            "line": n, **target, "from_depot_id": d.id, "from_depot": d.name, "resources": lines, "team": f"{d.name.split()[0]} team {n} ({crew} volunteers, 1 vehicle)",
            "crew": crew, "km": r["km"], "eta_h": r["eta_h"], "route_zones": r["zones"], "route_points": [[d.lat, d.lng], *r["points"][1:-1], end] if len(r["points"]) > 1 else [[d.lat, d.lng], end],
            "priority": round(priority, 1), "reason": f"{why}; {how}" + (f"; short by {', '.join(f'{v} {k}' for k, v in short.items())}" if short else ""),
            "evidence": evidence})
        if short:
            unmet.append({**target, "wants": short, "why": "partially covered: depot stock ran out", "evidence": evidence})

    # 1. shelter shortages (forecast)
    for t in analysis["transfers"]:
        if (t["shelter_id"], t["resource_type"]) in covered_sh or t["needed_for_48h"] <= 0:
            continue
        s = db.get(Shelter, t["shelter_id"])
        z = db.get(Zone, s.zone_id)
        add({"kind": "shelter", "shelter_id": s.id, "incident_id": None, "to_name": s.name, "lat": s.lat, "lng": s.lng},
            {t["resource_type"]: t["needed_for_48h"]}, CREW["default"], z,
            f"{t['resource_type'].replace('_', ' ')} at {s.name} runs out in ~{t['hours_left']:.0f} h; top up for 48 h",
            {"forecast": {"hours_left": t["hours_left"], "rate_per_h": t["rate_per_h"], "quantity": t["quantity"]}, "alert": f"shortage:projected:{s.id}:{t['resource_type']}"},
            90.0)
    # 2. incidents by priority
    incs = db.scalars(select(Incident).where(Incident.status.in_(["open", "planned"])).order_by(Incident.priority_score.desc())).all()
    for inc in incs:
        if inc.id in covered_inc or inc.confidence_level in ("false", "disputed") or inc.zone_id is None:
            continue
        if inc.confidence_level not in PLANNABLE and not (inc.life_safety and inc.confidence_level == "unverified"):
            continue
        wants = resource.incident_demand(inc)
        if inc.life_safety and inc.confidence_level == "unverified":
            wants = {**{k: max(1, round(v * 0.5)) for k, v in wants.items()}, "medical_kits": max(1, wants.get("medical_kits", 0))}
        if not wants:
            continue
        z = db.get(Zone, inc.zone_id)
        crew = CREW.get(inc.category, CREW["default"])
        refs = [r.ref for r in db.scalars(select(Report).where(Report.incident_id == inc.id).order_by(Report.received_at))]
        why = f"#{inc.id} {inc.title}: priority {inc.priority_score:.0f}, {inc.confidence_level}" + (
            " — verify on arrival (Fast Verify)" if inc.confidence_level == "unverified" else "")
        add({"kind": "incident", "incident_id": inc.id, "shelter_id": None, "to_name": inc.title, "lat": inc.lat, "lng": inc.lng},
            wants, crew, z, why, {"reports": refs, "confidence": inc.confidence_level, "confidence_score": inc.confidence_score,
                                  "priority": inc.priority_score}, inc.priority_score)
    version = (db.scalar(select(func.max(Plan.version))) or 0) + 1
    for old in db.scalars(select(Plan).where(Plan.status == "pending_approval")):
        old.status = "superseded"
    traced = sum(1 for a in assignments if a["evidence"].get("reports") or a["evidence"].get("forecast"))
    rationale = (f"Plan v{version} — trigger: {trigger}. {len(assignments)} deliveries: shelter shortages first (forecast), then incidents "
                 f"by priority. Each line uses the nearest depot reachable over open roads that still has stock and a free team after "
                 f"the lines above it. {len(unmet)} need(s) cannot be fully met"
                 + (": " + "; ".join(f"{u['to_name']} ({u['why']})" for u in unmet[:4]) if unmet else "") + ". "
                 f"{traced}/{len(assignments)} lines link to evidence. Nothing moves until a person approves.")
    plan = Plan(version=version, status="pending_approval", trigger=trigger, rationale=rationale,
                assignments=assignments + [{**u, "target_kind": u.get("kind"), "kind": "unmet"} for u in unmet], created_at_sim=state.now(db))
    db.add(plan)
    db.flush()
    state.audit(db, "coordination", "plan_proposed", f"v{version}: {len(assignments)} deliveries, {len(unmet)} unmet ({trigger})",
                object_type="plan", object_id=plan.id, outputs={"assignments": len(assignments), "unmet": len(unmet)})
    emit("plan", row(plan))
    return plan


# ---------------- human decisions ----------------
def approve(db: Session, plan: Plan, who: str, comment: str | None) -> list[Dispatch]:
    if plan.status != "pending_approval":
        raise ValueError(f"plan v{plan.version} is {plan.status}, not pending approval")
    now = state.now(db)
    plan.status = "approved"
    db.add(Approval(plan_id=plan.id, approver_name=who, decision="approved", comment=comment))
    out = []
    for a in plan.assignments:
        if a.get("kind") == "unmet":
            continue
        d = Dispatch(plan_id=plan.id, incident_id=a.get("incident_id"), from_depot_id=a["from_depot_id"],
                     to_type="shelter" if a["kind"] == "shelter" else "incident", to_id=a.get("shelter_id") or a.get("incident_id"),
                     to_lat=a["lat"], to_lng=a["lng"], to_name=a["to_name"], resource_lines=a["resources"], assigned_team=a["team"],
                     route=a["route_points"], status="dispatched", dispatched_at=now, eta=round(now + a["eta_h"], 2))
        db.add(d)
        db.flush()
        _move_stock(db, d, a.get("crew", 2), "dispatch")
        if d.incident_id:
            inc = db.get(Incident, d.incident_id)
            inc.status = "in_progress"
        out.append(d)
        emit("dispatch", row(d))
    for other in db.scalars(select(Plan).where(Plan.status == "pending_approval", Plan.id != plan.id)):
        other.status = "superseded"
    state.audit(db, who, "plan_approved", f"v{plan.version} approved: {len(out)} dispatches. {comment or ''}", actor_type="human",
                object_type="plan", object_id=plan.id, outputs={"dispatches": [d.id for d in out]})
    emit("plan", row(plan))
    return out


def reject(db: Session, plan: Plan, who: str, comment: str | None) -> Plan:
    plan.status = "rejected"
    db.add(Approval(plan_id=plan.id, approver_name=who, decision="rejected", comment=comment))
    state.audit(db, who, "plan_rejected", f"v{plan.version} rejected: {comment or 'no comment'}", actor_type="human", object_type="plan", object_id=plan.id)
    emit("plan", row(plan))
    return plan


def edit(db: Session, plan: Plan, who: str, remove_lines: list[int], quantities: dict, comment: str | None) -> Plan:
    """The approver edits a plan: drop lines and/or change quantities. Creates the next version, pending approval."""
    lines = []
    for a in plan.assignments:
        if a.get("kind") != "unmet" and a["line"] in remove_lines:
            continue
        a = {**a, "resources": [dict(r) for r in a.get("resources", [])]}
        for r in a.get("resources", []):
            k = f"{a.get('line')}:{r['resource_type']}"
            if k in quantities:
                r["quantity"] = max(0, int(quantities[k]))
        lines.append(a)
    version = (db.scalar(select(func.max(Plan.version))) or 0) + 1
    plan.status = "superseded"
    new = Plan(version=version, status="pending_approval", created_by_agent=f"coordination (edited by {who})", trigger=f"edit of v{plan.version}",
               rationale=f"Edited by {who} from v{plan.version}: removed lines {remove_lines or 'none'}, changed {len(quantities)} quantity(ies). "
                         f"{comment or ''}\n\nOriginal rationale: {plan.rationale}", assignments=lines, created_at_sim=state.now(db))
    db.add(new)
    db.flush()
    db.add(Approval(plan_id=plan.id, approver_name=who, decision="edited", comment=comment))
    state.audit(db, who, "plan_edited", f"v{plan.version} -> v{version}", actor_type="human", object_type="plan", object_id=new.id,
                inputs={"remove_lines": remove_lines, "quantities": quantities})
    emit("plan", row(new))
    return new


# ---------------- stock movement ----------------
def _item(db: Session, loc_type: str, loc_id: int, rt: str) -> InventoryItem:
    i = db.scalar(select(InventoryItem).where(InventoryItem.location_type == loc_type, InventoryItem.location_id == loc_id, InventoryItem.resource_type == rt))
    if not i:
        i = InventoryItem(location_type=loc_type, location_id=loc_id, resource_type=rt, quantity=0, unit=UNITS.get(rt, ""), last_updated_at=0)
        db.add(i)
        db.flush()
    return i


def _move_stock(db: Session, d: Dispatch, crew: int, how: str) -> None:
    """dispatch: depot quantity -> in transit (at destination shelter, or on the depot row for incidents); team taken.
    confirm: in transit -> shelter stock, or consumed for incidents; team back. fail: stock and team back to the depot."""
    now = state.now(db)
    for line in d.resource_lines:
        q, rt = line["quantity"], line["resource_type"]
        src = _item(db, "depot", d.from_depot_id, rt)
        dest = _item(db, "shelter", d.to_id, rt) if d.to_type == "shelter" else src
        if how == "dispatch":
            src.quantity = max(0, src.quantity - q)
            dest.in_transit += q
        elif how == "confirm":
            dest.in_transit = max(0, dest.in_transit - q)
            if d.to_type == "shelter":
                dest.quantity += q
                dest.last_updated_at = now
            else:
                dest.consumed += q
        elif how == "fail":
            dest.in_transit = max(0, dest.in_transit - q)
            src.quantity += q
        src.last_updated_at = now if how != "dispatch" else src.last_updated_at
    for rt, q in (("vehicles", 1), ("volunteers", crew)):
        i = _item(db, "depot", d.from_depot_id, rt)
        i.quantity = max(0, i.quantity - q) if how == "dispatch" else i.quantity + q
    db.flush()
    emit("inventory", {"dispatch": d.id, "how": how})


# ---------------- tracking and the closed loop ----------------
def _recipient(db: Session, d: Dispatch) -> tuple[str | None, str]:
    """Who confirms: the shelter manager, or the first reporter with a phone (in their language)."""
    if d.to_type == "shelter":
        s = db.get(Shelter, d.to_id)
        src = db.get(Source, s.manager_source_id) if s and s.manager_source_id else None
    else:
        src = None
        for r in db.scalars(select(Report).where(Report.incident_id == d.incident_id).order_by(Report.received_at)):
            cand = db.get(Source, r.source_id) if r.source_id else None
            if cand and cand.phone_hash and cand.type in ("citizen", "volunteer"):
                src = cand
                break
    return (src.phone_hash, src.preferred_language or "en") if src and src.phone_hash else (None, "en")


def _items_text(d: Dispatch) -> str:
    return ", ".join(f"{l['quantity']} {l['resource_type'].replace('_', ' ')}" for l in d.resource_lines)


def mark_delivered(db: Session, d: Dispatch, who: str = "field team") -> Dispatch:
    from app.channels.sms_flow import send
    d.status, d.delivered_at = "delivered", state.now(db)
    h, lang = _recipient(db, d)
    if h:
        d.confirmation_phone_hash, d.confirmation_language = h, lang
        place = d.to_name.split(" · ")[1] if " · " in d.to_name else d.to_name
        send(db, h, render("confirm_request", lang, items=_items_text(d), place=place), "confirmation_request", lang, dispatch_id=d.id)
    state.audit(db, who, "dispatch_delivered", f"D-{d.id} arrived at {d.to_name}; confirmation requested ({lang})", object_type="dispatch", object_id=d.id)
    emit("dispatch", row(d))
    return d


def confirm(db: Session, d: Dispatch, method: str, who: str) -> Dispatch:
    if d.status == "confirmed":
        return d
    if d.status not in ("delivered", "in_transit", "dispatched"):
        raise ValueError(f"D-{d.id} is {d.status}")
    d.status, d.confirmation_method, d.confirmed_at = "confirmed", method, state.now(db)
    d.overdue = False
    plan = db.get(Plan, d.plan_id)
    crew = next((a.get("crew", 2) for a in plan.assignments if a.get("to_name") == d.to_name), 2) if plan else 2
    _move_stock(db, d, crew, "confirm")
    if d.incident_id and not db.scalar(select(Dispatch.id).where(Dispatch.incident_id == d.incident_id, Dispatch.status != "confirmed").limit(1)):
        db.get(Incident, d.incident_id).status = "resolved"
    alerts.resolve(db, f"overdue:{d.id}", "delivery confirmed", actor="coordination")
    alerts.resolve(db, f"unconfirmed:{d.id}", "delivery confirmed", actor="coordination")
    state.audit(db, who, "dispatch_confirmed", f"D-{d.id} to {d.to_name} confirmed by {method}", actor_type="human" if method != "sms_reply" else "agent",
                object_type="dispatch", object_id=d.id)
    emit("dispatch", row(d))
    return d


def fail(db: Session, d: Dispatch, reason: str, who: str) -> Dispatch:
    d.status = "failed"
    plan = db.get(Plan, d.plan_id)
    crew = next((a.get("crew", 2) for a in plan.assignments if a.get("to_name") == d.to_name), 2) if plan else 2
    _move_stock(db, d, crew, "fail")
    if d.incident_id:
        db.get(Incident, d.incident_id).status = "open"
    alerts.raise_alert(db, type="delivery_overdue", severity="high", key=f"failed:{d.id}", actor="coordination",
                       message=f"Delivery D-{d.id} to {d.to_name} failed: {reason}. Replanning.", related={"dispatch_id": d.id})
    state.audit(db, who, "dispatch_failed", f"D-{d.id}: {reason}", object_type="dispatch", object_id=d.id)
    emit("dispatch", row(d))
    return d


def handle_confirmation_reply(db: Session, phone_hash: str, body: str) -> dict | None:
    """YES / NO (in any supported language) to our 'did you receive it?' SMS."""
    from app.channels.sms_flow import send
    d = db.scalar(select(Dispatch).where(Dispatch.confirmation_phone_hash == phone_hash, Dispatch.status == "delivered").order_by(Dispatch.id.desc()))
    if not d:
        return None
    word = body.strip().lower().strip(".!। ")
    lang = d.confirmation_language or "en"
    if word in {w.lower() for w in L.YES} or any(word.startswith(w.lower()) for w in L.YES if len(w) > 2):
        confirm(db, d, "sms_reply", "recipient (SMS)")
        reply = send(db, phone_hash, render("confirm_thanks", lang, id=d.id), "confirmation_reply", lang, dispatch_id=d.id)
    elif word in {w.lower() for w in L.NO}:
        fail(db, d, "recipient replied NO (not received)", "recipient (SMS)")
        reply = send(db, phone_hash, render("confirm_failed", lang, id=d.id), "confirmation_reply", lang, dispatch_id=d.id)
    else:
        return None
    return {"report": None, "dispatch": row(d), "replies": [reply]}


def confirm_by_checkin(db: Session, s: Shelter) -> list[int]:
    out = []
    for d in db.scalars(select(Dispatch).where(Dispatch.to_type == "shelter", Dispatch.to_id == s.id, Dispatch.status == "delivered")):
        confirm(db, d, "shelter_checkin", f"{s.name} manager")
        out.append(d.id)
    return out


def track(db: Session) -> list[dict]:
    """Time-based progress: dispatched -> in transit -> delivered at ETA; overdue and unconfirmed escalation.
    Returns failure triggers for replanning."""
    now = state.now(db)
    triggers = []
    for d in db.scalars(select(Dispatch).where(Dispatch.status.in_(["dispatched", "in_transit", "delivered"]))):
        if d.status == "dispatched" and now >= (d.dispatched_at or 0) + 0.2:
            d.status = "in_transit"
            emit("dispatch", row(d))
        if d.status == "in_transit":
            blocked = _route_blocked(db, d)
            if blocked:
                fail(db, d, f"route cut: {blocked}", "monitor")
                triggers.append({"key": f"failed:{d.id}", "why": f"D-{d.id} to {d.to_name} failed: route cut ({blocked})"})
                continue
            if now >= (d.eta or 0):
                mark_delivered(db, d, "field team (GPS)")
            elif now > (d.eta or 0) + S.OVERDUE_GRACE_H:
                d.overdue = True
        if d.status in ("dispatched", "in_transit") and now > (d.eta or 0) + S.OVERDUE_GRACE_H:
            d.overdue = True
            alerts.raise_alert(db, type="delivery_overdue", severity="high", key=f"overdue:{d.id}", actor="coordination",
                               message=f"D-{d.id} to {d.to_name} is overdue (ETA T+{d.eta:.1f} h)", related={"dispatch_id": d.id})
        if d.status == "delivered" and now > (d.delivered_at or 0) + S.CONFIRMATION_TIMEOUT_H:
            alerts.raise_alert(db, type="delivery_overdue", severity="medium", key=f"unconfirmed:{d.id}", actor="coordination",
                               message=f"D-{d.id} to {d.to_name} delivered but not confirmed for {now - d.delivered_at:.1f} h: call the recipient",
                               related={"dispatch_id": d.id})
    db.flush()
    return triggers


def _route_blocked(db: Session, d: Dispatch) -> str | None:
    """A dispatch whose path now crosses a closed road cannot arrive."""
    from app.models import Road
    plan = db.get(Plan, d.plan_id)
    a = next((x for x in (plan.assignments if plan else []) if x.get("to_name") == d.to_name and x.get("route_zones")), None)
    if not a:
        return None
    zones = a["route_zones"]
    for x, y in zip(zones, zones[1:]):
        r = db.scalar(select(Road).where(((Road.a == x) & (Road.b == y)) | ((Road.a == y) & (Road.b == x))))
        if r and r.status != "open":
            return f"{r.name} {r.status}"
    return None


def run(db: Session, st: dict) -> dict:
    triggers = st.get("triggers") or []
    if not triggers:
        return {"summary": "no trigger"}
    plan = build_plan(db, "; ".join(t["why"] for t in triggers[:3]) + (f" (+{len(triggers) - 3} more)" if len(triggers) > 3 else ""))
    return {"plan_id": plan.id, "summary": f"plan v{plan.version} proposed"}
