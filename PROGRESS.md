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

## Phase 10 — Digital twin, scenario engine, Run Demo, 3D (done)
- `sim/scenarios.py`: 3 scenarios (Kodagu monsoon flood; Harangi dam release; Madikeri hill landslides) with their own
  signal timelines, hazard polygons and report subsets. `sim/engine.py`: fresh reset, background clock (`clock_loop`,
  speed = sim hours per real second), timeline info, what-if events (close/reopen road, flood shelter, drop inventory,
  cut/restore internet, spike reports, silence village).
- `sim/demo.py` + `/api/sim/demo/step/{n}`: all 12 deck steps on the live system; 7 (plan) and 12 (recon) wait for a
  person. Frontend `DemoOverlay` (global, navigates to each step's page, approve buttons), Scenario Control page,
  `/twin3d` three.js twin rebuilt from live state (terrain seeded per scenario, water/debris from hazard polygons,
  villages by population, silent zones dark + red beacon, shelters by status, depots, pins, moving trucks).
- Checks: Run Demo completes all 12 steps from a fresh start and re-runs (pytest, twice); in the browser all 12 ran
  with UI approvals. Fix: demo captions use CSS animation (framer exit animations stall when frames are paused).
  66 backend tests pass.

## Phase 11 — Evaluation + Metrics page (done)
- `eval/heldout.py`: 29 held-out labelled reports written after tuning (adds te, mr, bn; new phrasings; 2 rumours with
  refutations; a Bengali single life-safety report). `eval/run_eval.py` (`make eval`): fresh temp DB, mock mode;
  development (seed) and held-out sets scored separately; duplicates P/R/F1 overall + per language; extraction
  accuracy (zone/need/people) + translation coverage per language; fake/true confusion (incident level); plan time
  + feasibility; shortage detection on 6 injected shortages; evidence traceability; delivery verification.
- Results (synthetic): held-out duplicates P 1.00 R 0.95; extraction zone 0.85 need 0.95 people 0.80; fake/true 2/2,
  0 false alarms; plan 0.27 s feasible; traceability 100%; shortages 6/6; deliveries verified 8/13 (rest lack a
  recipient phone). Development set is near-perfect because the rules were built on it — labelled as such.
- `/api/metrics` (+ `/run` in a subprocess), Metrics page (per-language Recharts, confusion matrix, disclaimer).
  Placeholder pages removed: every route is real. 67 pytest + 5 vitest pass.

## Phase 12 — Polish + final delivery (done)
- README (overview, mermaid architecture, agent table, setup, mock vs real, demo, evaluation table, research grounding,
  privacy + retention, limitations), DEMO.md rehearsal checklist, code-split heavy pages (main bundle 1.6 MB → 245 kB,
  no build warnings), warnings cleaned (one third-party LangGraph import notice remains and is documented).
- Final delivery checks (this machine, SQLite fallback; Docker not available here): clean database → auto-seed (82
  reports, 19 incidents) → full 12-step Run Demo via API completes → reset to T+12. 67 pytest + 5 vitest pass,
  typecheck clean, `npm run build` clean, `make eval` results in backend/eval/results.json.

---

# Enhancement round — "Final Implementation & Enhancement Prompt" (done)

Continued the existing build; nothing working was removed. Order followed: inspect → multi-disaster → multilingual →
routes → memory/volunteers → lifecycle/permissions/replanning → Scenario Lab → evaluation/safety → frontend → offline
check → docs.

- **Multi-disaster**: `app/disasters.py` (9 profiles: indicators, life-threat weights, per-person standards, overlay,
  fleet, recommendations); `state.disaster/standards` used by triage, resource, blackout; selector API + header;
  per-report disaster type; GDACS service with live/stale/fallback labels (fallback in mock mode).
- **Multilingual**: 19 languages with support levels (full 8 · basic 7 · pending 4) and template status; detection for
  Odia, Gujarati, Gurmukhi, Meitei Mayek, Devanagari hi/mr/ne markers, Assamese vs Bengali, Mizo and Khasi cues;
  lexicon and glossary additions; review flags on reports; the brief's three Kannada examples tested end to end.
  Outgoing: `public_templates.py` (3 templates × 13 languages), `services/comms.py` (fact check, English fallback,
  approval before mock send), Public messages page.
- **Routes**: `services/routing.py` rewritten — vehicle suitability, road kind/surface, verified + fresh status,
  caution-first road reports (`RoadReport`), safest-not-shortest with penalties, alternatives, safety label, ETA
  reliability; officer verification of road reports; dispatch requires a verified route.
- **Memory / volunteers**: `Volunteer`, `Precedent`, `Hospital`, `RoadReport`, `Communication` tables;
  `services/volunteers.py` (deterministic ranking, tie by ID, reliability (on_time+1)/(assigned+2));
  `services/precedents.py` (factual counts only).
- **Lifecycle / permissions**: coordination rewritten — created → approved → assigned → dispatched → delivered →
  confirmed (+failed/cancelled); `Forbidden` → 403, `InvalidTransition` → 409; roles from X-Role/X-Actor (no login);
  SMS YES and check-ins are evidence only; volunteer reliability updated on confirmation. Plans carry `changes`
  (previous vs updated, reasons, approval needed); stale routes and stale pending plans trigger replans.
- **Worlds and Scenario Lab**: world specs (`sim/worlds.py`), generic `load_world`; `sim/lab.py` generates 47 scenarios
  (all 36 states/UTs, 9 disasters, 3 levels, multi-stage events) + 3 Kodagu = 50; Lab API (launch, reset, status,
  final report) and page; map and 3D twin re-centre per scenario.
- **Ground truth isolated**: Kodagu labels moved to `eval/ground_truth.py`; scenario messages carry only origin zone;
  test fails if `app/` imports `eval`. LLM extraction schema `extra="forbid"`; prompt-injection tests with a fake LLM.
- **Evaluation** (`eval/extended.py`, `eval/multilingual_probe.py`): probe set per language and input type,
  verified-only vs all-reports allocation, route rules under 13 simulated closures, all 50 scenarios replayed. Measured
  results are in README; duplicate precision reported as measured (0.95 dev / 1.00 held-out), not as 0.70.
- **Bug found by the evaluation**: a sensational forwarded rumour merged into a real incident (Anantapur). Fixed in
  `trust.needs_compatible`; re-run shows 0 rumour-led incidents planned, 0 mixed incidents across 50 scenarios.
- **Bug found in the browser**: a plan pending approval kept a route through a road closed after it was proposed.
  Monitor now replaces such plans (`stale_plan` trigger).
- **Frontend**: Tasks board, Plans comparison panel, Scenario Lab, Public messages, Metrics sections, map tabs
  (priorities / arriving / disaster / volunteers / agents), hospitals and GDACS layers, disaster-styled overlays,
  role switcher, disaster selector, Explain-me sections for every new panel.
- **Migration** `e2a1` (new tables/columns, server defaults, status rename) — upgrade/downgrade checked on SQLite only.
- Checks: 98 pytest + 5 vitest pass; typecheck and `npm run build` clean; in the browser: Lab launch (Sundarbans) →
  map re-centred → replan with reason → approve → 409 on unverified dispatch → verify → assigned volunteer dispatches
  → public message drafted in en/hi/bn with facts preserved → Metrics shows the new sections.
- **Not tested**: Docker Compose, PostgreSQL, Gemini, Twilio, live GDACS, Nominatim (stated in README).

---

# Round 3 — agents talk, guided run, workflow, run anywhere (done)

User asked: (1) agents must communicate, (2) remove the 3D twin and radio, (3) the disaster dropdown and map clicks
must run the full model for that disaster/place, (4) a guided sequence that takes the user to each page as work
happens, (5) a flowchart of the complete workflow.

- **Agent bus** (`agents/bus.py`, `agent_messages`): inform/request/propose/accept/decline/escalate/reply, synchronous
  `ask()` so conversations are deterministic. Conversations that change outcomes: Coordination ⇄ Resource shortfall
  negotiation (second-source lines or escalation), Coordination ⇄ Trust credibility checks, Trust ⇄ Coordination ground
  checks, Blackout ⇄ Resource recon supplies, Monitor → Coordination → Duty Officer replans; plus Intake → Trust →
  Triage → Monitor hand-offs. API `/api/agents/messages`, `/api/agents/summary`; Agent conversations page (network + threads).
- **Removed** the 3D twin (and the `three` dependency) and the radio console (page, API, adapter, tests). The recon
  team's satellite-phone report remains on the Blackout page (channel renamed `satphone`).
- **Run anywhere**: disaster menu opens that disaster's scenarios across India; map has India-wide pins and an
  "All of India" button; either starts a guided run. Bug found: the dropdown only changed the profile.
- **Guided run** (`sim/guide.py`, `/api/lab/guide/*`, overlay): 14 steps for any scenario; auto-advances; waits for the
  Duty Officer (403 for others); handles repeated disruptions in step 13.
- **Workflow page** (`/workflow`): 17 steps / 5 phases with agents, messages, human gates and the loop; lights up live.
- **Bugs found in the browser and fixed**: guide start lost under React's dev double-mount; a map pin without
  coordinates crashed the map; boats could not use flooded roads (Puducherry plan had 0 deliveries) — boats now float on
  flooded roads and are trailered on open ones; non-water footprints now close roads as "blocked", not "flooded";
  approving a plan cancelled its own negotiated second-source line.
- Checks: 104 pytest (6 new) + 5 vitest; build clean; in the browser: Cyclone → Puducherry → guided run to the plan
  approval; Workflow and Agent conversations pages render live.

---

# Round 4 — UI redesign: brutalist · minimal · surreal (done)

- New design tokens (bone / ink / signal vermilion, square corners, hard shadows, Syne + Space Grotesk + JetBrains Mono +
  Instrument Serif); the old colour names kept as roles so every page restyled at once; inline map/chart colours swapped.
- Surreal + motion primitives: Moon, orb, Eye (follows the pointer, blinks), Door, Ladder, Cloud, Drip, SplitText,
  Magnetic, Parallax; black page wipe between routes.
- App shell: numbered brutalist index navigation, black ticker, square controls; page headers with a dusk panel and one
  surreal object each; Panel, Stat, Empty, Breakdown, badges, Explain and Ask RELAY restyled.
- Landing page rebuilt as a creative-agency portfolio: surreal hero scene, manifesto, live index, case-study rows with
  hover previews, capabilities, team showcase with surreal portraits, process, research, contact form (still files a
  real report — checked: R-1007 detected Kannada), giant footer wordmark.
- Checked in the browser at phone-pane and 1440 px widths; fixed mid-word headline breaks, an 18 px horizontal
  overflow, and clipped contact/footer type. Build clean; 5 vitest pass; backend untouched.

---

# Round 5 — calmer brutalist · minimal UI (done)

User asked: fewer animations, remove the eyeball, make the sidebar RELAY big and bold (it was covered), green approve
and red reject buttons everywhere, no animations when a page/section opens, natural map colours, and no surrealism.
- Removed every surreal element (moon, orb, eye, door, ladder, clouds, drips, dusk gradients) and the page wipe;
  motion helpers are now plain wrappers; all `initial`/`whileHover`/`whileInView` entrance animations stripped from pages.
- Sidebar logo: "RELAY." in bold 54 px Space Grotesk, fully visible (checked: text width = box width).
- `.btn-approve` (green #15803D) and `.btn-reject` (red #DC2626) applied to every approve / confirm / send and reject /
  refute / fail button (plans, tasks, fast verify, incidents, public messages, blackout recon, guided run).
- Map tiles back to natural OpenStreetMap colours (greyscale filter removed).
- Page headers: grid + big type + a solid black index block with the page number; landing hero: black live-index block.
- Checked in the browser (landing, map, plans); build clean; 5 vitest pass.

---

# Round 6 — full brutalism, no yellow (done)

- Design tokens v5: cream / black / white, flat red #FF2D00, blue #1F3BFF, green #00A33A; 3 px borders everywhere
  (borderWidth override), 6–12 px offset shadows, Archivo Black uppercase headings, monospace labels.
- No yellow: the "sun" role, P3 priority, map/chart inline colours and the drought overlay (#C9A227 → tan #B5835A) changed.
- Shell: red RELAY block; colour-blocked nav groups; black panel title bars; colour-blocked stat tiles; page headers with
  a giant number block in the section colour; landing page re-coloured in blocks.
- Video recording was cancelled by the user before it started (nothing recorded).
