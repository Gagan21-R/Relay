"""Phase 9: the explain-me assistant covers every page and answers with live facts (read-only)."""
from app.services.assistant import S

PAGES = ["map", "feed", "incidents", "fastverify", "plans", "dispatch", "resources", "shelters", "alerts", "blackout",
         "phone", "radio", "scenario", "twin3d", "metrics", "audit", "field", "about"]


def test_every_page_has_an_explanation():
    for p in PAGES:
        assert f"{p}.page" in S, p
    assert all(v["what"] and v["read"] and v["do"] for v in S.values())


def test_explain_uses_live_facts_and_changes_nothing(client):
    before = client.get("/api/summary").json()
    r = client.post("/api/assistant", json={"section": "blackout.page"}).json()
    assert r["title"].startswith("Blackout") and r["facts"] and r["method"].startswith("rule-based")
    assert any("T+" in f for f in r["facts"])
    r2 = client.post("/api/assistant", json={"section": "map.page", "question": "why is this shelter inaccessible and what should I do about the plan?"}).json()
    assert r2["section"].startswith(("plans", "shelters", "map"))
    r3 = client.post("/api/assistant", json={"section": "incidents.priority", "lang": "kn"}).json()
    assert r3["note"]
    assert client.get("/api/summary").json()["reports"] == before["reports"]
    assert len(client.get("/api/assistant/sections").json()) >= 30
