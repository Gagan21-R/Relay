"""GDACS (Global Disaster Alert and Coordination System) alerts for India, with an offline fallback.
Every alert says where it came from: LIVE (fetched now), STALE (last good fetch older than 30 min), FALLBACK (bundled
sample used because the network/feed is unavailable or mock mode is on). Fallback items are illustrative, not real."""
import time

from app.core.config import get_settings

URL = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"
STALE_AFTER_S = 1800
_cache: dict = {"at": 0.0, "items": []}

FALLBACK = [  # illustrative sample shaped like GDACS events (NOT real alerts)
    {"id": "FALLBACK-FL-1", "type": "FL", "name": "Flood alert (sample)", "country": "India", "lat": 26.2, "lng": 92.9, "level": "Orange",
     "from": "sample", "description": "Illustrative flood event in Assam used when the live feed is unavailable."},
    {"id": "FALLBACK-TC-1", "type": "TC", "name": "Tropical cyclone (sample)", "country": "India", "lat": 17.7, "lng": 83.3, "level": "Red",
     "from": "sample", "description": "Illustrative cyclone near the Andhra coast used when the live feed is unavailable."},
    {"id": "FALLBACK-EQ-1", "type": "EQ", "name": "Earthquake M5.1 (sample)", "country": "India", "lat": 26.1, "lng": 91.7, "level": "Green",
     "from": "sample", "description": "Illustrative earthquake near Guwahati used when the live feed is unavailable."},
    {"id": "FALLBACK-DR-1", "type": "DR", "name": "Drought (sample)", "country": "India", "lat": 14.7, "lng": 77.6, "level": "Orange",
     "from": "sample", "description": "Illustrative drought in Rayalaseema used when the live feed is unavailable."},
]


def _fetch() -> list[dict]:  # pragma: no cover - network
    import httpx
    r = httpx.get(URL, params={"country": "IND", "limit": 30}, timeout=6)
    r.raise_for_status()
    out = []
    for f in r.json().get("features", []):
        p, g = f.get("properties", {}), f.get("geometry", {}).get("coordinates", [None, None])
        out.append({"id": f"{p.get('eventtype')}-{p.get('eventid')}", "type": p.get("eventtype"), "name": p.get("name") or p.get("eventname"),
                    "country": p.get("country"), "lat": g[1], "lng": g[0], "level": p.get("alertlevel"),
                    "from": p.get("fromdate"), "description": p.get("description") or p.get("htmldescription", "")[:200]})
    return out


def alerts(force: bool = False) -> dict:
    now = time.time()
    if get_settings().mock:
        return {"status": "fallback", "reason": "mock mode: live feeds are not called", "items": [{**i, "data": "fallback"} for i in FALLBACK]}
    if force or now - _cache["at"] > 300:
        try:
            _cache.update(at=now, items=_fetch(), error=None)
        except Exception as e:  # noqa: BLE001
            _cache["error"] = str(e)[:120]
    if _cache["items"]:
        stale = now - _cache["at"] > STALE_AFTER_S
        return {"status": "stale" if stale else "live", "fetched_at": _cache["at"], "error": _cache.get("error"),
                "items": [{**i, "data": "stale" if stale else "live"} for i in _cache["items"]]}
    return {"status": "fallback", "reason": f"live feed unavailable ({_cache.get('error')})", "items": [{**i, "data": "fallback"} for i in FALLBACK]}
