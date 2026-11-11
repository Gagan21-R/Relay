# RELAY build progress

Read this file and the master prompt first after any context reset, then continue from "Next step".

## Environment notes (this machine)
- Docker and PostgreSQL are NOT installed. `docker-compose.yml` (postgis/postgis:16-3.4 + backend + frontend) is written
  but cannot be run here. Locally the backend uses SQLite through the same SQLAlchemy models (`DATABASE_URL`).
  Decision: keep all SQL portable (JSON columns, lat/lng + haversine, no PostGIS functions).
- Ports 8000 and 5173 are unusable on this machine; the project uses **8010 (API)** and **5180 (dashboard)** everywhere.
- Backend venv: `C:/Users/Gagan R/.venvs/relay2` (Python 3.12). `make` is not installed; run Makefile commands by hand.

## Phase 1 — Scaffold (done)
- Built: FastAPI app (`/api/health` checks DB, `/api/languages`, `/ws/live`), settings + mock mode, LLM/embedding
  provider interface (Gemini or mock/local n-gram), SMS provider interface (mock, Twilio), phone hashing/masking,
  languages.json (8 languages), LangGraph skeleton, Alembic, React+Vite+TS+Tailwind (purple), react-i18next EN/KN/HI,
  OSM map of Kodagu, Docker Compose, `.env.example`, Makefile.
- Checks: health OK with no keys; /docs loads; frontend loads; 9 pytest + 3 vitest pass. `docker compose up`: not
  verifiable here (no Docker).

## Phase 2 — Data model + seed (done)
- Tables (`app/models/tables.py`): sources, zones (population, tower/power, internet_down, blackout fields), gazetteer
  (multi-script aliases), roads, depots, shelters, inventory (depot or shelter; quantity/in_transit/consumed,
  last_updated_at), incidents, reports, plans, dispatches, approvals, alerts, signals, recon_tasks, sms_messages,
  audit_log, sim_state. Alembic migration `cc50a87e03ed_initial_schema`.
- Scenario: Kodagu, Karnataka (real coordinates, synthetic data): 10 zones, 13 roads, 3 depots (one NGO store with
  stale counts), 6 shelters, 17 named sources, 15 timeline signals (rain, CWC river, Harangi dam bulletin, 3 flood
  extent versions, Hattihole tower/power outage), 82 reports (kn/hi/ml/ta native, Kanglish/Hinglish/Manglish, English)
  with truth labels for evaluation. Hattihole (pop 2400) never reports; two relatives report missing contact.
- Decision: time is simulated hours since event start (`T+h`, stored as floats). The scenario engine
  (`app/sim/engine.py`) replays the timeline through the channels; seeding = replay to T+12 h. Translation memory:
  reference English for seed texts is loaded as a store of verified translations (labelled as such in the UI).
- Auto-seed on startup when empty; `python -m app.sim.seed --reset` resets. CRUD: /api/state, zones, roads,
  gazetteer, depots, shelters (PATCH), inventory (PATCH), sources (masked), reports, incidents, signals, alerts (ack), audit.
- Checks: migration upgrade + `alembic check` clean; counts printed; 17 tests pass.

## Phase 3 — Intake agent + channels (done)
- `app/agents/intake.py`: language+script detection (`i18n/detect.py`: Unicode blocks, Devanagari hi/mr split,
  romanized cue words for kn/hi/ml/ta/te/mr/bn, mixed-script), translation for display only (`i18n/translate.py`:
  translation memory → Gemini → glossary with coverage confidence), extraction on the ORIGINAL text (Gemini JSON
  schema validated by Pydantic `ExtractedReport`; fallback `rule_extract` with per-language lexicons in
  `i18n/lexicon.py`), people counts (digits in any script, number words, families×3.7, vehicles), vulnerable groups,
  life-safety, missing-contact, rumour signals (forward-chain phrases per language, sensational claims, old EXIF),
  geocoding (`services/geocode.py`: gazetteer exact/fuzzy in all scripts → Nominatim outside mock mode).
- Channels: SMS webhook (Twilio/Exotel/MSG91 field names + JSON), auto-reply with Ref in the sender's language,
  one clarification question (location first, else need) and reply merge into the same report, structured
  `HELP <need> <people> <landmark>`; voice IVR TwiML (language menu → record → transcribe → pipeline) + simulator
  endpoint; field app sync (idempotent client_id); radio console (satphone, police wireless, forest/railway, HAM);
  7 mock feed adapters behind `SourceAdapter`; outgoing templates in 8 languages (`i18n/templates.py`).
