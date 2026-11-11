"""Run Demo: the 12-step story from the RELAY deck, executed on the live system (real agents, real state).
Each call runs one step and returns its caption. Steps 7 (plan) and 12 (recon) wait for a person to approve; calling
them again after approval continues."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import coordination, rumour
from app.channels.sms_flow import handle_inbound
from app.core import state
from app.models import Dispatch, Incident, Plan, ReconTask, Report, Shelter, Source, Zone
from app.sim import engine
from app.sim.seed_sources import source_key_map

STEPS = [
    (1, "Reports arrive", "Web, social and SMS reports arrive in several languages and scripts.", "/feed"),
    (2, "Duplicates grouped", "A Kannada SMS and an English post about Karadigodu merge into one incident.", "/incidents"),
    (3, "Rumour marked false, correction broadcast", "'Harangi dam has burst' is contradicted by the dam bulletin; a correction goes out in every language.", "/alerts"),
    (4, "Urgent requests prioritised", "The Triage agent ranks incidents with visible reasons.", "/incidents"),
    (5, "Resource shortage detected", "Water at Napoklu camp is forecast to run out.", "/resources"),
    (6, "Allocation plan recommended", "The Coordination agent proposes deliveries with reasons and evidence.", "/plans"),
    (7, "Human approves", "Nothing moves until a person approves the plan.", "/plans"),
    (8, "Dispatch tracked on the map", "Trucks leave depots and move along open roads.", "/"),
    (9, "Delivery confirmed by SMS: ಹೌದು", "The Napoklu camp manager replies YES in Kannada; stock moves from in-transit to delivered.", "/dispatch"),
    (10, "Internet down — only SMS and voice get through", "Kushalnagar loses internet: web and social stop, SMS still arrives; a silent zone raises a blackout alert.", "/phone"),
    (11, "Shelter inaccessible → replan", "Flood water covers the roads to Siddapura camp; RELAY proposes a new plan for approval.", "/plans"),
    (12, "The village with no phones", "Hattihole sent nothing. RELAY ranks it top of the silent zones, proposes a recon team with supplies; after approval a satellite-phone report turns it into normal incidents.", "/blackout"),
]


def info() -> list[dict]:
    return [{"n": n, "title": t, "what": w, "page": p} for n, t, w, p in STEPS]


def _incident_with(db: Session, text_start: str) -> Incident | None:
    r = db.scalar(select(Report).where(Report.raw_text.like(text_start + "%")).order_by(Report.id))
    return db.get(Incident, r.incident_id) if r and r.incident_id else None


def run_step(db: Session, n: int, who: str = "Duty officer") -> dict:
    out = {"n": n, "title": STEPS[n - 1][1], "page": STEPS[n - 1][3], "status": "done", "lines": []}
    L = out["lines"]
    if n == 1:
        engine.start_scenario(db, "kodagu_flood", replay_until=0.0, fresh=True)
        engine.advance_to(db, 2.4)
        reps = db.scalars(select(Report)).all()
        langs = sorted({r.original_language for r in reps if r.original_language})
        chans = sorted({r.channel for r in reps})
        L += [f"T+{state.now(db):.1f} h: {len(reps)} reports arrived over {', '.join(chans)}", f"Languages detected: {', '.join(langs)}"]
        L += [f"“{r.raw_text[:70]}” → {r.original_language}/{r.script}" for r in reps if r.original_language != "en"][:3]
    elif n == 2:
        engine.advance_to(db, 5.2)
        inc = _incident_with(db, "ಕರಡಿಗೋಡು ಗ್ರಾಮದಲ್ಲಿ 30")
        if inc:
            reps = db.scalars(select(Report).where(Report.incident_id == inc.id)).all()
            L += [f"Incident #{inc.id}: {inc.title}", f"{len(reps)} reports in {', '.join(sorted({r.original_language for r in reps}))} grouped — one incident, not {len(reps)}",
                  "Forwards and copies count once; the people count is the max, never the sum"]
            out["focus"] = {"incident_id": inc.id}
    elif n == 3:
        engine.advance_to(db, 6.2)
        inc = _incident_with(db, "ಹಾರಂಗಿ ಅಣೆಕಟ್ಟು ಒಡೆದಿದೆ")
        if inc:
            if inc.confidence_level != "false":
                from app.agents import trust
                trust.verify(db, inc, "refute", who, "dam bulletin: structure safe")
            res = rumour.publish(db, inc, who)
            L += [f"'{inc.title}' scored {inc.confidence_score:.0%}: {inc.confidence_breakdown.get('level_reason')}"]
            L += [f"{k}: {res['translations'][k]}" for k in ("kn", "hi", "en")]
            L += [f"Correction sent in {len(res['translations'])} languages, {res['sms_sent']} SMS"]
    elif n == 4:
        top = db.scalars(select(Incident).where(Incident.status != "resolved").order_by(Incident.priority_score.desc()).limit(4)).all()
        L += [f"{i.priority_score:.0f}/100 · {i.title} · {i.confidence_level} — {i.priority_breakdown['components']['life_threat']['why']}" for i in top]
        fv = db.scalars(select(Incident).where(Incident.fast_verify.is_(True))).all()
        L += [f"Fast Verify (never discarded): {', '.join(i.title for i in fv) or 'none'}"]
    elif n == 5:
        from app.agents import resource
        a = resource.analyse(db)
        for t in a["transfers"]:
            L.append(f"{t['resource_type'].replace('_', ' ')} at {t['shelter']}: runs out in ~{t['hours_left']:.0f} h → {t['why']}")
        for c in a["current"]:
            L.append(f"Current gap: {c['resource_type']} demand {c['demand']} > supply {c['supply']}")
        if not a["transfers"]:
            L.append("No projected shortage yet")
    elif n == 6:
        p = db.scalar(select(Plan).where(Plan.status == "pending_approval")) or coordination.build_plan(db, "demo: plan requested")
        lines = [a for a in p.assignments if a.get("kind") != "unmet"]
        L += [f"Plan v{p.version}: {len(lines)} deliveries"] + [f"#{a['line']} {a['from_depot']} → {a['to_name']} ({a['reason'][:80]})" for a in lines[:4]]
        out["focus"] = {"plan_id": p.id}
    elif n == 7:
        approved = db.scalar(select(Plan).where(Plan.status == "approved").order_by(Plan.id.desc()))
        pend = db.scalar(select(Plan).where(Plan.status == "pending_approval"))
        if not approved:
            out.update(status="waiting_for_approval", focus={"plan_id": pend.id if pend else None})
            L.append(f"Plan v{pend.version if pend else '?'} is waiting for your approval. Approve it to continue.")
        else:
            n_d = db.scalar(select(Dispatch.id).where(Dispatch.plan_id == approved.id).limit(1))
            L.append(f"Plan v{approved.version} approved by a person; dispatches created" + ("" if n_d else " (none)"))
    elif n == 8:
        engine.advance_to(db, state.now(db) + 0.6)
        ds = db.scalars(select(Dispatch)).all()
        by = {}
        for d in ds:
            by[d.status] = by.get(d.status, 0) + 1
        L += [f"T+{state.now(db):.1f} h · dispatches: " + ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in by.items())]
    elif n == 9:
        s = db.scalar(select(Shelter).where(Shelter.name.like("Napoklu%")))
        d = db.scalar(select(Dispatch).where(Dispatch.to_type == "shelter", Dispatch.to_id == s.id).order_by(Dispatch.id.desc()))
        if d:
            if d.status in ("dispatched", "in_transit"):
                coordination.mark_delivered(db, d, "NDRF truck (GPS)")
            phone = "+919845012350"  # Napoklu camp manager (synthetic)
            r = handle_inbound(db, phone, "ಹೌದು")
            db.refresh(d)
            L += [f"RELAY → manager ({d.confirmation_language}): did you receive {', '.join(str(l['quantity']) + ' ' + l['resource_type'] for l in d.resource_lines)}?",
                  "Manager → RELAY: ಹೌದು (yes)", f"D-{d.id} is now {d.status} ({d.confirmation_method}); stock moved to the shelter"]
            if r.get("replies"):
                L.append(f"Reply sent: {r['replies'][0].body}")
        else:
            L.append("No Napoklu delivery in the approved plan")
    elif n == 10:
        engine.what_if(db, "cut_internet", {"zone": "kushalnagar"})
        before = {r.id for r in db.scalars(select(Report))}
        engine.advance_to(db, 9.6)
        new = [r for r in db.scalars(select(Report)) if r.id not in before]
        kz = db.scalar(select(Zone).where(Zone.code == "kushalnagar"))
        blocked = [r for r in new if r.status == "blocked"]
        got = [r for r in new if r.zone_id == kz.id and r.status != "blocked"]
        L += [f"Internet DOWN in Kushalnagar: {len(blocked)} web/social report(s) could not get out",
              f"{len(got)} Kushalnagar report(s) still arrived by " + ", ".join(sorted({r.channel for r in got}) or ["—"])]
        sil = db.scalars(select(Zone).where(Zone.blackout_flag)).all()
        L += [f"Blackout alert: {z.name} silent {z.blackout_breakdown.get('hours_silent')} h, risk {z.blackout_score:.0%}" for z in sil]
    elif n == 11:
        s = db.scalar(select(Shelter).where(Shelter.name.like("Siddapura%")))
        before = db.scalar(select(Plan.version).order_by(Plan.version.desc())) or 0
        changes = engine.what_if(db, "flood_shelter", {"shelter_id": s.id})
        db.refresh(s)
        newp = db.scalar(select(Plan).where(Plan.status == "pending_approval").order_by(Plan.version.desc()))
        L += changes + [f"{s.name}: {s.status} — {s.status_reason}"]
        L.append(f"New plan v{newp.version} awaits approval (trigger: {newp.trigger[:90]})" if newp and newp.version > before else "No new plan")
        out["focus"] = {"plan_id": newp.id if newp else None}
    elif n == 12:
        z = db.scalar(select(Zone).where(Zone.code == "hattihole"))
        if state.now(db) < 9.5:
            engine.advance_to(db, 9.5)
        t = db.scalar(select(ReconTask).where(ReconTask.zone_id == z.id).order_by(ReconTask.id.desc()))
        if t and t.status == "pending_approval":
            r = z.blackout_breakdown or {}
            out.update(status="waiting_for_approval", focus={"recon_id": t.id})
            L += [f"{z.name}: {z.population:,} people, 0 reports, risk {z.blackout_score:.0%} — ranked #1 silent zone",
                  "Why: " + "; ".join(c["why"] for c in r.get("components", {}).values() if c["value"] > 0),
                  f"Proposed: {t.team} carrying " + ", ".join(f"{p['quantity']} {p['resource_type'].replace('_', ' ')}" for p in t.prepositioned),
                  "Approve the recon task to continue."]
        elif t and t.status == "in_progress":
            from app.channels import ingest
            src = db.scalar(select(Source).where(Source.name == "NDRF-2 (satphone)")) or Source(type="field_team", name="NDRF-2 (satphone)", reliability_score=0.85)
            db.add(src)
            db.flush()
            rep = ingest.submit(db, channel="radio_entry", source=src, lat=z.lat, lng=z.lng, adapter=f"recon:{t.id}",
                                text="[satphone · NDRF team 2] Hattihole reached on foot: 40 houses damaged, about 300 people at the temple hall, need food, drinking water and a medical team.")
            db.refresh(t)
            db.refresh(z)
            L += [f"Satellite phone report {rep.ref} logged from inside {z.name}", f"Recon {t.status}; blackout {'resolved' if not z.blackout_flag else 'still flagged'}",
                  f"Village is now incident #{rep.incident_id} in the normal pipeline"]
        else:
            L.append(f"{z.name} is not flagged silent right now")
    db.flush()
    return out


def keys_ok(db: Session) -> bool:
    return "mgr_napoklu" in source_key_map(db)
