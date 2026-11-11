"""Coordination Agent — "Who goes where, with what, and did it arrive?"
1. Greedy allocation plan (deterministic, no LLM): shelter shortages first (forecast), then incidents by priority. Each
   line takes the depot with the SAFEST reachable route (routing.plan_route: verified roads preferred over the shortest,
   vehicle suitability checked), stock and a free vehicle after the lines before it; quantities are reserved inside the
   plan so nothing is promised twice. Each line carries its reason, evidence, route safety label, alternatives, the
   deterministic volunteer ranking and the factual approval-precedent counts.
2. Replanning compares the new plan with the previous allocation (depot, quantities, route) and says what changed, why,
   and which actions need approval.
3. Task lifecycle, enforced here (Forbidden -> HTTP 403, InvalidTransition -> HTTP 409):
     created -> approved -> assigned -> dispatched -> delivered -> confirmed      (failed / cancelled are terminal)
   approve/assign/verify route/confirm/fail: Duty Officer only. dispatch/deliver: Duty Officer or the assigned volunteer.
   Dispatch needs a route verified by a Duty Officer. Delivered is NOT confirmed: a recipient's SMS "YES" or a shelter
   check-in is recorded as evidence; only a Duty Officer confirms."""
import math

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.common import row
from app.core import state
from app.disasters import UNITS, profile
from app.i18n import lexicon as L
from app.i18n.templates import render
from app.models import Approval, Depot, Dispatch, Incident, InventoryItem, Plan, Report, Shelter, Source, Volunteer, Zone
from app.services import alerts, precedents, routing, volunteers
from app.services import scoring as S
from app.ws.manager import emit

PLANNABLE = ("verified", "likely")
CREW = {"rescue": 4, "medical": 3, "default": 2}
OPEN_STATES = ("created", "approved", "assigned", "dispatched", "delivered")
NEXT = {"created": {"approved", "cancelled"}, "approved": {"assigned", "failed", "cancelled"},
        "assigned": {"assigned", "dispatched", "failed", "cancelled"}, "dispatched": {"delivered", "failed"},
        "delivered": {"confirmed", "failed"}, "confirmed": set(), "failed": set(), "cancelled": set()}


class Forbidden(Exception):
    """The acting role may not do this (HTTP 403)."""


class InvalidTransition(ValueError):
    """The task is not in a state that allows this (HTTP 409)."""


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
    """Incidents already served by a live task."""
    return {d.incident_id for d in db.scalars(select(Dispatch).where(Dispatch.status.in_([*OPEN_STATES, "confirmed"]))) if d.incident_id}


def _covered_shelters(db: Session) -> set[tuple[int, str]]:
    out = set()
    for d in db.scalars(select(Dispatch).where(Dispatch.to_type == "shelter", Dispatch.status.in_(OPEN_STATES))):
        for line in d.resource_lines:
            out.add((d.to_id, line["resource_type"]))
    return out


def _vehicles_for(db: Session, need: str) -> list[str]:
    fleet = [v for v in profile(state.disaster(db))["fleet"] if v in routing.SPEED_KMH]
    order = fleet if need == "rescue" else ["truck", "4x4", *fleet]
    return list(dict.fromkeys([*order, "4x4", "boat"]))


def _pick_depot(db: Session, pool: dict, zone: Zone, wants: dict[str, float], crew: int, need: str) -> tuple[Depot | None, dict | None, str]:
    tried, options = [], []
    for d in db.scalars(select(Depot).order_by(Depot.id)):
        dz = db.get(Zone, d.zone_id)
        p = pool.get(d.id, {})
        if p.get("volunteers", 0) < crew:
            tried.append(f"{d.name}: no free crew")
            continue
        if not any(p.get(k, 0) > 0 for k in wants):
            tried.append(f"{d.name}: no stock of {', '.join(wants)}")
            continue
        usable = [v for v in _vehicles_for(db, need) if p.get("boats" if v == "boat" else "vehicles", 0) >= 1]
        r = routing.plan_route(db, dz.code, zone.code, usable) if usable else None
        if not r:
            tried.append(f"{d.name}: no usable route for {', '.join(usable) or 'any free vehicle'}")
            continue
        safe = r["safety"] == "verified passable"
        options.append(((0 if safe else 1, r["eta_h"], d.id), d, r))
    if not options:
        return None, None, "; ".join(tried)
    _, d, r = sorted(options, key=lambda o: o[0])[0]
    return d, r, f"depot with the safest reachable route ({r['km']} km by {r['vehicle']}, {r['safety']})"


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


def _target_key(a: dict) -> str:
    return f"incident:{a['incident_id']}" if a.get("incident_id") else f"shelter:{a.get('shelter_id')}"


def _dispatch_key(d: Dispatch) -> str:
    return f"incident:{d.incident_id}" if d.incident_id else f"shelter:{d.to_id}"


