"""Agents talk to each other (and the replies change outcomes); the guided run walks a whole scenario; boats use flooded
roads. Runs last: it replaces the world."""
OFFICER = {"X-Role": "duty_officer", "X-Actor": "Test officer"}


def _msgs(client, **q):
    qs = "&".join(f"{k}={v}" for k, v in q.items())
    return client.get(f"/api/agents/messages?limit=2000&{qs}").json()


def test_report_handoffs_between_agents(client):
    client.post("/api/lab/launch", json={"id": "kodagu_flood", "replay_until": 3.0})
    ms = _msgs(client)
    pairs = {(m["sender"], m["recipient"], m["topic"]) for m in ms}
    assert ("intake", "trust", "report_ready") in pairs          # Intake hands every report to Trust
    assert ("trust", "triage", "incident_update") in pairs       # Trust tells Triage which incident it joined
    assert ("triage", "monitor", "priorities") in pairs          # Triage tells Monitor the new ranking
    summary = client.get("/api/agents/summary").json()
    assert summary["total"] == len(ms) and summary["edges"]


def test_coordination_and_resource_negotiate_and_the_offer_changes_the_plan(client):
    client.post("/api/lab/launch", json={"id": "kodagu_flood", "replay_until": 12.0})
    asks = _msgs(client, topic="stock_shortfall")
    assert any(m["sender"] == "coordination" and m["recipient"] == "resource" and m["performative"] == "request" for m in asks)
    offers = [m for m in asks if m["performative"] == "propose"]
    accepts = [m for m in asks if m["performative"] == "accept"]
    escal = [m for m in asks if m["performative"] == "escalate" and m["recipient"] == "duty_officer"]
    assert offers and accepts and escal
    # an accepted offer became a real plan line from a second depot
    plans = client.get("/api/plans").json()
    negotiated = [a for p in plans for a in p["assignments"] if a.get("evidence", {}).get("negotiated")]
    assert negotiated and any("negotiated with the Resource agent" in a["reason"] for a in negotiated)
    # replies thread under their request
    req_ids = {m["id"] for m in asks if m["performative"] == "request"}
    assert all(m["in_reply_to"] in req_ids for m in offers)


def test_trust_and_coordination_talk_about_credibility_and_ground_checks(client):
    gc = _msgs(client, topic="ground_check")
    assert any(m["sender"] == "trust" and m["performative"] == "request" for m in gc)
    assert any(m["sender"] == "coordination" and m["performative"] == "propose" and m["content"].get("volunteer") for m in gc)
    cc = _msgs(client, topic="credibility_check")
    assert any(m["sender"] == "trust" and m["performative"] == "reply" and "plannable" in m["content"] for m in cc)
    rp = _msgs(client, topic="replan")
    assert any(m["sender"] == "monitor" and m["recipient"] == "coordination" for m in rp)
    assert any(m["sender"] == "coordination" and m["content"].get("plan_id") for m in rp)


def test_blackout_asks_resource_for_recon_supplies(client):
    ms = _msgs(client, topic="recon_supplies")
    ask = [m for m in ms if m["sender"] == "blackout" and m["recipient"] == "resource"]
    ans = [m for m in ms if m["sender"] == "resource" and m["performative"] == "propose"]
    assert ask and ans and ans[0]["content"]["prepositioned"]
    recon = client.get("/api/zones/blackout").json()[0]["recon"]
    assert recon["prepositioned"] == ans[-1]["content"]["prepositioned"]                 # the plan uses the reply


def test_guided_run_walks_every_step_and_waits_for_the_officer(client):
    info = client.post("/api/lab/guide/start", json={"scenario": "puducherry_cyclone"}).json()
    assert info["total"] == 14 and len(info["steps"]) == 14 and info["scenario"]["id"] == "puducherry_cyclone"
    pages = []
    for n in range(1, 15):
        r = client.post(f"/api/lab/guide/step/{n}").json()
        pages.append(r["page"])
        guard = 0
        while r["status"] == "waiting" and guard < 6:
            assert client.post(f"/api/lab/guide/act/{n}", json={"kind": r["action"]["kind"], "plan_id": r["action"].get("plan_id")},
                               headers={"X-Role": "volunteer", "X-Actor": "V-001"}).status_code == 403   # only an officer acts
            r = client.post(f"/api/lab/guide/act/{n}", json={"kind": r["action"]["kind"], "plan_id": r["action"].get("plan_id")},
                            headers=OFFICER).json()
            guard += 1
        assert r["status"] == "done" and r["lines"], (n, r)
    assert {"/", "/feed", "/agents", "/incidents", "/resources", "/plans", "/dispatch", "/comms", "/lab"} <= set(pages)
    tasks = client.get("/api/dispatches").json()
    assert any(d["status"] == "confirmed" for d in tasks)
    assert all(d["route_verified_by"] for d in tasks if d["status"] in ("dispatched", "delivered", "confirmed"))


def test_boats_cross_flooded_roads_trucks_do_not():
    from app.db import SessionLocal
    from app.models import Road
    from app.services import routing
    with SessionLocal() as db:
        r = db.query(Road).filter(Road.status == "open").first()
        r.status = "flooded"
        db.flush()
        assert not routing._usable(r, "truck") and routing._usable(r, "boat")
        r.status = "blocked"
        assert not routing._usable(r, "boat")
        db.rollback()
