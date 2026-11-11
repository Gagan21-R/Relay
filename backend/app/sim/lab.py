"""Scenario Lab: 47 generated scenarios across every Indian state and union territory, all nine disaster types and
three difficulty levels (plus the three hand-built Kodagu scenarios = 50).

Each scenario has its own real places (approximate town-centre coordinates), roads, shelters, hospitals, depots,
volunteers, hazard signals, multilingual reports (native script, romanized, English; duplicates, a rumour, vague and
missing-contact messages) and multi-stage disruption events (road closures, shelters cut off, stock losses, silent
villages) that run through the same channels and agents as live operation.

SYNTHETIC: every person, report, stock count, shelter/hospital name and capacity is invented. Report sentences in
regional languages are template-drafted and NOT validated by native speakers; Mizo and Khasi phrasing is especially
uncertain. Place names inside regional-language reports are kept in Latin script (native-script place aliases pending).

The scenario SCRIPT (which messages belong to which situation) is design data used by the generator, the final
report and the evaluation script. Operational agents only ever receive the rendered messages
(t, channel, sender, text, sender-metadata) — never the script."""
import re

from app.core import geo

# id, state/UT, region tags, disaster, difficulty, regional language, places [(name, lat, lng, population)]
LOCATIONS = [
    ("assam_brahmaputra_flood", "Assam", ["northeast", "riverine", "rural"], "flood", "advanced", "as",
     [("North Lakhimpur", 27.236, 94.105, 60000), ("Dhemaji", 27.482, 94.580, 15000), ("Majuli (Garamur)", 26.953, 94.170, 8000), ("Jorhat", 26.757, 94.203, 150000)]),
    ("bihar_kosi_flood", "Bihar", ["riverine", "rural", "border"], "flood", "advanced", "hi",
     [("Saharsa", 25.880, 86.600, 150000), ("Supaul", 26.122, 86.603, 65000), ("Birpur", 26.520, 87.010, 20000), ("Madhepura", 25.921, 86.792, 55000)]),
    ("kerala_kuttanad_flood", "Kerala", ["coastal", "riverine", "rural"], "flood", "intermediate", "ml",
     [("Alappuzha", 9.498, 76.339, 170000), ("Ramankary (Kuttanad)", 9.433, 76.460, 15000), ("Chengannur", 9.318, 76.611, 25000), ("Thiruvalla", 9.385, 76.575, 55000)]),
    ("mumbai_urban_flood", "Maharashtra", ["urban", "coastal"], "flood", "intermediate", "mr",
     [("Dadar", 19.018, 72.843, 400000), ("Sion", 19.040, 72.862, 300000), ("Kurla", 19.072, 72.879, 500000), ("Andheri East", 19.115, 72.870, 600000)]),
    ("chennai_urban_flood", "Tamil Nadu", ["urban", "coastal"], "flood", "beginner", "ta",
     [("Adyar", 13.006, 80.257, 200000), ("Velachery", 12.979, 80.218, 250000), ("Tambaram", 12.925, 80.127, 200000), ("Mudichur", 12.913, 80.070, 40000)]),
    ("srinagar_jhelum_flood", "Jammu and Kashmir", ["himalaya", "urban", "riverine"], "flood", "intermediate", "hi",
     [("Srinagar", 34.083, 74.797, 1200000), ("Pampore", 34.018, 74.933, 20000), ("Awantipora", 33.921, 75.011, 15000), ("Sopore", 34.300, 74.470, 70000)]),
    ("goa_mandovi_flood", "Goa", ["coastal", "urban"], "flood", "beginner", "en",
     [("Panaji", 15.490, 73.828, 115000), ("Mapusa", 15.593, 73.809, 40000), ("Bicholim", 15.600, 73.950, 17000), ("Ponda", 15.403, 74.015, 22000)]),
    ("tripura_gomati_flood", "Tripura", ["northeast", "border", "riverine"], "flood", "intermediate", "bn",
     [("Agartala", 23.831, 91.287, 400000), ("Udaipur", 23.533, 91.483, 35000), ("Sonamura", 23.470, 91.270, 15000), ("Khowai", 24.065, 91.605, 20000)]),
    ("punjab_sutlej_flood", "Punjab", ["riverine", "rural"], "flood", "intermediate", "pa",
     [("Rupnagar", 30.966, 76.533, 55000), ("Anandpur Sahib", 31.235, 76.502, 17000), ("Kiratpur Sahib", 31.182, 76.573, 8000), ("Nangal", 31.385, 76.376, 45000)]),
    ("odisha_puri_cyclone", "Odisha", ["coastal", "rural"], "cyclone", "advanced", "or",
     [("Bhubaneswar", 20.296, 85.825, 840000), ("Puri", 19.813, 85.831, 200000), ("Konark", 19.887, 86.095, 17000), ("Satapada", 19.667, 85.440, 8000)]),
    ("andhra_vizag_cyclone", "Andhra Pradesh", ["coastal", "urban"], "cyclone", "intermediate", "te",
     [("Visakhapatnam", 17.687, 83.218, 2000000), ("Anakapalli", 17.691, 83.004, 90000), ("Srikakulam", 18.297, 83.897, 150000), ("Bheemunipatnam", 17.890, 83.450, 55000)]),
    ("sundarbans_cyclone", "West Bengal", ["coastal", "remote", "riverine"], "cyclone", "advanced", "bn",
     [("Canning", 22.312, 88.666, 45000), ("Gosaba", 22.165, 88.808, 20000), ("Kakdwip", 21.872, 88.185, 30000), ("Sagar Island", 21.650, 88.080, 15000)]),
    ("kutch_cyclone", "Gujarat", ["coastal", "border", "rural"], "cyclone", "intermediate", "gu",
     [("Bhuj", 23.242, 69.667, 190000), ("Mandvi", 22.833, 69.353, 50000), ("Mundra", 22.839, 69.722, 25000), ("Jakhau", 23.220, 68.720, 5000)]),
    ("andaman_cyclone", "Andaman and Nicobar Islands", ["island", "remote", "coastal"], "cyclone", "advanced", "hi",
     [("Sri Vijaya Puram (Port Blair)", 11.623, 92.726, 100000), ("Baratang", 12.100, 92.750, 6000), ("Swaraj Dweep (Havelock)", 11.967, 93.000, 7000), ("Shaheed Dweep (Neil)", 11.833, 93.050, 3000)]),
    ("puducherry_cyclone", "Puducherry", ["coastal", "urban"], "cyclone", "beginner", "ta",
     [("Puducherry", 11.934, 79.830, 250000), ("Ariyankuppam", 11.900, 79.810, 40000), ("Villianur", 11.918, 79.762, 40000), ("Bahour", 11.805, 79.745, 25000)]),
    ("lakshadweep_cyclone", "Lakshadweep", ["island", "remote", "coastal"], "cyclone", "advanced", "ml",
     [("Kavaratti", 10.566, 72.642, 11000), ("Agatti", 10.857, 72.190, 7500), ("Amini", 11.123, 72.729, 7700), ("Andrott", 10.814, 73.681, 11000)]),
    ("daman_cyclone", "Dadra and Nagar Haveli and Daman and Diu", ["coastal", "urban"], "cyclone", "beginner", "gu",
     [("Daman", 20.414, 72.832, 45000), ("Vapi (adjacent, Gujarat)", 20.371, 72.904, 160000), ("Dadra", 20.322, 72.967, 10000), ("Silvassa", 20.273, 73.008, 100000)]),
    ("sikkim_earthquake", "Sikkim", ["himalaya", "hilly", "border"], "earthquake", "advanced", "ne",
     [("Gangtok", 27.330, 88.612, 100000), ("Singtam", 27.233, 88.500, 6000), ("Mangan", 27.510, 88.530, 4000), ("Namchi", 27.166, 88.364, 12000)]),
    ("manipur_earthquake", "Manipur", ["northeast", "hilly", "urban"], "earthquake", "intermediate", "mni",
     [("Imphal", 24.817, 93.937, 270000), ("Bishnupur", 24.630, 93.760, 15000), ("Moirang", 24.500, 93.770, 20000), ("Thoubal", 24.640, 94.000, 45000)]),
    ("delhi_earthquake", "Delhi", ["urban", "dense"], "earthquake", "advanced", "hi",
     [("Laxmi Nagar", 28.631, 77.277, 300000), ("Shahdara", 28.673, 77.289, 300000), ("Seelampur", 28.667, 77.268, 250000), ("Mayur Vihar", 28.607, 77.292, 200000)]),
    ("ladakh_earthquake", "Ladakh", ["himalaya", "remote", "border"], "earthquake", "intermediate", "hi",
     [("Leh", 34.164, 77.585, 30000), ("Nimmu", 34.190, 77.330, 1500), ("Thiksey", 34.056, 77.667, 3000), ("Diskit", 34.550, 77.550, 2000)]),
    ("mizoram_earthquake", "Mizoram", ["northeast", "hilly", "border"], "earthquake", "intermediate", "lus",
     [("Aizawl", 23.727, 92.718, 300000), ("Kolasib", 24.224, 92.676, 25000), ("Serchhip", 23.310, 92.850, 22000), ("Champhai", 23.470, 93.330, 33000)]),
    ("chandigarh_earthquake", "Chandigarh", ["urban"], "earthquake", "beginner", "pa",
     [("Chandigarh Sector 17", 30.741, 76.782, 300000), ("Manimajra", 30.720, 76.840, 100000), ("Panchkula (adjacent)", 30.695, 76.860, 200000), ("Mohali (adjacent)", 30.704, 76.717, 180000)]),
    ("wayanad_landslide", "Kerala", ["hilly", "rural", "remote"], "landslide", "advanced", "ml",
     [("Kalpetta", 11.608, 76.083, 32000), ("Meppadi", 11.553, 76.133, 20000), ("Chooralmala", 11.495, 76.150, 4000), ("Mundakkai", 11.478, 76.168, 3000)]),
    ("himachal_mandi_landslide", "Himachal Pradesh", ["himalaya", "hilly"], "landslide", "intermediate", "hi",
     [("Mandi", 31.708, 76.932, 30000), ("Pandoh", 31.670, 77.060, 5000), ("Aut", 31.750, 77.200, 4000), ("Kullu", 31.958, 77.109, 20000)]),
    ("joshimath_landslide", "Uttarakhand", ["himalaya", "hilly", "border"], "landslide", "advanced", "hi",
     [("Chamoli (Gopeshwar)", 30.400, 79.320, 20000), ("Karnaprayag", 30.260, 79.220, 10000), ("Joshimath", 30.555, 79.565, 17000), ("Badrinath", 30.744, 79.493, 2500)]),
    ("arunachal_capital_landslide", "Arunachal Pradesh", ["northeast", "hilly", "border"], "landslide", "intermediate", "en",
     [("Itanagar", 27.084, 93.605, 60000), ("Naharlagun", 27.104, 93.695, 40000), ("Doimukh", 27.140, 93.760, 10000), ("Ziro", 27.540, 93.830, 12000)]),
    ("nagaland_kohima_landslide", "Nagaland", ["northeast", "hilly"], "landslide", "beginner", "en",
     [("Kohima", 25.670, 94.110, 100000), ("Jotsoma", 25.660, 94.060, 5000), ("Chiephobozou", 25.790, 94.020, 4000), ("Phek", 25.660, 94.470, 15000)]),
    ("meghalaya_sohra_landslide", "Meghalaya", ["northeast", "hilly", "border"], "landslide", "intermediate", "kha",
     [("Shillong", 25.578, 91.893, 150000), ("Sohra (Cherrapunji)", 25.270, 91.730, 12000), ("Mawsynram", 25.300, 91.580, 3000), ("Pynursla", 25.300, 91.900, 5000)]),
    ("almora_wildfire", "Uttarakhand", ["himalaya", "hilly", "forest"], "wildfire", "intermediate", "hi",
     [("Almora", 29.597, 79.659, 35000), ("Ranikhet", 29.643, 79.432, 20000), ("Nainital", 29.380, 79.464, 42000), ("Bageshwar", 29.838, 79.771, 10000)]),
    ("simlipal_wildfire", "Odisha", ["forest", "rural", "tribal"], "wildfire", "beginner", "or",
     [("Baripada", 21.940, 86.720, 120000), ("Jashipur", 21.960, 86.060, 10000), ("Udala", 21.580, 86.570, 15000), ("Karanjia", 21.760, 85.970, 25000)]),
    ("bandipur_wildfire", "Karnataka", ["forest", "rural"], "wildfire", "beginner", "kn",
     [("Gundlupet", 11.810, 76.690, 30000), ("Bandipur", 11.667, 76.633, 2000), ("Begur", 11.880, 76.620, 5000), ("Nanjangud", 12.120, 76.680, 50000)]),
    ("bastar_wildfire", "Chhattisgarh", ["forest", "tribal", "remote"], "wildfire", "intermediate", "hi",
     [("Jagdalpur", 19.082, 82.022, 125000), ("Kondagaon", 19.590, 81.660, 40000), ("Dantewada", 18.900, 81.350, 15000), ("Kanker", 20.270, 81.490, 30000)]),
    ("marathwada_drought", "Maharashtra", ["rural", "semi-arid"], "drought", "beginner", "mr",
     [("Latur", 18.400, 76.560, 380000), ("Ambajogai", 18.730, 76.390, 75000), ("Beed", 18.990, 75.760, 150000), ("Dharashiv (Osmanabad)", 18.180, 76.040, 110000)]),
    ("barmer_drought", "Rajasthan", ["desert", "border", "remote"], "drought", "intermediate", "hi",
     [("Barmer", 25.750, 71.390, 100000), ("Balotra", 25.830, 72.240, 80000), ("Pokaran", 26.920, 71.920, 20000), ("Jaisalmer", 26.915, 70.908, 65000)]),
    ("bundelkhand_drought", "Uttar Pradesh", ["rural", "semi-arid"], "drought", "beginner", "hi",
     [("Banda", 25.480, 80.330, 150000), ("Mahoba", 25.290, 79.870, 95000), ("Hamirpur", 25.950, 80.150, 35000), ("Chitrakoot (Karwi)", 25.200, 80.900, 60000)]),
    ("anantapur_drought", "Andhra Pradesh", ["rural", "semi-arid"], "drought", "intermediate", "te",
     [("Anantapur", 14.681, 77.600, 260000), ("Dharmavaram", 14.410, 77.720, 120000), ("Penukonda", 14.080, 77.590, 30000), ("Kadiri", 14.110, 78.160, 90000)]),
    ("haryana_heatwave", "Haryana", ["rural", "semi-arid"], "heatwave", "beginner", "hi",
     [("Hisar", 29.149, 75.721, 300000), ("Fatehabad", 29.515, 75.455, 70000), ("Sirsa", 29.534, 75.029, 180000), ("Bhiwani", 28.793, 76.139, 200000)]),
    ("vidarbha_heatwave", "Maharashtra", ["urban", "rural"], "heatwave", "intermediate", "mr",
     [("Nagpur", 21.146, 79.088, 2400000), ("Wardha", 20.745, 78.602, 110000), ("Chandrapur", 19.961, 79.296, 320000), ("Brahmapuri", 20.610, 79.860, 40000)]),
    ("telangana_heatwave", "Telangana", ["industrial", "rural"], "heatwave", "intermediate", "te",
     [("Karimnagar", 18.439, 79.129, 300000), ("Peddapalli", 18.614, 79.374, 45000), ("Ramagundam", 18.755, 79.474, 230000), ("Mancherial", 18.871, 79.461, 90000)]),
    ("nagapattinam_tsunami", "Tamil Nadu", ["coastal", "rural"], "tsunami", "advanced", "ta",
     [("Nagapattinam", 10.766, 79.843, 100000), ("Velankanni", 10.681, 79.849, 12000), ("Karaikal (Puducherry UT)", 10.925, 79.838, 90000), ("Tharangambadi", 11.028, 79.855, 25000)]),
    ("kollam_tsunami", "Kerala", ["coastal"], "tsunami", "intermediate", "ml",
     [("Kollam", 8.893, 76.614, 350000), ("Karunagappally", 9.060, 76.535, 40000), ("Alappad", 9.050, 76.500, 25000), ("Kayamkulam", 9.172, 76.501, 70000)]),
    ("little_andaman_tsunami", "Andaman and Nicobar Islands", ["island", "remote", "coastal"], "tsunami", "advanced", "hi",
     [("Sri Vijaya Puram (Port Blair)", 11.623, 92.726, 100000), ("Hut Bay (Little Andaman)", 10.590, 92.550, 18000), ("Rangat", 12.500, 92.930, 6000), ("Wandoor", 11.600, 92.610, 3000)]),
    ("vizag_gas_leak", "Andhra Pradesh", ["industrial", "urban"], "industrial", "intermediate", "te",
     [("Gopalapatnam", 17.750, 83.220, 120000), ("RR Venkatapuram", 17.766, 83.207, 15000), ("Pendurthi", 17.810, 83.200, 60000), ("Simhachalam", 17.766, 83.250, 30000)]),
    ("ankleshwar_chemical", "Gujarat", ["industrial", "urban"], "industrial", "beginner", "gu",
     [("Bharuch", 21.705, 72.998, 170000), ("Ankleshwar", 21.626, 73.015, 90000), ("Jhagadia", 21.730, 73.130, 15000), ("Dahej", 21.700, 72.530, 10000)]),
    ("jharia_coalfire_industrial", "Jharkhand", ["industrial", "mining"], "industrial", "advanced", "hi",
     [("Dhanbad", 23.795, 86.430, 1100000), ("Jharia", 23.750, 86.410, 85000), ("Sindri", 23.650, 86.480, 75000), ("Bokaro", 23.670, 86.150, 400000)]),
    ("bhopal_chemical", "Madhya Pradesh", ["industrial", "urban"], "industrial", "advanced", "hi",
     [("Bhopal (Chola)", 23.280, 77.420, 1800000), ("Mandideep", 23.100, 77.530, 60000), ("Sehore", 23.200, 77.080, 110000), ("Vidisha", 23.530, 77.810, 155000)]),
]

