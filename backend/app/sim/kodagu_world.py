"""Static world for the demo scenario: Kodagu (Coorg) district, Karnataka — a real flood- and landslide-prone district
(2018 and 2019 monsoon floods). Real town coordinates; every person, report, stock count and incident is SYNTHETIC."""

DISTRICT = {"name": "Kodagu", "state": "Karnataka", "center": [12.42, 75.76], "event_start_note": "T+0 h = start of the synthetic monsoon flood"}

# code, name, lat, lng, population, normal reports/hour, vulnerability, gazetteer aliases (several scripts and spellings)
ZONES = [
    ("madikeri", "Madikeri", 12.4244, 75.7382, 33000, 3.0, {"elderly_share": 0.11, "children_share": 0.22, "medical_facilities": 2, "remoteness": 0.1},
     ["madikeri", "mercara", "madkeri", "madikeri town", "ಮಡಿಕೇರಿ", "मडिकेरी", "മടിക്കേരി", "மடிகேரி", "మడికేరి", "মাদিকেরি"]),
    ("makkandur", "Makkandur", 12.4716, 75.7712, 4200, 0.4, {"elderly_share": 0.16, "children_share": 0.2, "medical_facilities": 0, "remoteness": 0.5},
     ["makkandur", "makkanduru", "makkandoor", "ಮಕ್ಕಂದೂರು", "ಮಕ್ಕಂದೂರಿನಲ್ಲಿ", "मक्कंदूर"]),
    ("jodupala", "Jodupala", 12.4898, 75.6290, 1800, 0.3, {"elderly_share": 0.14, "children_share": 0.2, "medical_facilities": 0, "remoteness": 0.6},
     ["jodupala", "jodupal", "jodupaala", "ಜೋಡುಪಾಲ", "जोडुपाला", "ജോഡുപാല", "sampaje", "ಸಂಪಾಜೆ"]),
    ("bhagamandala", "Bhagamandala", 12.3870, 75.5318, 3500, 0.5, {"elderly_share": 0.18, "children_share": 0.18, "medical_facilities": 1, "remoteness": 0.6},
     ["bhagamandala", "bhagamandla", "bagamandala", "ಭಾಗಮಂಡಲ", "भागमंडला", "ഭാഗമണ്ഡല", "பாகமண்டலா", "triveni sangama", "ತ್ರಿವೇಣಿ ಸಂಗಮ", "त्रिवेणी संगम", "திரிவேணி சங்கமம்"]),
    ("napoklu", "Napoklu", 12.3050, 75.7010, 6500, 0.6, {"elderly_share": 0.15, "children_share": 0.21, "medical_facilities": 1, "remoteness": 0.4},
     ["napoklu", "napokulu", "napoklu town", "ನಾಪೋಕ್ಲು", "नापोक्लु", "നാപോക്ലു", "நாபோக்லு"]),
    ("siddapura", "Siddapura", 12.3540, 75.8840, 8000, 0.8, {"elderly_share": 0.12, "children_share": 0.24, "medical_facilities": 1, "remoteness": 0.3},
     ["siddapura", "siddapur", "siddhapura", "ಸಿದ್ದಾಪುರ", "सिद्दापुर", "സിദ്ധാപുര", "karadigodu", "karadigod", "ಕರಡಿಗೋಡು", "करडिगोडु"]),
    ("kushalnagar", "Kushalnagar", 12.4580, 75.9590, 16000, 1.6, {"elderly_share": 0.1, "children_share": 0.23, "medical_facilities": 1, "remoteness": 0.1},
     ["kushalnagar", "kushalnagara", "kushal nagar", "ಕುಶಾಲನಗರ", "ಕುಶಾಲನಗರದ", "कुशालनगर", "കുശാൽനഗർ", "குஷால்நகர்", "குஷால்நகர", "കുശാൽനഗറ", "harangi", "ಹಾರಂಗಿ", "हारंगी"]),
    ("somwarpet", "Somwarpet", 12.5970, 75.8510, 9000, 0.9, {"elderly_share": 0.13, "children_share": 0.2, "medical_facilities": 1, "remoteness": 0.3},
     ["somwarpet", "somavarapete", "somvarpet", "ಸೋಮವಾರಪೇಟೆ", "ಸೋಮವಾರಪೇಟೆಯಲ್ಲಿ", "सोमवारपेट", "సోమవారపేట"]),
    ("virajpet", "Virajpet", 12.1970, 75.8050, 18000, 1.8, {"elderly_share": 0.11, "children_share": 0.22, "medical_facilities": 2, "remoteness": 0.2},
     ["virajpet", "virajapete", "virajpete", "ವಿರಾಜಪೇಟೆ", "विराजपेट", "വിരാജ്പേട്ട", "விராஜ்பேட்டை"]),
    ("hattihole", "Hattihole", 12.5450, 75.7850, 2400, 0.4, {"elderly_share": 0.2, "children_share": 0.21, "medical_facilities": 0, "remoteness": 0.8},
     ["hattihole", "hatti hole", "hattiholé", "ಹಟ್ಟಿಹೊಳೆ", "ಹಟ್ಟಿಹೊಳೆಯಲ್ಲಿರುವ", "हट्टीहोले"]),
]

