"""Phase 2: data model, multilingual seed, CRUD."""
import re

from app.core import geo
from app.i18n.languages import script_of_char
from app.sim import kodagu_reports as KR
from app.sim import kodagu_world as KW


def test_seed_row_counts(client):
    zones = client.get("/api/zones").json()
    assert len(zones) == 10 and sum(z["population"] for z in zones) > 90000
    assert len(client.get("/api/shelters").json()) == 6
    depots = client.get("/api/depots").json()
    assert len(depots) == 3 and all(len(d["inventory"]) == 7 for d in depots)
    assert len(client.get("/api/reports?limit=1000").json()) >= 80
    assert len(client.get("/api/roads").json()) == 13


def test_reports_span_scripts_and_romanized_variants():
    scripts = set()
    romanized = 0
    for r in KR.REPORTS:
        text = r[3]
        found = {script_of_char(c) for c in text if script_of_char(c)}
        scripts |= found
        if not found and re.search(r"\b(neeru|beku|maadi|chahiye|venam|alli|jana)\b", text):
            romanized += 1
    assert {"kn", "hi", "ml", "ta"} <= scripts
    assert romanized >= 6


def test_scenario_has_duplicates_rumours_vague_life_safety_and_silent_village():
    from eval.ground_truth import KODAGU   # labels live with the evaluation, not in the scenario module
    truth = [KODAGU[(r[0], r[3])] for r in KR.REPORTS]
    keys = [t["key"] for t in truth]
    assert keys.count("B") >= 4 and keys.count("A") >= 4                        # cross-language duplicates
    assert sum(1 for t in truth if t["real"] is False) >= 8                      # rumours
    assert sum(1 for t in truth if t["key"] is None and t["zone"] is None and t["need"] == "rescue") >= 3  # vague
    hatti = [t for t in truth if t["zone"] == "hattihole"]
    assert hatti and all(t["need"] == "missing_contact" for t in hatti)        # the village itself never reports
    assert all(set(r[4]) == {"origin_zone"} for r in KR.REPORTS)                # the scenario carries no labels


def test_real_coordinates_inside_kodagu():
    for _, _, lat, lng, *_ in KW.ZONES:
        assert 11.9 < lat < 12.9 and 75.4 < lng < 76.2


def test_geometry_helpers():
    assert abs(geo.haversine_m(12.4244, 75.7382, 12.4580, 75.9590) - 24300) < 1500    # Madikeri–Kushalnagar ~24 km
    sq = [[0, 0], [0, 1], [1, 1], [1, 0]]
    assert geo.point_in_polygon(0.5, 0.5, sq) and not geo.point_in_polygon(1.5, 0.5, sq)


def test_phone_numbers_never_leave_unmasked(client):
    body = client.get("/api/sources").text
    assert "phone_hash" not in body and "+919845012345" not in body
    assert "98XXXXX345" in body


def test_patch_shelter_and_inventory_are_audited(client):
    s = client.get("/api/shelters").json()[0]
    r = client.patch(f"/api/shelters/{s['id']}", json={"occupancy": s["occupancy"] + 5})
    assert r.status_code == 200 and r.json()["occupancy"] == s["occupancy"] + 5
    item = client.get("/api/inventory?location_type=depot").json()[0]
    assert client.patch(f"/api/inventory/{item['id']}", json={"quantity": item["quantity"]}).status_code == 200
    actions = [a["action"] for a in client.get("/api/audit?actor_type=human").json()]
    assert "shelter_updated" in actions and "stock_counted" in actions


def test_stale_stock_is_flagged(client):
    stale = [i for i in client.get("/api/inventory?location_type=depot").json() if i["stale"]]
    assert stale and all(i["location_id"] == 3 for i in stale)      # the NGO store counted 20 h before the event