def compare(db: Session, new_lines: list[dict]) -> dict:
    """Previous allocation (live tasks, else the last plan) vs this plan: what changed, why, what needs approval."""
    from app.models import Road
    prev: dict[str, dict] = {}
    last = db.scalar(select(Plan).where(Plan.status.in_(["approved", "pending_approval", "superseded"])).order_by(Plan.version.desc()))
    for a in (last.assignments if last else []):
        if a.get("kind") != "unmet":
            prev[_target_key(a)] = {"source": f"plan v{last.version}", "depot": a["from_depot"], "roads": a.get("route_roads", []),
                                    "road_names": a.get("route_names", []), "resources": {r["resource_type"]: r["quantity"] for r in a["resources"]}}
    for d in db.scalars(select(Dispatch).where(Dispatch.status.in_(OPEN_STATES))):
        dep = db.get(Depot, d.from_depot_id)
        prev[_dispatch_key(d)] = {"source": f"task D-{d.id} ({d.status})", "dispatch_id": d.id, "status": d.status, "depot": dep.name if dep else "?",
                                  "roads": (d.route_info or {}).get("roads", []), "road_names": (d.route_info or {}).get("road_names", []),
                                  "resources": {r["resource_type"]: r["quantity"] for r in d.resource_lines}}
    closed = {r.code: f"{r.name} {r.status} ({r.status_source}{'' if r.status_verified else ', unverified'})"
              for r in db.scalars(select(Road).where(Road.status != "open"))}
    changes = []
    for a in new_lines:
        p = prev.get(_target_key(a))
        res = {r["resource_type"]: r["quantity"] for r in a["resources"]}
        if not p:
            changes.append({"line": a["line"], "to": a["to_name"], "change": "new", "why": a["reason"], "needs_approval": True})
            continue
        why, what = [], []
        if p["depot"] != a["from_depot"]:
            what.append(f"depot {p['depot']} → {a['from_depot']}")
        if p["roads"] != a.get("route_roads"):
            what.append(f"route {' + '.join(p['road_names']) or 'in-town'} → {' + '.join(a.get('route_names', [])) or 'in-town'}")
            why += [closed[c] for c in p["roads"] if c in closed]
        if p["resources"] != res:
            what.append(f"quantities {p['resources']} → {res}")
        if what:
            changes.append({"line": a["line"], "to": a["to_name"], "change": "; ".join(what), "previous": p["source"],
                            "why": "; ".join(why) or "updated stock, priorities or road conditions", "needs_approval": True,
                            "replaces_dispatch": p.get("dispatch_id")})
    keys = {_target_key(a) for a in new_lines}
    gone = [{"to": k, "previous": v["source"], "change": "no longer in the plan", "needs_approval": True}
            for k, v in prev.items() if k not in keys and not v.get("dispatch_id")]
    return {"changed": changes, "dropped": gone, "closed_roads": list(closed.values()),
            "note": "Every line needs Duty Officer approval; rerouted tasks also need their new route verified before dispatch."}