# landmarks inside zones (canonical, zone, lat, lng, aliases)
LANDMARKS = [
    ("Govt High School, Napoklu", "napoklu", 12.3068, 75.6992, ["napoklu school", "govt school napoklu", "govt high school", "ನಾಪೋಕ್ಲು ಸರ್ಕಾರಿ ಶಾಲೆ", "ಸರ್ಕಾರಿ ಶಾಲೆ", "നാപോക്ലു സ്കൂൾ", "സ്കൂളിനടുത്ത്"]),
    ("Karadigodu village", "siddapura", 12.3420, 75.8790, ["karadigodu", "karadigod", "ಕರಡಿಗೋಡು", "करडिगोडु"]),
    ("Triveni Sangama, Bhagamandala", "bhagamandala", 12.3855, 75.5300, ["triveni sangama", "sangama", "ತ್ರಿವೇಣಿ ಸಂಗಮ", "त्रिवेणी संगम", "திரிவேணி சங்கமம்", "bhagamandala mandir", "bhagamandala temple"]),
    ("Indira Nagar, Madikeri", "madikeri", 12.4300, 75.7330, ["indira nagar", "indiranagar", "ಇಂದಿರಾನಗರ", "ಇಂದಿರಾನಗರದಲ್ಲಿ"]),
    ("Madikeri bus stand", "madikeri", 12.4230, 75.7400, ["bus stand", "ಬಸ್ ನಿಲ್ದಾಣ"]),
    ("Sai Layout, Kushalnagar", "kushalnagar", 12.4620, 75.9520, ["sai layout", "ಸಾಯಿ ಬಡಾವಣೆ", "ಸಾಯಿ ಬಡಾವಣೆಯಲ್ಲಿ", "साई लेआउट", "சாய் லேஅவுட்"]),
    ("Harangi dam", "kushalnagar", 12.4920, 75.9070, ["harangi dam", "ಹಾರಂಗಿ ಅಣೆಕಟ್ಟು", "हारंगी बांध"]),
    ("NH275 at Jodupala", "jodupala", 12.4890, 75.6320, ["nh275", "nh 275", "highway jodupala", "ಹೆದ್ದಾರಿ"]),
    ("Siddapura estate lines", "siddapura", 12.3600, 75.8920, ["siddapura estate", "सिद्दापुर एस्टेट", "estate lines"]),
    ("Kushalnagar old-age home", "kushalnagar", 12.4550, 75.9640, ["old age home", "oldage home", "ವೃದ್ಧಾಶ್ರಮ", "वृद्धाश्रम"]),
]

# roads between zone centres (code, name, a, b). Points are the two towns with a mid-point bend.
ROADS = [
    ("r_mad_mak", "Madikeri–Makkandur road", "madikeri", "makkandur"),
    ("r_mad_jod", "NH275 Madikeri–Jodupala ghat", "madikeri", "jodupala"),
    ("r_mad_nap", "Madikeri–Napoklu road", "madikeri", "napoklu"),
    ("r_nap_bha", "Napoklu–Bhagamandala road", "napoklu", "bhagamandala"),
    ("r_mad_bha", "Madikeri–Bhagamandala road", "madikeri", "bhagamandala"),
    ("r_mad_kus", "NH275 Madikeri–Kushalnagar", "madikeri", "kushalnagar"),
    ("r_kus_sid", "Kushalnagar–Siddapura road", "kushalnagar", "siddapura"),
    ("r_sid_vir", "Siddapura–Virajpet road", "siddapura", "virajpet"),
    ("r_mad_vir", "Madikeri–Virajpet road (Murnad)", "madikeri", "virajpet"),
    ("r_kus_som", "Kushalnagar–Somwarpet road", "kushalnagar", "somwarpet"),
    ("r_som_hat", "Somwarpet–Hattihole road", "somwarpet", "hattihole"),
    ("r_mak_hat", "Makkandur–Hattihole road", "makkandur", "hattihole"),
    ("r_nap_sid", "Napoklu–Siddapura road (Cauvery bank)", "napoklu", "siddapura"),
]

