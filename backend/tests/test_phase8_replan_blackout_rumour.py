"""Phase 8: replanning triggers, blackout detection + recon, rumour corrections, signal feeds."""
from app.core import geo
from app.db import SessionLocal
from app.models import Road, Shelter


def test_silent_village_is_top_ranked_with_recon_and_supply_estimate(client):
    zones = client.get("/api/zones/blackout").json()
    top = zones[0]
    assert top["code"] == "hattihole" and top["blackout_flag"]
    comps = top["risk"]["components"]
    assert comps["silence"]["value"] > 0 and comps["infrastructure"]["value"] == 1.0
    assert comps["missing_contact"]["value"] > 0                      # relatives' reports count toward the blackout
    assert top["recon"]["status"] == "pending_approval"
    assert top["recon"]["estimated_needs"]["needs_one_day"]["water_litres"] > 0 and top["recon"]["prepositioned"]
    assert any(a["type"] == "blackout" and "Hattihole" in a["message"] for a in client.get("/api/alerts?open_only=true").json())


def test_satphone_report_from_the_village_resolves_the_blackout(client):
    zone = client.get("/api/zones/blackout").json()[0]
    rid = zone["recon"]["id"]
    assert client.post(f"/api/recon/{rid}/approve", json={"who": "DC Kodagu"}).json()["status"] == "in_progress"
    out = client.post(f"/api/recon/{rid}/report", json={"callsign": "NDRF-2",
        "message": "Hattihole reached on foot: 40 houses damaged, about 300 people at the temple hall, need food, drinking water and a medical team."}).json()
    assert out["report"]["zone_id"] == zone["id"] and out["report"]["incident_id"]
    assert out["recon"]["status"] == "completed" and not out["zone"]["blackout_flag"]
    alerts = client.get("/api/alerts").json()
    assert any(a["type"] == "blackout" and a["resolved"] for a in alerts)
    incs = [i for i in client.get("/api/incidents").json() if i["zone_id"] == zone["id"] and i["category"] != "other"]
    assert incs and incs[0]["people_affected"] == 300


def test_flooding_a_shelters_access_roads_triggers_a_new_plan(client):
    with SessionLocal() as db:
        s = db.query(Shelter).filter(Shelter.name.like("Siddapura%")).one()
        polys = []
        for code in s.access_road_ids:
            r = db.query(Road).filter_by(code=code).one()
            p = geo.lerp_point(r.points[0], r.points[-1], 0.3)
            polys.append(geo.circle(p[0], p[1], 2500))
        sid = s.id
    before = max(p["version"] for p in client.get("/api/plans").json())
    current = client.get("/api/state").json()["flood_extent"]
    out = client.post("/api/signals/flood_extent", json={"value": {"version": 99, "polygons": current + polys}, "source": "test satellite"}).json()
    assert any("roads now cut" in c for c in out["changes"])
    shelters = {x["id"]: x for x in client.get("/api/shelters").json()}
    assert shelters[sid]["status"] == "inaccessible" and "access roads closed" in shelters[sid]["status_reason"]
    plans = client.get("/api/plans").json()
    newest = max(plans, key=lambda p: p["version"])
    assert newest["version"] > before and newest["status"] == "pending_approval" and "inaccessible" in newest["trigger"]
    assert any(a["type"] == "shelter_inaccessible" and "Siddapura" in a["message"] for a in client.get("/api/alerts?open_only=true").json())


def test_rumour_correction_in_at_least_three_languages(client):
    false = [i for i in client.get("/api/incidents").json() if i["confidence_level"] == "false"]
    dam = next(i for i in false if "Harangi" in i["title"])
    out = client.post("/api/alerts/rumour", json={"incident_id": dam["id"]}).json()
    assert out["kind"] == "dam_burst" and len(out["translations"]) >= 8
    assert "ಹಾರಂಗಿ" in out["translations"]["kn"] and "हारंगी" in out["translations"]["hi"] and "FALSE" in out["translations"]["en"]
    assert out["sms_sent"] > 0
    pub = client.get("/api/public/corrections").json()
    assert pub and set(pub[0]["translations"]) >= {"en", "kn", "hi"}
    real = next(i for i in client.get("/api/incidents").json() if i["confidence_level"] == "verified")
    assert client.post("/api/alerts/rumour", json={"incident_id": real["id"]}).status_code == 409


def test_signal_feeds(client):
    r = client.post("/api/signals/tower_outage", json={"zone_code": "virajpet", "value": {"towers_down": 3, "towers_total": 3}}).json()
    assert r["changes"] and "towers down" in r["changes"][0]
    assert client.post("/api/signals/quake", json={"value": {"magnitude": 4.1, "place": "near Bhagamandala"}}).status_code == 200
    assert client.post("/api/signals/volcano", json={"value": {}}).status_code == 404
    client.post("/api/signals/tower_outage", json={"zone_code": "virajpet", "value": {"towers_down": 0, "towers_total": 3}})