def build_plan(db: Session, trigger: str) -> Plan:
    from app.agents import resource
    analysis = resource.analyse(db)
    pool = _depot_pool(db)
    covered_inc, covered_sh = _covered_incidents(db), _covered_shelters(db)
    # a not-yet-moving task whose route is now cut is planned again (the old task is cancelled when this plan is approved)
    rerouting = {_dispatch_key(d) for d in db.scalars(select(Dispatch).where(Dispatch.status.in_(["approved", "assigned"])))
                 if (d.route_info or {}).get("stale")}
    assignments, unmet, chosen_vols = [], [], set()
    n = 0

    def make_line(d: Depot, r: dict, lines: list, target: dict, crew: int, need: str, reason: str, evidence: dict, priority: float) -> dict:
        nonlocal n
        vkey = "boats" if r["vehicle"] == "boat" else "vehicles"
        pool[d.id][vkey] = pool[d.id].get(vkey, 0) - 1
        pool[d.id]["volunteers"] = pool[d.id].get("volunteers", 0) - crew
        n += 1
        end = [target["lat"], target["lng"]]
        ranking = volunteers.rank(db, need, target["lat"], target["lng"], r["vehicle"], exclude=chosen_vols)
        top = ranking["ranked"][0] if ranking["ranked"] else None
        if top:
            chosen_vols.add(top["volunteer_id"])
        line = {
            "line": n, **target, "from_depot_id": d.id, "from_depot": d.name, "resources": lines,
            "team": f"{d.name.split()[0]} team {n} ({crew} people, 1 {r['vehicle']})", "crew": crew, "need": need,
            "km": r["km"], "eta_h": r["eta_h"], "eta_reliable": r["eta_reliable"], "vehicle": r["vehicle"],
            "route_zones": r["zones"], "route_roads": r["roads"], "route_names": r["road_names"], "safety": r["safety"],
            "unverified_roads": r["unverified_roads"], "route_why": r["why"], "alternatives": r["alternatives"], "shortest": r["shortest"],
            "route_points": [[d.lat, d.lng], *r["points"][1:-1], end] if len(r["points"]) > 1 else [[d.lat, d.lng], end],
            "priority": round(priority, 1), "reason": reason, "evidence": evidence,
            "recommended_volunteer": top and {k: top[k] for k in ("code", "name", "score", "reasons")},
            "volunteer_ranking": [{k: x[k] for k in ("rank", "code", "name", "score", "reasons")} for x in ranking["ranked"][:3]]}
        line["precedent"] = precedents.lookup(db, precedents.signature(db, line))
        assignments.append(line)
        return line

    def add(target: dict, wants: dict, crew: int, zone: Zone, why: str, evidence: dict, priority: float, need: str):
        d, r, how = _pick_depot(db, pool, zone, wants, crew, need)
        if not d:
            unmet.append({**target, "wants": wants, "why": f"no depot can serve it: {how}", "evidence": evidence})
            return
        lines, short = _take(pool, d.id, wants)
        short_txt = ", ".join(f"{v} {k}" for k, v in short.items())
        make_line(d, r, lines, target, crew, need, f"{why}; {how}" + (f"; short by {short_txt}" if short else ""), evidence, priority)
        if short:
            short = negotiate(target, zone, d, short, need, evidence, priority)
        if short:
            unmet.append({**target, "wants": short, "why": "partially covered: no depot can supply the rest (escalated by the Resource agent)",
                          "evidence": evidence})

    def negotiate(target: dict, zone: Zone, d: Depot, short: dict, need: str, evidence: dict, priority: float) -> dict:
        """Ask the Resource agent for a second source; accept offers the plan can still carry, decline the rest."""
        from app.agents import bus
        key = f"incident:{target['incident_id']}" if target.get("incident_id") else f"shelter:{target.get('shelter_id')}"
        short_txt = ", ".join(f"{v} {k}" for k, v in short.items())
        replies = bus.ask(db, "coordination", "resource", "stock_shortfall",
                          f"For {target['to_name']} I am short of {short_txt} after taking what {d.name} has. Can another depot cover the rest?",
                          {"zone_id": zone.id, "target": target["to_name"], "short": short, "exclude_depot": d.id,
                           "pool": {str(k): v for k, v in pool.items()}, "vehicles": _vehicles_for(db, need)},
                          conversation=f"shortfall:{state.now(db):.2f}:{key}")
        left = dict(short)
        for m in replies:
            if m.performative != "propose":
                continue
            for o in m.content.get("offers", []):
                od = db.get(Depot, o["depot_id"])
                p = pool.get(od.id, {})
                if p.get("volunteers", 0) < CREW["default"]:
                    bus.reply(db, m, "decline", f"{od.name} has the stock but no free crew left in this plan", {"depot_id": od.id})
                    continue
                r2 = routing.plan_route(db, db.get(Zone, od.zone_id).code, zone.code, [o["vehicle"]])
                want = {k: min(v, left.get(k, 0)) for k, v in o["items"].items() if left.get(k, 0) > 0}
                if not r2 or not want:
                    bus.reply(db, m, "decline", f"{od.name}: the route or the need changed since your offer", {"depot_id": od.id})
                    continue
                got, _ = _take(pool, od.id, want)
                for g in got:
                    left[g["resource_type"]] = left.get(g["resource_type"], 0) - g["quantity"]
                left = {k: v for k, v in left.items() if v >= 1}
                ln = make_line(od, r2, got, target, CREW["default"], need,
                               f"second source for {target['to_name']}, negotiated with the Resource agent ({o['km']} km, {o['safety']})",
                               {**evidence, "negotiated": True}, priority)
                got_txt = ", ".join(str(g["quantity"]) + " " + g["resource_type"] for g in got)
                bus.reply(db, m, "accept", f"Accepted: {got_txt} from {od.name} as plan line #{ln['line']}", {"depot_id": od.id, "line": ln["line"]})
        return left

    # 1. shelter shortages (forecast)
    for t in analysis["transfers"]:
        s = db.get(Shelter, t["shelter_id"])
        if t["needed_for_48h"] <= 0 or ((s.id, t["resource_type"]) in covered_sh and f"shelter:{s.id}" not in rerouting):
            continue
        z = db.get(Zone, s.zone_id)
        add({"kind": "shelter", "shelter_id": s.id, "incident_id": None, "to_name": s.name, "lat": s.lat, "lng": s.lng},
            {t["resource_type"]: t["needed_for_48h"]}, CREW["default"], z,
            f"{t['resource_type'].replace('_', ' ')} at {s.name} runs out in ~{t['hours_left']:.0f} h; top up for 48 h",
            {"forecast": {"hours_left": t["hours_left"], "rate_per_h": t["rate_per_h"], "quantity": t["quantity"]}, "alert": f"shortage:projected:{s.id}:{t['resource_type']}"},
            90.0, "water" if t["resource_type"] == "water_litres" else "food")
    # 2. incidents by priority
    incs = db.scalars(select(Incident).where(Incident.status.in_(["open", "planned", "in_progress"])).order_by(Incident.priority_score.desc(), Incident.id)).all()
    for inc in incs:
        if inc.confidence_level in ("false", "disputed") or inc.zone_id is None:
            continue
        if inc.id in covered_inc and f"incident:{inc.id}" not in rerouting:
            continue
        if inc.confidence_level not in PLANNABLE and not (inc.life_safety and inc.confidence_level == "unverified"):
            continue
        if inc.life_safety and inc.confidence_level == "unverified":
            from app.agents import bus
            ans = bus.ask(db, "coordination", "trust", "credibility_check",
                          f"#{inc.id} {inc.title} is unverified but life-safety. Before I put a team on it: is it still credible?",
                          {"incident_id": inc.id}, conversation=f"credibility:{inc.id}:{state.now(db):.1f}")
            if ans and not ans[0].content.get("plannable", True):
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
                                  "priority": inc.priority_score}, inc.priority_score, inc.category)
    changes = compare(db, assignments)
    version = (db.scalar(select(func.max(Plan.version))) or 0) + 1
    for old in db.scalars(select(Plan).where(Plan.status == "pending_approval")):
        old.status = "superseded"
    traced = sum(1 for a in assignments if a["evidence"].get("reports") or a["evidence"].get("forecast"))
    unverified = sum(1 for a in assignments if a["safety"] != "verified passable")
    rationale = (f"Plan v{version} — trigger: {trigger}. {len(assignments)} deliveries: shelter shortages first (forecast), then incidents "
                 f"by priority. Each line uses the depot with the safest reachable route (verified roads preferred over the shortest) "
                 f"that still has stock and a free team after the lines above it. {unverified} route(s) are not verified and must be "
                 f"checked by a Duty Officer before dispatch. {len(unmet)} need(s) cannot be fully met"
                 + (": " + "; ".join(f"{u['to_name']} ({u['why']})" for u in unmet[:4]) if unmet else "") + ". "
                 f"{traced}/{len(assignments)} lines link to evidence. {len(changes['changed'])} line(s) differ from the previous allocation. "
                 "Nothing moves until a person approves.")
    plan = Plan(version=version, status="pending_approval", trigger=trigger, rationale=rationale, changes=changes,
                assignments=assignments + [{**u, "target_kind": u.get("kind"), "kind": "unmet"} for u in unmet], created_at_sim=state.now(db))
    db.add(plan)
    db.flush()
    state.audit(db, "coordination", "plan_proposed", f"v{version}: {len(assignments)} deliveries, {len(unmet)} unmet, "
                f"{len(changes['changed'])} changed ({trigger})", object_type="plan", object_id=plan.id,
                outputs={"assignments": len(assignments), "unmet": len(unmet), "changed": len(changes["changed"])})
    emit("plan", row(plan))
    return plan