DEPOTS = [
    ("Madikeri District Relief Depot", "District administration", "madikeri", 12.4205, 75.7440,
     {"food_kits": 900, "water_litres": 20000, "medical_kits": 150, "boats": 4, "blankets": 800, "volunteers": 40, "vehicles": 8}, 0.0),
    ("Kushalnagar KSDMA Warehouse", "KSDMA (state)", "kushalnagar", 12.4560, 75.9555,
     {"food_kits": 600, "water_litres": 14000, "medical_kits": 80, "boats": 3, "blankets": 500, "volunteers": 25, "vehicles": 5}, 0.0),
    ("Virajpet Coorg Relief Collective store", "NGO (synthetic)", "virajpet", 12.1990, 75.8020,
     {"food_kits": 300, "water_litres": 6000, "medical_kits": 60, "boats": 1, "blankets": 300, "volunteers": 15, "vehicles": 3}, -20.0),  # last counted 20 h before the event: stale
]

UNITS = {"food_kits": "kits", "water_litres": "L", "medical_kits": "kits", "boats": "boats", "blankets": "pcs", "volunteers": "people", "vehicles": "vehicles"}

# name, zone, lat, lng, capacity, occupancy, access roads (all must be closed for the shelter to be cut off), stock
SHELTERS = [
    ("Madikeri Town Hall relief camp", "madikeri", 12.4250, 75.7395, 350, 210, [], {"water_litres": 9000, "food_kits": 260, "medical_kits": 30, "blankets": 250}),
    ("Napoklu Govt High School camp", "napoklu", 12.3070, 75.6985, 300, 240, ["r_mad_nap", "r_nap_sid"], {"water_litres": 4500, "food_kits": 160, "medical_kits": 12, "blankets": 200}),
    ("Kushalnagar Rotary Hall camp", "kushalnagar", 12.4600, 75.9600, 400, 300, [], {"water_litres": 12000, "food_kits": 320, "medical_kits": 25, "blankets": 320}),
    ("Siddapura Govt School camp", "siddapura", 12.3560, 75.8830, 250, 190, ["r_kus_sid", "r_sid_vir"], {"water_litres": 6500, "food_kits": 180, "medical_kits": 14, "blankets": 150}),
    ("Virajpet Kodava Samaja Hall camp", "virajpet", 12.1985, 75.8070, 300, 150, [], {"water_litres": 7000, "food_kits": 170, "medical_kits": 10, "blankets": 160}),
    ("Somwarpet Community Hall camp", "somwarpet", 12.5960, 75.8530, 200, 120, ["r_kus_som"], {"water_litres": 4000, "food_kits": 120, "medical_kits": 8, "blankets": 120}),
]

# Sphere-style per-person standards (configurable): water 15 L/person/day minimum; one food kit feeds a person 3 days.
STANDARDS_PER_PERSON_DAY = {"water_litres": 15.0, "food_kits": 1 / 3, "medical_kits": 0.02, "blankets": 0.0}

# key, type, name, phone (synthetic), preferred language
SOURCES = [
    ("ksdma", "official_agency", "KSDMA control room", None, "en"),
    ("dc_office", "official_agency", "Kodagu DC office", None, "kn"),
    ("cwc", "sensor", "CWC river gauge network", None, "en"),
    ("imd", "sensor", "IMD rain gauges", None, "en"),
    ("ndrf2", "field_team", "NDRF team 2", "+919900011002", "en"),
    ("sdrf", "field_team", "SDRF Kodagu", "+919900011003", "kn"),
    ("fire", "field_team", "Fire & Emergency Services Madikeri", "+919900011004", "kn"),
    ("vol_ravi", "volunteer", "Ravi K (volunteer)", "+919845012345", "kn"),
    ("vol_anita", "volunteer", "Anita P (volunteer)", "+919845012346", "en"),
    ("vol_salim", "volunteer", "Salim M (volunteer)", "+919845012347", "ml"),
    ("ngo_crc", "ngo", "Coorg Relief Collective", "+919845012348", "en"),
    ("mgr_napoklu", "volunteer", "Napoklu camp manager", "+919845012350", "kn"),
    ("mgr_kushal", "volunteer", "Kushalnagar camp manager", "+919845012351", "kn"),
    ("news_kn", "social", "Prajavani-style regional news (mock)", None, "kn"),
    ("news_en", "social", "Coorg Today (mock news)", None, "en"),
    ("news_hi", "social", "Hindi regional news (mock)", None, "hi"),
    ("news_ml", "social", "Malayalam regional news (mock)", None, "ml"),
]

