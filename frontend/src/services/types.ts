// Shapes returned by the RELAY API (only the fields the UI reads).
export type Report = {
  id: number; ref: string; channel: string; adapter?: string; raw_text: string; original_language?: string; language_confidence: number;
  script?: string; translated_text_en?: string; translation_method?: string; translation_confidence: number; received_at: number;
  location_text?: string; lat?: number; lng?: number; zone_id?: number; geocode_confidence: number; geocode_method?: string;
  need_types: string[]; people_count?: number; vulnerable_groups: string[]; urgency_hint?: string; life_safety: boolean;
  rumour_signals: { signal: string; phrases?: string[]; detail?: string }[]; missing_contact: boolean; extraction_method?: string;
  extraction?: any; needs_clarification: string[]; incident_id?: number; cluster_evidence?: any; status: string; audio_url?: string;
  media_urls: string[]; media_meta?: any;
  source?: { type: string; name: string; phone_masked?: string; reliability: number } | null;
};

export type Incident = {
  id: number; title: string; category: string; need_types: string[]; lat?: number; lng?: number; area_name?: string; zone_id?: number;
  confidence_level: string; confidence_score: number; confidence_breakdown: any; priority_score: number; priority_breakdown: any;
  people_affected: number; vulnerable_groups: string[]; life_safety: boolean; fast_verify: boolean; verification_note?: string;
  official_status?: string; status: string; first_report_at: number; last_report_at: number;
};

export type Zone = {
  id: number; code: string; name: string; lat: number; lng: number; polygon: number[][]; population: number; tower_status: string;
  power_status: string; internet_down: boolean; last_report_at?: number; blackout_flag: boolean; blackout_score: number;
  blackout_breakdown: any; vulnerability: any; normal_reports_per_hour: number;
};

export type SmsMsg = { id: number; direction: "in" | "out"; body: string; kind: string; language?: string; t: number };

export type SimState = { clock: number; scenario: any; flood_extent: number[][][]; flood_version?: number; network_down: string[] };