# ---------------- task lifecycle ----------------
def _check(d: Dispatch, to: str) -> None:
    if to not in NEXT.get(d.status, set()):
        raise InvalidTransition(f"D-{d.id} is {d.status}: cannot go to {to} (allowed: {', '.join(sorted(NEXT.get(d.status, []))) or 'none'})")


def _officer(actor, action: str) -> None:
    if actor.role != "duty_officer":
        raise Forbidden(f"only a Duty Officer can {action} (acting as {actor.role} {actor.name})")


def _officer_or_assignee(db: Session, d: Dispatch, actor, action: str) -> None:
    if actor.role == "duty_officer":
        return
    v = db.get(Volunteer, d.volunteer_id) if d.volunteer_id else None
    if actor.role == "volunteer" and v and actor.name == v.code:
        return
    raise Forbidden(f"only a Duty Officer or the assigned volunteer ({v.code if v else 'none assigned'}) can {action}"
                    f" (acting as {actor.role} {actor.name})")


def _move(db: Session, d: Dispatch, to: str, actor, note: str | None = None) -> None:
    d.status = to
    d.history = [*(d.history or []), {"status": to, "by": actor.name, "role": actor.role, "at": state.now(db), **({"note": note} if note else {})}]


def approve(db: Session, plan: Plan, actor, comment: str | None, assign_recommended: bool = True) -> list[Dispatch]:
    _officer(actor, "approve a plan")
    if plan.status != "pending_approval":
        raise InvalidTransition(f"plan v{plan.version} is {plan.status}, not pending approval")
    plan.status = "approved"
    db.add(Approval(plan_id=plan.id, approver_name=actor.name, decision="approved", comment=comment))
    precedents.record(db, plan, "approved", actor.name)
    out = []
    for a in plan.assignments:
        if a.get("kind") == "unmet":
            continue
        # a rerouted target: the old, not-yet-moving task is cancelled and replaced by this line
        for old in db.scalars(select(Dispatch).where(Dispatch.status.in_(["created", "approved", "assigned"]), Dispatch.plan_id != plan.id)):
            if _dispatch_key(old) == _target_key(a):
                if old.volunteer_id and old.status == "assigned":
                    v = db.get(Volunteer, old.volunteer_id)
                    v.assigned_tasks = max(0, v.assigned_tasks - 1)
                _move(db, old, "cancelled", actor, f"replaced by plan v{plan.version}")
                emit("dispatch", row(old, {"confirmation_phone_hash"}))
        d = Dispatch(plan_id=plan.id, incident_id=a.get("incident_id"), from_depot_id=a["from_depot_id"],
                     to_type="shelter" if a["kind"] == "shelter" else "incident", to_id=a.get("shelter_id") or a.get("incident_id"),
                     to_lat=a["lat"], to_lng=a["lng"], to_name=a["to_name"], resource_lines=a["resources"], assigned_team=a["team"],
                     route=a["route_points"], status="created", vehicle=a.get("vehicle"), eta=None,
                     route_info={**{k: a.get(k) for k in ("route_zones", "safety", "unverified_roads", "route_why", "alternatives", "shortest",
                                                           "km", "eta_h", "eta_reliable", "vehicle", "crew", "need")},
                                 "roads": a.get("route_roads", []), "road_names": a.get("route_names", []), "verified": False},
                     history=[{"status": "created", "by": "coordination agent", "role": "agent", "at": plan.created_at_sim}])
        db.add(d)
        db.flush()
        _move(db, d, "approved", actor, comment)
        if d.incident_id:
            db.get(Incident, d.incident_id).status = "planned"
        if assign_recommended and a.get("recommended_volunteer"):
            try:
                assign(db, d, actor, a["recommended_volunteer"]["code"])
            except (InvalidTransition, Forbidden):
                try:
                    assign(db, d, actor)          # the recommended person became busy: next best by the same tool
                except (InvalidTransition, Forbidden):
                    pass                          # nobody free: stays approved; the officer assigns by hand
        out.append(d)
        emit("dispatch", row(d, {"confirmation_phone_hash"}))
    for other in db.scalars(select(Plan).where(Plan.status == "pending_approval", Plan.id != plan.id)):
        other.status = "superseded"
    state.audit(db, actor.name, "plan_approved", f"v{plan.version} approved: {len(out)} task(s) "
                f"({sum(1 for d in out if d.status == 'assigned')} assigned). {comment or ''}", actor_type="human",
                object_type="plan", object_id=plan.id, outputs={"dispatches": [d.id for d in out]})
    emit("plan", row(plan))
    return out