ROMANIZED = {"kn": "kn_rom", "hi": "hi_rom"}

# need templates per language. {place} and {n}. Regional sentences are template-drafted, not native-validated.
T = {
    "en": {"rescue": "{n} people trapped near {place}, need rescue urgently",
           "water": "No drinking water at {place} camp for {n} people since yesterday",
           "food": "{n} people at {place} have had no food since morning, please send food",
           "medical": "{n} injured people at {place} need a doctor and medicines",
           "shelter": "{n} families at {place} have lost their homes, need shelter and tarpaulins"},
    "hi": {"rescue": "{place} के पास {n} लोग फंसे हुए हैं, तुरंत बचाव चाहिए",
           "water": "{place} कैंप में {n} लोगों के लिए पीने का पानी नहीं है",
           "food": "{place} में {n} लोगों को सुबह से खाना नहीं मिला, खाना भेजो",
           "medical": "{place} में {n} घायल लोगों को डॉक्टर और दवाई चाहिए",
           "shelter": "{place} में {n} परिवारों के घर टूट गए, रहने की जगह चाहिए"},
    "hi_rom": {"rescue": "{place} ke paas {n} log phase hue hain, jaldi rescue bhejo",
               "water": "{place} camp me {n} logon ke liye peene ka paani nahi hai",
               "food": "{place} me {n} logo ko subah se khana nahi mila, khana bhejo please",
               "medical": "{place} me {n} log ghayal hain, doctor aur dawai chahiye",
               "shelter": "{place} me {n} parivaar ke ghar toot gaye, rehne ki jagah chahiye"},
    "kn": {"rescue": "{place} ಹತ್ತಿರ {n} ಜನ ಸಿಕ್ಕಿಹಾಕಿಕೊಂಡಿದ್ದಾರೆ, ತಕ್ಷಣ ರಕ್ಷಣೆ ಬೇಕು",
           "water": "{place} ಶಿಬಿರದಲ್ಲಿ {n} ಜನರಿಗೆ ಕುಡಿಯುವ ನೀರು ಇಲ್ಲ",
           "food": "{place} ನಲ್ಲಿ {n} ಜನರಿಗೆ ಬೆಳಿಗ್ಗೆಯಿಂದ ಊಟ ಸಿಕ್ಕಿಲ್ಲ, ಆಹಾರ ಕಳುಹಿಸಿ",
           "medical": "{place} ನಲ್ಲಿ {n} ಜನ ಗಾಯಗೊಂಡಿದ್ದಾರೆ, ವೈದ್ಯರು ಮತ್ತು ಔಷಧಿ ಬೇಕು",
           "shelter": "{place} ನಲ್ಲಿ {n} ಕುಟುಂಬಗಳ ಮನೆ ಹಾಳಾಗಿದೆ, ಆಶ್ರಯ ಬೇಕು"},
    "kn_rom": {"rescue": "{place} hatra {n} jana sikkiddare, bega rescue beku",
               "water": "{place} camp alli {n} janakke kudiyo neeru illa",
               "food": "{place} alli {n} janakke beliggeinda oota sikkilla, food kalsi",
               "medical": "{place} alli {n} jana gaaya aagidare, doctor mattu medicine beku",
               "shelter": "{place} alli {n} family mane haalaagide, ashraya beku"},
    "ta": {"rescue": "{place} அருகே {n} பேர் சிக்கியுள்ளனர், உடனடியாக மீட்பு தேவை",
           "water": "{place} முகாமில் {n} பேருக்கு குடிநீர் இல்லை",
           "food": "{place} இல் {n} பேருக்கு காலை முதல் உணவு இல்லை, உணவு அனுப்புங்கள்",
           "medical": "{place} இல் {n} பேர் காயமடைந்துள்ளனர், மருத்துவர் மற்றும் மருந்து தேவை",
           "shelter": "{place} இல் {n} குடும்பங்களின் வீடுகள் சேதமடைந்தன, தங்குமிடம் தேவை"},
    "te": {"rescue": "{place} దగ్గర {n} మంది చిక్కుకుపోయారు, వెంటనే రక్షణ కావాలి",
           "water": "{place} శిబిరంలో {n} మందికి తాగునీరు లేదు",
           "food": "{place} లో {n} మందికి ఉదయం నుంచి ఆహారం లేదు, ఆహారం పంపండి",
           "medical": "{place} లో {n} మంది గాయపడ్డారు, డాక్టర్ మరియు మందులు కావాలి",
           "shelter": "{place} లో {n} కుటుంబాల ఇళ్ళు దెబ్బతిన్నాయి, ఆశ్రయం కావాలి"},
    "ml": {"rescue": "{place} സമീപം {n} പേർ കുടുങ്ങിക്കിടക്കുന്നു, ഉടൻ രക്ഷാപ്രവർത്തനം വേണം",
           "water": "{place} ക്യാമ്പിൽ {n} പേർക്ക് കുടിവെള്ളമില്ല",
           "food": "{place} ൽ {n} പേർക്ക് രാവിലെ മുതൽ ഭക്ഷണമില്ല, ഭക്ഷണം അയക്കൂ",
           "medical": "{place} ൽ {n} പേർക്ക് പരിക്കേറ്റു, ഡോക്ടറും മരുന്നും വേണം",
           "shelter": "{place} ൽ {n} കുടുംബങ്ങളുടെ വീടുകൾ തകർന്നു, താമസസ്ഥലം വേണം"},
    "mr": {"rescue": "{place} जवळ {n} लोक अडकले आहेत, लगेच बचाव पाहिजे",
           "water": "{place} शिबिरात {n} लोकांसाठी पिण्याचे पाणी नाही",
           "food": "{place} येथे {n} लोकांना सकाळपासून जेवण मिळाले नाही, अन्न पाठवा",
           "medical": "{place} येथे {n} लोक जखमी आहेत, डॉक्टर आणि औषध पाहिजे",
           "shelter": "{place} येथे {n} कुटुंबांची घरे पडली, निवारा पाहिजे"},
    "bn": {"rescue": "{place} এর কাছে {n} জন আটকে আছে, এখনই উদ্ধার দরকার",
           "water": "{place} শিবিরে {n} জনের জন্য পানীয় জল নেই",
           "food": "{place} এ {n} জন সকাল থেকে খাবার পায়নি, খাবার পাঠান",
           "medical": "{place} এ {n} জন আহত, ডাক্তার আর ওষুধ দরকার",
           "shelter": "{place} এ {n} পরিবারের ঘর ভেঙে গেছে, আশ্রয় দরকার"},
    "as": {"rescue": "{place} ৰ ওচৰত {n} জন মানুহ আবদ্ধ হৈ আছে, সোনকালে উদ্ধাৰ লাগে",
           "water": "{place} শিবিৰত {n} জনৰ বাবে খোৱা পানী নাই",
           "food": "{place} ত {n} জনে ৰাতিপুৱাৰ পৰা খাদ্য পোৱা নাই, খাদ্য পঠিয়াওক",
           "medical": "{place} ত {n} জন আহত, চিকিৎসক আৰু ঔষধ লাগে",
           "shelter": "{place} ত {n} টা পৰিয়ালৰ ঘৰ ভাঙি গৈছে, আশ্ৰয় লাগে"},
    "or": {"rescue": "{place} ପାଖରେ {n} ଜଣ ଫସି ରହିଛନ୍ତି, ତୁରନ୍ତ ଉଦ୍ଧାର ଦରକାର",
           "water": "{place} ଶିବିରରେ {n} ଜଣଙ୍କ ପାଇଁ ପିଇବା ପାଣି ନାହିଁ",
           "food": "{place} ରେ {n} ଜଣ ସକାଳୁ ଖାଇବା ପାଇନାହାନ୍ତି, ଖାଦ୍ୟ ପଠାନ୍ତୁ",
           "medical": "{place} ରେ {n} ଜଣ ଆହତ, ଡାକ୍ତର ଓ ଔଷଧ ଦରକାର",
           "shelter": "{place} ରେ {n} ପରିବାରର ଘର ଭାଙ୍ଗିଯାଇଛି, ଆଶ୍ରୟ ଦରକାର"},
    "gu": {"rescue": "{place} પાસે {n} લોકો ફસાયેલા છે, તાત્કાલિક બચાવ જોઈએ",
           "water": "{place} કેમ્પમાં {n} લોકો માટે પીવાનું પાણી નથી",
           "food": "{place} માં {n} લોકોને સવારથી ખાવાનું મળ્યું નથી, ખોરાક મોકલો",
           "medical": "{place} માં {n} લોકો ઘાયલ છે, ડૉક્ટર અને દવા જોઈએ",
           "shelter": "{place} માં {n} પરિવારોના ઘર તૂટી ગયા, આશ્રય જોઈએ"},
    "pa": {"rescue": "{place} ਨੇੜੇ {n} ਲੋਕ ਫਸੇ ਹੋਏ ਹਨ, ਤੁਰੰਤ ਬਚਾਅ ਚਾਹੀਦਾ ਹੈ",
           "water": "{place} ਕੈਂਪ ਵਿੱਚ {n} ਲੋਕਾਂ ਲਈ ਪੀਣ ਵਾਲਾ ਪਾਣੀ ਨਹੀਂ ਹੈ",
           "food": "{place} ਵਿੱਚ {n} ਲੋਕਾਂ ਨੂੰ ਸਵੇਰ ਤੋਂ ਖਾਣਾ ਨਹੀਂ ਮਿਲਿਆ, ਖਾਣਾ ਭੇਜੋ",
           "medical": "{place} ਵਿੱਚ {n} ਲੋਕ ਜ਼ਖਮੀ ਹਨ, ਡਾਕਟਰ ਅਤੇ ਦਵਾਈ ਚਾਹੀਦੀ ਹੈ",
           "shelter": "{place} ਵਿੱਚ {n} ਪਰਿਵਾਰਾਂ ਦੇ ਘਰ ਟੁੱਟ ਗਏ, ਰਹਿਣ ਦੀ ਥਾਂ ਚਾਹੀਦੀ ਹੈ"},
    "ne": {"rescue": "{place} नजिक {n} जना फसेका छन्, तुरुन्तै उद्धार चाहियो",
           "water": "{place} शिविरमा {n} जनाका लागि खानेपानी छैन",
           "food": "{place} मा {n} जनाले बिहानदेखि खाना पाएका छैनन्, खाना पठाउनुहोस्",
           "medical": "{place} मा {n} जना घाइते छन्, डाक्टर र औषधि चाहियो",
           "shelter": "{place} मा {n} परिवारको घर भत्कियो, आश्रय चाहियो"},
    "lus": {"rescue": "{place} bulah mi {n} an tang, min chhanhim turin lo kal vat rawh",
            "water": "{place} camp-ah mi {n} tan tui in tur a awm lo",
            "food": "{place} ah mi {n} chaw an ei lo, chaw min rawn thawn rawh",
            "medical": "{place} ah mi {n} an hliam, doctor leh damdawi kan mamawh",
            "shelter": "{place} ah chhungkua {n} in a chim, awmna kan mamawh"},
    "kha": {"rescue": "Ha {place} ki {n} ngut ki la kem, ai ïarap kloi",
            "water": "Ha {place} camp ym don um dih na ka bynta ki {n} ngut",
            "food": "Ha {place} ki {n} ngut ym pat bam ja, phah ja",
            "medical": "Ha {place} ki {n} ngut ki la shah pynmynsaw, donkam doktor bad dawai",
            "shelter": "Ha {place} ki {n} ngut ki la duh ïing, donkam jaka sah"},
}
# languages without a template set fall back to these for generated reports (Manipuri script support pending)
TEMPLATE_FALLBACK = {"mni": "en", "brx": "hi", "grt": "en", "trp": "bn"}

