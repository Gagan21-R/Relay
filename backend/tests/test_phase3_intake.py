"""Phase 3: Intake agent and channels (native, romanized and code-mixed; clarification loop; voice; radio; field; feeds)."""
import pytest

from app.agents import intake
from app.agents.intake import ExtractedReport, rule_extract, structured_sms
from app.i18n.detect import detect
from app.i18n.translate import glossary_translate

CASES = [
    # text, language, script, need, people
    ("ನಾಪೋಕ್ಲು ಸರ್ಕಾರಿ ಶಾಲೆ ಹತ್ತಿರ 12 ಜನ ಮೇಲ್ಛಾವಣಿ ಮೇಲೆ ಸಿಕ್ಕಿಹಾಕಿಕೊಂಡಿದ್ದಾರೆ", "kn", "native", "rescue", 12),
    ("napoklu school hatra 12 jana roof mele sikkikondidare, boat kalisi", "kn", "romanized", "rescue", 12),
    ("करडिगोडु गांव में 30 परिवारों को खाना और पीने का पानी चाहिए", "hi", "native", "food", 111),
    ("Bhagamandala mandir ke paas hum 45 log phase hain, paani aur khana chahiye", "hi", "romanized", "food", 45),
    ("നാപോക്ലു സ്കൂളിനടുത്ത് 12 പേർ മേൽക്കൂരയിൽ കുടുങ്ങി, ബോട്ട് വേണം", "ml", "native", "rescue", 12),
    ("jodupala il NH road poyi, 20 lorry kudungi, food venam", "ml", "mixed", "food", 20),
    ("ಮಡಿಕೇರಿ hospital ಗೆ ambulance ಬೇಕು, 2 ಜನ ಗಾಯ", "kn", "mixed", "medical", 2),
    ("Landslide at Indira Nagar, Madikeri. One house collapsed, 2 injured. Need ambulance.", "en", "native", "medical", 2),
]


@pytest.mark.parametrize("text,lang,script,need,people", CASES)
def test_detection_and_rule_extraction(text, lang, script, need, people):
    d = detect(text)
    assert (d.language, d.script) == (lang, script)
    f, ev = rule_extract(text)
    assert need in f["need_types"], ev
    assert f["people_count"] == people


def test_vulnerable_groups_and_life_safety_across_languages():
    f, _ = rule_extract("ಭಾಗಮಂಡಲ ಬಳಿ 45 ಯಾತ್ರಿಕರು ಸಿಲುಕಿದ್ದಾರೆ, ಅದರಲ್ಲಿ ವೃದ್ಧರು ಇದ್ದಾರೆ")
    assert "elderly" in f["vulnerable_groups"] and f["life_safety"]
    f, _ = rule_extract("सिद्दापुर एस्टेट में एक गर्भवती महिला को प्रसव पीड़ा है")
    assert "pregnant" in f["vulnerable_groups"] and "medical" in f["need_types"] and f["people_count"] == 1


def test_missing_contact_is_not_a_life_safety_report():
    f, _ = rule_extract("Can't reach my family in Hattihole village since yesterday, phones switched off.")
    assert f["missing_contact"] and f["need_types"] == ["missing_contact"] and not f["life_safety"]


def test_structured_sms_format():
    assert structured_sms("HELP FOOD 12 Napoklu school") == {"need": "food", "people": 12, "landmark": "Napoklu school"}
    f, _ = rule_extract("HELP WATER 40 Siddapura camp")
    assert f["need_types"] == ["water"] and f["people_count"] == 40


def test_rumour_signals_in_several_languages():
    for t in ["ಹಾರಂಗಿ ಅಣೆಕಟ್ಟು ಒಡೆದಿದೆ!! ಎಲ್ಲರಿಗೂ ಶೇರ್ ಮಾಡಿ", "हारंगी बांध टूट गया है, सबको शेयर करो", "Forwarded as received: dam has burst"]:
        kinds = {s["signal"] for s in intake.rumour_signals(t, {})}
        assert "forward_chain" in kinds
    assert intake.rumour_signals("photo", {"taken_at": "2018-08-16T10:00:00"})[0]["signal"] == "old_media"


def test_llm_output_is_schema_validated():
    with pytest.raises(Exception):
        ExtractedReport.model_validate({"language": "xx", "script": "native"})
    ok = ExtractedReport.model_validate({"language": "kn", "script": "romanized", "need_types": ["food"], "people_count": 3})
    assert ok.need_types == ["food"]