def reject(db: Session, plan: Plan, actor, comment: str | None) -> Plan:
    _officer(actor, "reject a plan")
    if plan.status != "pending_approval":
        raise InvalidTransition(f"plan v{plan.version} is {plan.status}")
    plan.status = "rejected"
    db.add(Approval(plan_id=plan.id, approver_name=actor.name, decision="rejected", comment=comment))
    precedents.record(db, plan, "rejected", actor.name)
    state.audit(db, actor.name, "plan_rejected", f"v{plan.version} rejected: {comment or 'no comment'}", actor_type="human", object_type="plan", object_id=plan.id)
    emit("plan", row(plan))
    return plan


def edit(db: Session, plan: Plan, actor, remove_lines: list[int], quantities: dict, comment: str | None) -> Plan:
    """The approver edits a plan: drop lines and/or change quantities. Creates the next version, pending approval."""
    _officer(actor, "edit a plan")
    if plan.status != "pending_approval":
        raise InvalidTransition(f"plan v{plan.version} is {plan.status}")
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
    precedents.record(db, plan, "edited", actor.name, remove_lines)
    version = (db.scalar(select(func.max(Plan.version))) or 0) + 1
    plan.status = "superseded"
    new = Plan(version=version, status="pending_approval", created_by_agent=f"coordination (edited by {actor.name})", trigger=f"edit of v{plan.version}",
               rationale=f"Edited by {actor.name} from v{plan.version}: removed lines {remove_lines or 'none'}, changed {len(quantities)} quantity(ies). "
                         f"{comment or ''}\n\nOriginal rationale: {plan.rationale}", assignments=lines, changes=plan.changes, created_at_sim=state.now(db))
    db.add(new)
    db.flush()
    db.add(Approval(plan_id=plan.id, approver_name=actor.name, decision="edited", comment=comment))
    state.audit(db, actor.name, "plan_edited", f"v{plan.version} -> v{version}", actor_type="human", object_type="plan", object_id=new.id,
                inputs={"remove_lines": remove_lines, "quantities": quantities})
    emit("plan", row(new))
    return new


def assign(db: Session, d: Dispatch, actor, volunteer_code: str | None = None) -> Dispatch:
    _officer(actor, "assign a volunteer")
    _check(d, "assigned")
    info = d.route_info or {}
    ranking = volunteers.rank(db, info.get("need", "food"), d.to_lat, d.to_lng, d.vehicle)
    pick = next((r for r in ranking["ranked"] if r["code"] == volunteer_code), None) if volunteer_code else (ranking["ranked"][0] if ranking["ranked"] else None)
    if not pick:
        raise InvalidTransition(f"volunteer {volunteer_code or '(any)'} is not available for D-{d.id}")
    if d.volunteer_id and d.status == "assigned":
        prev = db.get(Volunteer, d.volunteer_id)
        prev.assigned_tasks = max(0, prev.assigned_tasks - 1)
    v = db.get(Volunteer, pick["volunteer_id"])
    v.assigned_tasks += 1
    d.volunteer_id = v.id
    d.route_info = {**info, "volunteer_ranking": [{k: x[k] for k in ("rank", "code", "name", "score", "reasons")} for x in ranking["ranked"][:5]]}
    _move(db, d, "assigned", actor, f"{v.code} (rank {pick['rank']}, score {pick['score']})")
    state.audit(db, actor.name, "task_assigned", f"D-{d.id} → {v.code} {v.name}: " + "; ".join(pick["reasons"]), actor_type="human",
                object_type="dispatch", object_id=d.id)
    emit("dispatch", row(d, {"confirmation_phone_hash"}))
    return d


def _target_zone(db: Session, d: Dispatch) -> Zone | None:
    if d.to_type == "shelter":
        s = db.get(Shelter, d.to_id)
        return db.get(Zone, s.zone_id) if s else None
    inc = db.get(Incident, d.incident_id) if d.incident_id else None
    return db.get(Zone, inc.zone_id) if inc and inc.zone_id else None


