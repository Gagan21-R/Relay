"""Supported languages, loaded from languages.json so a new language is a config change, not a code change."""
import json
from pathlib import Path

_RAW = json.loads((Path(__file__).with_name("languages.json")).read_text(encoding="utf-8"))
LANGUAGES: dict[str, dict] = {k: v for k, v in _RAW.items() if not k.startswith("_")}


def is_supported(code: str) -> bool:
    return code in LANGUAGES


def script_of_char(ch: str) -> str | None:
    """Return the language code whose Unicode block contains this character (first match), else None."""
    cp = ord(ch)
    for code, v in LANGUAGES.items():
        rng = v.get("unicode_range")
        if rng and int(rng[0], 16) <= cp <= int(rng[1], 16):
            return code
    return None
