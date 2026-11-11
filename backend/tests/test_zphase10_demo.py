"""Phase 10: scenarios, what-if events and the full 12-step Run Demo from a fresh start (re-runnable)."""


def _run_demo(client):
    out = {}
    for n in range(1, 13):
        r = client.post(f"/api/sim/demo/step/{n}", json={}).json()
        if r["status"] == "waiting_for_approval":
            if n == 7:
                client.post(f"/api/plans/{r['focus']['plan_id']}/approve", json={"approver_name": "Test officer"})
            else:
                client.post(f"/api/recon/{r['focus']['recon_id']}/approve", json={"who": "Test officer"})
            r = client.post(f"/api/sim/demo/step/{n}", json={}).json()
        assert r["status"] == "done", (n, r)
        out[n] = r
    return out


def test_run_demo_completes_all_12_steps_and_can_rerun(client):
    for _ in range(2):   # reset and re-run
        s = _run_demo(client)
        assert any("kn" in l for l in s[1]["lines"])
        assert "grouped" in " ".join(s[2]["lines"])
        assert "ಹಾರಂಗಿ" in " ".join(s[3]["lines"])
        assert "runs out" in " ".join(s[5]["lines"])
        assert "approved" in s[7]["lines"][0]
        assert "confirmed" in " ".join(s[9]["lines"]) and "ಹೌದು" in " ".join(s[9]["lines"])
        assert "could not get out" in s[10]["lines"][0] and any("Blackout alert" in l for l in s[10]["lines"])
        assert "inaccessible" in " ".join(s[11]["lines"]) and any("awaits approval" in l for l in s[11]["lines"])
        assert "resolved" in " ".join(s[12]["lines"])


def test_scenarios_differ_and_what_if_events(client):
    sc = client.get("/api/sim/scenarios").json()
    assert {x["id"] for x in sc["scenarios"]} == {"kodagu_flood", "harangi_release", "madikeri_landslides"}
    a = client.post("/api/sim/scenario/start", json={"scenario": "harangi_release", "replay_until": 7}).json()
    flood_a = client.get("/api/state").json()["flood_extent"]
    b = client.post("/api/sim/scenario/start", json={"scenario": "madikeri_landslides", "replay_until": 7}).json()
    flood_b = client.get("/api/state").json()["flood_extent"]
    assert a["released"] != b["released"] and flood_a != flood_b
    r = client.post("/api/sim/event", json={"type": "close_road", "params": {"road": "r_mad_kus"}}).json()
    assert "blocked" in r["changes"][0]
    assert client.post("/api/sim/event", json={"type": "drop_inventory", "params": {"depot_id": 1, "fraction": 0.5}}).status_code == 200
    assert client.post("/api/sim/event", json={"type": "spike_reports", "params": {"count": 4}}).status_code == 200
    r = client.post("/api/sim/event", json={"type": "silence_village", "params": {"zone": "somwarpet"}}).json()
    assert "silenced" in r["changes"][0]
    assert client.post("/api/sim/event", json={"type": "nope"}).status_code == 422
    c = client.post("/api/sim/clock", json={"action": "step", "hours": 1}).json()
    assert c["clock"] >= 8
