"""RELAY evaluation (`make eval` / `python -m eval.run_eval`). Runs on a throwaway SQLite database in mock mode.

EVALUATED ON SYNTHETIC DATA; REAL-WORLD VALIDATION PENDING.
Two sets, reported separately:
  development — the 82 seed reports the rules were built against (expect optimistic numbers);
  held-out    — 30 reports written after tuning and never used to tune (the honest number).
Metrics: duplicate precision/recall (overall + per language), extraction accuracy (zone, need, people; per language),
translation coverage, fake/true confusion matrix, time to a feasible plan, shortage detection rate on injected
shortages, evidence traceability, delivery verification rate."""
import itertools
import json
import os
import statistics
import sys
import tempfile
import time
from pathlib import Path

_tmp = tempfile.mkdtemp(prefix="relay-eval-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/eval.db"
os.environ["RELAY_MOCK_MODE"] = "true"
os.environ["GEMINI_API_KEY"] = ""

from sqlalchemy import select  # noqa: E402

from app.agents import coordination, resource  # noqa: E402
from app.channels import ingest  # noqa: E402
from app.core import state  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.models import Dispatch, Incident, InventoryItem, Plan, Report, Shelter, Zone  # noqa: E402
from app.sim import engine as sim  # noqa: E402
from app.sim import kodagu_reports as KR  # noqa: E402
from app.sim.seed import load_world  # noqa: E402
from app.core.roles import Actor  # noqa: E402
from app.ws.manager import mute  # noqa: E402
from eval import extended as X  # noqa: E402
from eval import heldout  # noqa: E402

OUT = Path(__file__).with_name("results.json")


def pr(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    f = 2 * p * r / (p + r) if p and r else None
    return {"precision": None if p is None else round(p, 3), "recall": None if r is None else round(r, 3), "f1": None if f is None else round(f, 3),
            "tp": tp, "fp": fp, "fn": fn}


def run_set(db, reports: list, label: str) -> dict:
    """Replay a labelled set on a fresh world and score it."""
    sim.reset_world(db)
    sim.start_scenario(db, "kodagu_flood", replay_until=None)
    # signals for context (sensor consistency) but our own report list
    for ev in sim.timeline("kodagu_flood"):
        if ev[1] == "signal":
            sim._release(db, ev)
    truth: dict[int, dict] = {}
    for t, ch, who, text, tr, *_ in sorted(reports, key=lambda r: r[0]):
        state.set_now(db, max(state.now(db), t))
        r = ingest.from_timeline(db, channel=ch, who=who, text=text, received_at=t, media=KR.MEDIA.get(text))
        truth[r.id] = tr
    db.flush()
    reps = {r.id: r for r in db.scalars(select(Report).where(Report.id.in_(list(truth))))}

    # --- duplicates (pairwise) ---
    def pair_scores(filter_lang=None):
        tp = fp = fn = 0
        for a, b in itertools.combinations(truth, 2):
            ra, rb = reps[a], reps[b]
            if filter_lang and filter_lang not in (ra.original_language, rb.original_language):
                continue
            same_t = truth[a]["key"] is not None and truth[a]["key"] == truth[b]["key"]
            same_p = ra.incident_id is not None and ra.incident_id == rb.incident_id
            tp += same_t and same_p
            fp += (not same_t) and same_p
            fn += same_t and not same_p
        return pr(tp, fp, fn)
    langs = sorted({r.original_language for r in reps.values() if r.original_language})
    dup = {"overall": pair_scores(), "per_language": {l: pair_scores(l) for l in langs}}

    # --- extraction ---
    zones = {z.id: z.code for z in db.scalars(select(Zone))}
    rows = []
    for rid, tr in truth.items():
        r = reps[rid]
        rows.append({
            "lang": r.original_language, "script": r.script,
            "zone": None if tr["zone"] is None else zones.get(r.zone_id) == tr["zone"],
            "need": None if tr["need"] == "other" or tr["key"] is None else tr["need"] in (r.need_types or []),
            "people": None if not tr["people"] else (r.people_count is not None and abs(r.people_count - tr["people"]) <= 0.15 * tr["people"]),
            "translated": r.original_language == "en" or r.translation_confidence >= 0.7,
        })

    def acc(field, sub=None, script=None):
        vals = [x[field] for x in rows if x[field] is not None and (sub is None or x["lang"] == sub) and (script is None or x["script"] == script)]
        return {"accuracy": round(sum(vals) / len(vals), 3) if vals else None, "n": len(vals)}
    extraction = {"overall": {f: acc(f) for f in ("zone", "need", "people")},
                  "per_input_type": {t: {f: acc(f, script=t) for f in ("zone", "need", "people")} for t in ("native", "romanized", "mixed")},
                  "per_language": {l: {f: acc(f, l) for f in ("zone", "need", "people", "translated")} for l in langs}}
    coverage = {l: acc("translated", l) for l in langs}

    # --- fake / true (incident level: majority truth of its reports) ---
    cm = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}   # positive = FAKE
    for inc in db.scalars(select(Incident)):
        members = [truth[r.id] for r in db.scalars(select(Report).where(Report.incident_id == inc.id)) if r.id in truth and truth[r.id]["key"]]
        if not members:
            continue
        fake_true = sum(1 for m in members if m["real"] is False) > len(members) / 2
        fake_pred = inc.confidence_level == "false"
        cm["tp" if fake_true and fake_pred else "fn" if fake_true else "fp" if fake_pred else "tn"] += 1
    return {"reports": len(truth), "languages": langs, "duplicates": dup, "extraction": extraction, "translation_coverage": coverage,
            "fake_true_confusion": cm, "fake_detection": pr(cm["tp"], cm["fp"], cm["fn"])}


def ops_metrics(db) -> dict:
    """Plan time, shortage detection, traceability and delivery verification on the seed scenario."""
    sim.reset_world(db)
    sim.start_scenario(db, "kodagu_flood", replay_until=12.0)
    # time to a feasible plan
    times, feasible = [], []
    for _ in range(5):
        t0 = time.perf_counter()
        p = coordination.build_plan(db, "eval timing")
        times.append(time.perf_counter() - t0)
        lines = [a for a in p.assignments if a.get("kind") != "unmet"]
        feasible.append(all(a["route_points"] and all(r["quantity"] >= 0 for r in a["resources"]) for a in lines))
    traced = sum(1 for a in lines if a["evidence"].get("reports") or a["evidence"].get("forecast"))
    # shortage detection on injected shortages: set one item per shelter to ~10 h of stock
    injected = []
    for s, rt in zip(db.scalars(select(Shelter)).all(), ["food_kits", "water_litres", "medical_kits", "water_litres", "food_kits", "water_litres"]):
        burn = {b["resource_type"]: b for b in resource.shelter_burn(db, s)}
        if rt in burn and burn[rt]["rate_per_h"] > 0:
            i = db.scalar(select(InventoryItem).where(InventoryItem.location_type == "shelter", InventoryItem.location_id == s.id, InventoryItem.resource_type == rt))
            i.quantity = round(burn[rt]["rate_per_h"] * 10, 2)
            injected.append((s.id, rt))
    db.flush()
    found = {(p_["shelter_id"], p_["resource_type"]) for p_ in resource.analyse(db)["projected"]}
    detected = sum(1 for x in injected if x in found)
    # delivery verification: approve, run the clock, recipients reply YES where a phone exists, managers check in
    plan = coordination.build_plan(db, "eval delivery")
    officer = Actor("duty_officer", "Eval officer")
    coordination.approve(db, plan, officer, None)
    for d in db.scalars(select(Dispatch).where(Dispatch.plan_id == plan.id, Dispatch.status == "assigned")).all():
        try:
            coordination.verify_route(db, d, officer)
            coordination.dispatch(db, d, officer)
        except coordination.InvalidTransition:
            pass
    for _ in range(12):
        sim.advance_to(db, state.now(db) + 0.5)
    delivered = db.scalars(select(Dispatch).where(Dispatch.status.in_(["delivered", "confirmed"]))).all()
    for d in delivered:
        if d.status == "delivered" and d.confirmation_phone_hash:
            coordination.handle_confirmation_reply(db, d.confirmation_phone_hash, "ಹೌದು" if d.confirmation_language == "kn" else "yes")
    # only a Duty Officer confirms; here the officer confirms tasks that have recipient evidence (SMS YES or check-in)
    for d in db.scalars(select(Dispatch).where(Dispatch.status == "delivered")).all():
        if d.recipient_confirmed_at is not None:
            coordination.confirm(db, d, officer, d.confirmation_method or "sms_reply")
    allds = db.scalars(select(Dispatch).where(Dispatch.plan_id == plan.id)).all()
    reached = [d for d in allds if d.status in ("delivered", "confirmed")]
    confirmed = [d for d in allds if d.status == "confirmed"]
    return {
        "plan_generation_seconds": {"mean": round(statistics.mean(times), 3), "max": round(max(times), 3), "runs": len(times), "all_feasible": all(feasible)},
        "evidence_traceability": {"traced_lines": traced, "lines": len(lines), "rate": round(traced / len(lines), 3) if lines else None},
        "shortage_detection": {"injected": len(injected), "detected": detected, "rate": round(detected / len(injected), 3) if injected else None},
        "delivery_verification": {"dispatched": len(allds), "reached_destination": len(reached), "confirmed": len(confirmed),
                                  "rate_of_reached": round(len(confirmed) / len(reached), 3) if reached else None,
                                  "methods": sorted({d.confirmation_method for d in confirmed if d.confirmation_method}),
                                  "note": "recipient replies are simulated; deliveries without a recipient phone stay unconfirmed until a field team or check-in confirms them"},
    }


def main() -> dict:
    Base.metadata.create_all(engine)
    mute(True)
    t0 = time.perf_counter()
    with SessionLocal() as db:
        load_world(db)
        db.commit()
        from eval.ground_truth import KODAGU
        dev = run_set(db, [(r[0], r[1], r[2], r[3], KODAGU[(r[0], r[3])]) for r in KR.REPORTS], "development")
        db.commit()
        held = run_set(db, heldout.REPORTS, "held-out")
        db.commit()
        ops = ops_metrics(db)
        db.commit()
        alloc = X.allocation_comparison(db)
        db.commit()
        routes = X.route_eval(db)
        db.commit()
        suite = X.scenario_suite(db)
        db.commit()
    probes = X.probe_eval()
    res = {"disclaimer": "Evaluated on synthetic data; real-world validation pending.",
           "generated_in_seconds": round(time.perf_counter() - t0, 1), "mode": "mock (rule-based extraction, local embeddings)",
           "development": dev, "held_out": held, "operations": ops,
           "multilingual_probes": probes, "allocation_policy": alloc, "routes": routes, "scenarios": suite,
           "notes": ["development = the seed reports the rules were built against; held-out = written after tuning, never used to tune",
                     "duplicate metrics are pairwise over report pairs; per-language counts pairs involving that language",
                     "fake/true is incident-level: positive class = fake/rumour"]}
    OUT.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    return res


def _fmt(x):
    return "—" if x is None else f"{x:.2f}" if isinstance(x, float) else str(x)


if __name__ == "__main__":
    r = main()
    print("RELAY evaluation —", r["disclaimer"])
    for name in ("development", "held_out"):
        s = r[name]
        d = s["duplicates"]["overall"]
        e = s["extraction"]["overall"]
        f = s["fake_detection"]
        print(f"\n[{name}] {s['reports']} reports, languages {', '.join(s['languages'])}")
        print(f"  duplicates  P {_fmt(d['precision'])}  R {_fmt(d['recall'])}  F1 {_fmt(d['f1'])}")
        for l, v in s["duplicates"]["per_language"].items():
            print(f"    {l:3s} P {_fmt(v['precision'])}  R {_fmt(v['recall'])}")
        print(f"  extraction  zone {_fmt(e['zone']['accuracy'])}  need {_fmt(e['need']['accuracy'])}  people {_fmt(e['people']['accuracy'])}")
        print(f"  fake/true   {s['fake_true_confusion']}  P {_fmt(f['precision'])}  R {_fmt(f['recall'])}")
    o = r["operations"]
    print(f"\n[operations] plan {o['plan_generation_seconds']['mean']} s (feasible {o['plan_generation_seconds']['all_feasible']}), "
          f"traceability {_fmt(o['evidence_traceability']['rate'])}, shortage detection {o['shortage_detection']['detected']}/{o['shortage_detection']['injected']}, "
          f"delivery verification {o['delivery_verification']['confirmed']}/{o['delivery_verification']['reached_destination']}")
    print(f"\nwritten to {OUT}")
    sys.exit(0)
