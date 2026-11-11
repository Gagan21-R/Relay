"""Guided run: walks a person through ONE scenario, step by step, on the live system, and says where the work is
happening right now. Works for every scenario (Kodagu and all Scenario Lab worlds).

Each step does its work (moves the clock, lets agents act), returns the page where that work shows up and plain-language
lines about what just happened, and either finishes ("done" → the UI moves on by itself) or waits for the Duty Officer
("waiting" → approve a plan, verify routes and dispatch, approve a public message, confirm deliveries). Calling a
waiting step again re-checks it; clock moves happen only once per step. Every action still goes through the same
agents, permissions and audit log as a manual run."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents import coordination
from app.core import state
from app.core.roles import Actor
from app.disasters import profile
from app.models import AgentMessage, AuditLog, Communication, Dispatch, Incident, Plan, Report, Road, Shelter, Signal, Zone
from app.sim import engine
from app.sim.scenarios import SCENARIOS

OFFICER = Actor("duty_officer", "Duty Officer (guided run)")

STEPS = [
    (1, "The disaster begins", "/", "Sensors and satellites report the hazard; the map centres on the affected places."),
    (2, "Reports arrive in many languages", "/feed", "SMS, social posts and field reports arrive in native script, romanized and mixed language."),
    (3, "The agents talk to each other", "/agents", "Intake hands each report to Trust, Trust to Triage; Trust asks Coordination for ground checks."),
    (4, "Duplicates grouped, rumours flagged", "/incidents", "Reports about the same thing become one incident; forwards and sensational claims lose credibility."),
    (5, "Who needs help first", "/incidents", "The Triage agent ranks incidents out of 100, with a reason for every point."),
    (6, "Shortages forecast", "/resources", "The Resource agent compares stock with what shelters and incidents will need."),
    (7, "A plan is proposed — the Duty Officer approves", "/plans", "Coordination negotiates with Resource for stock and checks credibility with Trust, then asks a person."),
    (8, "Volunteers assigned, routes verified, tasks dispatched", "/dispatch", "Ranked volunteers are assigned; a Duty Officer verifies each route before anything moves."),
    (9, "Teams on the move", "/", "Tasks move along their verified routes on the map."),
    (10, "Disruption: the situation changes", "/", "A road is reported blocked or a shelter is cut off; Monitor tells Coordination to re-plan."),
    (11, "Replan: previous vs updated", "/plans", "The new plan shows what changed and why; the Duty Officer approves the change."),
    (12, "Tell people, in their language", "/comms", "A public update is drafted in each language spoken in the area, facts checked, and sent after approval."),
    (13, "Delivered → confirmed by the Duty Officer", "/dispatch", "Teams mark deliveries; recipients reply YES; only the Duty Officer confirms."),
    (14, "Final report", "/lab", "Decisions, successes, failures and what is still unresolved."),
]
TOTAL = len(STEPS)


def info(db: Session) -> dict:
    sc = state.get(db, "scenario", {}) or {}
    return {"scenario": sc, "total": TOTAL, "steps": [{"n": n, "title": t, "page": p, "what": w} for n, t, p, w in STEPS],
            "done": state.get(db, "guide_done", [])}


def start(db: Session, scenario: str | None) -> dict:
    sid = scenario or (state.get(db, "scenario", {}) or {}).get("id", "kodagu_flood")
    engine.start_scenario(db, sid, replay_until=0.0, fresh=True)
    state.put(db, "guide_done", [])
    state.put(db, "guide", {"scenario": sid})
    return info(db)


def _once(db: Session, n: int) -> bool:
    """True the first time a step runs (so it may move the clock)."""
    done = list(state.get(db, "guide_done", []))
    if n in done:
        return False
    state.put(db, "guide_done", done + [n])
    return True


def _latest_pending(db: Session) -> Plan | None:
    return db.scalar(select(Plan).where(Plan.status == "pending_approval").order_by(Plan.version.desc()))


def _msgs(db: Session, topics: tuple, k: int) -> list[str]:
    q = select(AgentMessage).where(AgentMessage.topic.in_(topics)).order_by(AgentMessage.id.desc()).limit(k)
    return [f"{m.sender} → {m.recipient.replace('_', ' ')} ({m.performative}): {m.summary}" for m in db.scalars(q)][::-1]


def run_step(db: Session, n: int) -> dict:
    n = max(1, min(TOTAL, n))
    _, title, page, what = STEPS[n - 1]
    out = {"n": n, "total": TOTAL, "title": title, "page": page, "what": what, "status": "done", "lines": [], "action": None}
    L = out["lines"]
    sc = state.get(db, "scenario", {}) or {}
    spec = SCENARIOS.get(sc.get("id", "kodagu_flood"), {})
    first = _once(db, n)

    if n == 1:
        if first and state.now(db) < 0.6:
            engine.advance_to(db, 0.6)
        prof = profile(state.disaster(db))
        zones = db.scalars(select(Zone)).all()
        L.append(f"{sc.get('name')} · {sc.get('state', '')} · {prof['name']} · {len(zones)} places on the map")
        L += [f"Signal: {s.type.replace('_', ' ')} — {', '.join(f'{k} {v}' for k, v in s.value.items() if not isinstance(v, (list, dict)))}"
              for s in db.scalars(select(Signal).order_by(Signal.id).limit(4))]
        L.append(f"Hazard overlay: {prof['overlay']['label']}. Every report and stock count is synthetic.")
    elif n == 2:
        if first:
            engine.advance_to(db, max(state.now(db), 2.0))
        reps = db.scalars(select(Report)).all()
        langs = sorted({r.original_language for r in reps if r.original_language})
        L.append(f"T+{state.now(db):.1f} h: {len(reps)} reports over {', '.join(sorted({r.channel for r in reps}))}")
        L.append(f"Languages detected: {', '.join(langs)}")
        L += [f"“{r.raw_text[:70]}” → {r.original_language} ({r.script}){' · needs a human check' if (r.extraction or {}).get('needs_human_review') else ''}"
              for r in reps if r.original_language != "en"][:3]
    elif n == 3:
        total = db.scalar(select(func.count()).select_from(AgentMessage)) or 0
        L.append(f"{total} messages between agents so far")
        L += _msgs(db, ("report_ready", "incident_update", "ground_check", "credibility_check"), 5)
    elif n == 4:
        reps = db.scalar(select(func.count()).select_from(Report)) or 0
        incs = db.scalars(select(Incident)).all()
        L.append(f"{reps} reports → {len(incs)} incidents")
        big = max(incs, key=lambda i: db.scalar(select(func.count()).select_from(Report).where(Report.incident_id == i.id)) or 0, default=None)
        if big:
            members = db.scalars(select(Report).where(Report.incident_id == big.id)).all()
            L.append(f"Biggest merge: #{big.id} {big.title} — {len(members)} reports in {', '.join(sorted({m.original_language for m in members}))}")
        rum = [i for i in incs if i.confidence_level in ("disputed", "false") or any(r.rumour_signals for r in db.scalars(select(Report).where(Report.incident_id == i.id)))]
        L += [f"Flagged claim: #{i.id} {i.title} — {i.confidence_level} {i.confidence_score:.0%}" for i in rum[:2]]
        fv = sum(1 for i in incs if i.fast_verify)
        L.append(f"{fv} life-safety incident(s) on Fast Verify (never discarded)")
    elif n == 5:
        top = db.scalars(select(Incident).where(Incident.status != "resolved").order_by(Incident.priority_score.desc()).limit(3)).all()
        L += [f"{i.priority_score:.0f}/100 · {i.title} · {i.confidence_level} — {i.priority_breakdown['components']['life_threat']['why']}" for i in top]
    elif n == 6:
        from app.agents import resource
        a = resource.analyse(db)
        L += [f"{t['resource_type'].replace('_', ' ')} at {t['shelter']}: runs out in ~{t['hours_left']:.0f} h" for t in a["transfers"][:3]]
        L += [f"Gap: {c['resource_type'].replace('_', ' ')} demand {c['demand']} > supply {c['supply']}" for c in a["current"][:3]]
        if len(L) == 0:
            L.append("No shortage forecast yet — stock covers the next day")
    elif n == 7:
        p = _latest_pending(db)
        if p is None and not db.scalar(select(Plan.id).where(Plan.status == "approved").limit(1)):
            p = coordination.build_plan(db, "guided run: plan requested")
        if p is not None:
            lines = [a for a in p.assignments if a.get("kind") != "unmet"]
            neg = sum(1 for a in lines if a.get("evidence", {}).get("negotiated"))
            esc = sum(1 for a in p.assignments if a.get("kind") == "unmet")
            L += [f"Plan v{p.version}: {len(lines)} deliveries ({neg} negotiated with the Resource agent), {esc} need(s) escalated"]
            L += [f"#{a['line']} {a['from_depot']} → {a['to_name']} · {a['safety']} · suggested {(a.get('recommended_volunteer') or {}).get('code', '—')}"
                  for a in lines[:3]]
            L += _msgs(db, ("stock_shortfall",), 2)
            out.update(status="waiting", action={"label": f"Approve plan v{p.version} as Duty Officer", "kind": "approve_plan", "plan_id": p.id},
                       focus={"plan_id": p.id})
        else:
            L.append("Plan approved — tasks created and volunteers assigned")
    elif n == 8:
        waiting = db.scalars(select(Dispatch).where(Dispatch.status.in_(["approved", "assigned"]))).all()
        moving = db.scalars(select(Dispatch).where(Dispatch.status.in_(["dispatched", "delivered", "confirmed"]))).all()
        if waiting:
            L += [f"D-{d.id} → {d.to_name}: {d.status}, {(d.route_info or {}).get('safety')}" for d in waiting[:4]]
            L.append("A Duty Officer must verify each route before dispatch (the backend refuses otherwise: 409)")
            out.update(status="waiting", action={"label": f"Verify {len(waiting)} route(s) and dispatch as Duty Officer", "kind": "dispatch_all"})
        else:
            L.append(f"{len(moving)} task(s) dispatched on verified routes")
    elif n == 9:
        first_event = min([t for t, *_ in spec.get("events", [])] or [99])
        if first:
            engine.advance_to(db, min(state.now(db) + 1.0, max(state.now(db), first_event - 0.1)))
        ds = db.scalars(select(Dispatch).where(Dispatch.status.in_(["dispatched", "delivered"]))).all()
        L.append(f"T+{state.now(db):.1f} h: {len(ds)} task(s) on the move")
        L += [f"D-{d.id} → {d.to_name} · ETA T+{d.eta:.1f} h{' (unreliable)' if not (d.route_info or {}).get('eta_reliable', True) else ''}" for d in ds[:4] if d.eta]
    elif n == 10:
        if first:
            events = sorted(t for t, *_ in spec.get("events", []))
            if events:
                target = next((t for t in events if t > state.now(db)), None)
                engine.advance_to(db, (target + 0.3) if target else state.now(db) + 1.0)
            else:   # hand-built scenario without staged events: a citizen reports the road a task is using blocked
                d = db.scalar(select(Dispatch).where(Dispatch.status.in_(["dispatched", "assigned"])).order_by(Dispatch.id))
                code = ((d.route_info or {}).get("roads") or [None])[0] if d else None
                if code:
                    engine.what_if(db, "close_road", {"road": code, "why": "citizen SMS: road blocked", "source_type": "citizen", "verified": False})
                engine.advance_to(db, state.now(db) + 0.3)
        ev = db.scalars(select(AuditLog).where(AuditLog.action.in_(["stage_event", "whatif_close_road", "whatif_flood_shelter",
                                                                     "whatif_silence_village", "whatif_drop_inventory"])).order_by(AuditLog.id.desc()).limit(3)).all()
        L += [f"T+{a.sim_time:.1f} h — {a.summary}" for a in ev[::-1]]
        L += [f"Road now {r.status}: {r.name} ({r.status_source}{'' if r.status_verified else ', unverified — caution first'})"
              for r in db.scalars(select(Road).where(Road.status != "open")).all()[:3]]
        L += _msgs(db, ("replan",), 2)
    elif n == 11:
        p = _latest_pending(db)
        if p is not None:
            ch = (p.changes or {}).get("changed", [])
            L.append(f"Plan v{p.version}: {len(ch)} line(s) differ from the previous allocation")
            L += [f"#{c['line']} {c['to']}: {c['change']} — why: {c['why']}" for c in ch[:3]]
            out.update(status="waiting", action={"label": f"Approve replan v{p.version} as Duty Officer", "kind": "approve_plan", "plan_id": p.id},
                       focus={"plan_id": p.id})
        else:
            L.append("Replan approved (or nothing needed changing)")
            assigned = db.scalars(select(Dispatch).where(Dispatch.status == "assigned")).all()
            if assigned:
                out.update(status="waiting", action={"label": f"Verify {len(assigned)} new route(s) and dispatch", "kind": "dispatch_all"})
    elif n == 12:
        drafts = db.scalars(select(Communication)).all()
        if not drafts:
            from app.services import comms
            sh = next((s for s in db.scalars(select(Shelter).order_by(Shelter.id)) if s.status == "open"), None) \
                or db.scalars(select(Shelter)).first()
            z = db.get(Zone, sh.zone_id) if sh else None
            drafts = comms.draft(db, "shelter_open", {"area": z.name if z else "the district", "shelter": sh.name if sh else "the nearest camp",
                                                      "phone": "1077"}, None, None, OFFICER.name)
        L += [f"{c.language}: {c.status} · {c.translation_status} · facts {'preserved' if c.fact_check.get('ok') else 'MISSING'}" for c in drafts[:6]]
        if any(c.status in ("draft", "approved") for c in drafts):
            out.update(status="waiting", action={"label": "Approve and send all drafts as Duty Officer (mock SMS)", "kind": "send_comms"})
        else:
            L.append(f"Sent to {sum(c.recipients for c in drafts)} phone(s) (mock SMS)")
    elif n == 13:
        # keep the clock moving until something is delivered; if the situation changes again on the way, stop and ask
        from app.agents.coordination import handle_confirmation_reply
        for _ in range(8):
            if db.scalar(select(Dispatch.id).where(Dispatch.status.in_(["delivered", "confirmed"])).limit(1)):
                break   # something arrived (or was already confirmed): stop the clock so the officer can act
            if _latest_pending(db) or db.scalar(select(Dispatch.id).where(Dispatch.status.in_(["approved", "assigned"])).limit(1)):
                break
            if not db.scalar(select(Dispatch.id).where(Dispatch.status == "dispatched").limit(1)):
                break
            engine.advance_to(db, state.now(db) + 0.5)
        for d in db.scalars(select(Dispatch).where(Dispatch.status == "delivered", Dispatch.recipient_confirmed_at.is_(None),
                                                    Dispatch.confirmation_phone_hash.is_not(None))):
            handle_confirmation_reply(db, d.confirmation_phone_hash, "yes")      # simulated recipient reply
        delivered = db.scalars(select(Dispatch).where(Dispatch.status == "delivered")).all()
        confirmed = db.scalars(select(Dispatch).where(Dispatch.status == "confirmed")).all()
        pending = _latest_pending(db)
        waiting_tasks = db.scalars(select(Dispatch).where(Dispatch.status.in_(["approved", "assigned"]))).all()
        L.append(f"T+{state.now(db):.1f} h: {len(delivered)} delivered (awaiting the officer), {len(confirmed)} confirmed")
        L += [f"D-{d.id} → {d.to_name}: delivered{' · recipient said YES (evidence, not confirmation)' if d.recipient_confirmed_at else ''}"
              for d in delivered[:4]]
        if delivered:
            out.update(status="waiting", action={"label": f"Confirm {len(delivered)} delivery(ies) as Duty Officer", "kind": "confirm_all"})
        elif pending or waiting_tasks:
            L.append("The situation changed again on the way: " + (f"plan v{pending.version} re-routes around it" if pending else "new tasks wait for dispatch"))
            L += _msgs(db, ("replan",), 1)
            out.update(status="waiting", page="/plans" if pending else "/dispatch",
                       action={"label": "Approve the new plan, verify routes and dispatch as Duty Officer", "kind": "approve_and_dispatch",
                               "plan_id": pending.id if pending else None})
        elif not confirmed:
            L.append("No task could reach its destination: every route is cut. See the unmet needs in the final report.")
    elif n == 14:
        from app.api.lab import report
        r = report(db)
        L.append(f"{len(r['decisions'])} human decisions · {len(r['successes'])} successes · {len(r['failures'])} failures · {len(r['unresolved'])} unresolved")
        L += [f"✔ {x}" for x in r["successes"][:2]] + [f"✖ {x}" for x in r["failures"][:2]] + [f"… {x}" for x in r["unresolved"][:2]]
        L.append("Open the final report on the Scenario Lab page for the full list.")
    db.flush()
    return out


def act(db: Session, n: int, kind: str, plan_id: int | None = None) -> dict:
    """The Duty Officer action a waiting step asks for, done through the normal lifecycle functions."""
    if kind == "approve_plan" and plan_id:
        coordination.approve(db, db.get(Plan, plan_id), OFFICER, "approved during the guided run")
    elif kind == "approve_and_dispatch":
        if plan_id and db.get(Plan, plan_id).status == "pending_approval":
            coordination.approve(db, db.get(Plan, plan_id), OFFICER, "approved during the guided run")
        act(db, n, "dispatch_all")
    elif kind == "dispatch_all":
        for d in db.scalars(select(Dispatch).where(Dispatch.status.in_(["approved", "assigned"])).order_by(Dispatch.id)).all():
            try:
                if d.status == "approved":
                    coordination.assign(db, d, OFFICER)
                if not (d.route_info or {}).get("verified"):
                    coordination.verify_route(db, d, OFFICER, "checked during the guided run")
                coordination.dispatch(db, d, OFFICER)
            except coordination.InvalidTransition:
                pass
    elif kind == "send_comms":
        from app.services import comms
        for c in db.scalars(select(Communication).where(Communication.status.in_(["draft", "approved"]))).all():
            try:
                if c.status == "draft":
                    comms.approve(db, c, OFFICER.name)
                comms.send(db, c, OFFICER.name)
            except ValueError:
                pass
    elif kind == "confirm_all":
        for d in db.scalars(select(Dispatch).where(Dispatch.status == "delivered")).all():
            coordination.confirm(db, d, OFFICER, "sms_reply" if d.recipient_confirmed_at else "officer_review")
    db.flush()
    return run_step(db, n)
