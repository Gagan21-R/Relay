"""Phase 7: allocation plan, approval gate, dispatch + stock, delivery confirmation (SMS YES in Kannada), audit."""
from app.db import SessionLocal
from app.models import Dispatch, InventoryItem, Source
from app.sim.seed_sources import source_key_map


def _pending(client):
    return next(p for p in client.get("/api/plans").json() if p["status"] == "pending_approval")


def test_plan_has_rationale_evidence_and_nothing_is_dispatched_before_approval(client):
    p = _pending(client)
    lines = [a for a in p["assignments"] if a["kind"] != "unmet"]
    assert lines and "Nothing moves until a person approves" in p["rationale"]
    assert all(a["reason"] and (a["evidence"].get("reports") or a["evidence"].get("forecast")) for a in lines)
    assert all(a["route_points"] and a["eta_h"] > 0 for a in lines)
    assert lines[0]["kind"] == "shelter" and "Napoklu" in lines[0]["to_name"]          # forecast shortage first
    assert client.get("/api/dispatches").json() == []


def test_edit_creates_new_version_and_reject_is_recorded(client):
    p = _pending(client)
    first = next(a for a in p["assignments"] if a["kind"] != "unmet")
    new = client.post(f"/api/plans/{p['id']}/edit", json={"remove_lines": [first["line"]], "comment": "drop line 1"}).json()
    assert new["version"] == p["version"] + 1 and new["status"] == "pending_approval"
    assert all(a.get("line") != first["line"] for a in new["assignments"] if a["kind"] != "unmet")
    plans = client.get("/api/plans").json()
    assert next(x for x in plans if x["id"] == p["id"])["status"] == "superseded"
    fresh = client.post("/api/plans", json={"reason": "test: rebuild"}).json()
    assert client.post(f"/api/plans/{new['id']}/approve", json={}).status_code == 409   # superseded by the rebuild
    rej = client.post(f"/api/plans/{fresh['id']}/reject", json={"comment": "not now"}).json()
    assert rej["status"] == "rejected"


OFFICER = {"X-Role": "duty_officer", "X-Actor": "DC Kodagu"}


def test_approval_creates_tasks_assigns_volunteers_and_stock_moves_only_on_dispatch(client):
    p = client.post("/api/plans", json={"reason": "test: approve"}).json()
    line = next(a for a in p["assignments"] if a["kind"] != "unmet")
    assert line["safety"] in ("verified passable", "unverified — verify before dispatch") and line["volunteer_ranking"]
    assert "approved" in line["precedent"]["text"] or "no precedent" in line["precedent"]["text"]
    with SessionLocal() as db:
        before = {(i.resource_type): i.quantity for i in db.query(InventoryItem).filter_by(location_type="depot", location_id=line["from_depot_id"])}
    volunteer = {"X-Role": "volunteer", "X-Actor": "V-001"}
    assert client.post(f"/api/plans/{p['id']}/approve", json={}, headers=volunteer).status_code == 403   # volunteers cannot approve
    out = client.post(f"/api/plans/{p['id']}/approve", json={"comment": "go"}, headers=OFFICER).json()
    assert out["plan"]["status"] == "approved" and out["dispatches"]
    ds = out["dispatches"]
    assert all(d["status"] in ("assigned", "approved") for d in ds) and sum(1 for d in ds if d["volunteer"]) >= min(len(ds), 5)
    ds = [d for d in ds if d["status"] == "assigned"]                         # more tasks than free volunteers stay approved
    assert [h["status"] for h in ds[0]["history"]] == ["created", "approved", "assigned"]
    with SessionLocal() as db:   # approval reserves nothing physically: stock leaves only on dispatch
        mid = {(i.resource_type): i.quantity for i in db.query(InventoryItem).filter_by(location_type="depot", location_id=line["from_depot_id"])}
    assert mid == before
    d0 = next(d for d in ds if d["from_depot_id"] == line["from_depot_id"])
    if not d0["route_info"]["verified"]:
        assert client.post(f"/api/dispatches/{d0['id']}/dispatch", headers=OFFICER).status_code == 409   # route not verified
    assert client.post(f"/api/dispatches/{d0['id']}/verify-route", json={}, headers=volunteer).status_code == 403
    assert client.post(f"/api/dispatches/{d0['id']}/verify-route", json={}, headers=OFFICER).json()["route_info"]["verified"]
    other = "V-009" if d0["volunteer"]["code"] != "V-009" else "V-010"
    assert client.post(f"/api/dispatches/{d0['id']}/dispatch", headers={"X-Role": "volunteer", "X-Actor": other}).status_code == 403
    me = {"X-Role": "volunteer", "X-Actor": d0["volunteer"]["code"]}
    assert client.post(f"/api/dispatches/{d0['id']}/dispatch", headers=me).json()["status"] == "dispatched"   # the assignee may
    with SessionLocal() as db:
        after = {(i.resource_type): i.quantity for i in db.query(InventoryItem).filter_by(location_type="depot", location_id=line["from_depot_id"])}
    r0 = d0["resource_lines"][0]
    assert after[r0["resource_type"]] <= before[r0["resource_type"]] - r0["quantity"]
    assert client.post(f"/api/plans/{p['id']}/approve", json={}, headers=OFFICER).status_code == 409   # cannot approve twice
    assert client.post(f"/api/dispatches/{d0['id']}/confirm", json={}, headers=OFFICER).status_code == 409  # dispatched != delivered
    res = client.post(f"/api/plans/{p['id']}/dispatch-all", json={"verify_routes": True}, headers=OFFICER).json()
    assert res["dispatched"] or res["skipped"] is not None


