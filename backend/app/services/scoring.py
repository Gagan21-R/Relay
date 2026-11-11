"""All scoring weights and thresholds in one place (configurable, documented, never tuned silently).
Every score RELAY shows is a weighted sum of named components; the components and weights are stored with it."""

# ---- duplicate clustering (Trust & Evidence) ----
CLUSTER = {
    "similarity_threshold": 0.60,        # cosine of embeddings of (English translation + place + needs); true pairs >= 0.73 on the seed
    "similarity_threshold_gemini": 0.72,  # Gemini multilingual embeddings are on a different scale
    "max_distance_m": 2500,
    "time_window_h": 8.0,
    "forward_similarity": 0.85,          # near-identical RAW text = a forward/copy: same source chain
    "no_location_similarity": 0.85,      # without a location, only very similar text may join
}

# ---- confidence (weights of positive components sum to 1.0) ----
CONFIDENCE_WEIGHTS = {
    "corroboration": 0.25,     # distinct independent sources
    "reliability": 0.20,       # best source tier / track record
    "sensor_consistency": 0.15,  # flood extent, river gauge, rainfall agree with the place
    "official_or_field": 0.15,   # a field team / official / sensor supports it
    "plausibility": 0.10,      # place exists, time after event start, place matches the zone
    "specificity": 0.10,       # people count, landmark, concrete need
    "media": 0.05,             # EXIF date and GPS
}
PENALTIES = {"contradiction": 0.35, "contradiction_max": 0.6, "forward_chain": 0.15, "sensational_claim": 0.10, "old_media": 0.20}
LEVELS = [(0.75, "verified"), (0.55, "likely"), (0.0, "unverified")]
CREDIBLE_CONTRADICTOR = 0.7     # a refuting report counts as a contradiction when its source is at least this reliable
RELIABILITY_PRIOR_WEIGHT = 5    # reliability = (prior*k + confirmed) / (k + confirmed + refuted)

# ---- triage priority (points out of 100) ----
PRIORITY_WEIGHTS = {"life_threat": 30, "people": 20, "vulnerable": 15, "waiting_time": 10, "confidence": 15, "access_difficulty": 10}
LIFE_THREAT_BY_CATEGORY = {"rescue": 1.0, "medical": 0.9, "water": 0.55, "food": 0.45, "shelter": 0.4, "infrastructure": 0.3, "other": 0.1}

# ---- blackout risk (0..1) ----
BLACKOUT_WEIGHTS = {"hazard": 0.30, "population": 0.15, "silence": 0.20, "infrastructure": 0.15, "missing_contact": 0.10, "vulnerability": 0.10}
BLACKOUT_THRESHOLD = 0.6

# ---- resources ----
SHORTAGE_HORIZON_H = 24.0       # projected shortage when stock runs out within this many hours
STALE_STOCK_H = 12.0            # stock not counted for this long is flagged stale
OVERDUE_GRACE_H = 1.0
CONFIRMATION_TIMEOUT_H = 2.0
SHELTER_CHECKIN_STALE_H = 6.0
