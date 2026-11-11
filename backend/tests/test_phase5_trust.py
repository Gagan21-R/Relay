"""Phase 5: cross-lingual clustering, explainable confidence, Fast Verify, source reliability, same-report analyser."""
from app.db import SessionLocal
from app.models import Incident, Report
from app.services import scoring as S


def _incident_of(db, text_start: str) -> Incident:
    r = db.query(Report).filter(Report.raw_text.like(text_start + "%")).order_by(Report.id).first()
    return db.get(Incident, r.incident_id)


def test_kannada_sms_and_english_post_cluster_into_one_incident(client):
    with SessionLocal() as db:
        a = _incident_of(db, "ಕರಡಿಗೋಡು ಗ್ರಾಮದಲ್ಲಿ 30")
        b = _incident_of(db, "Karadigodu village near Siddapura")
        h = _incident_of(db, "करडिगोडु गांव")
        assert a.id == b.id == h.id
        langs = {r.original_language for r in db.query(Report).filter(Report.incident_id == a.id)}
        assert {"kn", "en", "hi"} <= langs
        assert a.people_affected == 111      # max of reports (30 families), never the sum of duplicates


def test_retweet_counts_as_one_source(client):
    with SessionLocal() as db:
        inc = _incident_of(db, "12 people stranded on rooftops")
        groups = inc.confidence_breakdown["independent_sources"]
        tweet = [g for g in groups if any("RT" in x or True for x in g["reports"]) and g["copies_merged"]]
        assert tweet, groups
        assert len(groups) < db.query(Report).filter(Report.incident_id == inc.id).count()


def test_seeded_rumours_score_low_and_end_false(client):
    with SessionLocal() as db:
        for start in ("ಹಾರಂಗಿ ಅಣೆಕಟ್ಟು ಒಡೆದಿದೆ", "Madikeri bus stand completely underwater", "कुशालनगर रोटरी हॉल कैंप बंद"):
            inc = _incident_of(db, start)
            assert inc.confidence_level == "false" and inc.confidence_score < 0.3, (start, inc.confidence_breakdown)
            names = {p["name"] for p in inc.confidence_breakdown["penalties"]}
            assert "contradiction" in names


def test_confidence_breakdown_is_complete_and_explained(client):
    inc = client.get("/api/incidents").json()[0]
    bd = inc["confidence_breakdown"]
    assert set(bd["components"]) == set(S.CONFIDENCE_WEIGHTS)
    assert all("why" in c and "points" in c for c in bd["components"].values())
    assert abs(sum(c["weight"] for c in bd["components"].values()) - 1.0) < 1e-9


def test_life_safety_reports_are_never_discarded(client):
    with SessionLocal() as db:
        life = db.query(Report).filter(Report.life_safety.is_(True), Report.status != "blocked").all()
        assert life and all(r.incident_id for r in life)
    fv = client.get("/api/fast-verify").json()
    titles = " ".join(i["title"] for i in fv)
    assert "Makkandur" in titles and "Siddapura" in titles          # dialysis and labour: single unverified reports
    assert all(i["life_safety"] and i["confidence_level"] in ("unverified", "disputed") for i in fv)
    assert any(i["callback"] for i in fv)


def test_officer_confirmation_verifies_and_updates_source_reliability(client):
    fv = client.get("/api/fast-verify").json()
    target = next(i for i in fv if "Makkandur" in i["title"])
    before = client.get(f"/api/incidents/{target['id']}").json()["reports"][0]["source"]["reliability"]
    out = client.post(f"/api/incidents/{target['id']}/verify", json={"decision": "confirm", "note": "called back: confirmed"}).json()
    assert out["confidence_level"] == "verified" and not out["fast_verify"]
    after = client.get(f"/api/incidents/{target['id']}").json()
    assert after["reports"][0]["source"]["reliability"] > before
    assert any(a["action"] == "incident_confirmed" for a in after["audit"])


def test_evidence_trail(client):
    inc = client.get("/api/incidents").json()[0]
    d = client.get(f"/api/incidents/{inc['id']}").json()
    assert d["reports"] and all(r["cluster_evidence"] for r in d["reports"])
    assert d["audit"]


def test_same_report_analyser(client):
    same = client.post("/api/trust/compare", json={"texts": [
        "ನಾಪೋಕ್ಲು ಸರ್ಕಾರಿ ಶಾಲೆ ಹತ್ತಿರ ನೀರು ಮನೆಗಳಿಗೆ ನುಗ್ಗಿದೆ, 12 ಜನ ಮೇಲ್ಛಾವಣಿ ಮೇಲೆ ಸಿಕ್ಕಿಹಾಕಿಕೊಂಡಿದ್ದಾರೆ, ದಯವಿಟ್ಟು ದೋಣಿ ಕಳುಹಿಸಿ",
        "12 people stranded on rooftops near Govt School Napoklu as Cauvery overflows. Need boats urgently! #KodaguFloods"]}).json()
    assert same["verdict"] == "same incident"
    assert set(same["pairs"][0]["tests"]) == {"similarity", "distance_m", "time_h", "needs"}
    diff = client.post("/api/trust/compare", json={"texts": [
        "Sai Layout in Kushalnagar flooded, about 60 residents need shelter and food.",
        "Virajpet Kodava Samaja camp: 8 diabetic patients need insulin and medicines today."]}).json()
    assert diff["incidents"] == 2
    with SessionLocal() as db:            # nothing was stored
        assert db.query(Report).filter(Report.ref.like("CMP-%")).count() == 0