def test_kannada_yes_is_evidence_and_only_the_officer_confirms(client):
    ds = client.get("/api/dispatches").json()
    shelter = next(d for d in ds if d["to_type"] == "shelter" and d["status"] == "dispatched")
    vol = {"X-Role": "volunteer", "X-Actor": shelter["volunteer"]["code"]}
    assert client.post(f"/api/dispatches/{shelter['id']}/deliver", headers=vol).json()["status"] == "delivered"
    with SessionLocal() as db:
        d = db.get(Dispatch, shelter["id"])
        assert d.status == "delivered" and d.confirmation_language == "kn"      # Napoklu camp manager speaks Kannada
        water_in_transit = db.query(InventoryItem).filter_by(location_type="shelter", location_id=d.to_id, resource_type="water_litres").one().in_transit
        assert water_in_transit > 0
    r = client.post("/api/intake/sms", json={"from": "+919845012350", "body": "ಹೌದು"}).json()
    assert r["kind"] == "confirmation_reply" and r["replies"][0]["language"] == "kn"
    with SessionLocal() as db:
        d = db.get(Dispatch, shelter["id"])
        assert d.status == "delivered" and d.recipient_confirmed_at is not None    # Delivered is not Confirmed
    assert client.post(f"/api/dispatches/{shelter['id']}/confirm", json={}, headers=vol).status_code == 403
    c = client.post(f"/api/dispatches/{shelter['id']}/confirm", json={"method": "sms_reply"}, headers=OFFICER).json()
    assert c["status"] == "confirmed" and [h["status"] for h in c["history"]][-1] == "confirmed"
    with SessionLocal() as db:
        item = db.query(InventoryItem).filter_by(location_type="shelter", location_id=shelter["to_id"], resource_type="water_litres").one()
        assert item.in_transit < water_in_transit
    assert client.post(f"/api/dispatches/{shelter['id']}/confirm", json={}, headers=OFFICER).status_code == 409   # already confirmed
    audit = [a["action"] for a in client.get("/api/audit?limit=300").json()]
    for step in ("plan_proposed", "plan_approved", "task_assigned", "route_verified", "task_dispatched", "dispatch_delivered",
                 "recipient_confirmed_receipt", "dispatch_confirmed"):
        assert step in audit


def test_failure_is_officer_only_and_triggers_alert(client):
    ds = [d for d in client.get("/api/dispatches").json() if d["status"] in ("dispatched", "assigned")]
    a = ds[0]
    assert client.post(f"/api/dispatches/{a['id']}/fail", json={"reason": "boat capsized"}, headers={"X-Role": "viewer"}).status_code == 403
    assert client.post(f"/api/dispatches/{a['id']}/fail", json={"reason": "boat capsized, returned"}, headers=OFFICER).json()["status"] == "failed"
    assert any(x["type"] == "delivery_overdue" and "failed" in x["message"] for x in client.get("/api/alerts?open_only=true").json())
    assert client.post(f"/api/dispatches/{a['id']}/dispatch", headers=OFFICER).status_code == 409    # terminal