def verify_route(db: Session, d: Dispatch, actor, note: str | None = None) -> Dispatch:
    """A Duty Officer checks the current recommended route (recomputed from road conditions now) and verifies it."""
    _officer(actor, "verify a route")
    if d.status not in ("approved", "assigned"):
        raise InvalidTransition(f"D-{d.id} is {d.status}: routes are verified before dispatch")
    dep = db.get(Depot, d.from_depot_id)
    zone = _target_zone(db, d)
    r = routing.plan_route(db, db.get(Zone, dep.zone_id).code, zone.code, [d.vehicle] if d.vehicle else None) if zone else None
    if not r:
        raise InvalidTransition(f"D-{d.id}: no usable route for a {d.vehicle or 'vehicle'} right now — replan")
    prev = (d.route_info or {}).get("roads")
    d.route = [[dep.lat, dep.lng], *r["points"][1:-1], [d.to_lat, d.to_lng]] if len(r["points"]) > 1 else [[dep.lat, dep.lng], [d.to_lat, d.to_lng]]
    d.route_info = {**(d.route_info or {}), "route_zones": r["zones"], "roads": r["roads"], "road_names": r["road_names"], "safety": r["safety"],
                    "unverified_roads": r["unverified_roads"], "km": r["km"], "eta_h": r["eta_h"], "eta_reliable": r["eta_reliable"],
                    "alternatives": r["alternatives"], "shortest": r["shortest"], "route_why": r["why"], "verified": True, "stale": None,
                    "verified_note": note or (f"route checked by {actor.name}" + (f"; unverified segments accepted after a check: "
                                                                                    f"{', '.join(r['unverified_roads'])}" if r["unverified_roads"] else "")),
                    "previous_roads": prev if prev != r["roads"] else None}
    d.route_verified_by = actor.name
    state.audit(db, actor.name, "route_verified", f"D-{d.id}: {' + '.join(r['road_names']) or 'in-town'} ({r['safety']})", actor_type="human",
                object_type="dispatch", object_id=d.id)
    emit("dispatch", row(d, {"confirmation_phone_hash"}))
    return d


def dispatch(db: Session, d: Dispatch, actor) -> Dispatch:
    _officer_or_assignee(db, d, actor, "dispatch this task")
    _check(d, "dispatched")
    if not d.route_verified_by or not (d.route_info or {}).get("verified"):
        raise InvalidTransition(f"D-{d.id}: route not verified — a Duty Officer must verify the route before dispatch")
    cut = _route_blocked(db, d)
    if cut:
        d.route_info = {**d.route_info, "verified": False, "stale": cut}
        d.route_verified_by = None
        raise InvalidTransition(f"D-{d.id}: the verified route is now cut ({cut}) — verify a new route or replan")
    now = state.now(db)
    _move(db, d, "dispatched", actor)
    d.dispatched_at, d.eta = now, round(now + (d.route_info or {}).get("eta_h", 1.0), 2)
    _move_stock(db, d, (d.route_info or {}).get("crew", 2), "dispatch")
    if d.incident_id:
        db.get(Incident, d.incident_id).status = "in_progress"
    state.audit(db, actor.name, "task_dispatched", f"D-{d.id} → {d.to_name}, ETA T+{d.eta:.1f} h"
                + ("" if (d.route_info or {}).get("eta_reliable") else " (ETA unreliable: unverified roads)"),
                actor_type="human", object_type="dispatch", object_id=d.id)
    emit("dispatch", row(d, {"confirmation_phone_hash"}))
    return d


def mark_delivered(db: Session, d: Dispatch, actor) -> Dispatch:
    from app.channels.sms_flow import send
    _officer_or_assignee(db, d, actor, "mark this delivery")
    _check(d, "delivered")
    _move(db, d, "delivered", actor)
    d.delivered_at = state.now(db)
    h, lang = _recipient(db, d)
    if h:
        d.confirmation_phone_hash, d.confirmation_language = h, lang
        place = d.to_name.split(" · ")[1] if " · " in d.to_name else d.to_name
        send(db, h, render("confirm_request", lang, items=_items_text(d), place=place), "confirmation_request", lang, dispatch_id=d.id)
    state.audit(db, actor.name, "dispatch_delivered", f"D-{d.id} arrived at {d.to_name}; recipient asked to confirm ({lang}); "
                "awaiting Duty Officer confirmation", actor_type="human", object_type="dispatch", object_id=d.id)
    emit("dispatch", row(d, {"confirmation_phone_hash"}))
    return d


def confirm(db: Session, d: Dispatch, actor, method: str = "officer_review", note: str | None = None) -> Dispatch:
    _officer(actor, "confirm a delivery")
    _check(d, "confirmed")
    _move(db, d, "confirmed", actor, note or method)
    d.confirmation_method, d.confirmed_at, d.overdue = method, state.now(db), False
    _move_stock(db, d, (d.route_info or {}).get("crew", 2), "confirm")
    v = db.get(Volunteer, d.volunteer_id) if d.volunteer_id else None
    on_time = d.delivered_at is not None and d.eta is not None and d.delivered_at <= d.eta + S.OVERDUE_GRACE_H
    if v and on_time:
        v.on_time_confirmations += 1
    if d.incident_id and not db.scalar(select(Dispatch.id).where(Dispatch.incident_id == d.incident_id,
                                                                   Dispatch.status.in_(OPEN_STATES)).limit(1)):
        db.get(Incident, d.incident_id).status = "resolved"
    for k in (f"overdue:{d.id}", f"unconfirmed:{d.id}", f"recipient_yes:{d.id}"):
        alerts.resolve(db, k, "delivery confirmed by a Duty Officer", actor=actor.name)
    state.audit(db, actor.name, "dispatch_confirmed", f"D-{d.id} to {d.to_name} confirmed ({method}"
                + (f"; recipient said YES at T+{d.recipient_confirmed_at:.1f} h" if d.recipient_confirmed_at else "") + ")"
                + (f"; {v.code} on time" if v and on_time else ""), actor_type="human", object_type="dispatch", object_id=d.id)
    emit("dispatch", row(d, {"confirmation_phone_hash"}))
    return d


