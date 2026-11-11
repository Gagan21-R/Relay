"""~80 SYNTHETIC multilingual reports over a 12-hour timeline in Kodagu. Native scripts (Kannada, Hindi, Malayalam,
Tamil), romanized and code-mixed variants (Kanglish, Hinglish, Manglish) and English. Deliberate cross-language
duplicates, rumours (dam-burst forward, recycled 2018 photo, "camp closed" hoax), vague reports with no location,
life-safety reports, and two "missing contact" reports about a village that has gone silent (Hattihole).

Each row: t (hours), channel, source key (or a synthetic citizen phone), text, truth dict, english reference.
`truth` is ground truth for evaluation only — the pipeline never reads it.
  key: incident cluster id (None = no incident: chatter/news/vague-only)   real: True / False (rumour)
  need: primary need   people: true count or None   zone: zone code or None
`en` is a human reference translation. It is loaded as RELAY's *translation memory* (a store of verified
translations); new text that is not in memory falls back to Gemini, then to the glossary translator."""

T = dict  # truth shorthand

REPORTS = [
    # ---- A: people trapped on rooftops near Napoklu Govt High School (rescue, life safety) ----
    (0.6, "sms", "+919812300101", "ನಾಪೋಕ್ಲು ಸರ್ಕಾರಿ ಶಾಲೆ ಹತ್ತಿರ ನೀರು ಮನೆಗಳಿಗೆ ನುಗ್ಗಿದೆ, 12 ಜನ ಮೇಲ್ಛಾವಣಿ ಮೇಲೆ ಸಿಕ್ಕಿಹಾಕಿಕೊಂಡಿದ್ದಾರೆ, ದಯವಿಟ್ಟು ದೋಣಿ ಕಳುಹಿಸಿ",
     T(key="A", real=True, need="rescue", people=12, zone="napoklu"),
     "Water has entered houses near Napoklu Govt school, 12 people are stuck on the roof, please send a boat"),
    (0.8, "social_feed", "@coorg_rains", "12 people stranded on rooftops near Govt School Napoklu as Cauvery overflows. Need boats urgently! #KodaguFloods",
     T(key="A", real=True, need="rescue", people=12, zone="napoklu"), None),
    (0.9, "social_feed", "@kodagu_news_rt", "RT @coorg_rains: 12 people stranded on rooftops near Govt School Napoklu as Cauvery overflows. Need boats urgently! #KodaguFloods",
     T(key="A", real=True, need="rescue", people=12, zone="napoklu"), None),
    (1.1, "sms", "+919812300102", "napoklu school hatra 12 jana roof mele sikkikondidare, neeru jaasti agtide, boat kalisi pls",
     T(key="A", real=True, need="rescue", people=12, zone="napoklu"),
     "12 people are stuck on the roof near Napoklu school, the water is rising, please send a boat"),
    (1.4, "sms", "vol_salim", "നാപോക്ലു സ്കൂളിനടുത്ത് 12 പേർ മേൽക്കൂരയിൽ കുടുങ്ങി, ബോട്ട് വേണം",
     T(key="A", real=True, need="rescue", people=12, zone="napoklu"),
     "12 people are trapped on the roof near Napoklu school, a boat is needed"),
    (2.2, "field_app", "ndrf2", "NDRF team 2 at Napoklu: confirmed 12 persons on rooftops near Govt High School, 2 elderly. Boat ops starting.",
     T(key="A", real=True, need="rescue", people=12, zone="napoklu"), None),

    # ---- B: Karadigodu (Siddapura) flooded houses, food + water — the demo's Kannada SMS + English post pair ----
    (3.0, "sms", "+919812300201", "ಕರಡಿಗೋಡು ಗ್ರಾಮದಲ್ಲಿ 30 ಕುಟುಂಬಗಳ ಮನೆಗಳಿಗೆ ನೀರು ನುಗ್ಗಿದೆ, ಊಟ ಮತ್ತು ಕುಡಿಯುವ ನೀರು ಬೇಕು",
     T(key="B", real=True, need="food", people=110, zone="siddapura"),
     "Water has entered the houses of 30 families in Karadigodu village, food and drinking water are needed"),
    (3.3, "social_feed", "@siddapura_updates", "Karadigodu village near Siddapura: around 30 families' houses flooded by Cauvery. They need food and drinking water. Please RT",
     T(key="B", real=True, need="food", people=110, zone="siddapura"), None),
    (3.9, "sms", "+919812300202", "करडिगोडु गांव में 30 परिवारों के घरों में पानी घुस गया है, खाना और पीने का पानी चाहिए",
     T(key="B", real=True, need="food", people=110, zone="siddapura"),
     "Water has entered the houses of 30 families in Karadigodu village, food and drinking water are needed"),
    (4.4, "sms", "+919812300203", "karadigodu alli 30 family mane olage neeru bandide, oota neeru beku",
     T(key="B", real=True, need="food", people=110, zone="siddapura"),
     "In Karadigodu water has come inside the houses of 30 families, food and water are needed"),
    (5.1, "field_app", "vol_anita", "Volunteer update Karadigodu: 30 families, about 110 people, kids and elderly among them, need food kits and drinking water.",
     T(key="B", real=True, need="food", people=110, zone="siddapura"), None),

    # ---- C: pilgrims stranded at Triveni Sangama, Bhagamandala ----
    (1.5, "sms", "+919812300301", "ಭಾಗಮಂಡಲ ತ್ರಿವೇಣಿ ಸಂಗಮದ ಬಳಿ 45 ಯಾತ್ರಿಕರು ಸಿಲುಕಿದ್ದಾರೆ, ಅದರಲ್ಲಿ ವೃದ್ಧರು ಇದ್ದಾರೆ, ಆಹಾರ ಬೇಕು",
     T(key="C", real=True, need="food", people=45, zone="bhagamandala"),
     "45 pilgrims are stuck near Triveni Sangama in Bhagamandala, there are elderly among them, food is needed"),
    (1.9, "sms", "+919812300302", "भागमंडला त्रिवेणी संगम के पास 45 तीर्थयात्री फंसे हैं, बुजुर्ग भी हैं, खाना और पानी चाहिए",
     T(key="C", real=True, need="food", people=45, zone="bhagamandala"),
     "45 pilgrims are stuck near Triveni Sangama in Bhagamandala, there are elderly people too, food and water are needed"),
    (2.3, "sms", "+919812300303", "பாகமண்டலா திரிவேணி சங்கமம் அருகே 45 யாத்ரீகர்கள் சிக்கியுள்ளனர், உணவு தேவை",
     T(key="C", real=True, need="food", people=45, zone="bhagamandala"),
     "45 pilgrims are stuck near Triveni Sangama in Bhagamandala, food is needed"),
    (2.6, "official_feed", "dc_office", "Bhagamandala: 45 pilgrims stranded at Triveni Sangama guest house, road submerged. Taluk office confirms. Food and water required.",
     T(key="C", real=True, need="food", people=45, zone="bhagamandala"), None),
    (3.4, "sms", "+919812300304", "Bhagamandala mandir ke paas hum 45 log phase hain, paani aur khana chahiye, bujurg log bhi hain",
     T(key="C", real=True, need="food", people=45, zone="bhagamandala"),
     "45 of us are stuck near the Bhagamandala temple, we need water and food, there are elderly people too"),

    # ---- D: landslide at Indira Nagar, Madikeri, injured (medical, life safety) ----
    (2.0, "voice", "+919812300401", "ಮಡಿಕೇರಿ ಇಂದಿರಾನಗರದಲ್ಲಿ ಭೂಕುಸಿತ, ಒಂದು ಮನೆ ಕುಸಿದಿದೆ, ಇಬ್ಬರಿಗೆ ಗಾಯ, ಆಂಬ್ಯುಲೆನ್ಸ್ ಬೇಕು",
     T(key="D", real=True, need="medical", people=2, zone="madikeri"),
     "Landslide at Indira Nagar in Madikeri, one house has collapsed, two people are injured, an ambulance is needed"),
    (2.3, "web", "vol_ravi", "Landslide at Indira Nagar, Madikeri. One house collapsed, 2 injured. Need ambulance and medical kits.",
     T(key="D", real=True, need="medical", people=2, zone="madikeri"), None),
    (2.5, "sms", "+919812300402", "madikeri indira nagar alli guddi kusidide, 2 janakke gaaya, ambulance beku",
     T(key="D", real=True, need="medical", people=2, zone="madikeri"),
     "The hill has collapsed at Indira Nagar in Madikeri, 2 people are injured, an ambulance is needed"),
    (3.2, "field_app", "fire", "Fire & Emergency: Indira Nagar Madikeri landslide site, 2 injured evacuated to district hospital, 6 families need shelter.",
     T(key="D", real=True, need="medical", people=2, zone="madikeri"), None),

    # ---- E: dialysis patient in Makkandur, single report (life safety, unverified -> Fast Verify) ----
    (4.0, "sms", "+919812300501", "ಮಕ್ಕಂದೂರಿನಲ್ಲಿ ನನ್ನ ತಂದೆಗೆ ಡಯಾಲಿಸಿಸ್ ಬೇಕು, ರಸ್ತೆ ಮುಚ್ಚಿದೆ, ತುರ್ತು ಸಹಾಯ ಬೇಕು",
     T(key="E", real=True, need="medical", people=1, zone="makkandur"),
     "My father in Makkandur needs dialysis, the road is closed, urgent help is needed"),

    # ---- F: NH275 cut by landslide at Jodupala, trucks stranded ----
    (5.0, "sms", "vol_salim", "ജോഡുപാല NH275 റോഡ് മണ്ണിടിച്ചിലിൽ തകർന്നു, 20 ലോറികൾ കുടുങ്ങി, ഭക്ഷണവും വെള്ളവും വേണം",
     T(key="F", real=True, need="food", people=20, zone="jodupala"),
     "The NH275 road at Jodupala is broken by a landslide, 20 lorries are stuck, food and water are needed"),
    (5.3, "sms", "+919812300601", "ಜೋಡುಪಾಲ ಬಳಿ ಹೆದ್ದಾರಿಯಲ್ಲಿ ಗುಡ್ಡ ಕುಸಿದು 20 ಲಾರಿಗಳು ಸಿಲುಕಿವೆ, ಚಾಲಕರಿಗೆ ಊಟ ಬೇಕು",
     T(key="F", real=True, need="food", people=20, zone="jodupala"),
     "A hill collapsed on the highway near Jodupala and 20 lorries are stuck, the drivers need food"),
    (5.6, "news_feed", "news_en", "NH275 blocked at Jodupala after landslide; around 20 trucks and their drivers stranded, says police.",
     T(key="F", real=True, need="food", people=20, zone="jodupala"), None),
    (6.0, "sms", "+919812300602", "jodupala il NH road poyi, 20 lorry kudungi, food venam",
     T(key="F", real=True, need="food", people=20, zone="jodupala"),
     "At Jodupala the NH road is gone, 20 lorries are stuck, food is needed"),

    # ---- G: Sai Layout, Kushalnagar flooded, residents need shelter ----
    (6.2, "sms", "+919812300701", "ಕುಶಾಲನಗರದ ಸಾಯಿ ಬಡಾವಣೆಯಲ್ಲಿ ಕಾವೇರಿ ನೀರು ನುಗ್ಗಿದೆ, 60 ಜನರಿಗೆ ಆಶ್ರಯ ಬೇಕು",
     T(key="G", real=True, need="shelter", people=60, zone="kushalnagar"),
     "Cauvery water has entered Sai Layout in Kushalnagar, 60 people need shelter"),
    (6.4, "social_feed", "@kushalnagar_now", "Sai Layout in Kushalnagar flooded, about 60 residents need shelter and food. Water at waist level.",
     T(key="G", real=True, need="shelter", people=60, zone="kushalnagar"), None),
    (6.7, "sms", "+919812300702", "குஷால்நகர் சாய் லேஅவுட்டில் வெள்ளம், 60 பேருக்கு தங்குமிடம் தேவை",
     T(key="G", real=True, need="shelter", people=60, zone="kushalnagar"),
     "Flood in Sai Layout, Kushalnagar, 60 people need shelter"),
    (6.9, "sms", "+919812300703", "कुशालनगर साई लेआउट में बाढ़, 60 लोगों को रहने की जगह चाहिए",
     T(key="G", real=True, need="shelter", people=60, zone="kushalnagar"),
     "Flood in Sai Layout, Kushalnagar, 60 people need a place to stay"),
    (7.3, "field_app", "sdrf", "SDRF Kodagu: Sai Layout Kushalnagar, 60 residents moving to Rotary Hall camp, need food kits.",
     T(key="G", real=True, need="shelter", people=60, zone="kushalnagar"), None),

    # ---- H: insulin and medicines at Virajpet camp ----
    (7.0, "sms", "vol_ravi", "ವಿರಾಜಪೇಟೆ ಶಿಬಿರದಲ್ಲಿ 8 ಮಧುಮೇಹ ರೋಗಿಗಳಿಗೆ ಇನ್ಸುಲಿನ್ ಮತ್ತು ಔಷಧಿ ಬೇಕು",
     T(key="H", real=True, need="medical", people=8, zone="virajpet"),
     "8 diabetic patients at the Virajpet camp need insulin and medicines"),
    (7.4, "web", "ngo_crc", "Virajpet Kodava Samaja camp: 8 diabetic patients need insulin and medicines today.",
     T(key="H", real=True, need="medical", people=8, zone="virajpet"), None),

    # ---- I: contaminated drinking water in Somwarpet ----
    (8.0, "sms", "+919812300901", "ಸೋಮವಾರಪೇಟೆಯಲ್ಲಿ ಕುಡಿಯುವ ನೀರು ಕಲುಷಿತವಾಗಿದೆ, 200 ಜನಕ್ಕೆ ಶುದ್ಧ ನೀರು ಬೇಕು",
     T(key="I", real=True, need="water", people=200, zone="somwarpet"),
     "Drinking water in Somwarpet is contaminated, 200 people need clean water"),
    (8.3, "sms", "+919812300902", "somwarpet alli kudiyo neeru kettu hogide, 200 janakke neeru beku",
     T(key="I", real=True, need="water", people=200, zone="somwarpet"),
     "In Somwarpet the drinking water has gone bad, 200 people need water"),
    (8.6, "web", "vol_anita", "Somwarpet: drinking water supply contaminated after flooding, about 200 people need clean water.",
     T(key="I", real=True, need="water", people=200, zone="somwarpet"), None),

    # ---- J: woman in labour at Siddapura estate lines, single report (life safety -> Fast Verify) ----
    (8.8, "sms", "+919812301001", "सिद्दापुर एस्टेट में एक गर्भवती महिला को प्रसव पीड़ा है, सड़क बंद है, तुरंत मदद चाहिए",
     T(key="J", real=True, need="medical", people=1, zone="siddapura"),
     "A pregnant woman at the Siddapura estate is in labour, the road is closed, help is needed immediately"),

    # ---- K: blankets for children at Siddapura camp ----
    (9.2, "sms", "+919812301101", "ಸಿದ್ದಾಪುರ ಶಿಬಿರದಲ್ಲಿ 60 ಮಕ್ಕಳಿಗೆ ಹೊದಿಕೆ ಬೇಕು, ತುಂಬಾ ಚಳಿ ಇದೆ",
     T(key="K", real=True, need="shelter", people=60, zone="siddapura"),
     "60 children at the Siddapura camp need blankets, it is very cold"),
    (9.5, "web", "ngo_crc", "Siddapura Govt School camp needs blankets for about 60 children tonight.",
     T(key="K", real=True, need="shelter", people=60, zone="siddapura"), None),

    # ---- L: Napoklu–Bhagamandala road submerged (infrastructure) ----
    (4.6, "field_app", "sdrf", "SDRF Kodagu: Napoklu–Bhagamandala road submerged near Bhagamandala, no vehicle movement possible.",
     T(key="L", real=True, need="infrastructure", people=None, zone="bhagamandala"), None),
    (4.9, "sms", "+919812301201", "ಭಾಗಮಂಡಲ ರಸ್ತೆ ಮುಳುಗಿದೆ, ವಾಹನ ಓಡಾಟ ಇಲ್ಲ",
     T(key="L", real=True, need="infrastructure", people=None, zone="bhagamandala"),
     "The Bhagamandala road is submerged, there is no vehicle movement"),

    # ---- N: evacuation of the Kushalnagar old-age home ----
    (7.8, "sms", "+919812301301", "ಕುಶಾಲನಗರ ವೃದ್ಧಾಶ್ರಮದಲ್ಲಿ 25 ಹಿರಿಯರು ಇದ್ದಾರೆ, ನೀರು ಒಳಗೆ ಬರುತ್ತಿದೆ, ಸ್ಥಳಾಂತರ ಬೇಕು",
     T(key="N", real=True, need="rescue", people=25, zone="kushalnagar"),
     "There are 25 elderly people at the Kushalnagar old-age home, water is coming inside, evacuation is needed"),
    (8.1, "web", "vol_anita", "Kushalnagar old age home: 25 elderly residents, water entering ground floor, need evacuation and wheelchairs.",
     T(key="N", real=True, need="rescue", people=25, zone="kushalnagar"), None),
    (8.5, "field_app", "sdrf", "SDRF Kodagu: Kushalnagar old-age home, 25 elderly, evacuation in progress, need 2 vehicles.",
     T(key="N", real=True, need="rescue", people=25, zone="kushalnagar"), None),

    # ---- Rumour R1: "Harangi dam has burst" forwards (false; the dam bulletin says the structure is safe) ----
    (3.5, "social_feed", "@kodagu_whatsapp_fwd", "ಹಾರಂಗಿ ಅಣೆಕಟ್ಟು ಒಡೆದಿದೆ!! ಕುಶಾಲನಗರ ಖಾಲಿ ಮಾಡಿ, ಎಲ್ಲರಿಗೂ ಶೇರ್ ಮಾಡಿ",
     T(key="R1", real=False, need="rescue", people=None, zone="kushalnagar"),
     "The Harangi dam has burst!! Evacuate Kushalnagar, share with everyone"),
    (3.7, "social_feed", "@fwd_hindi", "हारंगी बांध टूट गया है, कुशालनगर खाली करो, सबको शेयर करो",
     T(key="R1", real=False, need="rescue", people=None, zone="kushalnagar"),
     "The Harangi dam has broken, evacuate Kushalnagar, share with everyone"),
    (3.9, "social_feed", "@fwd_english", "Forwarded as received: Harangi dam has burst, Kushalnagar will be washed away, share to all!!",
     T(key="R1", real=False, need="rescue", people=None, zone="kushalnagar"), None),
    (4.1, "sms", "+919812301401", "harangi dam odedide antha news, ellarigu share maadi",
     T(key="R1", real=False, need="rescue", people=None, zone="kushalnagar"),
     "There is news that the Harangi dam has burst, share it with everyone"),
    (4.3, "official_feed", "ksdma", "KSDMA: Harangi dam is safe. Controlled release of 20,000 cusecs only. The dam has NOT burst — do not believe or forward rumours.",
     T(key="R1", real=False, need="rescue", people=None, zone="kushalnagar"), None),

    # ---- Rumour R2: recycled 2018 photo of Madikeri bus stand underwater ----
    (5.5, "social_feed", "@viral_coorg", "Madikeri bus stand completely underwater right now!! See photo. Share to all",
     T(key="R2", real=False, need="rescue", people=None, zone="madikeri"), None),
    (5.8, "social_feed", "@kn_viral", "ಮಡಿಕೇರಿ ಬಸ್ ನಿಲ್ದಾಣ ಸಂಪೂರ್ಣ ಮುಳುಗಿದೆ, ಫೋಟೋ ನೋಡಿ, ಎಲ್ಲರಿಗೂ ಶೇರ್ ಮಾಡಿ",
     T(key="R2", real=False, need="rescue", people=None, zone="madikeri"),
     "Madikeri bus stand is completely submerged, see the photo, share with everyone"),
    (6.1, "field_app", "vol_ravi", "Checked Madikeri bus stand myself: it is dry, buses running. The viral photo is from 2018.",
     T(key="R2", real=False, need="rescue", people=None, zone="madikeri"), None),

    # ---- Rumour R3: "Kushalnagar camp is closed" hoax (contradicted by the camp manager's check-in) ----
    (7.1, "social_feed", "@fwd_kushal", "कुशालनगर रोटरी हॉल कैंप बंद हो गया है, वहाँ मत जाओ, सबको शेयर करो",
     T(key="R3", real=False, need="shelter", people=None, zone="kushalnagar"),
     "The Kushalnagar Rotary Hall camp has closed, don't go there, share with everyone"),
    (7.5, "sms", "mgr_kushal", "ಕುಶಾಲನಗರ ರೋಟರಿ ಹಾಲ್ ಶಿಬಿರ ತೆರೆದಿದೆ, 300 ಜನ ಇದ್ದಾರೆ, ಇನ್ನೂ 100 ಜನರಿಗೆ ಜಾಗ ಇದೆ",
     T(key="R3", real=False, need="shelter", people=None, zone="kushalnagar"),
     "The Kushalnagar Rotary Hall camp is open, 300 people are here, there is space for 100 more people"),

    # ---- vague reports with no location (trigger clarification SMS) ----
    (2.8, "sms", "+919812301501", "ಮನೆಗೆ ನೀರು ಬರುತ್ತಿದೆ, ದಯವಿಟ್ಟು ಸಹಾಯ ಮಾಡಿ",
     T(key=None, real=True, need="rescue", people=None, zone=None), "Water is coming into the house, please help"),
    (4.7, "sms", "+919812301502", "हमारे घर में पानी आ गया है, मदद करो",
     T(key=None, real=True, need="rescue", people=None, zone=None), "Water has come into our house, help"),
    (6.6, "web", "+919812301503", "Please help, water rising fast, we have small kids",
     T(key=None, real=True, need="rescue", people=None, zone=None), None),
    (9.0, "sms", "+919812301504", "neeru mane olage bandide, help maadi",
     T(key=None, real=True, need="rescue", people=None, zone=None), "Water has come inside the house, please help"),

    # ---- missing contact about Hattihole (the silent village); sent from outside the district ----
    (7.2, "web", "+919812301601", "ಹಟ್ಟಿಹೊಳೆಯಲ್ಲಿರುವ ನನ್ನ ತಂದೆ ತಾಯಿ ನಿನ್ನೆಯಿಂದ ಸಂಪರ್ಕಕ್ಕೆ ಸಿಗುತ್ತಿಲ್ಲ",
     T(key="X", real=True, need="missing_contact", people=None, zone="hattihole"),
     "My parents in Hattihole have been unreachable since yesterday"),
    (9.4, "sms", "+919812301602", "Can't reach my family in Hattihole village since yesterday, phones switched off. Please check.",
     T(key="X", real=True, need="missing_contact", people=None, zone="hattihole"), None),

    # ---- shelter manager check-ins and status reports ----
    (5.9, "sms", "mgr_napoklu", "ನಾಪೋಕ್ಲು ಶಾಲೆ ಶಿಬಿರದಲ್ಲಿ 240 ಜನ ಇದ್ದಾರೆ, ಕುಡಿಯುವ ನೀರು ನಾಳೆ ಬೆಳಿಗ್ಗೆವರೆಗೆ ಮಾತ್ರ ಸಾಕು",
     T(key="W", real=True, need="water", people=240, zone="napoklu"),
     "There are 240 people at the Napoklu school camp, drinking water is enough only until tomorrow morning"),
    (6.3, "official_feed", "ksdma", "KSDMA: Napoklu Govt High School camp reports 240 people; drinking water stock low, resupply requested.",
     T(key="W", real=True, need="water", people=240, zone="napoklu"), None),

    # ---- news headlines and chatter (multilingual; no actionable incident) ----
    (0.2, "news_feed", "news_kn", "ಕೊಡಗಿನಲ್ಲಿ ಭಾರೀ ಮಳೆ, ಜಿಲ್ಲೆಗೆ ರೆಡ್ ಅಲರ್ಟ್ ಘೋಷಣೆ",
     T(key=None, real=True, need="other", people=None, zone=None), "Heavy rain in Kodagu, red alert declared for the district"),
    (0.3, "news_feed", "news_hi", "कोडगु में भारी बारिश, रेड अलर्ट जारी",
     T(key=None, real=True, need="other", people=None, zone=None), "Heavy rain in Kodagu, red alert issued"),
    (0.4, "news_feed", "news_ml", "കുടകിൽ കനത്ത മഴ, റെഡ് അലർട്ട് പ്രഖ്യാപിച്ചു",
     T(key=None, real=True, need="other", people=None, zone=None), "Heavy rain in Kodagu, red alert declared"),
    (0.5, "official_feed", "ksdma", "KSDMA: Red alert for Kodagu district for the next 48 hours. Avoid travel on ghat roads.",
     T(key=None, real=True, need="other", people=None, zone=None), None),
    (1.0, "social_feed", "@coorg_rains", "Very heavy rain in Madikeri since morning, visibility poor on the ghat road.",
     T(key=None, real=True, need="other", people=None, zone="madikeri"), None),
    (1.3, "official_feed", "dc_office", "ಕೊಡಗು ಜಿಲ್ಲಾಧಿಕಾರಿ: ಎಲ್ಲಾ ಶಾಲೆಗಳಿಗೆ ರಜೆ ಘೋಷಿಸಲಾಗಿದೆ",
     T(key=None, real=True, need="other", people=None, zone=None), "Kodagu Deputy Commissioner: holiday declared for all schools"),
    (2.7, "news_feed", "news_en", "Cauvery crosses danger mark at Bhagamandala; low-lying areas being evacuated.",
     T(key=None, real=True, need="other", people=None, zone="bhagamandala"), None),
    (3.6, "social_feed", "@ml_kodagu", "കുടകിൽ മഴ തുടരുന്നു, ശ്രദ്ധിക്കുക",
     T(key=None, real=True, need="other", people=None, zone=None), "Rain continues in Kodagu, be careful"),
    (4.5, "news_feed", "news_kn", "ಕಾವೇರಿ ನದಿ ಅಪಾಯದ ಮಟ್ಟ ಮೀರಿ ಹರಿಯುತ್ತಿದೆ",
     T(key=None, real=True, need="other", people=None, zone=None), "The Cauvery river is flowing above the danger level"),
    (5.2, "social_feed", "@tn_traveller", "கொடகில் கனமழை, சுற்றுலா பயணிகள் கவனமாக இருக்கவும்",
     T(key=None, real=True, need="other", people=None, zone=None), "Heavy rain in Kodagu, tourists please be careful"),
    (7.6, "news_feed", "news_hi", "कोडगु में राहत शिविरों में हज़ारों लोग, सेना तैयार",
     T(key=None, real=True, need="other", people=None, zone=None), "Thousands of people in relief camps in Kodagu, army on standby"),
    (8.9, "news_feed", "news_en", "Power and mobile network down in parts of Somwarpet taluk, officials say.",
     T(key=None, real=True, need="other", people=None, zone="somwarpet"), None),
    (10.0, "official_feed", "ksdma", "KSDMA: rainfall expected to ease after 18:00; relief camps remain open.",
     T(key=None, real=True, need="other", people=None, zone=None), None),

    # ---- late duplicates and corroboration ----
    (9.8, "sms", "+919812301701", "ಭಾಗಮಂಡಲದಲ್ಲಿ ಯಾತ್ರಿಕರಿಗೆ ಇನ್ನೂ ಊಟ ತಲುಪಿಲ್ಲ, 45 ಜನ ಕಾಯುತ್ತಿದ್ದಾರೆ",
     T(key="C", real=True, need="food", people=45, zone="bhagamandala"),
     "Food has still not reached the pilgrims in Bhagamandala, 45 people are waiting"),
    (10.2, "sms", "+919812301702", "karadigodu jana innu oota sikkilla, makkalu hasivininda iddare",
     T(key="B", real=True, need="food", people=None, zone="siddapura"),
     "The people of Karadigodu still have not got food, the children are hungry"),
    (10.5, "web", "vol_anita", "Sai Layout Kushalnagar: 60 displaced residents still waiting for food kits at Rotary Hall.",
     T(key="G", real=True, need="shelter", people=60, zone="kushalnagar"), None),
    (10.8, "sms", "+919812301801", "jodupala highway alli lorry driver galige neeru beku, 20 jana iddare",
     T(key="F", real=True, need="food", people=20, zone="jodupala"),
     "The lorry drivers on the Jodupala highway need water, there are 20 people"),
    (11.1, "voice", "+919812301901", "ನಾಪೋಕ್ಲು ಶಾಲೆ ಶಿಬಿರಕ್ಕೆ ಕುಡಿಯುವ ನೀರು ಬೇಕು, ತುಂಬಾ ಕಡಿಮೆ ಇದೆ",
     T(key="W", real=True, need="water", people=None, zone="napoklu"),
     "The Napoklu school camp needs drinking water, there is very little left"),
    (11.4, "social_feed", "@coorg_rains", "Update: rooftop rescue at Napoklu school done by NDRF, all 12 safe. Thank you!",
     T(key="A", real=True, need="rescue", people=12, zone="napoklu"), None),
    (11.7, "sms", "+919812302001", "विराजपेट कैंप में डायबिटीज के मरीजों को इंसुलिन चाहिए, 8 लोग हैं",
     T(key="H", real=True, need="medical", people=8, zone="virajpet"),
     "The diabetic patients at the Virajpet camp need insulin, there are 8 people"),
    (11.9, "news_feed", "news_ml", "ജോഡുപാലയിൽ കുടുങ്ങിയ ലോറി ഡ്രൈവർമാർക്ക് ഭക്ഷണം എത്തിക്കണം",
     T(key="F", real=True, need="food", people=None, zone="jodupala"),
     "Food must be delivered to the lorry drivers stranded at Jodupala"),
]

