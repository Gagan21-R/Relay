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