# Signals (non-human feeds) on the scenario timeline. Flood extents are polygons [[lat, lng], ...].
FLOOD_V1 = [  # Cauvery at Bhagamandala and Napoklu
    [[12.392, 75.522], [12.395, 75.540], [12.380, 75.545], [12.376, 75.526]],
    [[12.312, 75.690], [12.312, 75.712], [12.298, 75.712], [12.298, 75.690]],
]
FLOOD_V2 = FLOOD_V1 + [  # Siddapura / Karadigodu and Kushalnagar Sai Layout
    [[12.350, 75.870], [12.350, 75.890], [12.334, 75.890], [12.334, 75.870]],
    [[12.468, 75.945], [12.468, 75.960], [12.455, 75.960], [12.455, 75.945]],
]
FLOOD_V3 = FLOOD_V2 + [  # Hattihole landslide-and-flood belt (the silent village)
    [[12.556, 75.772], [12.556, 75.798], [12.535, 75.798], [12.535, 75.772]],
]
# demo step 11 adds this: the Cauvery covers both roads into Siddapura camp
FLOOD_SIDDAPURA_ROADS = [[12.40, 75.86], [12.40, 75.95], [12.33, 75.95], [12.33, 75.86]]
FLOOD_SIDDAPURA_SOUTH = [[12.35, 75.83], [12.35, 75.89], [12.26, 75.89], [12.26, 75.83]]

SIGNALS = [
    # t, type, zone code or None, value, source
    (0.0, "rainfall", "bhagamandala", {"mm_24h": 212, "category": "extremely heavy"}, "IMD (mock)"),
    (0.0, "rainfall", "madikeri", {"mm_24h": 184, "category": "very heavy"}, "IMD (mock)"),
    (0.0, "rainfall", "napoklu", {"mm_24h": 160, "category": "very heavy"}, "IMD (mock)"),
    (0.0, "flood_extent", None, {"version": 1, "polygons": FLOOD_V1}, "Satellite flood extent (mock, Sentinel-1 style)"),
    (1.0, "river", "bhagamandala", {"station": "Cauvery at Bhagamandala", "level_m": 7.9, "danger_m": 7.5}, "CWC (mock)"),
    (1.0, "river", "napoklu", {"station": "Cauvery at Napoklu", "level_m": 6.8, "danger_m": 6.5}, "CWC (mock)"),
    (2.0, "tower_outage", "hattihole", {"towers_down": 2, "towers_total": 2}, "Telecom operator feed (mock)"),
    (2.0, "power_outage", "hattihole", {"feeders_off": 1}, "CESC power feed (mock)"),
    (3.0, "dam", "kushalnagar", {"dam": "Harangi", "release_cusecs": 20000, "structure": "safe", "bulletin": "Controlled release; dam structure safe"}, "Water Resources Dept (mock)"),
    (4.0, "rainfall", "hattihole", {"mm_24h": 230, "category": "extremely heavy"}, "IMD (mock)"),
    (5.0, "river", "siddapura", {"station": "Cauvery at Siddapura", "level_m": 9.4, "danger_m": 8.8}, "CWC (mock)"),
    (6.0, "flood_extent", None, {"version": 2, "polygons": FLOOD_V2}, "Satellite flood extent (mock, Sentinel-1 style)"),
    (6.5, "river", "kushalnagar", {"station": "Cauvery at Kudige", "level_m": 8.1, "danger_m": 7.9}, "CWC (mock)"),
    (7.0, "tower_outage", "jodupala", {"towers_down": 1, "towers_total": 2}, "Telecom operator feed (mock)"),
    (9.0, "flood_extent", None, {"version": 3, "polygons": FLOOD_V3}, "Satellite flood extent (mock, Sentinel-1 style)"),
]

# Shelter manager check-ins on the timeline (t, shelter name prefix, occupancy). Somwarpet misses its later check-ins.
CHECKINS = [
    (3.0, "Somwarpet", 120),
    (4.0, "Madikeri", 215), (4.5, "Napoklu", 240), (5.0, "Kushalnagar", 300), (5.5, "Siddapura", 190), (6.0, "Virajpet", 150),
    (9.0, "Madikeri", 222), (9.5, "Napoklu", 240), (10.0, "Kushalnagar", 340), (10.5, "Siddapura", 195), (11.0, "Virajpet", 160),
]