FLAVOUR = {"flood": "Flood water rising", "cyclone": "After the cyclone", "earthquake": "Earthquake, buildings collapsed",
           "landslide": "Landslide", "wildfire": "Forest fire spreading", "drought": "Drought, wells dry",
           "heatwave": "Heatwave, heatstroke cases", "tsunami": "Tsunami waves hit the coast", "industrial": "Gas leak, eyes burning"}
RUMOUR = {
    "flood": "FORWARD AS RECEIVED: the dam above {place} has burst, the whole town will drown in 1 hour, share to all",
    "cyclone": "Forwarded: a second cyclone bigger than this one will hit {place} tonight, govt is hiding it, share to all",
    "earthquake": "Forwarded: 8.5 earthquake predicted at {place} tonight at 2 am, sleep outside, share to all",
    "landslide": "Forwarded: the whole {place} hill will collapse tonight, scientists warned, share to all",
    "wildfire": "Forwarded: fire has reached {place} market, the entire town is burning, share to all",
    "drought": "Forwarded: water tankers at {place} are poisoned, do not drink, share to all",
    "heatwave": "Forwarded: temperature will touch 55 degrees in {place} tomorrow, share to all",
    "tsunami": "URGENT forwarded: a second tsunami wave 30 m high will hit {place} in 20 minutes, share to all",
    "industrial": "Forwarded: the gas from {place} will spread 50 km, everyone must leave the district, share to all",
}
# disaster -> needs of the four situations (place index 1, 2, 3, 0)
NEEDS = {
    "flood": ["rescue", "water", "food", "medical"], "cyclone": ["shelter", "food", "rescue", "medical"],
    "earthquake": ["rescue", "medical", "shelter", "water"], "landslide": ["rescue", "food", "medical", "shelter"],
    "wildfire": ["shelter", "medical", "food", "water"], "drought": ["water", "water", "food", "medical"],
    "heatwave": ["medical", "water", "medical", "shelter"], "tsunami": ["rescue", "water", "medical", "food"],
    "industrial": ["medical", "shelter", "medical", "water"],
}
PEOPLE = [14, 60, 35, 9]
SENSORS = {"flood": "CWC river gauges (mock)", "cyclone": "IMD cyclone bulletins (mock)", "earthquake": "Seismic network (mock)",
           "landslide": "Landslide early-warning (mock)", "wildfire": "Satellite fire hotspots, FIRMS-style (mock)",
           "drought": "Drought monitor (mock)", "heatwave": "IMD heat bulletins (mock)", "tsunami": "INCOIS tsunami bulletins (mock)",
           "industrial": "Pollution control board sensors (mock)"}
