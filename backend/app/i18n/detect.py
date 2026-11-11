"""Lightweight language + script detection (the fallback when Gemini is unavailable).
- Native script: Unicode block counts. Shared blocks are split by markers: Devanagari -> Hindi / Marathi / Nepali by
  marker words; Bengali block -> Assamese when ৰ/ৱ appear, else Bengali. Bodo (Devanagari), Manipuri in Bengali script,
  Garo and Kokborok are NOT reliably detected yet (support "pending" in languages.json).
- Romanized: token cues per language (Kanglish, Hinglish, Manglish, Mizo, Khasi, ...), English by stop-word ratio.
- Script: native | romanized | mixed (native script plus Latin words in one message)."""
import re
import unicodedata
from dataclasses import dataclass

from app.i18n.languages import script_of_char
from app.i18n.lexicon import ASSAMESE_CHARS, ENGLISH_CUES, MARATHI_MARKERS, NEPALI_MARKERS, ROMAN_CUES

_HINDI = {"है", "हैं", "में", "और", "नहीं", "चाहिए", "पानी", "मदद", "को", "के", "लोग", "लोगों", "पास", "तुरंत", "भेजो", "दवाई"}


@dataclass
class Detection:
    language: str
    script: str            # native | romanized | mixed
    confidence: float
    evidence: str


def normalise(text: str) -> str:
    return unicodedata.normalize("NFC", text or "").strip()


def latin_words(text: str) -> list[str]:
    """Latin-alphabet words, ignoring hashtags/handles, URLs and all-caps codes like NH275."""
    words = re.findall(r"(?<![#@/\w])[A-Za-z][A-Za-z']+", text)
    return [w.lower() for w in words if not (w.isupper() and len(w) <= 6)]


def detect(text: str) -> Detection:
    t = normalise(text)
    counts: dict[str, int] = {}
    for ch in t:
        code = script_of_char(ch)
        if code:
            counts[code] = counts.get(code, 0) + 1
    words = latin_words(t)
    native_total = sum(counts.values())
    if native_total:
        lang = max(counts, key=counts.get)
        block = lang
        if lang == "hi":  # Devanagari: Hindi, Marathi or Nepali
            toks = set(re.findall(r"[ऀ-ॿ]+", t))
            score = {"hi": len(toks & _HINDI), "mr": len(toks & MARATHI_MARKERS), "ne": len(toks & NEPALI_MARKERS)}
            top = max(score, key=score.get)
            if score[top] > score["hi"]:
                lang = top
        elif lang == "bn" and any(c in ASSAMESE_CHARS for c in t):
            lang = "as"
        share = counts.get(block, 0) / max(1, native_total)
        mixed = sum(1 for w in words if len(w) >= 3) >= 2
        script = "mixed" if mixed else "native"
        conf = round(min(0.99, 0.75 + 0.24 * share - (0.1 if mixed else 0)), 2)
        return Detection(lang, script, conf, f"{native_total} characters in the {lang} Unicode block" + (", plus Latin words" if mixed else ""))
    if not words:
        return Detection("en", "romanized", 0.3, "no letters found")
    scores = {lang: sum(1 for w in words if w in cues) for lang, cues in ROMAN_CUES.items()}
    eng = sum(1 for w in words if w in ENGLISH_CUES)
    best = max(scores, key=scores.get)
    if scores[best] >= 2 or (scores[best] >= 1 and scores[best] >= eng):
        conf = round(min(0.95, 0.5 + 0.1 * scores[best]), 2)
        script = "mixed" if eng >= 2 else "romanized"
        return Detection(best, script, conf, f"romanized {best} cue words: {scores[best]} (English cues {eng})")
    conf = round(min(0.97, 0.55 + 0.4 * eng / max(1, len(words))), 2)
    return Detection("en", "native", conf, f"{eng} of {len(words)} words are common English words")


def to_ascii_digits(text: str) -> str:
    """Kannada, Devanagari, Malayalam, Tamil, Telugu, Bengali digits -> 0-9."""
    out = []
    for ch in text:
        if ch.isdigit() and not ch.isascii():
            try:
                out.append(str(unicodedata.digit(ch)))
                continue
            except (TypeError, ValueError):
                pass
        out.append(ch)
    return "".join(out)
