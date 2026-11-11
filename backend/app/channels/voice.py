"""Voice / IVR. Twilio-compatible TwiML: language menu -> record -> transcribe -> same pipeline as SMS.
Transcription: Gemini audio input when a key is set; otherwise the provider's transcription (Twilio
TranscriptionText) or, in the simulator, the browser's speech-recognition transcript or a typed transcript."""
from pathlib import Path
from xml.sax.saxutils import escape

from app.core.config import get_settings
from app.i18n.languages import LANGUAGES

MEDIA_DIR = Path(__file__).resolve().parents[2] / "media"

PROMPTS = {
    "en": "Welcome to RELAY disaster helpline. After the beep, say your village, what you need and how many people.",
    "kn": "RELAY ವಿಪತ್ತು ಸಹಾಯವಾಣಿಗೆ ಸ್ವಾಗತ. ಬೀಪ್ ನಂತರ ನಿಮ್ಮ ಗ್ರಾಮ, ನಿಮಗೆ ಏನು ಬೇಕು ಮತ್ತು ಎಷ್ಟು ಜನ ಎಂದು ಹೇಳಿ.",
    "hi": "RELAY आपदा हेल्पलाइन में आपका स्वागत है। बीप के बाद अपना गाँव, क्या चाहिए और कितने लोग हैं बताइए।",
    "ml": "RELAY ദുരന്ത ഹെൽപ്‌ലൈനിലേക്ക് സ്വാഗതം. ബീപ്പിന് ശേഷം നിങ്ങളുടെ ഗ്രാമം, ആവശ്യം, ആളുകളുടെ എണ്ണം പറയുക.",
    "ta": "RELAY பேரிடர் உதவி எண்ணுக்கு வரவேற்கிறோம். பீப் ஒலிக்குப் பிறகு உங்கள் ஊர், தேவை, எத்தனை பேர் என்று சொல்லுங்கள்.",
    "te": "RELAY విపత్తు హెల్ప్‌లైన్‌కు స్వాగతం. బీప్ తర్వాత మీ గ్రామం, అవసరం, ఎంత మంది అని చెప్పండి.",
    "mr": "RELAY आपत्ती हेल्पलाइनमध्ये स्वागत. बीप नंतर तुमचे गाव, गरज आणि किती लोक आहेत ते सांगा.",
    "bn": "RELAY দুর্যোগ হেল্পলাইনে স্বাগতম। বিপের পরে আপনার গ্রাম, কী দরকার এবং কতজন বলুন।",
}


def menu_twiml(action: str) -> str:
    opts = " ".join(f"Press {v['ivr_key']} for {v['native']}." for k, v in LANGUAGES.items())
    return (f'<?xml version="1.0" encoding="UTF-8"?><Response><Gather numDigits="1" action="{escape(action)}" method="POST">'
            f"<Say>{escape(opts)}</Say></Gather></Response>")


def lang_for_digit(d: str) -> str:
    return next((k for k, v in LANGUAGES.items() if v["ivr_key"] == d), "en")


def record_twiml(lang: str, action: str) -> str:
    return (f'<?xml version="1.0" encoding="UTF-8"?><Response><Say language="{lang}-IN">{escape(PROMPTS.get(lang, PROMPTS["en"]))}</Say>'
            f'<Record maxLength="60" transcribe="true" action="{escape(action)}" method="POST"/></Response>')


def done_twiml(lang: str) -> str:
    msg = {"en": "Thank you. Your report is recorded. You will get an SMS with a reference number.",
           "kn": "ಧನ್ಯವಾದಗಳು. ನಿಮ್ಮ ವರದಿ ದಾಖಲಾಗಿದೆ. ಸಂಖ್ಯೆಯೊಂದಿಗೆ SMS ಬರುತ್ತದೆ.",
           "hi": "धन्यवाद। आपकी रिपोर्ट दर्ज हो गई है। आपको संदर्भ संख्या के साथ SMS मिलेगा।"}.get(lang)
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Say>{escape(msg or "Thank you.")}</Say><Hangup/></Response>'


def transcribe(audio: bytes | None, lang: str, provided: str | None) -> tuple[str, str]:
    """Returns (transcript, method)."""
    if audio and not get_settings().mock:  # pragma: no cover - needs a key
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=get_settings().gemini_api_key)
            r = client.models.generate_content(model=get_settings().gemini_model, contents=[
                f"Transcribe this emergency call in its original language ({LANGUAGES.get(lang, {}).get('name', lang)}). Return only the transcript.",
                types.Part.from_bytes(data=audio, mime_type="audio/webm")])
            if r.text:
                return r.text.strip(), "gemini audio"
        except Exception:  # noqa: BLE001
            pass
    if provided and provided.strip():
        return provided.strip(), "provider / browser transcript (mock mode)"
    return "", "no transcript"


def save_audio(data: bytes, name: str) -> str:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    (MEDIA_DIR / name).write_bytes(data)
    return f"/media/{name}"
