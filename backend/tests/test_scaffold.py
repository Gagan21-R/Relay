"""Phase 1: the skeleton runs in mock mode with no keys, the WebSocket hub delivers events, providers are mocked."""
import json

from app.channels.sms import MockSmsProvider, parse_inbound
from app.core.privacy import hash_phone, mask_phone
from app.graph.pipeline import AGENTS, run
from app.i18n.languages import LANGUAGES, script_of_char
from app.services.llm import LocalEmbedder, MockLLM, cosine, get_embedder, get_llm


def test_health_reports_mock_mode_without_keys(client):
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["database_ok"]
    assert h["mock_mode"] is True and h["llm"] == "mock" and h["sms_provider"] == "mock"


def test_openapi_docs_are_generated(client):
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200


def test_eight_languages_are_configured(client):
    codes = {l["code"] for l in client.get("/api/languages").json()["languages"]}
    assert {"en", "kn", "hi", "ml", "ta", "te", "mr", "bn"} <= codes
    assert script_of_char("ನ") == "kn" and script_of_char("ന") == "ml" and script_of_char("a") is None
    assert len(LANGUAGES) >= 8


def test_websocket_hello_and_ping(client):
    with client.websocket_connect("/ws/live") as ws:
        hello = json.loads(ws.receive_text())
        assert hello["type"] == "hello"
        ws.send_text("ping")
        assert json.loads(ws.receive_text())["type"] == "pong"


def test_mock_llm_returns_nothing_so_rules_take_over():
    assert isinstance(get_llm(), MockLLM)
    assert get_llm().generate_json("extract") is None


def test_local_embeddings_are_script_agnostic_and_normalised():
    e = get_embedder()
    assert isinstance(e, LocalEmbedder)
    a, b, c = e.embed(["school flooded near the bridge", "school flooded near bridge", "ಶಾಲೆ ಮುಳುಗಿದೆ"])
    assert abs(cosine(a, a) - 1) < 1e-9
    assert cosine(a, b) > cosine(a, c)


def test_sms_mock_and_inbound_parsing():
    p = MockSmsProvider()
    m = p.send("+919812345210", "RELAY: ವರದಿ ಸ್ವೀಕರಿಸಲಾಗಿದೆ")
    assert m.ref == "MOCK-00001" and p.outbox[0].body.endswith("ಸ್ವೀಕರಿಸಲಾಗಿದೆ")
    assert parse_inbound({"From": "+919812345210", "Body": " help "})["body"] == "help"
    assert parse_inbound({"sender": "98123", "text": "x"})["from"] == "98123"


def test_phone_privacy():
    assert mask_phone("+91 98123 45210") == "+91 98XXXXX210"
    assert mask_phone("9812345210") == "+91 98XXXXX210"
    assert hash_phone("9812345210") == hash_phone("+919812345210") != hash_phone("+919812345211")


def test_langgraph_routes_a_report_through_the_agents(client):
    from app.db import SessionLocal
    from app.models import Report
    with SessionLocal() as db:
        rid = db.query(Report.id).order_by(Report.id).first()[0]
        out = run(db, "report_received", report_ids=[rid])
        db.rollback()
    agents = [t["agent"] for t in out["trace"]]
    assert agents[:6] == ["intake", "trust", "triage", "resource", "blackout", "monitor"] and set(agents) <= set(AGENTS)
