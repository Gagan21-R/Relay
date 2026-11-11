"""Translation to English for display (extraction never depends on it). Order:
1. translation memory — previously verified translations (seed scenario + simulator samples), exact match;
2. Gemini, when a key is configured;
3. glossary translation — word/phrase dictionary; confidence = share of words it could translate.
The original text is always kept; the UI shows the method and confidence next to every translation."""
import re

from app.services.llm import get_llm

_TM: dict[str, str] = {}

# phrase -> English (longest phrases first when applied)
GLOSSARY: dict[str, str] = {
    # Kannada
    "ದಯವಿಟ್ಟು": "please", "ಸಹಾಯ ಮಾಡಿ": "help", "ಸಹಾಯ": "help", "ನೀರು": "water", "ಮನೆ": "house", "ಮನೆಗೆ": "to the house",
    "ಮನೆಗಳಿಗೆ": "into houses", "ನುಗ್ಗಿದೆ": "has entered", "ಬರುತ್ತಿದೆ": "is coming", "ಜನ": "people", "ಜನರಿಗೆ": "for people",
    "ಬೇಕು": "needed", "ಊಟ": "food", "ಆಹಾರ": "food", "ಕುಡಿಯುವ ನೀರು": "drinking water", "ಮತ್ತು": "and", "ಹತ್ತಿರ": "near",
    "ಬಳಿ": "near", "ಸಿಕ್ಕಿಹಾಕಿಕೊಂಡಿದ್ದಾರೆ": "are trapped", "ಸಿಲುಕಿದ್ದಾರೆ": "are stuck", "ದೋಣಿ": "boat", "ಕಳುಹಿಸಿ": "send",
    "ಗಾಯ": "injury", "ಆಂಬ್ಯುಲೆನ್ಸ್": "ambulance", "ಔಷಧಿ": "medicine", "ಆಶ್ರಯ": "shelter", "ಶಿಬಿರ": "camp", "ಶಿಬಿರದಲ್ಲಿ": "at the camp",
    "ರಸ್ತೆ": "road", "ಮುಚ್ಚಿದೆ": "is closed", "ಮುಳುಗಿದೆ": "is submerged", "ತುರ್ತು": "urgent", "ಮಕ್ಕಳು": "children", "ಮಕ್ಕಳಿಗೆ": "for children",
    "ವೃದ್ಧರು": "elderly", "ಹಿರಿಯರು": "elderly", "ಗ್ರಾಮದಲ್ಲಿ": "in the village", "ಭೂಕುಸಿತ": "landslide", "ಎಲ್ಲರಿಗೂ ಶೇರ್ ಮಾಡಿ": "share with everyone",
    # Kanglish
    "neeru": "water", "mane": "house", "olage": "inside", "bandide": "has come", "help maadi": "please help", "beku": "needed",
    "oota": "food", "jana": "people", "alli": "in", "hatra": "near", "sikkikondidare": "are stuck", "kalisi": "send", "pls": "please",
    "jaasti": "a lot", "agtide": "is happening", "makkalu": "children", "innu": "still", "sikkilla": "not received",
    # Hindi + Hinglish
    "मदद करो": "help", "मदद": "help", "पानी": "water", "घर": "house", "में": "in", "आ गया है": "has come", "हमारे": "our",
    "खाना": "food", "चाहिए": "needed", "लोग": "people", "लोगों": "people", "फंसे हैं": "are stuck", "बुजुर्ग": "elderly",
    "और": "and", "के पास": "near", "बाढ़": "flood", "सड़क बंद है": "road is closed", "तुरंत": "immediately", "बच्चे": "children",
    "paani": "water", "khana": "food", "chahiye": "needed", "log": "people", "madad": "help", "ghar": "house", "aur": "and",
    # Malayalam + Manglish
    "വെള്ളം": "water", "ഭക്ഷണം": "food", "വേണം": "needed", "കുടുങ്ങി": "stuck", "സഹായം": "help", "റോഡ്": "road",
    "venam": "needed", "kudungi": "stuck", "poyi": "is gone", "food venam": "food needed",
    # Tamil
    "தண்ணீர்": "water", "உணவு": "food", "தேவை": "needed", "உதவி": "help", "வெள்ளம்": "flood", "சிக்கியுள்ளனர்": "are stuck",
    # Telugu, Marathi, Bengali (small)
    "నీరు": "water", "ఆహారం": "food", "సహాయం": "help", "కావాలి": "needed", "पाणी": "water", "मदत": "help", "हवे": "needed",
    "জল": "water", "খাবার": "food", "সাহায্য": "help", "দরকার": "needed",
    # enhancement round: Kannada flood phrasing, Kanglish, and key words for the newer languages (partial coverage:
    # confidence stays low, so these reports are flagged for a speaker to check)
    "ಒಳಗೆ": "inside", "ಬಂದಿದೆ": "has come", "ide": "is there", "madi": "please do", "help madi": "please help", "full": "full",
    "sikkiddare": "are stuck", "bega": "quickly", "rescue beku": "rescue needed",
    "ওচৰত": "near", "মানুহ": "people", "আবদ্ধ হৈ আছে": "are trapped", "উদ্ধাৰ": "rescue", "লাগে": "needed", "খোৱা পানী": "drinking water",
    "খাদ্য": "food", "আহত": "injured", "ঔষধ": "medicine", "জন": "people", "শিবিৰত": "in the camp", "নাই": "not available",
    "ପାଖରେ": "near", "ଜଣ": "people", "ଫସି ରହିଛନ୍ତି": "are trapped", "ଉଦ୍ଧାର": "rescue", "ଦରକାର": "needed", "ପିଇବା ପାଣି": "drinking water",
    "ଖାଦ୍ୟ": "food", "ଆହତ": "injured", "ଔଷଧ": "medicine", "ଶିବିରରେ": "in the camp", "ନାହିଁ": "not available",
    "પાસે": "near", "લોકો": "people", "ફસાયેલા છે": "are trapped", "બચાવ": "rescue", "જોઈએ": "needed", "પીવાનું પાણી": "drinking water",
    "ખોરાક": "food", "ઘાયલ": "injured", "દવા": "medicine", "કેમ્પમાં": "in the camp", "નથી": "not available",
    "ਨੇੜੇ": "near", "ਲੋਕ": "people", "ਫਸੇ ਹੋਏ ਹਨ": "are trapped", "ਬਚਾਅ": "rescue", "ਚਾਹੀਦਾ ਹੈ": "needed", "ਪਾਣੀ": "water",
    "ਖਾਣਾ": "food", "ਜ਼ਖਮੀ": "injured", "ਦਵਾਈ": "medicine", "ਤੁਰੰਤ": "immediately",
    "नजिक": "near", "जना": "people", "फसेका छन्": "are trapped", "उद्धार": "rescue", "चाहियो": "needed", "खानेपानी": "drinking water",
    "तुरुन्तै": "immediately", "घाइते": "injured", "औषधि": "medicine",
    "bulah": "near", "mi": "people", "an tang": "are stuck", "chhanhim": "rescue", "tui": "water", "chaw": "food", "mamawh": "need",
    "ngut": "people", "ki la kem": "are stuck", "ïarap": "help", "um": "water", "donkam": "need",
}
_ORDERED = sorted(GLOSSARY, key=len, reverse=True)


