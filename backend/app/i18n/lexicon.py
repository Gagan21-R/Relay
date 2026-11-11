"""Per-language keyword lists for the rule-based fallback extractor and the rumour/urgency detectors.
Native script and romanized spellings (Kanglish, Hinglish, Manglish, Tanglish) for every supported language.
Matching: native-script phrases are substring matches; Latin phrases match at word starts (so "evacuat" matches
"evacuate"/"evacuation"). Adding a language = adding its entries here and in languages.json."""

NEEDS: dict[str, list[str]] = {
    "rescue": [
        # en
        "trapped", "stranded", "stuck on", "rescue", "boat", "evacuat", "drowning", "rooftop", "on the roof", "washed away",
        # kn + Kanglish
        "ಸಿಕ್ಕಿಹಾಕಿ", "ಸಿಲುಕಿ", "ದೋಣಿ", "ರಕ್ಷಿಸಿ", "ಸ್ಥಳಾಂತರ", "ಮೇಲ್ಛಾವಣಿ", "ಖಾಲಿ ಮಾಡಿ", "sikki", "roof mele", "boat kalisi", "kapadi",
        # hi + Hinglish
        "फंसे", "फंस", "नाव", "बचाओ", "बचाव", "खाली करो", "phase hain", "phas gaye", "fase", "bachao", "naav",
        # ml + Manglish
        "കുടുങ്ങി", "ബോട്ട്", "രക്ഷിക്ക", "kudungi", "rakshikk",
        # ta, te, mr, bn
        "சிக்கி", "படகு", "மீட்க", "చిక్కుకు", "పడవ", "కాపాడండి", "अडकले", "बोट", "वाचवा", "আটকে", "নৌকা", "বাঁচাও",
    ],
    "medical": [
        "injured", "injury", "ambulance", "medicine", "insulin", "dialysis", "pregnant", "in labour", "in labor", "hospital",
        "medical", "bleeding", "diabetic", "unconscious", "heart attack", "fracture",
        "ಗಾಯ", "ಆಂಬ್ಯುಲೆನ್ಸ್", "ಔಷಧಿ", "ಇನ್ಸುಲಿನ್", "ಡಯಾಲಿಸಿಸ್", "ಆಸ್ಪತ್ರೆ", "ರೋಗಿ", "ಗರ್ಭಿಣಿ", "gaaya", "aushadhi", "dialysis",
        "घायल", "दवा", "इंसुलिन", "प्रसव", "अस्पताल", "मरीज", "गर्भवती", "डायलिसिस", "dawai", "davai", "ghayal", "marij",
        "പരിക്ക്", "മരുന്ന്", "ആംബുലൻസ്", "ആശുപത്രി", "ഇൻസുലിൻ", "marunnu",
        "காயம்", "மருந்து", "மருத்துவ", "గాయ", "మందులు", "ఆసుపత్రి", "जखमी", "औषध", "আহত", "ওষুধ", "হাসপাতাল",
    ],
    "food": [
        "food", "hungry", "meal", "rations", "food kits",
        "ಊಟ", "ಆಹಾರ", "ಹಸಿವ", "oota", "aahaara", "hasiv",
        "खाना", "भोजन", "राशन", "khana", "khaana",
        "ഭക്ഷണ", "bhakshanam",
        "உணவு", "சாப்பாடு", "ఆహారం", "భోజనం", "अन्न", "जेवण", "খাবার",
    ],
    "water": [
        "drinking water", "clean water", "need water", "needs water", "water required", "water needed", "water and food",
        "and drinking water", "food and water", "need clean water",
        "ಕುಡಿಯುವ ನೀರು", "ಶುದ್ಧ ನೀರು", "ನೀರು ಬೇಕು", "neeru beku", "kudiyo neeru", "kudiyuva neeru",
        "पीने का पानी", "पानी चाहिए", "और पानी", "paani aur", "paani chahiye", "peene ka paani",
        "കുടിവെള്ള", "വെള്ളവും വേണം", "വെള്ളം വേണം", "vellam venam",
        "குடிநீர்", "தண்ணீர் தேவை", "తాగునీరు", "నీరు కావాలి", "पिण्याचे पाणी", "पाणी हवे", "খাবার জল", "জল দরকার",
    ],
    "shelter": [
        "shelter", "blanket", "place to stay", "homeless", "displaced", "need shelter",
        "ಆಶ್ರಯ", "ಹೊದಿಕೆ", "ಕಂಬಳಿ", "ashraya",
        "रहने की जगह", "कंबल", "आश्रय", "rehne ki jagah", "kambal",
        "അഭയം", "പുതപ്പ്", "தங்குமிடம்", "போர்வை", "ఆశ్రయం", "దుప్పటి", "निवारा", "ब्लँकेट", "আশ্রয়", "কম্বল",
    ],
    "infrastructure": [
        "road submerged", "road blocked", "road cut", "road closed", "blocked at", "bridge", "highway", "nh275", "nh 275",
        "no vehicle movement", "power and mobile", "network down",
        "ರಸ್ತೆ ಮುಳುಗಿದೆ", "ಹೆದ್ದಾರಿ", "ರಸ್ತೆ ಮುಚ್ಚಿದೆ", "ವಾಹನ ಓಡಾಟ ಇಲ್ಲ", "highway alli",
        "सड़क बंद", "पुल", "राजमार्ग", "road band",
        "റോഡ്", "മണ്ണിടിച്ചിൽ", "road poyi", "சாலை", "రోడ్డు", "रस्ता बंद", "রাস্তা বন্ধ",
    ],
}

