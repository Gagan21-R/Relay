"""Scenario definitions. The three hand-built ones are in Kodagu; the Scenario Lab adds ~47
generated ones across India (app.sim.lab). All synthetic. They share the world but differ in the
hazard footprint, the signal timeline and which reports arrive, so the map looks and behaves differently."""
from app.sim import kodagu_reports as KR
from app.sim import kodagu_world as KW
from app.sim import lab

HARANGI_FLOOD_1 = [
    [[12.47, 75.93], [12.47, 75.975], [12.445, 75.975], [12.445, 75.93]],          # Kushalnagar riverside
    [[12.505, 75.895], [12.505, 75.925], [12.485, 75.925], [12.485, 75.895]],       # below Harangi dam
]
HARANGI_FLOOD_2 = HARANGI_FLOOD_1 + [
    [[12.365, 75.865], [12.365, 75.9], [12.335, 75.9], [12.335, 75.865]],          # Siddapura / Karadigodu
    [[12.556, 75.772], [12.556, 75.798], [12.535, 75.798], [12.535, 75.772]],       # Hattihole
]
SLIDE_ZONES = [
    [[12.44, 75.715], [12.44, 75.745], [12.418, 75.745], [12.418, 75.715]],         # Madikeri hills
    [[12.50, 75.615], [12.50, 75.645], [12.48, 75.645], [12.48, 75.615]],           # Jodupala ghat
    [[12.485, 75.76], [12.485, 75.785], [12.46, 75.785], [12.46, 75.76]],           # Makkandur
    [[12.556, 75.772], [12.556, 75.798], [12.535, 75.798], [12.535, 75.772]],       # Hattihole
]

SCENARIOS = {
    "kodagu_flood": {
        "name": "Kodagu monsoon flood", "hazard": "flood", "colour": "#9FB7BC",
        "description": "Cauvery overflows at Bhagamandala, Napoklu, Siddapura and Kushalnagar over 12 hours; Hattihole goes silent. The full demo story.",
        "signals": KW.SIGNALS, "zones": None, "world": "kodagu", "disaster": "flood", "difficulty": "advanced",
        "region": ["hilly", "rural", "south"], "state": "Karnataka",
        "objectives": ["Rescue the 12 people on rooftops at Napoklu", "Keep every shelter supplied for 48 h", "Notice the silent village (Hattihole)", "Stop the dam-burst rumour"],
        "expected": ["Rooftop rescue planned within 2 h of first report", "No shelter runs dry", "Recon team proposed for Hattihole", "Correction published in 8 languages"],
    },
    "harangi_release": {
        "name": "Harangi dam release", "hazard": "flood", "colour": "#C2D4B1",
        "description": "Heavy controlled releases from Harangi flood Kushalnagar and Siddapura first; rumours say the dam burst.",
        "signals": [
            (0.0, "rainfall", "kushalnagar", {"mm_24h": 170, "category": "very heavy"}, "IMD (mock)"),
            (1.0, "dam", "kushalnagar", {"dam": "Harangi", "release_cusecs": 45000, "structure": "safe", "bulletin": "Heavy controlled release; dam safe"}, "Water Resources Dept (mock)"),
            (1.5, "flood_extent", None, {"version": 1, "polygons": HARANGI_FLOOD_1}, "Satellite flood extent (mock)"),
            (2.0, "tower_outage", "hattihole", {"towers_down": 2, "towers_total": 2}, "Telecom operator feed (mock)"),
            (2.0, "power_outage", "hattihole", {"feeders_off": 1}, "CESC power feed (mock)"),
            (4.0, "river", "kushalnagar", {"station": "Cauvery at Kudige", "level_m": 9.0, "danger_m": 7.9}, "CWC (mock)"),
            (6.0, "flood_extent", None, {"version": 2, "polygons": HARANGI_FLOOD_2}, "Satellite flood extent (mock)"),
        ],
        "zones": {"kushalnagar", "siddapura", "somwarpet", "hattihole", "virajpet"}, "world": "kodagu", "disaster": "flood", "difficulty": "intermediate",
        "region": ["hilly", "rural", "south"], "state": "Karnataka",
        "objectives": ["Supply Kushalnagar and Siddapura camps", "Counter the dam-burst rumour with the official bulletin"],
        "expected": ["Plan proposed for Kushalnagar/Siddapura", "Dam-burst reports marked disputed/false"],
    },
    "madikeri_landslides": {
        "name": "Madikeri hill landslides", "hazard": "landslide", "colour": "#D2A98A",
        "description": "Extreme rain triggers landslides around Madikeri, the Jodupala ghat and Makkandur; roads cut, a small quake shakes the hills.",
        "signals": [
            (0.0, "rainfall", "madikeri", {"mm_24h": 260, "category": "extremely heavy"}, "IMD (mock)"),
            (0.5, "rainfall", "jodupala", {"mm_24h": 240, "category": "extremely heavy"}, "IMD (mock)"),
            (1.0, "flood_extent", None, {"version": 1, "polygons": SLIDE_ZONES[:2]}, "Landslide susceptibility / slide extent (mock)"),
            (2.0, "tower_outage", "hattihole", {"towers_down": 2, "towers_total": 2}, "Telecom operator feed (mock)"),
            (2.0, "power_outage", "hattihole", {"feeders_off": 1}, "CESC power feed (mock)"),
            (3.0, "quake", None, {"magnitude": 3.4, "place": "near Madikeri", "depth_km": 10}, "Seismic network (mock)"),
            (5.0, "flood_extent", None, {"version": 2, "polygons": SLIDE_ZONES}, "Landslide extent (mock)"),
            (7.0, "tower_outage", "jodupala", {"towers_down": 2, "towers_total": 2}, "Telecom operator feed (mock)"),
        ],
        "zones": {"madikeri", "jodupala", "makkandur", "hattihole", "somwarpet", "napoklu"}, "world": "kodagu", "disaster": "landslide", "difficulty": "intermediate",
        "region": ["hilly", "rural", "south"], "state": "Karnataka",
        "objectives": ["Reroute supplies around cut ghat roads", "Reach stranded drivers at Jodupala"],
        "expected": ["Routes avoid blocked ghat roads", "Food line planned to Jodupala"],
    },
}


SCENARIOS.update(lab.SCENARIOS)


def reports_for(sid: str) -> list:
    sc = SCENARIOS[sid]
    if sc.get("reports") is not None:
        return sc["reports"]
    zones = sc["zones"]
    if zones is None:
        return KR.REPORTS
    return [r for r in KR.REPORTS if r[4]["origin_zone"] in zones or r[4]["origin_zone"] is None]