def fail(db: Session, d: Dispatch, reason: str, actor) -> Dispatch:
    if actor.role != "agent":
        _officer(actor, "mark a task failed")
    _check(d, "failed")
    moving = d.status in ("dispatched", "delivered")
    _move(db, d, "failed", actor, reason)
    if moving:
        _move_stock(db, d, (d.route_info or {}).get("crew", 2), "fail")
    if d.incident_id:
        db.get(Incident, d.incident_id).status = "open"
    alerts.raise_alert(db, type="delivery_overdue", severity="high", key=f"failed:{d.id}", actor="coordination",
                       message=f"Task D-{d.id} to {d.to_name} failed: {reason}. Replanning.", related={"dispatch_id": d.id})
    state.audit(db, actor.name, "dispatch_failed", f"D-{d.id}: {reason}", object_type="dispatch", object_id=d.id)
    emit("dispatch", row(d, {"confirmation_phone_hash"}))
    return d


# ---------------- stock movement ----------------
def _item(db: Session, loc_type: str, loc_id: int, rt: str) -> InventoryItem:
    i = db.scalar(select(InventoryItem).where(InventoryItem.location_type == loc_type, InventoryItem.location_id == loc_id, InventoryItem.resource_type == rt))
    if not i:
        i = InventoryItem(location_type=loc_type, location_id=loc_id, resource_type=rt, quantity=0, unit=UNITS.get(rt, ""), last_updated_at=0)
        db.add(i)
        db.flush()
    return i


def _move_stock(db: Session, d: Dispatch, crew: int, how: str) -> None:
    """dispatch: depot quantity -> in transit (at destination shelter, or on the depot row for incidents); team and
    vehicle taken. confirm: in transit -> shelter stock, or consumed for incidents; team back. fail: stock back."""
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
    for rt, q in (("boats" if d.vehicle == "boat" else "vehicles", 1), ("volunteers", crew)):
        i = _item(db, "depot", d.from_depot_id, rt)
        i.quantity = max(0, i.quantity - q) if how == "dispatch" else i.quantity + q
    db.flush()
    emit("inventory", {"dispatch": d.id, "how": how})


# ---------------- tracking and the closed loop ----------------
def _recipient(db: Session, d: Dispatch) -> tuple[str | None, str]:
    """Who is asked to confirm receipt: the shelter manager, or the first reporter with a phone (in their language)."""
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


def record_recipient_yes(db: Session, d: Dispatch, how: str) -> None:
    """Evidence, not confirmation: tell the Duty Officer the task is ready to confirm."""
    d.recipient_confirmed_at = state.now(db)
    d.history = [*(d.history or []), {"status": "recipient_yes", "by": how, "role": "recipient", "at": state.now(db)}]
    alerts.raise_alert(db, type="delivery_overdue", severity="low", key=f"recipient_yes:{d.id}", actor="coordination",
                       message=f"D-{d.id} to {d.to_name}: recipient confirmed receipt ({how}). A Duty Officer can now confirm.",
                       related={"dispatch_id": d.id})
    state.audit(db, how, "recipient_confirmed_receipt", f"D-{d.id} to {d.to_name}", actor_type="human", object_type="dispatch", object_id=d.id)
    emit("dispatch", row(d, {"confirmation_phone_hash"}))


def handle_confirmation_reply(db: Session, phone_hash: str, body: str) -> dict | None:
    """YES / NO (in any supported language) to our 'did you receive it?' SMS. Recorded as evidence for the officer."""
    from app.channels.sms_flow import send
    d = db.scalar(select(Dispatch).where(Dispatch.confirmation_phone_hash == phone_hash, Dispatch.status == "delivered").order_by(Dispatch.id.desc()))
    if not d:
        return None
    word = body.strip().lower().strip(".!। ")
    lang = d.confirmation_language or "en"
    if word in {w.lower() for w in L.YES} or any(word.startswith(w.lower()) for w in L.YES if len(w) > 2):
        record_recipient_yes(db, d, "recipient (SMS)")
        d.confirmation_method = "sms_reply"
        reply = send(db, phone_hash, render("confirm_thanks", lang, id=d.id), "confirmation_reply", lang, dispatch_id=d.id)
    elif word in {w.lower() for w in L.NO}:
        alerts.raise_alert(db, type="delivery_overdue", severity="high", key=f"recipient_no:{d.id}", actor="coordination",
                           message=f"D-{d.id} to {d.to_name}: recipient says NOT received. Check with the team before confirming.",
                           related={"dispatch_id": d.id})
        d.history = [*(d.history or []), {"status": "recipient_no", "by": "recipient (SMS)", "role": "recipient", "at": state.now(db)}]
        reply = send(db, phone_hash, render("confirm_failed", lang, id=d.id), "confirmation_reply", lang, dispatch_id=d.id)
    else:
        return None
    return {"report": None, "dispatch": row(d, {"confirmation_phone_hash"}), "replies": [reply]}


def confirm_by_checkin(db: Session, s: Shelter) -> list[int]:
    out = []
    for d in db.scalars(select(Dispatch).where(Dispatch.to_type == "shelter", Dispatch.to_id == s.id, Dispatch.status == "delivered")):
        if not d.recipient_confirmed_at:
            record_recipient_yes(db, d, f"{s.name} manager check-in")
            d.confirmation_method = d.confirmation_method or "shelter_checkin"
            out.append(d.id)
    return out


class _Agent:
    role, name = "agent", "monitor"


