"""Extended evaluation sections (enhancement round). Imported by run_eval after it has set up the throwaway database.
EVALUATION ONLY — reads ground truth and scenario design, which operational agents never see."""
import statistics

from sqlalchemy import select

from app.agents import coordination
from app.models import Incident, Plan, Report, Zone
from app.sim import engine as sim


def probe_eval() -> dict:
    """Language detection and need/people/disaster extraction on the developer-written probe set, per language and per
    input type (native / romanized / mixed). The intake agent's rule path in mock mode."""
    from app.agents.intake import rule_extract
    from app.disasters import detect as detect_disaster
    from app.i18n.detect import detect
    from app.i18n.languages import LANGUAGES
    from eval.multilingual_probe import PROBES
    rows = []
    for lang, kind, text, need, people, dis in PROBES:
        d = detect(text)
        f, _ = rule_extract(text)
        rows.append({"lang": lang, "type": kind, "lang_ok": d.language == lang, "need_ok": need in f["need_types"],
                     "people_ok": None if people is None else f["people_count"] == people,
                     "disaster_ok": None if dis is None else detect_disaster(text)[0] == dis, "text": text,
                     "got": {"language": d.language, "needs": f["need_types"], "people": f["people_count"]}})

    def agg(sel):
        out = {"n": len(sel)}
        for k in ("lang_ok", "need_ok", "people_ok", "disaster_ok"):
            v = [r[k] for r in sel if r[k] is not None]
            out[k.replace("_ok", "")] = {"accuracy": round(sum(v) / len(v), 3) if v else None, "n": len(v)}
        return out
    langs = sorted({r["lang"] for r in rows})
    return {"overall": agg(rows),
            "per_language": {l: {**agg([r for r in rows if r["lang"] == l]), "support": LANGUAGES[l]["support"]} for l in langs},
            "per_input_type": {t: agg([r for r in rows if r["type"] == t]) for t in ("native", "romanized", "mixed")},
            "errors": [{"lang": r["lang"], "type": r["type"], "text": r["text"], "got": r["got"]} for r in rows
                       if not (r["lang_ok"] and r["need_ok"] and r["people_ok"] is not False)],
            "not_evaluated": sorted(set(LANGUAGES) - set(langs)),
            "note": f"{len(rows)} developer-written probes (not native speakers), 2-6 per language: indicative only, NOT validated accuracy."}


def allocation_comparison(db) -> dict:
    """Verified-only policy (RELAY: verified/likely + unverified life-safety checks) vs acting on ALL reports, on the
    Kodagu scenario at T+12, scored against ground truth (incident truth = majority of its reports' labels)."""
    from eval.ground_truth import KODAGU
    sim.reset_world(db)
    sim.start_scenario(db, "kodagu_flood", replay_until=12.0)
    truth_of = {}
    for inc in db.scalars(select(Incident)):
        labs = [KODAGU.get((r.received_at, r.raw_text)) for r in db.scalars(select(Report).where(Report.incident_id == inc.id))]
        labs = [x for x in labs if x and x["key"]]
        truth_of[inc.id] = None if not labs else sum(1 for x in labs if x["real"] is False) <= len(labs) / 2

    def score(plan):
        lines = [a for a in plan.assignments if a.get("kind") == "incident"]
        to_false = [a for a in lines if truth_of.get(a["incident_id"]) is False]
        to_real = [a for a in lines if truth_of.get(a["incident_id"]) is True]

        def units(ls):
            return sum(r["quantity"] for a in ls for r in a["resources"] if r["resource_type"] != "water_litres")
        return {"incident_lines": len(lines), "lines_to_real_incidents": len(to_real), "lines_to_false_incidents": len(to_false),
                "kit_units_to_false": units(to_false), "kit_units_total": units(lines),
                "unmet_lines": sum(1 for a in plan.assignments if a.get("kind") == "unmet")}
    verified = score(coordination.build_plan(db, "eval: verified-only policy"))
    old = coordination.PLANNABLE
    orig = [(i.id, i.confidence_level) for i in db.scalars(select(Incident))]
    coordination.PLANNABLE = ("verified", "likely", "unverified")
    try:
        for i in db.scalars(select(Incident)):       # 'all reports' baseline: every incident counts, rumours included
            if i.confidence_level in ("false", "disputed"):
                i.confidence_level = "unverified"
        db.flush()
        allr = score(coordination.build_plan(db, "eval: act on all reports"))
    finally:
        coordination.PLANNABLE = old
        for iid, lvl in orig:
            db.get(Incident, iid).confidence_level = lvl
        db.flush()
    return {"verified_only": verified, "all_reports": allr,
            "note": "Same world, stock and moment; only the plannable-incident policy differs. Synthetic data."}


