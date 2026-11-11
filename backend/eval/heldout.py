"""HELD-OUT synthetic evaluation reports, written after the rules were tuned on the seed scenario and never used for
tuning. Same format as the seed: (t, channel, who, text, truth). Truth keys are prefixed H to keep them separate.
Includes Telugu, Marathi and Bengali (absent from the seed), new phrasings, cross-language duplicates and rumours."""

T = dict

REPORTS = [
    # H1: family on a roof near Virajpet bus stand — kn, en, Kanglish
    (0.5, "sms", "+918800000101", "ವಿರಾಜಪೇಟೆ ಬಸ್ ನಿಲ್ದಾಣದ ಹತ್ತಿರ ಒಂದು ಕುಟುಂಬದ 6 ಜನ ಮನೆಯ ಮೇಲೆ ಸಿಲುಕಿದ್ದಾರೆ", T(key="H1", real=True, need="rescue", people=6, zone="virajpet")),
    (0.9, "social_feed", "@vjp_watch", "Family of 6 stuck on their roof near Virajpet bus stand, water still rising. Boats needed.", T(key="H1", real=True, need="rescue", people=6, zone="virajpet")),
    (1.3, "sms", "+918800000102", "virajpet bus stand hatra 6 jana mane mele sikkiddare, boat beku", T(key="H1", real=True, need="rescue", people=6, zone="virajpet")),
    # H2: Somwarpet hostel students need food — te, hi, en
    (1.0, "sms", "+918800000201", "సోమవారపేటలో హాస్టల్ లో 35 మంది విద్యార్థులకు ఆహారం కావాలి", T(key="H2", real=True, need="food", people=35, zone="somwarpet")),
    (1.5, "sms", "+918800000202", "सोमवारपेट हॉस्टल में 35 छात्रों को खाना चाहिए", T(key="H2", real=True, need="food", people=35, zone="somwarpet")),
    (2.1, "web", "+918800000203", "Somwarpet hostel: 35 students without food since last night.", T(key="H2", real=True, need="food", people=35, zone="somwarpet")),
    # H3: Napoklu injured farmer — mr, kn
    (2.0, "sms", "+918800000301", "नापोक्लु येथे एक शेतकरी जखमी आहे, औषध पाहिजे", T(key="H3", real=True, need="medical", people=1, zone="napoklu")),
    (2.6, "sms", "+918800000302", "ನಾಪೋಕ್ಲುವಿನಲ್ಲಿ ಒಬ್ಬ ರೈತನಿಗೆ ಗಾಯವಾಗಿದೆ, ಔಷಧಿ ಬೇಕು", T(key="H3", real=True, need="medical", people=1, zone="napoklu")),
    # H4: Bhagamandala drinking water — ta, ml, en
    (3.0, "sms", "+918800000401", "பாகமண்டலாவில் 70 பேருக்கு குடிநீர் தேவை", T(key="H4", real=True, need="water", people=70, zone="bhagamandala")),
    (3.4, "sms", "+918800000402", "ഭാഗമണ്ഡലയിൽ 70 പേർക്ക് കുടിവെള്ളം വേണം", T(key="H4", real=True, need="water", people=70, zone="bhagamandala")),
    (3.9, "official_feed", "dc_office", "Bhagamandala: about 70 people need drinking water, tanker requested.", T(key="H4", real=True, need="water", people=70, zone="bhagamandala")),
    # H5: Madikeri hospital needs blankets for 40 patients — bn, en
    (4.0, "sms", "+918800000501", "মাদিকেরি হাসপাতালে 40 জন রোগীর জন্য কম্বল দরকার", T(key="H5", real=True, need="shelter", people=40, zone="madikeri")),
    (4.5, "web", "vol_anita", "Madikeri district hospital needs 40 blankets for patients tonight.", T(key="H5", real=True, need="shelter", people=40, zone="madikeri")),
    # H6: Siddapura elderly couple trapped — hi romanized, kn
    (5.0, "sms", "+918800000601", "siddapur mein do bujurg phase hue hain, ghar mein paani hai, madad karo", T(key="H6", real=True, need="rescue", people=2, zone="siddapura")),
    (5.4, "sms", "+918800000602", "ಸಿದ್ದಾಪುರದಲ್ಲಿ ಇಬ್ಬರು ವೃದ್ಧರು ಮನೆಯಲ್ಲಿ ಸಿಲುಕಿದ್ದಾರೆ", T(key="H6", real=True, need="rescue", people=2, zone="siddapura")),
    # H7: Kushalnagar pregnant woman — en, ml
    (6.0, "sms", "+918800000701", "Pregnant woman in labour at Kushalnagar, road flooded, need ambulance urgently", T(key="H7", real=True, need="medical", people=1, zone="kushalnagar")),
    (6.3, "sms", "+918800000702", "കുശാൽനഗറിൽ ഗർഭിണിക്ക് പ്രസവ വേദന, ആംബുലൻസ് വേണം", T(key="H7", real=True, need="medical", people=1, zone="kushalnagar")),
    # H8: Makkandur road blocked — kn, en
    (6.5, "sms", "+918800000801", "ಮಕ್ಕಂದೂರು ರಸ್ತೆಯಲ್ಲಿ ಮರಗಳು ಬಿದ್ದು ರಸ್ತೆ ಮುಚ್ಚಿದೆ", T(key="H8", real=True, need="infrastructure", people=None, zone="makkandur")),
    (6.9, "field_app", "sdrf", "SDRF: Makkandur road blocked by fallen trees, clearing team needed.", T(key="H8", real=True, need="infrastructure", people=None, zone="makkandur")),
    # H9 rumour: "army airlifting everyone from Madikeri, go to the stadium" — false, refuted by official
    (7.0, "social_feed", "@fwd_army", "Army is airlifting everyone from Madikeri today, go to the stadium now, share to all", T(key="H9", real=False, need="other", people=None, zone="madikeri")),
    (7.3, "social_feed", "@fwd_army_kn", "ಸೇನೆ ಇಂದು ಮಡಿಕೇರಿಯಿಂದ ಎಲ್ಲರನ್ನೂ ಏರ್‌ಲಿಫ್ಟ್ ಮಾಡುತ್ತಿದೆ, ಎಲ್ಲರಿಗೂ ಶೇರ್ ಮಾಡಿ", T(key="H9", real=False, need="other", people=None, zone="madikeri")),
    (7.8, "official_feed", "ksdma", "KSDMA: no airlift is planned from Madikeri. This message is false — do not go to the stadium.", T(key="H9", real=False, need="other", people=None, zone="madikeri")),
    # H10 rumour: old video "Kushalnagar bridge collapsed" — false
    (8.0, "social_feed", "@viral_bridge", "Kushalnagar bridge has collapsed!! forward this to everyone", T(key="H10", real=False, need="other", people=None, zone="kushalnagar")),
    (8.4, "field_app", "fire", "Fire & Emergency: Kushalnagar bridge is open and safe, the viral video is old.", T(key="H10", real=False, need="other", people=None, zone="kushalnagar")),
    # H11: Jodupala stranded bus — en, kn
    (8.5, "sms", "+918800001101", "KSRTC bus with 30 passengers stranded near Jodupala, need food and water", T(key="H11", real=True, need="food", people=30, zone="jodupala")),
    (8.9, "sms", "+918800001102", "ಜೋಡುಪಾಲ ಬಳಿ 30 ಪ್ರಯಾಣಿಕರಿರುವ ಬಸ್ ಸಿಲುಕಿದೆ, ಊಟ ನೀರು ಬೇಕು", T(key="H11", real=True, need="food", people=30, zone="jodupala")),
    # H12 single life-safety report in Bengali
    (9.0, "sms", "+918800001201", "সিদ্দাপুরে একজন বয়স্ক মানুষ আটকে আছেন, সাহায্য দরকার", T(key="H12", real=True, need="rescue", people=1, zone="siddapura")),
    # noise
    (9.5, "news_feed", "news_en", "Rain eases slightly over Kodagu, more showers expected tomorrow.", T(key=None, real=True, need="other", people=None, zone=None)),
    (9.8, "news_feed", "news_kn", "ಕೊಡಗಿನಲ್ಲಿ ಮಳೆ ಸ್ವಲ್ಪ ಕಡಿಮೆಯಾಗಿದೆ", T(key=None, real=True, need="other", people=None, zone=None)),
]