- LangGraph graph is real now (intake → trust → triage → resource → monitor → coordination, network-block exit).
- Decision: phone numbers are kept only in memory for replies (hash+mask in DB); real providers reply by conversation.
- Probe: rule extraction matches zone/need/people on all 82 seed reports (seed texts; held-out eval in Phase 11).
- Checks: 35 tests pass (kn/hi/ml/en native, romanized and code-mixed; clarification SMS; voice; radio; field; feeds).

## Phase 4 — Live feed, Phone Simulator, Network toggle (done)
- Backend: `POST /api/sim/network` (per-zone internet DOWN; blocked reports are stored with status `blocked` = "did
  not get out" so the demo can show what was lost), `GET /api/sim/samples` (13 quick messages, all 8 languages +
  structured + rumour + YES), live `report`/`sms`/`network` WebSocket events from the pipeline.
- Frontend: Live Report Feed (channel icon, language badge, original + EN with method/confidence, filters, blocked
  counter), Phone Simulator (mock phone thread, sample buttons, phone personas, voice call via MediaRecorder + browser
  speech recognition or typed transcript, network grid, "arriving now" stream), `/field` offline-queue app
  (localStorage, GPS or zone pick, idempotent sync, simulate-no-signal), Radio Console.
- Checks (browser): Kannada SMS on the dashboard in 171 ms with translation and a Kannada auto-reply; with
  Kushalnagar DOWN a web report is blocked while SMS/radio arrive. 38 pytest + 3 vitest pass.

## Phase 5 — Trust & Evidence agent (done)
- `app/agents/trust.py`: clustering = similarity ≥ threshold AND distance ≤ 2.5 km AND Δt ≤ 8 h AND compatible needs
  (shared core need, or both spreading claims). Mock-mode embeddings run on a language-neutral form (EN translation +
  place + needs); with Gemini, multilingual embeddings on raw text. Forwards/copies (raw-text similarity ≥ 0.85, or
  forward-chain phrases) count as one source. Corrections ("dam is safe", "bus stand is dry", "camp is open") attach
  to the claim they correct. Resolution updates ("all 12 safe") look back 24 h.
- Confidence: 7 weighted components + penalties (contradiction, forward chain, sensational claim, old EXIF), stored in
  `confidence_breakdown` with a `why` per component; levels verified/likely/unverified/disputed/false; Fast Verify for
  life-safety + unverified/disputed; human confirm/refute updates each source's reliability (Beta-style prior by tier).
- All thresholds/weights in `app/services/scoring.py`. Seed probe: pairwise precision 0.95, recall 1.00; three rumours
  auto-score false; dialysis + labour reports sit in Fast Verify.
- API: `/api/incidents/{id}` evidence trail, `/api/fast-verify`, `/api/incidents/{id}/verify`, `/api/trust/compare`
  (same-report analyser, savepoint-rolled-back, nothing stored).
- Checks: 46 tests pass.

## User request (mid-build): maximalist, motion-driven UI
- "bold creative agency portfolio landing page with maximalism elements, motion-driven animations, case study
  previews, team showcase, and contact form" → applied as RELAY's whole design system; the agency sections become a
  RELAY landing at `/about` (hero, case studies = demo stories, team = agents/modules/people, contact form = files a
  real web report). Command Map stays home.
- Done: maximalist design system (`tailwind.config.js` tokens: paper/ink/brand purple + pink/lime/tangerine/cobalt/
  sun/mint, hard offset shadows, patterns, Bricolage Grotesque + Instrument Serif + Noto Indic fonts), framer-motion
  primitives (`components/motion.tsx`: Reveal, Stagger, Marquee, Blob, CountUp, Tilt, Rotator; reduced-motion
  respected via MotionConfig), new shell (live marquee ticker from `/api/summary`, colour-chip nav, page transitions),
  restyled UI kit (`Breakdown` component for every score), `/about` landing (hero, live numbers, 5 case studies,
  team = 5 agents + 4 modules + people, research grounding, contact form → real web report).

## Phase 6 — Triage + Resource agents (done)
- Triage (`agents/triage.py`): priority /100 = life threat 30 + people 20 (log) + vulnerable 15 + waiting 10 +
  confidence 15 (unverified life-safety keeps 0.6) + access difficulty 10 (roads closed, flood extent, towers);
  false/resolved = 0. Breakdown with `why` per component.
- Resource (`agents/resource.py`): demand = verified/likely incidents (and unverified life-safety) × per-need kit
  rules + shelter 48 h top-up; supply = depot stock reachable over open roads (`services/routing.py` Dijkstra),
  stale stock (>12 h uncounted) excluded and alerted per depot; projected shortages by burn rate at Sphere
  standards (15 L/person/day); transfer proposals from the nearest reachable fresh depot, else escalation.
  Shelters consume stock as simulated time passes (`engine._pass_time`). Alerts de-duplicated by key and
  auto-resolved (`services/alerts.py`). `/api/resources/overview` with 48 h projection series.