# phrases saying "I cannot reach someone in place X" (count toward Blackout Detection for X)
MISSING_CONTACT = [
    "can't reach", "cannot reach", "can not reach", "unreachable", "not reachable", "no contact", "phones switched off",
    "lost contact", "not answering",
    "ಸಂಪರ್ಕಕ್ಕೆ ಸಿಗುತ್ತಿಲ್ಲ", "ಸಂಪರ್ಕ ಸಿಗುತ್ತಿಲ್ಲ", "contact sigtilla", "phone sigtilla",
    "संपर्क नहीं हो", "बात नहीं हो पा रही", "फोन बंद", "sampark nahi", "baat nahi ho",
    "ബന്ധപ്പെടാൻ കഴിയുന്നില്ല", "தொடர்பு கொள்ள முடியவில்லை", "సంప్రదించలేకపోతున్నాం", "संपर्क होत नाही", "যোগাযোগ করতে পারছি না",
]

# life-safety markers: these reports are never discarded for low confidence (Fast Verify)
LIFE_SAFETY = [
    "trapped", "stranded", "drowning", "rooftop", "on the roof", "injured", "unconscious", "bleeding", "dialysis", "in labour",
    "in labor", "heart attack", "collapsed", "washed away", "evacuat",
    "ಸಿಕ್ಕಿಹಾಕಿ", "ಸಿಲುಕಿ", "ಮೇಲ್ಛಾವಣಿ", "ಗಾಯ", "ಡಯಾಲಿಸಿಸ್", "ಕುಸಿದ", "ಸ್ಥಳಾಂತರ", "sikki", "roof mele", "gaaya",
    "फंसे", "घायल", "प्रसव", "डूब", "phase hain", "bachao",
    "കുടുങ്ങി", "പരിക്ക്", "kudungi", "சிக்கி", "காயம்", "చిక్కుకు", "గాయ", "अडकले", "जखमी", "আটকে", "আহত",
]

URGENCY = {
    "critical": ["urgent", "urgently", "immediately", "emergency", "sos", "dying", "ತುರ್ತು", "ತಕ್ಷಣ", "तुरंत", "जल्दी", "turant",
                 "jaldi", "അടിയന്തര", "உடனடி", "అత్యవసర", "तातडीने", "জরুরি", "!!"],
    "high": ["please", "help", "fast", "rising", "ದಯವಿಟ್ಟು", "ಸಹಾಯ", "मदद", "madad", "help maadi", "pls", "സഹായ", "உதவி"],
}

