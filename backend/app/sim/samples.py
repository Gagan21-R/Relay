"""Quick-send samples for the Phone Simulator (one tap per language/script), with verified translations so the
dashboard shows a clean English line in mock mode. Synthetic messages."""

SAMPLES = [
    {"label": "ಕನ್ನಡ · rescue", "lang": "kn", "text": "ಸಿದ್ದಾಪುರ ಶಾಲೆ ಹತ್ತಿರ 7 ಜನ ಮನೆಯ ಮೇಲೆ ಸಿಲುಕಿದ್ದಾರೆ, ದೋಣಿ ಬೇಕು",
     "en": "7 people are stuck on top of a house near Siddapura school, a boat is needed"},
    {"label": "ಕನ್ನಡ · food (Karadigodu)", "lang": "kn", "text": "ಕರಡಿಗೋಡು ಗ್ರಾಮದಲ್ಲಿ 20 ಜನರಿಗೆ ಊಟ ಮತ್ತು ಕುಡಿಯುವ ನೀರು ಬೇಕು",
     "en": "20 people in Karadigodu village need food and drinking water"},
    {"label": "Kanglish · no location", "lang": "kn", "text": "neeru mane olage bandide, help maadi",
     "en": "Water has come inside the house, please help"},
    {"label": "हिंदी · medical", "lang": "hi", "text": "विराजपेट में मेरी माँ को दवा चाहिए, सड़क बंद है, तुरंत मदद करो",
     "en": "My mother in Virajpet needs medicine, the road is closed, help immediately"},
    {"label": "Hinglish · food", "lang": "hi", "text": "Kushalnagar Sai layout mein 25 log phase hain, khana aur paani chahiye",
     "en": "25 people are stuck in Sai Layout, Kushalnagar, food and water are needed"},
    {"label": "മലയാളം · trapped", "lang": "ml", "text": "ഭാഗമണ്ഡല ക്ഷേത്രത്തിനടുത്ത് 10 പേർ കുടുങ്ങി, ഭക്ഷണം വേണം",
     "en": "10 people are trapped near the Bhagamandala temple, food is needed"},
    {"label": "தமிழ் · shelter", "lang": "ta", "text": "குஷால்நகரில் 15 பேருக்கு தங்குமிடம் தேவை",
     "en": "15 people in Kushalnagar need shelter"},
    {"label": "తెలుగు · water", "lang": "te", "text": "సోమవారపేటలో 40 మందికి తాగునీరు కావాలి",
     "en": "40 people in Somwarpet need drinking water"},
    {"label": "मराठी · rescue", "lang": "mr", "text": "नापोक्लु येथे 6 लोक अडकले आहेत, बोट पाहिजे",
     "en": "6 people are stuck at Napoklu, a boat is needed"},
    {"label": "বাংলা · food", "lang": "bn", "text": "মাদিকেরিতে 12 জন শ্রমিকের খাবার দরকার",
     "en": "12 workers in Madikeri need food"},
    {"label": "Structured SMS", "lang": "en", "text": "HELP FOOD 12 Napoklu school", "en": None},
    {"label": "Forward (rumour)", "lang": "kn", "text": "ಹಾರಂಗಿ ಅಣೆಕಟ್ಟು ಒಡೆದಿದೆ, ಎಲ್ಲರಿಗೂ ಶೇರ್ ಮಾಡಿ",
     "en": "The Harangi dam has burst, share with everyone"},
    {"label": "ಹೌದು (YES, delivery)", "lang": "kn", "text": "ಹೌದು", "en": "Yes"},
]

PHONES = [
    {"label": "Lakshmi (Kannada)", "phone": "+919845500101", "lang": "kn"},
    {"label": "Ramesh (Hindi, estate worker)", "phone": "+919845500102", "lang": "hi"},
    {"label": "Biju (Malayalam, lorry driver)", "phone": "+919845500103", "lang": "ml"},
    {"label": "Selvi (Tamil)", "phone": "+919845500104", "lang": "ta"},
]


def verified_translations() -> dict[str, str]:
    return {s["text"]: s["en"] for s in SAMPLES if s["en"]}
