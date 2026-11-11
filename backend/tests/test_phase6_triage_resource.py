"""Phase 6: priority with visible reasons; inventory, burn rate, shortages, transfers, stale stock."""
from app.agents.resource import incident_demand, shelter_burn
from app.agents.triage import prioritise
from app.db import SessionLocal
from app.models import Incident, Shelter
from app.services import routing
from app.services import scoring as S


def test_incidents_ranked_with_visible_reasons(client):
    incs = client.get("/api/incidents").json()
    scores = [i["priority_score"] for i in incs]
    assert scores == sorted(scores, reverse=True)
    top = incs[0]
    comps = top["priority_breakdown"]["components"]
    assert set(comps) == set(S.PRIORITY_WEIGHTS) and all(c["why"] for c in comps.values())
    assert abs(sum(c["points"] for c in comps.values()) - top["priority_score"]) < 0.5
    assert all(i["priority_score"] == 0 for i in incs if i["confidence_level"] == "false")


def test_unverified_life_safety_is_not_pushed_down():
    with SessionLocal() as db:
        a = Incident(title="t", category="medical", confidence_level="unverified", life_safety=True, people_affected=1,
                     vulnerable_groups=["medical"], first_report_at=0)
        b = Incident(title="t", category="food", confidence_level="verified", life_safety=False, people_affected=1, first_report_at=0)
        assert prioritise(db, a).priority_score > prioritise(db, b).priority_score


def test_seeded_water_shortfall_is_forecast_with_hours(client):
    ov = client.get("/api/resources/overview").json()
    nap = [p for p in ov["projected"] if "Napoklu" in p["shelter"] and p["resource_type"] == "water_litres"]
    assert nap and 12 <= nap[0]["hours_left"] <= 24
    tr = next(t for t in ov["transfers"] if t["shelter_id"] == nap[0]["shelter_id"])
    assert tr["proposal"] and tr["proposal"]["depot"].startswith("Madikeri")
    alerts = client.get("/api/alerts?open_only=true").json()
    assert any(a["type"] == "shortage" and "runs out in ~" in a["message"] and "Napoklu" in a["message"] for a in alerts)
    assert ov["series"] and all(p["level"] >= 0 for s in ov["series"] for p in s["points"])


def test_burn_rate_uses_sphere_standard():
    with SessionLocal() as db:
        s = db.query(Shelter).filter(Shelter.name.like("Napoklu%")).one()
        water = next(b for b in shelter_burn(db, s) if b["resource_type"] == "water_litres")
        assert water["per_person_day"] == 15.0 and abs(water["rate_per_h"] - s.occupancy * 15 / 24) < 0.01


def test_stale_stock_is_flagged_and_excluded(client):
    ov = client.get("/api/resources/overview").json()
    assert ov["stale"] and all(r["depot"].startswith("Virajpet") for r in ov["stale"])
    ngo = next(d for d in ov["depots"] if d["name"].startswith("Virajpet"))
    assert all(i["stale"] for i in ngo["inventory"])
    assert any(a["type"] == "stale_stock" for a in client.get("/api/alerts?open_only=true").json())


def test_demand_from_needs_and_routing():
    inc = Incident(title="t", category="food", need_types=["food", "water"], people_affected=10)
    assert incident_demand(inc) == {"food_kits": 10, "water_litres": 300}
    with SessionLocal() as db:
        r = routing.route(db, "madikeri", "virajpet")
        assert r and r["zones"][0] == "madikeri" and r["zones"][-1] == "virajpet" and r["eta_h"] > 0