# forward-chain / rumour phrases per language
FORWARD = [
    "forwarded", "fwd", "share to all", "share with all", "share this", "forward this", "forward to all", "please rt", "viral",
    "as received", "share to everyone",
    "ಎಲ್ಲರಿಗೂ ಶೇರ್ ಮಾಡಿ", "ಶೇರ್ ಮಾಡಿ", "ellarigu share", "share maadi",
    "सबको शेयर करो", "शेयर करें", "आगे भेजें", "sabko share", "share karo",
    "എല്ലാവരിലേക്കും ഷെയർ", "ഷെയർ ചെയ്യുക", "எல்லோருக்கும் பகிரவும்", "అందరికీ షేర్", "सर्वांना शेअर", "সবাইকে শেয়ার",
]

# claims that are typical of panic rumours (catastrophe without detail)
SENSATIONAL = ["has burst", "burst", "washed away", "completely underwater", "fully underwater", "ಒಡೆದಿದೆ", "odedide",
               "ಸಂಪೂರ್ಣ ಮುಳುಗಿದೆ", "टूट गया", "बांध टूट", "पूरा डूब", "closed, don't go", "बंद हो गया है", "मत जाओ"]

# statements that deny or correct a claim (used to find contradictions between reports)
REFUTE = [
    "is safe", "not burst", "has not burst", "do not believe", "don't believe", "is dry", "is open", "rumour", "rumor",
    "fake", "false", "photo is from", "old photo", "no flooding", "buses running",
    "ಸುರಕ್ಷಿತ", "ತೆರೆದಿದೆ", "ಸುಳ್ಳು", "ವದಂತಿ", "सुरक्षित", "अफवाह", "झूठ", "खुला है", "സുരക്ഷിത", "വ്യാജ", "பொய்", "அவதூறு",
]

# completion statements (an incident is being handled / done)
RESOLVED = ["all safe", "rescue done", "evacuated to", "all 12 safe", "rescued", "ರಕ್ಷಿಸಲಾಗಿದೆ", "बचा लिया"]

VULNERABLE = {
    "elderly": ["elderly", "old age", "senior", "aged", "ವೃದ್ಧ", "ಹಿರಿಯ", "ಅಜ್ಜ", "ajji", "ajja", "vruddha", "बुजुर्ग", "वृद्ध", "bujurg",
                "buzurg", "പ്രായമായ", "முதியவர்", "వృద్ధ", "वृद्ध", "বয়স্ক"],
    "children": ["children", "kids", "child", "baby", "infant", "ಮಕ್ಕಳ", "ಮಗು", "makkalu", "बच्चे", "बच्चा", "bacche", "bachche",
                 "കുട്ടികൾ", "குழந்தை", "పిల్లలు", "मुले", "শিশু"],
    "pregnant": ["pregnant", "in labour", "in labor", "ಗರ್ಭಿಣಿ", "गर्भवती", "प्रसव", "garbhini", "ഗർഭിണി", "கர்ப்பிணி", "గర్భిణీ", "গর্ভবতী"],
    "disabled": ["disabled", "wheelchair", "handicapped", "bedridden", "ಅಂಗವಿಕಲ", "विकलांग", "വികലാംഗ", "மாற்றுத்திறனாளி"],
    "medical": ["dialysis", "diabetic", "insulin", "patient", "ಡಯಾಲಿಸಿಸ್", "ಮಧುಮೇಹ", "ರೋಗಿ", "मरीज", "डायबिटीज", "डायलिसिस",
                "ഡയാലിസിസ്", "நோயாளி"],
}