SHELTER_NAME = {"cyclone": "Multipurpose cyclone shelter, {p}", "heatwave": "Cooling centre, {p}", "industrial": "Evacuation camp, {p}",
                "wildfire": "Evacuation camp, {p}", "drought": "Water distribution point, {p}"}


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower().split("(")[0]).strip("_")


def _lang_for(code: str) -> str:
    return code if code in T else TEMPLATE_FALLBACK.get(code, "en")


def _zoom(places) -> int:
    d = max(geo.haversine_m(a[1], a[2], b[1], b[2]) for a in places for b in places) / 1000
    return 13 if d < 8 else 12 if d < 18 else 11 if d < 40 else 10 if d < 80 else 9 if d < 160 else 8


def _stock(dis: str, island: bool, scale: float) -> dict:
    from app.disasters import profile
    s = {"food_kits": 500, "water_litres": 14000, "medical_kits": 100, "blankets": 300, "volunteers": 30, "vehicles": 6,
         "boats": 6 if dis in ("flood", "tsunami", "cyclone") or island else 1}
    for k in profile(dis)["per_person_day"]:
        s.setdefault(k, 1500)
    return {k: round(v * scale) for k, v in s.items()}


def _spec(loc, idx: int) -> dict:
    sid, st, tags, dis, diff, lang, places = loc
    codes = [slug(p[0]) for p in places]
    island = "island" in tags
    zones = []
    for (name, lat, lng, pop), code in zip(places, codes):
        remote = 0.7 if ("remote" in tags or "island" in tags) else 0.3
        aliases = sorted({name.lower(), name.split(" (")[0].lower(), *(re.findall(r"\(([^)]+)\)", name.lower()))})
        zones.append((code, name.split(" (adjacent")[0], lat, lng, pop, max(0.3, min(3.0, pop / 60000)),
                      {"elderly_share": 0.12, "children_share": 0.22, "medical_facilities": 1, "remoteness": remote}, aliases))
    pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (2, 3)]
    roads = []
    for a, b in pairs:
        attrs: dict = {}
        if island and a == 0:
            attrs = {"kind": "ferry", "allowed_vehicles": ["boat"]}
        elif "hilly" in tags and (a, b) == (0, 1):
            attrs = {"kind": "ghat"}
        elif ("riverine" in tags or "coastal" in tags) and (a, b) == (1, 2):
            attrs = {"kind": "bridge"}
        elif "remote" in tags and (a, b) == (2, 3):
            attrs = {"surface": "unpaved", "allowed_vehicles": ["4x4", "two_wheeler"]}
        name = f"{zones[a][1]}–{zones[b][1]} {'ferry' if attrs.get('kind') == 'ferry' else 'road'}"
        roads.append((f"r_{codes[a]}_{codes[b]}"[:32], name, codes[a], codes[b], attrs))
    shelters = []
    for k, i in enumerate((1, 2, 3)):
        p = zones[i]
        nm = SHELTER_NAME.get(dis, "Govt school relief camp, {p}").format(p=p[1])
        access = [r[0] for r in roads if p[0] in (r[2], r[3])]
        cap = (250, 200, 300)[k]
        occ = round(cap * (0.85, 0.7, 0.6)[k])
        water = 3000 if (k == 0 and diff != "beginner") else 7000
        shelters.append((nm, p[0], round(p[2] + 0.003, 5), round(p[3] - 0.003, 5), cap, occ, access,
                         {"water_litres": water, "food_kits": round(occ * 0.6), "medical_kits": 10, "blankets": round(occ * 0.5)}))
    big = zones[0]
    depots = [(f"{big[1]} district relief depot", f"{st} SDMA (synthetic)", big[0], round(big[2] - 0.004, 5), round(big[3] + 0.004, 5),
               _stock(dis, island, 1.0), 0.0),
              (f"{zones[2][1]} NGO store", "NGO (synthetic)", zones[2][0], round(zones[2][2] - 0.004, 5), round(zones[2][3] + 0.004, 5),
               _stock(dis, island, 0.4), -20.0 if diff == "advanced" else 0.0)]
    hospitals = [(f"District hospital, {big[1]}", big[0], round(big[2] + 0.005, 5), round(big[3] - 0.005, 5), 200),
                 (f"Community Health Centre, {zones[2][1]}", zones[2][0], round(zones[2][2] + 0.005, 5), round(zones[2][3] + 0.005, 5), 30)]
    reg = lang
    ph = f"+9170{idx:02d}"
    sources = [("sdma", "official_agency", f"{st} SDMA control room (synthetic)", None, "en"),
               ("sensor", "sensor", SENSORS[dis], None, "en"),
               ("ndrf", "field_team", f"NDRF team {idx % 16 + 1} (synthetic)", f"{ph}00001", "en"),
               ("vol_a", "volunteer", "Volunteer A (synthetic)", f"{ph}00002", reg),
               ("ngo", "ngo", f"{big[1]} relief NGO (synthetic)", f"{ph}00003", "en"),
               ("news_reg", "social", "Regional news (mock)", None, reg),
               ("news_en", "social", "English news (mock)", None, "en"),
               ("mgr1", "volunteer", f"{zones[1][1]} camp manager (synthetic)", f"{ph}00004", reg)]
    vskills = {"flood": ["boat", "rescue"], "tsunami": ["boat", "rescue"], "cyclone": ["rescue", "logistics"], "earthquake": ["rescue", "medical"],
               "landslide": ["rescue", "driving"], "wildfire": ["firefighting", "first_aid"], "drought": ["logistics", "driving"],
               "heatwave": ["medical", "first_aid"], "industrial": ["medical", "hazmat"]}[dis]
    vols = [("V-001", "Volunteer 1", codes[0], [*vskills, "driving"], "boat" if island else "4x4", [reg, "en"], (5, 4)),
            ("V-002", "Volunteer 2", codes[1], ["medical", "first_aid"], "truck" if not island else "boat", [reg, "hi"], (3, 3)),
            ("V-003", "Volunteer 3", codes[2], vskills, "boat" if dis in ("flood", "tsunami") or island else "4x4", [reg], (6, 3)),
            ("V-004", "Volunteer 4", codes[3], ["logistics", "translation"], "two_wheeler", [reg, "en", "hi"], (1, 1)),
            ("V-005", "Volunteer 5", codes[0], ["driving", "logistics"], "truck", ["hi", "en"], (8, 7)),
            ("V-006", "Volunteer 6", codes[1], [*vskills], None, [reg], (0, 0))]
    checkins = [(3.0, shelters[0][0], shelters[0][5]), (3.2, shelters[1][0], shelters[1][5]), (3.4, shelters[2][0], shelters[2][5]),
                (7.0, shelters[0][0], shelters[0][5] + 10), (7.2, shelters[1][0], shelters[1][5] + 5)]
    if diff != "advanced":
        checkins.append((7.4, shelters[2][0], shelters[2][5] + 5))
    landmarks = [(f"{zones[1][1]} market", codes[1], round(zones[1][2] + 0.002, 5), round(zones[1][3] + 0.002, 5), [f"{zones[1][1].lower()} market"]),
                 (f"{zones[3][1]} bus stand", codes[3], round(zones[3][2] - 0.002, 5), round(zones[3][3] + 0.002, 5), [f"{zones[3][1].lower()} bus stand"])]
    return {"id": f"lab:{sid}", "name": f"{places[0][0]} area", "state": st, "center": [round(sum(p[1] for p in places) / 4, 4), round(sum(p[2] for p in places) / 4, 4)],
            "zoom": _zoom(places), "languages": sorted({reg, "en", "hi"}), "zones": zones, "landmarks": landmarks, "roads": roads,
            "depots": depots, "shelters": shelters, "hospitals": hospitals, "sources": sources, "volunteers": vols, "checkins": checkins,
            "managers": {codes[1]: "mgr1"}}