def load_memory(pairs: dict[str, str]) -> None:
    _TM.update({k.strip(): v for k, v in pairs.items() if v})


def translate_to_en(text: str, language: str) -> tuple[str, str, float]:
    """Returns (english, method, confidence)."""
    t = (text or "").strip()
    if language == "en":
        return t, "original (English)", 1.0
    ensure_memory()
    if t in _TM:
        return _TM[t], "translation memory (verified)", 0.98
    out = get_llm().generate_text(
        f"Translate this {language} disaster report into plain English. Keep numbers and place names. Reply with the translation only.\n\n{t}")
    if out:
        return out.strip(), "gemini", 0.9
    return glossary_translate(t)


def glossary_translate(text: str) -> tuple[str, str, float]:
    s = text
    hits = 0
    for phrase in _ORDERED:
        pat = re.escape(phrase) if not phrase.isascii() else r"\b" + re.escape(phrase) + r"\b"
        s, n = re.subn(pat, f"⟨{GLOSSARY[phrase]}⟩", s, flags=re.IGNORECASE)
        hits += n * len(phrase.split())
    words = re.findall(r"\w+", text)
    conf = round(min(0.85, hits / max(1, len(words))), 2)
    gloss = re.sub(r"⟨([^⟩]+)⟩", r"\1", s)
    return gloss, "glossary (word-by-word, mock mode)", conf


_loaded = False


def ensure_memory() -> None:
    """Load verified translations once: the scenario's reference translations, feed items and simulator samples."""
    global _loaded
    if _loaded:
        return
    from app.channels.adapters import verified_translations
    from app.sim.kodagu_reports import translation_memory
    load_memory(translation_memory())
    load_memory(verified_translations())
    try:
        from app.sim.samples import verified_translations as samples
        load_memory(samples())
    except ImportError:
        pass
    _loaded = True