# words that, right after a number, mean "people" (families are converted at 3.7 people each)
PEOPLE_UNITS = [
    "people", "persons", "person", "injured", "residents", "pilgrims", "patients", "elderly", "children", "kids", "drivers", "of us",
    "jana", "janakke", "log", "lok", "ಜನ", "ಜನರಿಗೆ", "ಜನಕ್ಕೆ", "ಯಾತ್ರಿಕರು", "ಹಿರಿಯರು", "ಮಕ್ಕಳಿಗೆ", "ರೋಗಿಗಳಿಗೆ", "ಮಧುಮೇಹ",
    "लोग", "लोगों", "तीर्थयात्री", "मरीज", "पेर", "പേർ", "യാത്രക്കാർ", "பேர்", "பேருக்கு", "யாத்ரீகர்கள்", "మంది", "लोक", "জন",
]
FAMILY_UNITS = ["families", "family", "ಕುಟುಂಬ", "परिवार", "കുടുംബ", "குடும்ப", "కుటుంబ", "कुटुंब", "পরিবার"]
VEHICLE_UNITS = ["lorries", "lorry", "trucks", "ಲಾರಿ", "ലോറി", "लॉरी", "ट्रक"]
FAMILY_SIZE = 3.7

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "dozen": 12,
    "ಒಬ್ಬ": 1, "ಒಬ್ಬರು": 1, "ಇಬ್ಬರು": 2, "ಇಬ್ಬರಿಗೆ": 2, "ಮೂವರು": 3, "ನಾಲ್ವರು": 4, "ಐದು": 5, "ಹತ್ತು": 10,
    "obba": 1, "ibbaru": 2, "ibbarige": 2, "mooru": 3, "aidu": 5, "hattu": 10,
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "दस": 10, "do log": 2, "teen": 3, "paanch": 5, "das": 10,
    "ഒരു": 1, "രണ്ട്": 2, "മൂന്ന്": 3, "ஒரு": 1, "இரண்டு": 2, "ఒక": 1, "రెండు": 2, "দুই": 2,
}
# a single named person ("my father") means one person
SINGLE_PERSON = ["my father", "my mother", "my son", "my daughter", "a pregnant woman", "ನನ್ನ ತಂದೆ", "ನನ್ನ ತಾಯಿ", "ನನ್ನ ಮಗ",
                 "एक गर्भवती महिला", "मेरे पिता", "मेरी माँ", "എന്റെ അച്ഛൻ", "என் அப்பா"]

# romanized language cues (token level) for detecting Kanglish / Hinglish / Manglish / Tanglish
ROMAN_CUES: dict[str, set[str]] = {
    "kn": {"beku", "maadi", "alli", "ide", "illa", "neeru", "jana", "agtide", "bandide", "sikki", "kalisi", "hatra", "oota", "mane",
           "olage", "ellarigu", "antha", "kettu", "hogide", "iddare", "sikkilla", "galige", "kudiyo", "sikkikondidare", "mele",
           "janakke", "gaaya", "kusidide", "guddi", "odedide", "innu", "hasivininda", "makkalu", "jaasti", "agide", "barthide"},
    "hi": {"hai", "hain", "nahi", "chahiye", "paani", "khana", "log", "ghar", "ke", "paas", "mein", "madad", "karo", "bujurg",
           "phase", "hum", "aur", "bhi", "mandir", "bachao", "jaldi", "kya", "hamare", "gaya", "raha"},
    "ml": {"venam", "poyi", "kudungi", "il", "undu", "vellam", "aanu", "ente", "veedu", "sahayikku", "evide", "illa"},
    "ta": {"venum", "irukku", "thanni", "udhavi", "veedu", "illai", "romba", "seekiram"},
    "te": {"kavali", "undi", "ledu", "neellu", "intlo", "sahayam"},
    "mr": {"pahije", "aahe", "ahe", "madat", "pani", "lavkar"},
    "bn": {"chai", "achhe", "lagbe", "jol", "bachao", "sahajjo"},
}
ENGLISH_CUES = {"the", "is", "are", "and", "need", "needs", "people", "help", "near", "water", "please", "at", "in", "of", "to",
                "a", "an", "from", "our", "we", "my", "has", "have", "been", "since", "food", "road", "village", "camp", "about",
                "after", "their", "they", "them", "all", "for", "with", "not", "no", "safe", "update", "today", "still"}

# Structured SMS format: HELP <need> <people> <landmark...>
STRUCTURED_NEEDS = {"rescue": "rescue", "medical": "medical", "med": "medical", "food": "food", "water": "water", "shelter": "shelter",
                    "ರಕ್ಷಣೆ": "rescue", "ಆಹಾರ": "food", "ನೀರು": "water", "ಆಶ್ರಯ": "shelter", "बचाव": "rescue", "खाना": "food", "पानी": "water"}