def _signals(dis: str, z: list, spec: dict) -> list:
    c = z  # zone codes
    P = {zz[0]: zz for zz in spec["zones"]}

    def ring(i, r):
        # never wider than a fifth of the distance to the nearest other place, so a footprint over a town does not
        # silently cut every road out of it (roads are cut by explicit stage events instead)
        near = min(geo.haversine_m(P[c[i]][2], P[c[i]][3], P[o][2], P[o][3]) for o in c if o != c[i])
        return geo.circle(P[c[i]][2], P[c[i]][3], min(r, 0.2 * near))

    def ext(v, polys, label):
        return {"version": v, "polygons": polys, "label": label}
    if dis == "flood":
        return [(0.0, "rainfall", c[0], {"mm_24h": 190, "category": "very heavy"}, "IMD (mock)"),
                (1.0, "river", c[1], {"station": f"River at {P[c[1]][1]}", "level_m": 8.4, "danger_m": 7.9}, "CWC (mock)"),
                (1.5, "flood_extent", None, ext(1, [ring(1, 1800)], "satellite flood extent"), "Satellite flood extent (mock, Sentinel-1 style)"),
                (5.0, "flood_extent", None, ext(2, [ring(1, 2200), ring(2, 1500)], "satellite flood extent"), "Satellite flood extent (mock, Sentinel-1 style)")]
    if dis == "cyclone":
        return [(0.0, "wind", c[1], {"speed_kmph": 165, "category": "very severe cyclonic storm"}, "IMD (mock)"),
                (1.0, "storm_surge", c[1], {"height_m": 2.5}, "INCOIS (mock)"),
                (1.5, "flood_extent", None, ext(1, [ring(1, 2500)], "cyclone surge and wind-damage footprint"), "Wind/surge footprint (mock)"),
                (3.0, "power_outage", c[2], {"feeders_off": 6}, "Power utility feed (mock)"),
                (3.0, "tower_outage", c[3], {"towers_down": 2, "towers_total": 3}, "Telecom operator feed (mock)")]
    if dis == "earthquake":
        return [(0.0, "quake", None, {"magnitude": 6.4, "place": f"near {P[c[1]][1]}", "depth_km": 12}, "Seismic network (mock)"),
                (0.5, "tower_outage", c[2], {"towers_down": 2, "towers_total": 3}, "Telecom operator feed (mock)"),
                (1.0, "flood_extent", None, ext(1, [ring(1, 1500), ring(0, 900)], "damage proxy map"), "Satellite damage proxy map (mock)"),
                (5.0, "quake", None, {"magnitude": 4.8, "place": f"aftershock near {P[c[1]][1]}", "depth_km": 9}, "Seismic network (mock)")]
    if dis == "landslide":
        return [(0.0, "rainfall", c[1], {"mm_24h": 250, "category": "extremely heavy"}, "IMD (mock)"),
                (1.0, "flood_extent", None, ext(1, [ring(1, 1200)], "landslide extent"), "Landslide extent (mock)"),
                (2.0, "tower_outage", c[3], {"towers_down": 2, "towers_total": 2}, "Telecom operator feed (mock)"),
                (5.0, "flood_extent", None, ext(2, [ring(1, 1500), ring(3, 1000)], "landslide extent"), "Landslide extent (mock)")]
    if dis == "wildfire":
        return [(0.0, "fire", c[1], {"hotspots": 42, "frp_mw": 310}, SENSORS["wildfire"]),
                (1.0, "flood_extent", None, ext(1, [ring(1, 2000)], "fire perimeter"), "Fire perimeter (mock)"),
                (3.0, "aqi", c[2], {"aqi": 380, "pm25": 260}, "Air quality monitors (mock)"),
                (5.0, "flood_extent", None, ext(2, [ring(1, 2600), ring(2, 1200)], "fire perimeter"), "Fire perimeter (mock)")]
    if dis == "drought":
        return [(0.0, "drought_index", c[0], {"spi_3month": -2.1, "reservoir_pct": 8}, SENSORS["drought"]),
                (1.0, "groundwater", c[1], {"depth_m": 180, "borewells_dry_pct": 70}, "Groundwater board (mock)"),
                (4.0, "heat", c[2], {"tmax_c": 43}, "IMD (mock)")]
    if dis == "heatwave":
        return [(0.0, "heat", c[0], {"tmax_c": 46.5, "heat_index_c": 52}, SENSORS["heatwave"]),
                (2.0, "heat", c[1], {"tmax_c": 47.2, "night_min_c": 34}, SENSORS["heatwave"]),
                (3.0, "power_outage", c[2], {"feeders_off": 4}, "Power utility feed (mock)")]
    if dis == "tsunami":
        return [(0.0, "quake", None, {"magnitude": 8.6, "place": "offshore, Indian Ocean", "depth_km": 25}, "Seismic network (mock)"),
                (0.2, "tsunami_warning", None, {"level": "warning", "eta_min": 40}, SENSORS["tsunami"]),
                (1.0, "flood_extent", None, ext(1, [ring(1, 1600), ring(0, 1000)], "coastal inundation"), "Coastal inundation (mock)"),
                (1.5, "tower_outage", c[2], {"towers_down": 2, "towers_total": 2}, "Telecom operator feed (mock)")]
    return [(0.0, "gas", c[0], {"chemical": "styrene-like vapour (synthetic)", "ppm": 400}, SENSORS["industrial"]),
            (0.5, "flood_extent", None, ext(1, [ring(0, 1500)], "gas plume model"), "Plume dispersion model (mock)"),
            (2.0, "aqi", c[1], {"aqi": 420}, "Air quality monitors (mock)"),
            (3.0, "flood_extent", None, ext(2, [ring(0, 1800), ring(1, 1200)], "gas plume model"), "Plume dispersion model (mock)")]


