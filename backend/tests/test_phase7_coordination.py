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


def test_approval_creates_dispatches_and_moves_stock(client):
    p = client.post("/api/plans", json={"reason": "test: approve"}).json()
    line = next(a for a in p["assignments"] if a["kind"] != "unmet")
    with SessionLocal() as db:
        before = {(i.resource_type): i.quantity for i in db.query(InventoryItem).filter_by(location_type="depot", location_id=line["from_depot_id"])}
    out = client.post(f"/api/plans/{p['id']}/approve", json={"approver_name": "DC Kodagu", "comment": "go"}).json()
    assert out["plan"]["status"] == "approved" and out["dispatches"]
    with SessionLocal() as db:
        after = {(i.resource_type): i.quantity for i in db.query(InventoryItem).filter_by(location_type="depot", location_id=line["from_depot_id"])}
    r0 = line["resources"][0]
    assert after[r0["resource_type"]] <= before[r0["resource_type"]] - r0["quantity"]
    assert after["vehicles"] < before["vehicles"]
    assert client.post(f"/api/plans/{p['id']}/approve", json={}).status_code == 409   # cannot approve twice


def test_kannada_yes_sms_confirms_delivery_and_closes_the_loop(client):
    ds = client.get("/api/dispatches").json()
    shelter = next(d for d in ds if d["to_type"] == "shelter")
    client.patch(f"/api/dispatches/{shelter['id']}", json={"status": "delivered"})
    with SessionLocal() as db:
        d = db.get(Dispatch, shelter["id"])
        assert d.status == "delivered" and d.confirmation_language == "kn"      # Napoklu camp manager speaks Kannada
        mgr = db.get(Source, source_key_map(db)["mgr_napoklu"])
        water_in_transit = db.query(InventoryItem).filter_by(location_type="shelter", location_id=d.to_id, resource_type="water_litres").one().in_transit
        assert water_in_transit > 0
    # the manager's phone (synthetic) replies "ಹೌದು" (yes)
    r = client.post("/api/intake/sms", json={"from": "+919845012350", "body": "ಹೌದು"}).json()
    assert r["kind"] == "confirmation_reply" and r["replies"][0]["language"] == "kn"
    with SessionLocal() as db:
        d = db.get(Dispatch, shelter["id"])
        assert d.status == "confirmed" and d.confirmation_method == "sms_reply"
        item = db.query(InventoryItem).filter_by(location_type="shelter", location_id=d.to_id, resource_type="water_litres").one()
        assert item.in_transit < water_in_transit
    audit = [a["action"] for a in client.get("/api/audit?limit=200").json()]
    for step in ("plan_proposed", "plan_approved", "dispatch_delivered", "dispatch_confirmed"):
        assert step in audit


def test_no_reply_fails_and_field_confirmation_works(client):
    ds = [d for d in client.get("/api/dispatches").json() if d["status"] in ("dispatched", "in_transit")]
    a, b = ds[0], ds[1]
    client.patch(f"/api/dispatches/{a['id']}", json={"status": "failed", "note": "boat capsized, returned"})
    assert next(d for d in client.get("/api/dispatches").json() if d["id"] == a["id"])["status"] == "failed"
    assert any(x["type"] == "delivery_overdue" and "failed" in x["message"] for x in client.get("/api/alerts?open_only=true").json())
    c = client.post(f"/api/dispatches/{b['id']}/confirm", json={"method": "field_team", "who": "SDRF"}).json()
    assert c["status"] == "confirmed" and c["confirmation_method"] == "field_team"
