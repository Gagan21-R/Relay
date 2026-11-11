"""Phase 4: live feed over WebSocket, phone simulator, network toggle."""
import json


def _drain_until(ws, kind, limit=40):
    for _ in range(limit):
        e = json.loads(ws.receive_text())
        if e["type"] == kind:
            return e
    raise AssertionError(f"no {kind} event")


def test_kannada_sms_appears_live_with_translation_and_kannada_reply(client):
    with client.websocket_connect("/ws/live") as ws:
        json.loads(ws.receive_text())  # hello
        r = client.post("/api/intake/sms", json={"from": "+919845500101", "body": "ಕರಡಿಗೋಡು ಗ್ರಾಮದಲ್ಲಿ 20 ಜನರಿಗೆ ಊಟ ಮತ್ತು ಕುಡಿಯುವ ನೀರು ಬೇಕು"}).json()
        ev = _drain_until(ws, "report")
        assert ev["data"]["ref"] == r["report"]["ref"]
        assert ev["data"]["translated_text_en"].startswith("20 people in Karadigodu")
        sms = _drain_until(ws, "sms")
        assert sms["data"]["direction"] in ("in", "out")
    assert r["replies"][0]["language"] == "kn"


def test_internet_down_stops_web_social_field_but_not_sms_voice(client):
    assert client.post("/api/sim/network", json={"zone_code": "somwarpet", "internet_down": True}).json()["internet_down"]
    try:
        web = client.post("/api/intake/web", json={"text": "Somwarpet: 30 people need drinking water"}).json()
        field = client.post("/api/intake/field", json={"client_id": "net-test-1", "text": "Somwarpet camp needs food", "team": "T"}).json()
        sms = client.post("/api/intake/sms", json={"from": "+919845577001", "body": "ಸೋಮವಾರಪೇಟೆಯಲ್ಲಿ 30 ಜನಕ್ಕೆ ಕುಡಿಯುವ ನೀರು ಬೇಕು"}).json()
        voice = client.post("/api/intake/voice/simulate", data={"phone": "+919845577002", "language": "kn",
                                                                "transcript": "ಸೋಮವಾರಪೇಟೆಯಲ್ಲಿ 10 ಜನಕ್ಕೆ ಊಟ ಬೇಕು"}).json()
        assert web["blocked"] and web["report"]["status"] == "blocked"
        assert field["report"]["status"] == "blocked"
        assert sms["report"]["status"] in ("processed", "clarifying") and sms["replies"]
        assert voice["report"]["status"] != "blocked"
    finally:
        client.post("/api/sim/network", json={"zone_code": "somwarpet", "internet_down": False})
    assert "somwarpet" not in client.get("/api/state").json()["network_down"]


def test_simulator_samples_cover_every_language(client):
    s = client.get("/api/sim/samples").json()
    assert {m["lang"] for m in s["messages"]} >= {"en", "kn", "hi", "ml", "ta", "te", "mr", "bn"}
    for m in s["messages"]:
        if m["lang"] in ("te", "mr", "bn", "ta", "ml"):
            r = client.post("/api/intake/sms", json={"from": "+919845588000", "body": m["text"]}).json()["report"]
            assert r["original_language"] == m["lang"] and r["location_text"], m