- Seed result: "Water litres at Napoklu Govt High School camp runs out in ~18 h" + transfer from Madikeri depot
  (13.9 km); boats shortage; NGO store stale. 52 tests pass.
- UI: Incidents (ranked list, priority + confidence `Breakdown`, evidence trail with cluster tests, confirm/refute,
  same-report analyser), Fast Verify (callback numbers masked, in reporter's language), Resources (Recharts 48 h
  burn-rate lines, demand vs supply bars, transfers, depot stock with stale recount), Shelters (occupancy, access,
  burn, check-in endpoint `POST /api/shelters/{id}/checkin`).

## Phase 7 — Coordination + approvals + delivery loop (done)
- `agents/coordination.py`: greedy plan (shelter forecast shortages first, then incidents by priority; nearest
  reachable depot with fresh stock + free vehicle/crew; in-plan reservations; unverified life-safety gets a
  "verify on arrival" kit); rationale + per-line reason + evidence (report refs / forecast); unmet needs listed.
  approve (dispatches, depot stock → in transit, crews/vehicles taken, incidents in_progress), edit (new version),
  reject; tracking: dispatched → in_transit → delivered at ETA (route re-checked: a closed road fails the dispatch),
  confirmation SMS in the recipient's language, YES/NO in 8 languages, field confirm, shelter check-in confirm;
  overdue and unconfirmed (2 h) alerts; confirm moves stock to shelter / consumed and returns crews.
- `agents/monitor.py` (Phase 7 triggers): shortages, new high-priority incidents, failed deliveries; each trigger once.
- API `/api/plans` (+ approve/reject/edit), `/api/dispatches` (PATCH, confirm, tick). UI: Plans & Approvals (rationale,
  editable quantities/remove, route map, decision panel, version history), Dispatch kanban + live route map.
- Checks: nothing dispatched before approval; approval creates dispatches and decrements stock; Kannada "ಹೌದು"
  confirms a shelter delivery; audit has every step. 57 tests pass; browser approve → 11 dispatches.

## Phase 8 — Replanning, Blackout Detection, Rumour Control (done)
- `agents/blackout.py` (graph node between resource and monitor): per-zone risk = hazard 0.30 + population 0.15 +
  silence 0.20 (≥6 h vs normal rate) + infrastructure 0.15 + missing-contact 0.10 + vulnerability 0.10, threshold
  0.6; alert + recon task (method by road access: sat-phone field team / helicopter / drone; one-day needs for 60% of
  population at standards; pre-positioned supplies within carry limits) → approval → report from inside completes
  it, resolves the alert, zone back to normal. Shelter triggers: inaccessible (all access roads closed), full,
  unconfirmed (missed check-ins > 8 h; timeline check-ins added, Somwarpet misses its late ones).
- `agents/rumour.py`: correction for false incidents, kind auto-detected (dam burst / old photo / camp closed /
  generic), 8 languages with the place name in each script, SMS to reporters in the area in their language,
  public `/public` corrections page.
- API `/api/signals/{type}` (rainfall, river, dam, quake, flood_extent, tower_outage, power_outage, census),
  `/api/zones/blackout`, `/api/recon` (+approve/reject/report/image — drone check experimental, Gemini vision with a
  key), `/api/alerts/rumour`, `/api/public/corrections`. UI: Blackout & Recon, Alerts (+ rumour control), Public page.
- Checks: flooding Siddapura camp's access roads → inaccessible + new plan pending approval; Hattihole top-ranked with
  recon + supply estimate; recon report resolves it into incidents; correction in ≥3 languages. 62 tests pass.

## Phase 9 — Complete dashboard + i18n + Explain-me assistant (done)
- Explain-me (user extra): `services/assistant.py` registry of 38 sections (every page + key panels: what it is / how
  to read it / what you can do) + live facts from the current state; `/api/assistant` (Gemini writes the answer in the
  UI language when a key is set; rule-based in mock mode; follow-up questions routed to the best section).
  Frontend: `Explain` button on every page header and panel (`section` prop on PageHeader/Panel), slide-in drawer with
  follow-ups, floating "Ask RELAY" button.
- Command Map rebuilt as a real-time map: incidents (priority colour, confidence outline, false = grey), shelters by
  status, depots, dispatch routes with trucks positioned by sim-clock progress, breathing flood extent, hatched red
  blackout zones (SVG pattern), road status, report pulses from WebSocket, layer toggles (persisted), click → side
  panel (incident evidence / zone risk / shelter / depot), live counters.
- Audit Log page (actor type, action, text filters, inputs/outputs). i18n: nav, page headers, status and assistant UI in
  EN/KN/HI (deep panel copy stays English — noted as a limitation).
- Checks: every page renders with seed data; Kannada switch works; no console errors after startup; 64 tests pass.