def _script(loc, idx: int, spec: dict) -> tuple[list, list, list]:
    """Returns (script rows with labels, events, stages). Script rows: (t, channel, who, text, origin_zone, label)."""
    sid, st, tags, dis, diff, lang, places = loc
    reg = _lang_for(lang)
    zc = [z[0] for z in spec["zones"]]
    zn = [z[1] for z in spec["zones"]]
    ph = f"+9171{idx:02d}"
    rows = []
    k = 0
    n_sit = 3 if diff == "beginner" else 4
    order = [1, 2, 3, 0]
    for s in range(n_sit):
        need = NEEDS[dis][s]
        pi = order[s]
        place, n = zn[pi], PEOPLE[s]
        key = f"S{s + 1}"
        t0 = 0.5 + s * 1.2
        lab = {"key": key, "real": True, "need": need, "people": n, "zone": zc[pi]}
        rows.append((t0, "sms", f"{ph}{k:04d}", T[reg][need].format(place=place, n=n), zc[pi], lab)); k += 1
        rows.append((t0 + 0.3, "social_feed", "@local_updates", f"{FLAVOUR[dis]}: " + T["en"][need].format(place=place, n=n), zc[pi], lab))
        if s < 2 or diff == "advanced":
            alt = ROMANIZED.get(reg) or ("hi" if reg != "hi" else "hi_rom")
            rows.append((t0 + 0.6, "sms", f"{ph}{k:04d}", T[alt][need].format(place=place, n=n), zc[pi], lab)); k += 1
        if s == 0:
            rows.append((t0 + 1.4, "field_app", "ndrf", f"Field team at {place}: confirmed {n} people need {need}. {FLAVOUR[dis]}.", zc[pi], lab))
    rows.append((2.4, "social_feed", "@viral_news_fwd", RUMOUR[dis].format(place=zn[0]), zc[0],
                 {"key": "R", "real": False, "need": "rescue", "people": None, "zone": zc[0]}))
    if diff != "beginner":
        rows.append((3.1, "sms", f"{ph}9001", "Please help, many people stuck here, nobody has come yet", None,
                     {"key": None, "real": True, "need": "rescue", "people": None, "zone": None}))
    if diff == "advanced":
        rows.append((6.5, "sms", f"{ph}9002", f"Cannot reach my parents in {zn[3]} since morning, phones switched off", None,
                     {"key": "M", "real": True, "need": "missing_contact", "people": None, "zone": zc[3]}))
        rows.append((7.0, "sms", f"{ph}9003", T["hi"]["rescue"].format(place=zn[1], n=PEOPLE[0]), zc[1],
                     {"key": "S1", "real": True, "need": "rescue", "people": PEOPLE[0], "zone": zc[1]}))
    roads = spec["roads"]
    r_main = roads[0][0]           # hub -> place 1
    r_alt = roads[3][0]            # place 1 -> place 2
    events = [(4.0, "close_road", {"road": r_main, "why": "citizen SMS: road blocked", "source_type": "citizen", "verified": False},
               f"Stage 2 disruption: a citizen reports {roads[0][1]} blocked (unverified)")]
    stages = [{"name": "Onset", "from_t": 0.0, "to_t": 4.0, "summary": f"{FLAVOUR[dis]} around {zn[1]}; first reports and sensor signals"},
              {"name": "Disruption", "from_t": 4.0, "to_t": 7.0, "summary": f"{roads[0][1]} cut; plans must reroute"}]
    if diff != "beginner":
        events.append((5.5, "flood_shelter", {"shelter_name": spec["shelters"][1][0]}, f"Stage 2: {spec['shelters'][1][0]} becomes inaccessible"))
        stages[1]["summary"] += f"; {spec['shelters'][1][0]} cut off"
    if diff == "advanced":
        events.append((6.0, "silence_village", {"zone": zc[3], "with_hazard": False}, f"Stage 3: {zn[3]} goes silent (towers down)"))
        events.append((7.5, "drop_inventory", {"depot_name": spec["depots"][0][0], "fraction": 0.4}, "Stage 3: 40% of depot stock found damaged"))
        events.append((8.5, "close_road", {"road": r_alt, "why": "field team: road washed out", "source_type": "field_team"},
                       f"Stage 3: field team confirms {roads[3][1]} cut"))
        stages.append({"name": "Escalation", "from_t": 6.0, "to_t": 10.0, "summary": f"{zn[3]} silent, depot stock lost, second road cut"})
    else:
        stages.append({"name": "Recovery", "from_t": 7.0, "to_t": 10.0, "summary": "Deliveries complete and confirmations arrive"})
    return rows, events, stages