class SimVolunteer:
    """The simulated field app of an assigned volunteer (scenario replay only); it goes through the same permission check."""
    role = "volunteer"

    def __init__(self, code: str):
        self.name = code


def track(db: Session) -> list[dict]:
    """Time-based progress and escalation. Returns failure / reroute triggers for replanning."""
    now = state.now(db)
    triggers = []
    for d in db.scalars(select(Dispatch).where(Dispatch.status.in_(["approved", "assigned"]))):
        cut = _route_blocked(db, d)
        if cut and not (d.route_info or {}).get("stale"):
            d.route_info = {**(d.route_info or {}), "verified": False, "stale": cut}
            d.route_verified_by = None
            emit("dispatch", row(d, {"confirmation_phone_hash"}))
            triggers.append({"key": f"reroute:{d.id}:{cut}", "why": f"D-{d.id} to {d.to_name}: planned route now cut ({cut})"})
    for d in db.scalars(select(Dispatch).where(Dispatch.status.in_(["dispatched", "delivered"]))):
        if d.status == "dispatched":
            blocked = _route_blocked(db, d)
            if blocked:
                fail(db, d, f"route cut: {blocked}", _Agent())
                triggers.append({"key": f"failed:{d.id}", "why": f"D-{d.id} to {d.to_name} failed: route cut ({blocked})"})
                continue
            v = db.get(Volunteer, d.volunteer_id) if d.volunteer_id else None
            if now >= (d.eta or 0) and v:
                mark_delivered(db, d, SimVolunteer(v.code))
            elif now > (d.eta or 0) + S.OVERDUE_GRACE_H:
                d.overdue = True
                alerts.raise_alert(db, type="delivery_overdue", severity="high", key=f"overdue:{d.id}", actor="coordination",
                                   message=f"D-{d.id} to {d.to_name} is overdue (ETA T+{d.eta:.1f} h)", related={"dispatch_id": d.id})
        if d.status == "delivered" and now > (d.delivered_at or 0) + S.CONFIRMATION_TIMEOUT_H:
            alerts.raise_alert(db, type="delivery_overdue", severity="medium", key=f"unconfirmed:{d.id}", actor="coordination",
                               message=f"D-{d.id} to {d.to_name} delivered but not confirmed for {now - d.delivered_at:.1f} h",
                               related={"dispatch_id": d.id})
    db.flush()
    return triggers


def _route_blocked(db: Session, d: Dispatch) -> str | None:
    """A task whose path crosses a closed road cannot arrive."""
    from app.models import Road
    codes = (d.route_info or {}).get("roads") or []
    for r in db.scalars(select(Road).where(Road.code.in_(codes))):
        if r.status != "open" and not (d.vehicle == "boat" and r.status == "flooded"):
            return f"{r.name} {r.status}"
    return None


def run(db: Session, st: dict) -> dict:
    """The Monitoring agent's triggers arrive as a replan request; the answer is a plan proposal for the Duty Officer."""
    from app.agents import bus
    triggers = st.get("triggers") or []
    if not triggers:
        return {"summary": "no trigger"}
    why = "; ".join(t["why"] for t in triggers[:3]) + (f" (+{len(triggers) - 3} more)" if len(triggers) > 3 else "")
    replies = bus.ask(db, "monitor", "coordination", "replan", f"Something changed: {why}. Please re-plan.",
                      {"triggers": [t["key"] for t in triggers], "why": why}, conversation=f"replan:{state.now(db):.2f}")
    pid = next((m.content.get("plan_id") for m in replies if m.content.get("plan_id")), None)
    plan = db.get(Plan, pid) if pid else None
    return {"plan_id": pid, "summary": f"plan v{plan.version} proposed" if plan else "no plan"}


def handle(db: Session, msg) -> list[tuple]:
    """Requests the Coordination agent answers: re-plan (from Monitor) and ground checks (from Trust)."""
    if msg.topic == "replan":
        plan = build_plan(db, msg.content.get("why", "monitor request"))
        lines = [a for a in plan.assignments if a.get("kind") != "unmet"]
        unmet = sum(1 for a in plan.assignments if a.get("kind") == "unmet")
        changed = len((plan.changes or {}).get("changed", []))
        return [("propose", "replan", f"Plan v{plan.version} ready: {len(lines)} deliveries, {changed} changed from before, {unmet} unmet. "
                 "Sending it to the Duty Officer.", {"plan_id": plan.id, "version": plan.version}),
                ("propose", "approval", f"Plan v{plan.version} needs your approval ({len(lines)} deliveries, {changed} changed).",
                 {"_to": "duty_officer", "plan_id": plan.id})]
    if msg.topic == "ground_check":
        c = msg.content
        rk = volunteers.rank(db, "recon", c["lat"], c["lng"])
        top = rk["ranked"][0] if rk["ranked"] else None
        if not top:
            return [("decline", "ground_check", "No volunteer is free right now; keep it on Fast Verify and call the reporter back", {})]
        return [("propose", "ground_check", f"{top['code']} {top['name']} is free and {top['km']} km away (score {top['score']}): "
                 "suggest a ground check. A Duty Officer decides; nothing is assigned yet.",
                 {"incident_id": c["incident_id"], "volunteer": top["code"], "km": top["km"], "reasons": top["reasons"]})]
    return [("decline", msg.topic, f"Coordination agent does not handle '{msg.topic}'", {})]
