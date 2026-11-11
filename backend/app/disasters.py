"""Nine disaster categories through ONE configuration (no separate apps or agent systems). Each profile drives:
indicators (what to look for in reports, per language), severity factors (life threat per need), per-person resource
requirements, map overlay style, and response recommendations. Agents read the active profile."""

DISASTERS: dict[str, dict] = {
    "flood": {
        "name": "Flood", "gdacs": "FL", "overlay": {"label": "Flood extent", "colour": "#2E5BFF", "fill": 0.35},
        "indicators": ["flood", "flooded", "water entered", "submerged", "inundated", "overflow", "बाढ़", "पानी भर", "ನೆರೆ", "ಪ್ರವಾಹ", "ನೀರು ನುಗ್ಗಿ",
                       "வெள்ளம்", "వరద", "വെള്ളപ്പൊക്ക", "പ്രളയ", "पूर", "বন্যা", "বান", "ପ୍ରଳୟ", "ବନ୍ୟା", "પૂર", "ਹੜ੍ਹ", "बाढी", "neeru bandide", "olage neeru", "ನೀರು ಬಂದಿದೆ", "ಒಳಗೆ ನೀರು", "full water", "water inside", "flood water", "baadh", "pani bhar", "tuilian", "um shaniah"],
        "life_threat": {"rescue": 1.0, "medical": 0.9, "water": 0.6, "food": 0.45, "shelter": 0.45, "infrastructure": 0.3},
        "per_person_day": {"water_litres": 15.0, "food_kits": 1 / 3, "medical_kits": 0.02, "ors_packets": 0.2},
        "fleet": ["boat", "truck", "4x4"],
        "recommendations": ["Pre-position boats where water is rising", "Move people to shelters above the flood line",
                            "Chlorinate drinking water; watch for water-borne disease", "Avoid flooded roads: 30 cm of moving water can sweep a car"],
    },
    "cyclone": {
        "name": "Cyclone / severe storm", "gdacs": "TC", "overlay": {"label": "Storm impact zone", "colour": "#6FA8DC", "fill": 0.25},
        "indicators": ["cyclone", "storm", "strong wind", "gale", "storm surge", "roof blown", "चक्रवात", "तूफान", "ಚಂಡಮಾರುತ", "புயல்", "తుఫాను",
                       "ചുഴലിക്കാറ്റ്", "চক্রবাত", "ঘূর্ণিঝড়", "ବାତ୍ୟା", "ଘୂର୍ଣ୍ଣିଝଡ", "વાવાઝોડું", "ਤੂਫ਼ਾਨ", "toofan", "tufan"],
        "life_threat": {"rescue": 1.0, "medical": 0.9, "shelter": 0.65, "water": 0.55, "food": 0.45, "infrastructure": 0.45},
        "per_person_day": {"water_litres": 15.0, "food_kits": 1 / 3, "tarpaulins": 0.2, "medical_kits": 0.02},
        "fleet": ["truck", "4x4", "boat"],
        "recommendations": ["Evacuate coastal low-lying areas before landfall", "Tarpaulins and roofing for damaged homes",
                            "Clear fallen trees from access roads first", "Restore power and telecom to hospitals first"],
    },
    "earthquake": {
        "name": "Earthquake", "gdacs": "EQ", "overlay": {"label": "Shaking intensity zone", "colour": "#D08A4E", "fill": 0.3},
        "indicators": ["earthquake", "tremor", "quake", "collapsed", "building fell", "rubble", "भूकंप", "मलबा", "ಭೂಕಂಪ", "நிலநடுக்கம்", "భూకంపం",
                       "ഭൂകമ്പ", "ভূমিকম্প", "ଭୂମିକମ୍ପ", "ભૂકંપ", "ਭੂਚਾਲ", "भूकम्प", "bhukamp", "malba", "khawpui nghing"],
        "life_threat": {"rescue": 1.0, "medical": 0.95, "shelter": 0.6, "water": 0.5, "food": 0.4, "infrastructure": 0.5},
        "per_person_day": {"water_litres": 15.0, "food_kits": 1 / 3, "medical_kits": 0.05, "tarpaulins": 0.25},
        "fleet": ["truck", "4x4"],
        "recommendations": ["Search and rescue in collapsed buildings in the first 72 hours", "Structural check before re-entering buildings",
                            "Field hospitals for crush injuries", "Expect aftershocks: keep people in open shelters"],
    },
    "landslide": {
        "name": "Landslide", "gdacs": None, "overlay": {"label": "Slide / debris zone", "colour": "#8A5A2B", "fill": 0.45},
        "indicators": ["landslide", "mudslide", "hill collapsed", "debris", "rocks fell", "भूस्खलन", "पहाड़ खिसका", "ಭೂಕುಸಿತ", "ಗುಡ್ಡ ಕುಸಿ",
                       "நிலச்சரிவு", "కొండచరియలు", "ഉരുൾപൊട്ട", "മണ്ണിടിച്ചിൽ", "ভূমিধস", "ଭୂସ୍ଖଳନ", "ભૂસ્ખલન", "ਢਿੱਗਾਂ", "पहिरो", "guddi kusidide", "pahad khiska", "lei min"],
        "life_threat": {"rescue": 1.0, "medical": 0.9, "infrastructure": 0.55, "shelter": 0.5, "food": 0.45, "water": 0.45},
        "per_person_day": {"water_litres": 15.0, "food_kits": 1 / 3, "medical_kits": 0.03},
        "fleet": ["4x4", "truck"],
        "recommendations": ["Keep people away from slopes below the slide", "Earth-movers to reopen the main access road",
                            "Airlift or foot teams for cut-off hamlets", "Watch for river blockage forming a dam"],
    },
    "wildfire": {
        "name": "Wildfire", "gdacs": "WF", "overlay": {"label": "Fire perimeter", "colour": "#FF5A1F", "fill": 0.4},
        "indicators": ["forest fire", "wildfire", "fire", "smoke", "burning", "जंगल में आग", "आग", "धुआं", "ಕಾಡ್ಗಿಚ್ಚು", "ಬೆಂಕಿ", "காட்டுத்தீ",
                       "അഗ്നി", "കാട്ടുതീ", "দাবানল", "আগুন", "ଜଙ୍ଗଲ ନିଆଁ", "જંગલની આગ", "ਅੱਗ", "आगलागी", "jungle mein aag", "kaadu benki"],
        "life_threat": {"rescue": 1.0, "medical": 0.95, "shelter": 0.55, "water": 0.5, "food": 0.35, "infrastructure": 0.4},
        "per_person_day": {"water_litres": 20.0, "food_kits": 1 / 3, "respirator_masks": 1.0, "medical_kits": 0.03},
        "fleet": ["4x4", "truck"],
        "recommendations": ["Evacuate villages downwind first", "Masks for smoke exposure; watch the elderly and asthmatics",
                            "Fire lines and water tankers for the forest department", "Close roads crossing the fire perimeter"],
    },
    "drought": {
        "name": "Drought", "gdacs": "DR", "overlay": {"label": "Drought-affected area", "colour": "#C9A227", "fill": 0.25},
        "indicators": ["drought", "no water", "wells dried", "crop failed", "fodder", "tanker", "सूखा", "कुएं सूख", "ಬರ", "ಬರಗಾಲ", "வறட்சி",
                       "కరువు", "വരൾച്ച", "খরা", "ମରୁଡ଼ି", "દુષ્કાળ", "ਸੋਕਾ", "खडेरी", "sukha", "bara", "paani nahi"],
        "life_threat": {"water": 0.85, "food": 0.65, "medical": 0.7, "rescue": 0.5, "shelter": 0.3, "infrastructure": 0.3},
        "per_person_day": {"water_litres": 20.0, "food_kits": 1 / 3, "ors_packets": 0.1},
        "fleet": ["truck"],
        "recommendations": ["Water tankers on a published schedule per village", "Fodder for livestock", "Track water-borne and heat illness",
                            "Prioritise villages with dried wells and no piped supply"],
    },
    "heatwave": {
        "name": "Heatwave", "gdacs": None, "overlay": {"label": "Extreme-heat area", "colour": "#E11D48", "fill": 0.2},
        "indicators": ["heatwave", "heat stroke", "heatstroke", "extreme heat", "fainted", "dehydration", "लू", "गर्मी", "बेहोश", "ಬಿಸಿಗಾಳಿ", "ಬಿಸಿಲು",
                       "வெப்ப அலை", "వడగాలి", "వడదెబ్బ", "ഉഷ്ണതരംഗ", "তাপপ্রবাহ", "ଗ୍ରୀଷ୍ମ ଲହରୀ", "લૂ", "ਲੂ", "गर्मी लहर", "loo lagi", "garmi"],
        "life_threat": {"medical": 1.0, "water": 0.8, "rescue": 0.6, "shelter": 0.55, "food": 0.3, "infrastructure": 0.25},
        "per_person_day": {"water_litres": 20.0, "ors_packets": 1.0, "medical_kits": 0.03},
        "fleet": ["truck", "ambulance"],
        "recommendations": ["Cooling centres open 11:00–16:00", "ORS and water at bus stands and worksites", "Check on elderly living alone",
                            "Shift outdoor work away from midday"],
    },
    "tsunami": {
        "name": "Tsunami", "gdacs": None, "overlay": {"label": "Inundation zone", "colour": "#0E7490", "fill": 0.4},
        "indicators": ["tsunami", "sea water entered", "huge waves", "sea came in", "सुनामी", "समुद्र", "ಸುನಾಮಿ", "சுனாமி", "கடல் நீர்",
                       "సునామీ", "സുനാമി", "সুনামি", "ସୁନାମି", "ત્સુનામી", "ਸੁਨਾਮੀ", "sunami", "samudra ka paani"],
        "life_threat": {"rescue": 1.0, "medical": 0.95, "shelter": 0.6, "water": 0.6, "food": 0.45, "infrastructure": 0.4},
        "per_person_day": {"water_litres": 15.0, "food_kits": 1 / 3, "medical_kits": 0.04, "tarpaulins": 0.2},
        "fleet": ["4x4", "truck", "boat"],
        "recommendations": ["Move everyone to high ground; more waves may follow", "Search the coast for missing fishermen",
                            "Salt-contaminated wells: supply drinking water", "Keep people out of the inundation zone until cleared"],
    },
    "industrial": {
        "name": "Industrial / chemical incident", "gdacs": None, "overlay": {"label": "Plume / exclusion zone", "colour": "#9333EA", "fill": 0.3},
        "indicators": ["gas leak", "eyes burning", "fainting", "plume", "chemical", "explosion", "toxic", "factory fire", "smell", "breathing", "गैस रिसाव", "रसायन", "विस्फोट",
                       "ಅನಿಲ ಸೋರಿಕೆ", "ರಾಸಾಯನಿಕ", "வாயு கசிவு", "గ్యాస్ లీక్", "വാതക ചോർച്ച", "গ্যাস লিক", "ଗ୍ୟାସ ଲିକ", "ગેસ લીક", "ਗੈਸ ਲੀਕ", "gas leak hua"],
        "life_threat": {"medical": 1.0, "rescue": 0.95, "shelter": 0.55, "water": 0.45, "food": 0.3, "infrastructure": 0.4},
        "per_person_day": {"water_litres": 15.0, "respirator_masks": 1.0, "medical_kits": 0.05},
        "fleet": ["ambulance", "truck"],
        "recommendations": ["Evacuate downwind and uphill of the plume", "HAZMAT team before anyone enters the site",
                            "Decontaminate before hospital entry", "Tell residents: close windows, wet cloth over the face"],
    },
}
NEED_ORDER = ["rescue", "medical", "water", "food", "shelter", "infrastructure"]
RESOURCE_UNITS_EXTRA = {"ors_packets": "packets", "tarpaulins": "pcs", "respirator_masks": "pcs"}
UNITS = {"food_kits": "kits", "water_litres": "L", "medical_kits": "kits", "boats": "boats", "blankets": "pcs", "volunteers": "people",
         "vehicles": "vehicles", **RESOURCE_UNITS_EXTRA}


def profile(code: str | None) -> dict:
    return DISASTERS.get(code or "flood", DISASTERS["flood"])


def detect(text: str) -> tuple[str | None, list[str]]:
    """Disaster type named in a report (keyword evidence), or None."""
    low = (text or "").lower()
    best, hits = None, []
    for code, d in DISASTERS.items():
        h = [k for k in d["indicators"] if k.lower() in low]
        if len(h) > len(hits):
            best, hits = code, h
    return best, hits