def _build():
    worlds_, scen, scripts = {}, {}, {}
    for idx, loc in enumerate(LOCATIONS):
        sid, st, tags, dis, diff, lang, places = loc
        spec = _spec(loc, idx)
        rows, events, stages = _script(loc, idx, spec)
        from app.disasters import profile
        zn = [z[1] for z in spec["zones"]]
        worlds_[spec["id"]] = spec
        scripts[sid] = rows
        sits = sorted({(r[5]["key"], r[5]["need"], r[5]["zone"]) for r in rows if r[5]["key"] and r[5]["key"].startswith("S")})
        scen[sid] = {
            "name": f"{places[0][0].split(' (')[0]} — {profile(dis)['name'].lower()} ({st})", "hazard": dis, "disaster": dis, "colour": profile(dis)["overlay"]["colour"],
            "world": spec["id"], "difficulty": diff, "region": tags, "state": st, "language": lang, "lab": True,
            "description": f"{FLAVOUR[dis]} in {', '.join(zn[1:])} ({st}). {len(rows)} multilingual messages, {len(events)} disruption event(s).",
            "objectives": [f"Get {need} to {next(z[1] for z in spec['zones'] if z[0] == zc)}" for _, need, zc in sits]
                          + ["Do not act on the forwarded rumour", f"Reroute around the {spec['roads'][0][1]} closure"]
                          + ([f"Notice that {zn[3]} has gone silent"] if diff == "advanced" else []),
            "expected": ["Each real situation becomes one incident (duplicates merged across languages)", "Rumour marked disputed or false and never planned",
                         "A new plan after each disruption, with previous vs updated routes", "No dispatch without approval and route verification"]
                        + (["Recon proposed for the silent village"] if diff == "advanced" else []),
            "stages": stages, "events": events, "signals": _signals(dis, [z[0] for z in spec["zones"]], spec),
            "reports": [(t, ch, who, text, {"origin_zone": oz}, None) for t, ch, who, text, oz, _ in rows], "zones": None,
        }
    return worlds_, scen, scripts


WORLDS, SCENARIOS, _SCRIPTS = _build()


def world(world_id: str) -> dict:
    return WORLDS[world_id]


def script(sid: str) -> list:
    """Scenario design (labelled). For the final report and the evaluation script only — never passed to agents."""
    return _SCRIPTS.get(sid, [])


def coverage() -> dict:
    from collections import Counter
    sc = SCENARIOS.values()
    return {"scenarios": len(SCENARIOS), "states_and_uts": sorted({s["state"] for s in sc} | {"Karnataka"}), "by_disaster": dict(Counter(s["disaster"] for s in sc)),
            "by_difficulty": dict(Counter(s["difficulty"] for s in sc)), "by_region": dict(Counter(t for s in sc for t in s["region"]))}