def route_eval(db) -> dict:
    """Close each Kodagu road in turn (unverified citizen report = simulated disruption) and check every depot->zone
    recommendation: never uses a closed road, unverified roads are never labelled safe, and how often safest != shortest."""
    from app.models import Depot, Road
    from app.services import routing
    sim.reset_world(db)
    sim.start_scenario(db, "kodagu_flood", replay_until=0.0)
    zones = [z.code for z in db.scalars(select(Zone))]
    depots = [db.get(Zone, d.zone_id).code for d in db.scalars(select(Depot))]
    checks = violations = unlabelled = safest_differs = cut_off = 0
    roads = db.scalars(select(Road)).all()
    for r in roads:
        routing.report_road(db, r, "blocked", "eval: simulated closure", "citizen")
        for dz in depots:
            for z in zones:
                res = routing.plan_route(db, dz, z)
                checks += 1
                if not res:
                    cut_off += 1
                    continue
                violations += r.code in res["roads"]
                unlabelled += bool(res["unverified_roads"]) and res["safety"] == "verified passable"
                safest_differs += bool(res.get("shortest"))
        r.status, r.status_verified = "open", True
    db.flush()
    return {"closures_simulated": len(roads), "route_queries": checks, "routes_using_a_closed_road": violations,
            "unverified_routes_labelled_safe": unlabelled, "unreachable_after_closure": cut_off,
            "safest_differs_from_shortest": safest_differs,
            "note": "Deterministic check of the routing rules on the Kodagu road graph; not a real-world ETA validation."}


def scenario_suite(db) -> dict:
    """Replay all 50 scenarios to T+10 through the real pipeline: does each run, how many incidents vs designed
    situations (duplicate merging), and is a rumour ever planned."""
    from app.sim import lab
    from app.sim.scenarios import SCENARIOS
    out, errors = [], []
    for sid in SCENARIOS:
        try:
            sim.start_scenario(db, sid, replay_until=10.0, fresh=True)
        except Exception as e:  # noqa: BLE001
            errors.append({"scenario": sid, "error": str(e)[:160]})
            continue
        script = lab.script(sid)
        situations = len({lb["key"] for *_, lb in script if (lb.get("key") or "").startswith("S")})
        reports = db.scalars(select(Report)).all()
        incs = db.scalars(select(Incident)).all()
        from eval.ground_truth import KODAGU
        labels = {(t, text): lb for t, _, _, text, _, lb in script} if script else KODAGU
        votes: dict[int, list[bool]] = {}
        for r in reports:
            lb = labels.get((r.received_at, r.raw_text))
            if lb and lb.get("key") and r.incident_id:
                votes.setdefault(r.incident_id, []).append(lb["real"] is False)
        rumour_led = {i for i, v in votes.items() if sum(v) > len(v) / 2}
        mixed = sum(1 for v in votes.values() if any(v) and not all(v))
        planned_rumour = any(a.get("incident_id") in rumour_led for p in db.scalars(select(Plan)) for a in p.assignments if a.get("kind") == "incident")
        out.append({"scenario": sid, "disaster": SCENARIOS[sid].get("disaster"), "reports": len(reports), "incidents": len(incs),
                    "situations": situations or None, "plans": len(db.scalars(select(Plan.id)).all()), "rumour_planned": planned_rumour,
                    "incidents_mixing_rumour_and_real": mixed})
    lab_rows = [o for o in out if o["situations"]]
    return {"ran": len(out), "errors": errors, "rumour_ever_planned": sum(o["rumour_planned"] for o in out),
            "incidents_mixing_rumour_and_real": sum(o["incidents_mixing_rumour_and_real"] for o in out),
            "mean_reports_per_incident": round(statistics.mean(o["reports"] / max(1, o["incidents"]) for o in out), 2),
            "lab_incidents_vs_situations": {"mean_incidents": round(statistics.mean(o["incidents"] for o in lab_rows), 2),
                                             "mean_designed_situations": round(statistics.mean(o["situations"] for o in lab_rows), 2),
                                             "note": "incidents also include the rumour, vague and missing-contact messages"} if lab_rows else None,
            "per_scenario": out,
            "note": "Lab messages are template-generated, so this checks workflow behaviour, not language accuracy."}
