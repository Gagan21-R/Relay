"""Scenario Lab: coverage, launch through the real pipeline, multi-stage disruption -> replanning with a
previous-vs-updated comparison, the full task lifecycle, and the final report. Runs last: it replaces the world."""
from app.sim import lab

OFFICER = {"X-Role": "duty_officer", "X-Actor": "Lab officer"}

ALL_STATES_AND_UTS = {
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh",
    "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha",
    "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir",
    "Ladakh", "Lakshadweep", "Puducherry",
}


def test_coverage_all_states_disasters_and_levels(client):
    d = client.get("/api/lab/scenarios").json()
    assert d["coverage"]["total_with_kodagu"] == 50
    assert set(d["coverage"]["states_and_uts"]) == ALL_STATES_AND_UTS
    assert len(d["coverage"]["by_disaster"]) == 9 and set(d["coverage"]["by_difficulty"]) == {"beginner", "intermediate", "advanced"}
    for s in d["scenarios"]:
        assert s["objectives"] and s["expected"] and s["description"]


def test_released_messages_carry_no_labels():
    for sid, sc in lab.SCENARIOS.items():
        assert all(set(r[4]) == {"origin_zone"} and r[5] is None for r in sc["reports"]), sid


def test_launch_runs_real_pipeline_and_recentres_the_map(client):
    out = client.post("/api/lab/launch", json={"id": "kollam_tsunami", "replay_until": 3.5}).json()
    assert out["world"]["state"] == "Kerala" and out["scenario"]["center"][0] < 10
    reps = client.get("/api/reports?limit=500").json()
    assert {r["original_language"] for r in reps} >= {"ml", "en"}
    assert client.get("/api/disasters").json()["active"] == "tsunami"
    assert len(client.get("/api/hospitals").json()) == 2 and len(client.get("/api/volunteers").json()) == 6
    st = client.get("/api/lab/status").json()
    assert st["current_stage"] == "Onset" and st["counts"]["incidents"] >= 3


def test_stage_disruption_reroutes_with_comparison_and_lifecycle_to_final_report(client):
    client.post("/api/lab/launch", json={"id": "assam_brahmaputra_flood", "replay_until": 3.0})
    plan = next((p for p in client.get("/api/plans").json() if p["status"] == "pending_approval"), None) \
        or client.post("/api/plans", json={"reason": "lab test"}, headers=OFFICER).json()
    tasks = client.post(f"/api/plans/{plan['id']}/approve", json={"comment": "lab"}, headers=OFFICER).json()["dispatches"]
    assert tasks
    # stage 2 (T+4): a citizen reports the hub road blocked (unverified) -> caution closure -> reroute triggers -> new plan
    client.post("/api/sim/clock", json={"action": "step", "hours": 3.0})
    roads = {r["code"]: r for r in client.get("/api/roads/conditions").json()}
    hub = lab.SCENARIOS["assam_brahmaputra_flood"]["events"][0][2]["road"]
    assert roads[hub]["status"] == "blocked" and not roads[hub]["verified"]
    plans = client.get("/api/plans").json()
    newest = max(plans, key=lambda p: p["version"])
    assert newest["version"] > plan["version"] and "changes" in newest
    if newest["status"] == "pending_approval":
        assert newest["changes"]["note"].startswith("Every line needs Duty Officer approval")
        client.post(f"/api/plans/{newest['id']}/approve", json={}, headers=OFFICER)
    live = [d for d in client.get("/api/dispatches").json() if d["status"] == "assigned"]
    if live:
        client.post(f"/api/plans/{live[0]['plan_id']}/dispatch-all", json={"verify_routes": True}, headers=OFFICER)
    client.post("/api/sim/clock", json={"action": "step", "hours": 3.0})
    delivered = [d for d in client.get("/api/dispatches").json() if d["status"] == "delivered"]
    for d in delivered[:2]:
        assert client.post(f"/api/dispatches/{d['id']}/confirm", json={"method": "field_team"}, headers=OFFICER).json()["status"] == "confirmed"
    rep = client.get("/api/lab/report").json()
    assert rep["synthetic"] and rep["decisions"] and rep["objectives"]
    assert any(o["objective"] == "do not act on the rumour" for o in rep["objectives"])
    assert {"successes", "failures", "unresolved"} <= set(rep)


def test_reset_restarts_the_same_scenario(client):
    out = client.post("/api/lab/reset").json()
    assert out["scenario"] == "assam_brahmaputra_flood" and out["clock"] == 0.0
    client.post("/api/lab/launch", json={"id": "kodagu_flood", "replay_until": 12.0})      # leave the default world behind
