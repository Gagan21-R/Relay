"""Multilingual PROBE set — EVALUATION ONLY. Short messages written by the developer (NOT by native speakers) with
phrasing deliberately different from the Scenario Lab templates and the lexicon examples, across native script,
romanized and mixed input, with misspellings and voice-transcript style noise. Used to measure language detection and
need / people extraction per language and per input type. Small n: treat every number as indicative only.
Row: (language, input_type, text, need, people, disaster)."""

PROBES = [
    # Kannada — the three examples from the brief, plus variants
    ("kn", "native", "ಮನೆ ಒಳಗೆ ನೀರು ಬಂದಿದೆ.", "rescue", None, "flood"),
    ("kn", "romanized", "Mane olage neeru bandide.", "rescue", None, "flood"),
    ("kn", "mixed", "House full water ide, help madi.", "rescue", None, "flood"),
    ("kn", "native", "ನಮ್ಮ ಊರಲ್ಲಿ 8 ಜನರಿಗೆ ಔಷಧಿ ಬೇಕು, ಒಬ್ಬರಿಗೆ ಜ್ವರ", "medical", 8, None),
    ("kn", "romanized", "namma oorinalli 20 janakke oota illa, dayavittu food kalsi", "food", 20, None),
    ("kn", "mixed", "school hatra 6 jana sikkiddare plz boat kalsi fast", "rescue", 6, "flood"),
    # Hindi
    ("hi", "native", "हमारे मोहल्ले में 25 लोगों के पास पीने का पानी नहीं है", "water", 25, None),
    ("hi", "romanized", "gaon me 10 log phase hue hai, paani badh raha hai jaldi aao", "rescue", 10, "flood"),
    ("hi", "mixed", "bhai yaha 15 logo ko khana chahiye since kal raat", "food", 15, None),
    ("hi", "native", "पुल टूट गया है, 4 लोग घायल हैं, दवाई चाहिए", "medical", 4, None),
    # Malayalam / Tamil / Telugu / Marathi / Bengali
    ("ml", "native", "ഞങ്ങളുടെ വീട്ടിൽ 5 പേർ കുടുങ്ങി, വെള്ളം കയറുന്നു", "rescue", 5, None),
    ("ml", "romanized", "ivide 12 perkku bhakshanam venam", "food", 12, None),
    ("ta", "native", "எங்கள் தெருவில் 30 பேருக்கு குடிநீர் இல்லை", "water", 30, None),
    ("ta", "romanized", "inga 7 peru maatikittaanga, udhavi venum seekiram", "rescue", 7, None),
    ("te", "native", "మా ఊరిలో 9 మంది గాయపడ్డారు, మందులు కావాలి", "medical", 9, None),
    ("te", "romanized", "maa intlo neellu ledu, 6 mandi unnaru, sahayam kavali", "water", 6, None),
    ("mr", "native", "आमच्या गावात 40 लोकांना जेवण नाही, मदत पाहिजे", "food", 40, None),
    ("mr", "romanized", "ithe 5 lok adakle ahet, lavkar madat pahije", "rescue", 5, None),
    ("bn", "native", "আমাদের গ্রামে ১২ জন আটকে আছে, নৌকা দরকার", "rescue", 12, "flood"),
    ("bn", "romanized", "amader para te 20 jon er jol lagbe", "water", 20, None),
    # Assamese / Odia / Gujarati / Punjabi / Nepali
    ("as", "native", "আমাৰ গাঁৱত ১৫ জন মানুহ আবদ্ধ হৈ আছে", "rescue", 15, None),
    ("as", "native", "শিবিৰত খোৱা পানী নাই, ৩০ জন আছে", "water", 30, None),
    ("or", "native", "ଆମ ଗାଁରେ ୨୦ ଜଣଙ୍କ ପାଇଁ ଖାଦ୍ୟ ନାହିଁ", "food", 20, None),
    ("or", "native", "ଘୂର୍ଣ୍ଣିବଳୟ ପରେ ୮ ଜଣ ଆହତ, ଡାକ୍ତର ଦରକାର", "medical", 8, "cyclone"),
    ("gu", "native", "અમારા ગામમાં 12 લોકો ફસાયેલા છે, પૂર આવ્યું છે", "rescue", 12, "flood"),
    ("gu", "native", "ગેસ લીક પછી 6 લોકો ઘાયલ છે", "medical", 6, "industrial"),
    ("pa", "native", "ਪਿੰਡ ਵਿੱਚ 18 ਲੋਕਾਂ ਨੂੰ ਖਾਣਾ ਚਾਹੀਦਾ ਹੈ", "food", 18, None),
    ("pa", "native", "ਹੜ੍ਹ ਕਾਰਨ 5 ਲੋਕ ਫਸੇ ਹਨ", "rescue", 5, "flood"),
    ("ne", "native", "हाम्रो गाउँमा ७ जना घाइते छन्, औषधि चाहियो", "medical", 7, None),
    ("ne", "native", "पहिरोले बाटो बन्द, १० जना फसेका छन्", "rescue", 10, "landslide"),
    # Mizo / Khasi (basic support) — developer-written, very uncertain phrasing
    ("lus", "romanized", "kan khuaah mi 9 an tang, min chhanhim rawh", "rescue", 9, None),
    ("lus", "romanized", "mi 20 tan tui in tur kan mamawh", "water", 20, None),
    ("kha", "romanized", "ki 6 ngut ki la kem ha ka shnong, ai ïarap", "rescue", 6, None),
    ("kha", "romanized", "ki 15 ngut ym don ja, phah ja", "food", 15, None),
    # English with noise (voice transcript, misspellings)
    ("en", "native", "pls hlp 3 ppl stuck on roof water rising", "rescue", 3, "flood"),
    ("en", "native", "uh there is no drinking water here for like 40 people at the camp", "water", 40, None),
    ("en", "native", "earthquake building fell, 2 injured need ambulence", "medical", 2, "earthquake"),
    ("en", "native", "heat stroke cases in the colony, 5 elderly fainting", "medical", 5, "heatwave"),
]