YES = {"yes", "y", "ha", "haan", "haa", "han", "ok received", "received", "houdu", "howdu", "ಹೌದು", "ಸಿಕ್ಕಿದೆ", "ತಲುಪಿದೆ", "हाँ", "हां",
       "मिल गया", "ഉവ്വ്", "അതെ", "ലഭിച്ചു", "ஆம்", "கிடைத்தது", "అవును", "అందింది", "हो", "मिळाले", "হ্যাঁ", "পেয়েছি"}
NO = {"no", "n", "illa", "ಇಲ್ಲ", "ತಲುಪಿಲ್ಲ", "नहीं", "nahi", "नहीं मिला", "ഇല്ല", "இல்லை", "లేదు", "नाही", "না"}


# ---------------- enhancement round: more languages and noisier input ----------------
# Assamese, Odia, Gujarati, Punjabi, Nepali (native script), Mizo and Khasi (Latin), plus more Kanglish/Hinglish and
# the "water came into the house" family of flood reports. These lists are drafted for the prototype and have NOT been
# validated by native speakers; Mizo and Khasi entries are especially uncertain (support level "basic").
NEEDS["rescue"] += [
    "need rescue", "lost their homes", "water inside the house", "water entered the house", "house full water", "full water",
    "ರಕ್ಷಣೆ", "ಮನೆ ಒಳಗೆ ನೀರು", "ಒಳಗೆ ನೀರು ಬಂದಿದೆ", "mane olage neeru", "olage neeru", "neeru bandide", "water ide", "bega rescue",
    "ghar me paani", "घर में पानी", "phase hue", "phas", "மீட்பு", "రక్షణ", "രക്ഷാപ്രവർത്തനം", "উদ্ধার",
    "আবদ্ধ", "উদ্ধাৰ", "ଫସି", "ଉଦ୍ଧାର", "ફસાયેલા", "બચાવ", "ਫਸੇ", "ਬਚਾਅ", "फसेका", "उद्धार", "an tang", "chhanhim", "ki la kem", "ïarap",
]
NEEDS["water"] += [
    "no drinking water", "পানীয় জল", "খোৱা পানী", "ପିଇବା ପାଣି", "પીવાનું પાણી", "ਪੀਣ ਵਾਲਾ ਪਾਣੀ", "खानेपानी", "tui in", "um dih",
    "peene ka paani", "kudiyo neeru", "borewells dry", "wells dry", "water tanker",
]
NEEDS["food"] += ["no food", "খাদ্য", "ଖାଦ୍ୟ", "ଖାଇବା", "ખોરાક", "ખાવાનું", "ਖਾਣਾ", "chaw", "bam ja", "phah ja", "food kalsi"]
NEEDS["medical"] += [
    "doctor", "medicines", "heatstroke", "heat stroke", "burns", "breathing", "fainting", "eyes burning",
    "காயமடை", "പരിക്കേ", "ഡോക്ടർ", "চিকিৎসক", "ଆହତ", "ଡାକ୍ତର", "ઘાયલ", "ડૉક્ટર", "ਜ਼ਖਮੀ", "ਡਾਕਟਰ", "घाइते", "डाक्टर",
    "hliam", "damdawi", "pynmynsaw", "doktor", "dawai", "gaaya aagidare",
]
NEEDS["shelter"] += [
    "tarpaulin", "homes destroyed", "താമസസ്ഥലം", "আশ্ৰয়", "ଆଶ୍ରୟ", "આશ્રય", "ਰਹਿਣ ਦੀ ਥਾਂ", "आश्रय", "awmna", "jaka sah",
    "घर टूट", "ghar toot", "mane haalaagide",
]
LIFE_SAFETY += ["phase hue", "আবদ্ধ", "ଫସି", "ફસાયેલા", "ਫਸੇ", "फसेका", "an tang", "ki la kem", "heatstroke", "fainting",
                "sikkiddare", "full water", "ಒಳಗೆ ನೀರು", "olage neeru"]
