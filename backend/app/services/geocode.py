"""Geocoding: the multilingual gazetteer first (exact alias in any script, then fuzzy for spelling variants such as
"napokulu"/"madkeri"), then an external geocoder (OpenStreetMap Nominatim, only outside mock mode).
Returns coordinates with a confidence and the evidence used."""
import difflib
import re
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Gazetteer

KIND_RANK = {"landmark": 3, "shelter": 3, "hospital": 2, "depot": 2, "village": 1, "town": 1}


@dataclass
class GeoResult:
    lat: float | None = None
    lng: float | None = None
    zone_id: int | None = None
    location_text: str | None = None
    confidence: float = 0.0
    method: str = "none"
    matches: list = field(default_factory=list)


def _has(text_low: str, alias: str) -> bool:
    a = alias.lower()
    if a.isascii():
        return re.search(r"(?<![a-z])" + re.escape(a) + r"(?![a-z])", text_low) is not None
    return a in text_low


def gazetteer_lookup(db: Session, text: str) -> GeoResult:
    low = (text or "").lower()
    entries = list(db.scalars(select(Gazetteer)))
    hits = []
    for g in entries:
        for a in g.aliases or []:
            if len(a) >= 3 and _has(low, a):
                hits.append((KIND_RANK.get(g.kind, 0), len(a), g, a, "exact"))
                break
    if not hits:  # fuzzy: Latin words close to a single-word alias (spelling variants)
        words = set(re.findall(r"[a-z]{5,}", low))
        for g in entries:
            for a in g.aliases or []:
                if a.isascii() and " " not in a and len(a) >= 5:
                    for w in words:
                        r = difflib.SequenceMatcher(None, w, a).ratio()
                        if r >= 0.84:
                            hits.append((KIND_RANK.get(g.kind, 0), r, g, f"{w}≈{a}", "fuzzy"))
    if not hits:
        return GeoResult()
    hits.sort(key=lambda h: (h[0], h[1]), reverse=True)
    rank, _, g, alias, how = hits[0]
    zones = {h[2].zone_id for h in hits}
    conf = (0.95 if rank >= 3 else 0.85) if how == "exact" else 0.7
    if len(zones) > 1:
        conf -= 0.15           # the text names places in different zones: less sure which one is meant
    return GeoResult(g.lat, g.lng, g.zone_id, g.canonical, round(conf, 2), f"gazetteer ({how})",
                     [{"canonical": h[2].canonical, "kind": h[2].kind, "alias": h[3], "how": h[4]} for h in hits[:4]])


def external_geocode(text: str) -> GeoResult:  # pragma: no cover - network
    if get_settings().mock:
        return GeoResult(method="external geocoder skipped (mock mode)")
    try:
        import httpx
        r = httpx.get("https://nominatim.openstreetmap.org/search", timeout=6,
                      params={"q": text, "format": "json", "limit": 1, "viewbox": "75.40,12.90,76.20,11.90", "bounded": 1},
                      headers={"User-Agent": "RELAY-hackathon-demo"})
        j = r.json()
        if j:
            return GeoResult(float(j[0]["lat"]), float(j[0]["lon"]), None, j[0].get("display_name"), 0.6, "nominatim")
    except Exception:  # noqa: BLE001
        pass
    return GeoResult(method="external geocoder: no result")


def geocode(db: Session, text: str) -> GeoResult:
    g = gazetteer_lookup(db, text)
    return g if g.lat is not None else external_geocode(text)
