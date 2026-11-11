"""Phone numbers are stored hashed (for matching repeat senders) and shown masked (+91 98XXXXX210)."""
import hashlib
import re

from app.core.config import get_settings


def normalise_phone(raw: str) -> str:
    digits = re.sub(r"[^\d+]", "", raw or "")
    if digits and not digits.startswith("+"):
        digits = "+91" + digits[-10:] if len(digits) >= 10 else digits
    return digits


def hash_phone(raw: str) -> str:
    return hashlib.sha256((get_settings().phone_hash_salt + normalise_phone(raw)).encode()).hexdigest()


def mask_phone(raw: str) -> str:
    p = normalise_phone(raw)
    if len(p) < 8:
        return "XXXX"
    cc, local = (p[:3], p[3:]) if p.startswith("+91") else (p[:-10] or "", p[-10:])
    return f"{cc} {local[:2]}{'X' * (len(local) - 5)}{local[-3:]}".strip()