URGENCY["critical"] += ["এখনই", "সোনকালে", "ତୁରନ୍ତ", "તાત્કાલિક", "ਤੁਰੰਤ", "तुरुन्तै", "వెంటనే", "ഉടൻ", "लगेच", "bega",
                        "vat rawh", "kloi"]
URGENCY["high"] += ["madi", "help madi", "please help", "kripya", "bhejo"]
MISSING_CONTACT += ["can't contact", "cannot contact", "ফোন বন্ধ", "যোগাযোগ নাই", "ଯୋଗାଯୋଗ ହେଉନାହିଁ", "સંપર્ક થતો નથી", "ਸੰਪਰਕ ਨਹੀਂ"]
FORWARD += ["forward as received", "forwarded msg", "whatsapp forward"]
SENSATIONAL += ["will drown", "entire town", "whole town", "predicted", "govt is hiding", "poisoned", "55 degrees", "30 m high",
                "50 km", "will collapse tonight"]
PEOPLE_UNITS += ["জনৰ", "ଜଣ", "લોકો", "ਲੋਕ", "जना", "ngut", "ఇళ్ళు"]
FAMILY_UNITS += ["পৰিয়াল", "ପରିବାର", "પરિવાર", "ਪਰਿਵਾਰ", "chhungkua"]
NUMBER_WORDS.update({"ಹನ್ನೆರಡು": 12, "बारह": 12, "दुई": 2, "तीन जना": 3})

ROMAN_CUES["kn"] |= {"madi", "sikkiddare", "bega", "beliggeinda", "kalsi", "aagidare", "mattu", "haalaagide", "ashraya", "kudiyo",
                     "janakke", "neeru", "illa", "nodi", "barta"}
ROMAN_CUES["hi"] |= {"hue", "bhejo", "logon", "logo", "peene", "subah", "mila", "ghayal", "dawai", "parivaar", "toot", "rehne",
                     "jagah", "please", "kripya"}
ROMAN_CUES["lus"] = {"mi", "an", "rawh", "tui", "chaw", "kan", "mamawh", "leh", "ah", "bulah", "awm", "lo", "vat", "tang", "chhanhim",
                     "hliam", "damdawi", "chhungkua", "awmna", "turin", "rawn", "thawn", "ei"}
ROMAN_CUES["kha"] = {"ha", "ki", "ngut", "la", "ym", "ka", "bad", "donkam", "ja", "bam", "ïarap", "kloi", "um", "dih", "jaka", "sah",
                     "phah", "pat", "kem", "bynta", "duh", "ïing", "shah", "ai"}

YES |= {"হয়", "হয়", "ହଁ", "હા", "ਹਾਂ", "हजुर", "aw", "hooid"}
NO |= {"নহয়", "ନା", "ના", "ਨਹੀਂ", "होइन", "aih", "em"}

# Devanagari / Bengali-script disambiguation markers (used by detect.py)
NEPALI_MARKERS = {"छ", "छन्", "छैन", "छैनन्", "चाहियो", "मा", "जना", "जनाले", "जनाका", "गर्नुहोस्", "पठाउनुहोस्", "भत्कियो", "नजिक",
                  "हुनुहुन्छ", "घाइते", "खानेपानी", "पाएका", "बिहानदेखि", "तुरुन्तै", "उद्धार", "फसेका", "परिवारको", "औषधि"}
MARATHI_MARKERS = {"आहे", "आहेत", "आणि", "पाहिजे", "नाही", "पाणी", "आम्ही", "जवळ", "येथे", "लोकांना", "मिळाले", "पाठवा", "शिबिरात",
                   "अडकले", "घरे", "पडली", "लगेच", "लोकांसाठी", "पिण्याचे", "जेवण", "निवारा", "औषध", "जखमी", "कुटुंबांची", "लोकांची"}
ASSAMESE_CHARS = {"ৰ", "ৱ"}   # ৰ ৱ: used in Assamese, not in Bengali