def test_glossary_translation_keeps_unknown_words_and_reports_confidence():
    en, method, conf = glossary_translate("ನೀರು ಬೇಕು ದಯವಿಟ್ಟು")
    assert "water" in en and "needed" in en and "glossary" in method and 0 < conf <= 0.85


def test_kannada_sms_end_to_end_with_reply_in_kannada(client):
    r = client.post("/api/intake/sms", data={"From": "+919900099001", "Body": "ಕರಡಿಗೋಡು ಗ್ರಾಮದಲ್ಲಿ 8 ಜನರಿಗೆ ಊಟ ಬೇಕು"}).json()
    assert r["kind"] == "report"
    rep = r["report"]
    assert rep["original_language"] == "kn" and rep["channel"] == "sms" and rep["location_text"] == "Karadigodu village"
    assert rep["translated_text_en"] and rep["need_types"] == ["food"] and rep["people_count"] == 8
    ack = r["replies"][0]
    assert ack["language"] == "kn" and rep["ref"] in ack["body"] and "ಸ್ವೀಕರಿಸಲಾಗಿದೆ" in ack["body"]


def test_missing_location_triggers_one_followup_and_reply_merges(client):
    phone = "+919900099002"
    r = client.post("/api/intake/sms", json={"from": phone, "body": "हमारे घर में पानी आ गया है, 6 लोग फंसे हैं, मदद करो"}).json()
    assert [m["kind"] for m in r["replies"]] == ["ack", "clarification"]
    assert r["replies"][1]["language"] == "hi" and "कहाँ" in r["replies"][1]["body"]
    ref = r["report"]["ref"]
    r2 = client.post("/api/intake/sms", json={"from": phone, "body": "सिद्दापुर स्कूल के पास"}).json()
    assert r2["kind"] == "clarification_reply" and r2["report"]["ref"] == ref
    assert r2["report"]["location_text"] and r2["report"]["zone_id"] and "location" in r2["replies"][0]["body"] or r2["replies"]
    thread = client.get("/api/intake/sms/thread", params={"phone": phone}).json()
    assert [m["direction"] for m in thread] == ["in", "out", "out", "in", "out"]


def test_voice_ivr_twiml_and_simulator(client):
    menu = client.post("/api/intake/voice", data={}).text
    assert "<Gather" in menu and "ಕನ್ನಡ" in menu
    rec = client.post("/api/intake/voice", data={"Digits": "2"}).text
    assert "<Record" in rec and "ಬೀಪ್" in rec
    r = client.post("/api/intake/voice/simulate", data={"phone": "+919900099003", "language": "kn",
                                                        "transcript": "ಸೋಮವಾರಪೇಟೆಯಲ್ಲಿ 30 ಜನಕ್ಕೆ ಕುಡಿಯುವ ನೀರು ಬೇಕು"}).json()
    assert r["report"]["channel"] == "voice" and "water" in r["report"]["need_types"] and r["replies"][0]["language"] == "kn"


def test_radio_field_and_feed_channels(client):
    r = client.post("/api/intake/radio", json={"kind": "satphone", "callsign": "NDRF-2", "zone_code": "hattihole",
                                                "message": "Team at village: 300 people at temple hall, need food and water"}).json()["report"]
    assert r["channel"] == "radio_entry" and r["zone_id"] and r["geocode_method"] == "device GPS"
    body = {"client_id": "dev1-0001", "text": "Napoklu camp needs 50 blankets", "team": "Volunteer team A", "lat": 12.307, "lng": 75.698,
            "queued_offline": True}
    a = client.post("/api/intake/field", json=body).json()
    b = client.post("/api/intake/field", json=body).json()
    assert not a["duplicate"] and b["duplicate"] and a["report"]["id"] == b["report"]["id"]
    feeds = {f["name"] for f in client.get("/api/intake/feeds").json()}
    assert {"citizen_sms", "regional_social", "news", "field_team", "official", "missing_contact", "radio"} <= feeds
    out = client.post("/api/intake/feed/regional_social?n=2").json()["reports"]
    assert len(out) == 2 and all(x["original_language"] for x in out)
    assert client.post("/api/intake/feed/nope").status_code == 404