# The recycled-photo rumour carries an image whose EXIF says it was taken in August 2018 (media check).
MEDIA = {
    "Madikeri bus stand completely underwater right now!! See photo. Share to all":
        {"urls": ["/media/demo/madikeri_busstand.jpg"], "meta": {"taken_at": "2018-08-16T10:12:00", "gps": [12.4230, 75.7400], "camera": "unknown"}},
    "ಮಡಿಕೇರಿ ಬಸ್ ನಿಲ್ದಾಣ ಸಂಪೂರ್ಣ ಮುಳುಗಿದೆ, ಫೋಟೋ ನೋಡಿ, ಎಲ್ಲರಿಗೂ ಶೇರ್ ಮಾಡಿ":
        {"urls": ["/media/demo/madikeri_busstand.jpg"], "meta": {"taken_at": "2018-08-16T10:12:00", "gps": [12.4230, 75.7400], "camera": "unknown"}},
    "12 people stranded on rooftops near Govt School Napoklu as Cauvery overflows. Need boats urgently! #KodaguFloods":
        {"urls": ["/media/demo/napoklu_roof.jpg"], "meta": {"taken_at": "SCENARIO_T", "gps": [12.3068, 75.6992], "camera": "phone"}},
}


def translation_memory() -> dict[str, str]:
    return {r[3]: r[5] for r in REPORTS if r[5]}
