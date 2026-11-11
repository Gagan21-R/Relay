"""World specs. A world is the static geography a scenario runs on: zones (towns/villages with real coordinates),
landmarks, roads (with kind and vehicle suitability), depots and stock, shelters, hospitals, sources, volunteers and
shelter check-ins. Kodagu is hand-built; Scenario Lab worlds are generated from compact specs (app.sim.lab).
Every person, stock count, shelter/hospital capacity and report is SYNTHETIC; place coordinates are real but approximate."""
from app.sim import kodagu_world as KW

# volunteers: code, name, zone, skills, vehicle, languages, (assigned_tasks, on_time_confirmations) history
KODAGU_VOLUNTEERS = [
    ("V-001", "Ravi K", "madikeri", ["rescue", "driving", "first_aid"], "4x4", ["kn", "en"], (6, 5)),
    ("V-002", "Anita P", "kushalnagar", ["medical", "first_aid", "logistics"], "truck", ["en", "kn", "hi"], (4, 4)),
    ("V-003", "Salim M", "virajpet", ["boat", "rescue", "swimming"], "boat", ["ml", "kn"], (5, 3)),
    ("V-004", "Deepa B", "napoklu", ["logistics", "translation"], "two_wheeler", ["kn", "en", "ta"], (2, 2)),
    ("V-005", "Mahesh T", "somwarpet", ["driving", "logistics"], "truck", ["kn", "hi"], (8, 5)),
    ("V-006", "Joseph A", "siddapura", ["boat", "rescue"], "boat", ["ml", "en"], (3, 3)),
    ("V-007", "Kaveri N", "madikeri", ["medical", "translation"], None, ["kn", "en", "hi"], (0, 0)),
    ("V-008", "Imran S", "kushalnagar", ["driving", "rescue"], "4x4", ["hi", "kn", "en"], (5, 2)),
    ("V-009", "Lakshmi R", "bhagamandala", ["first_aid", "logistics"], "two_wheeler", ["kn"], (1, 1)),
    ("V-010", "Arjun C", "virajpet", ["driving", "logistics"], "truck", ["kn", "en"], (2, 1)),
]

KODAGU_HOSPITALS = [  # names are generic facility types; bed counts synthetic
    ("District hospital, Madikeri", "madikeri", 12.4215, 75.7365, 300),
    ("Community Health Centre, Napoklu", "napoklu", 12.3045, 75.7030, 30),
    ("Taluk hospital, Virajpet", "virajpet", 12.1955, 75.8030, 100),
    ("Community Health Centre, Kushalnagar", "kushalnagar", 12.4570, 75.9610, 30),
    ("Taluk hospital, Somwarpet", "somwarpet", 12.5955, 75.8495, 60),
]

# road attributes (kind, surface, allowed vehicles); anything not listed is a paved road open to every vehicle
KODAGU_ROAD_ATTRS = {
    "r_mad_jod": {"kind": "ghat"},
    "r_nap_sid": {"kind": "causeway", "allowed_vehicles": ["truck", "4x4", "ambulance", "two_wheeler", "boat"]},
    "r_mak_hat": {"surface": "unpaved", "allowed_vehicles": ["4x4", "two_wheeler"]},
    "r_som_hat": {"kind": "bridge", "allowed_vehicles": ["4x4", "ambulance", "two_wheeler"]},
    "r_nap_bha": {"kind": "bridge"},
}


def kodagu() -> dict:
    return {
        "id": "kodagu", "name": "Kodagu district", "state": "Karnataka", "center": KW.DISTRICT["center"], "zoom": 10,
        "languages": ["kn", "en", "hi", "ml"],
        "zones": KW.ZONES, "landmarks": KW.LANDMARKS,
        "roads": [(c, n, a, b, KODAGU_ROAD_ATTRS.get(c, {})) for c, n, a, b in KW.ROADS],
        "depots": KW.DEPOTS, "shelters": KW.SHELTERS, "hospitals": KODAGU_HOSPITALS, "sources": KW.SOURCES,
        "volunteers": KODAGU_VOLUNTEERS, "checkins": KW.CHECKINS,
        "managers": {"napoklu": "mgr_napoklu", "kushalnagar": "mgr_kushal"},
    }


def get(world_id: str) -> dict:
    if world_id == "kodagu":
        return kodagu()
    from app.sim import lab
    return lab.world(world_id)
