# RELAY — Resilient Emergency Logistics & Adaptive Yield

AgentX Hackathon 2026 (Hack4Hack) · PS-03 Multi-Agent Disaster Response Coordinator · Agentic AI track

RELAY turns fragmented, duplicate, unverified and multilingual emergency reports, arriving over the internet and over
SMS and voice calls, into evidence-backed, human-approved relief plans. It tracks every delivery until it is confirmed
and replans when conditions change.

**Core loop:** reports arrive (any channel, any language) → duplicates grouped → evidence verified and scored → needs
triaged → shortages detected → allocation plan recommended → a person approves → dispatch tracked → delivery
confirmed → replanning when something changes.

> Status: **Phase 1 (scaffold)**. See "Build phases" below for what is done and what is next.

## Run it

### One command (Docker)

```bash
cp .env.example .env
docker compose up --build
```

Dashboard: http://localhost:5180 · API docs: http://localhost:8010/docs

### Without Docker (local development)

The backend falls back to a local SQLite file when `DATABASE_URL` is not PostgreSQL, using the same SQLAlchemy models.

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8010

cd ../frontend
npm install
npm run dev                                          # http://localhost:5180, proxies /api and /ws to :8010
```

Tests: `make test` (pytest + Vitest). No API keys are needed: with `RELAY_MOCK_MODE=true` (or no `GEMINI_API_KEY`)
the LLM, embeddings and SMS/voice providers are mocked.

## Stack

React (Vite) + TypeScript + Tailwind · Leaflet + OpenStreetMap · Recharts · react-i18next (EN, ಕನ್ನಡ, हिंदी) ·
FastAPI · LangGraph · Google Gemini (optional) · PostgreSQL + PostGIS (SQLite fallback) · SQLAlchemy 2 + Alembic ·
WebSockets · Twilio-compatible SMS/voice webhooks + built-in simulator · Docker Compose · pytest + Vitest.

## Repository

```
relay/
  docker-compose.yml  .env.example  Makefile  README.md
  backend/
    app/
      main.py         FastAPI app + /ws/live
      api/            routers (system: health, languages)
      agents/         intake, trust, triage, resource, coordination, monitor, blackout (phases 3-8)
      graph/          LangGraph state graph (pipeline.py: one node per agent)
      i18n/           languages.json (adding a language is config), detection, gazetteer, rumour phrases
      channels/       sms.py (provider interface: mock, Twilio; Exotel/MSG91 next), voice, web, field, feeds
      models/         SQLAlchemy + pydantic schemas (phase 2)
      services/       llm.py (Gemini or mock, embeddings with local fallback), geocoding, scoring, allocation
      sim/            scenario engine, seed data, demo script (phases 2 and 10)
      ws/             WebSocket hub
      core/           settings, privacy (phone hashing and masking)
    migrations/       Alembic
    tests/  eval/
  frontend/
    src/  pages/  components/  i18n/  hooks/  services/
```

## Scenario area

Kodagu (Coorg) district, Karnataka, a real flood- and landslide-prone district (2018 and 2019 floods). The real
place only locates a **synthetic** scenario: every report, person, shelter stock and incident is invented and labelled so.

## Build phases

| # | Phase | Status |
|---|---|---|
| 1 | Scaffold: Compose, Postgres, FastAPI, React + Tailwind, `.env.example`, mock mode | done |
| 2 | Data model, multilingual seed data, CRUD APIs | next |
| 3 | Intake pipeline: web, SMS, voice, language detection, translation, extraction, gazetteer, clarification | |
| 4 | Phone simulator, network toggle, WebSocket live feed | |
| 5 | Trust & Evidence: cross-lingual clustering, confidence, Fast Verify | |
| 6 | Triage and Resource agents: priority, inventory, burn rate, shortages | |
| 7 | Coordination: allocation plan, approval, dispatch, SMS delivery confirmation | |
| 8 | Replanning, blackout detection, rumour correction | |
| 9 | Dashboard pages, i18n, map layers, Explain-me assistant on every section | |
| 10 | Digital twin / scenario engine, per-scenario 3D view, Run Demo | |
| 11 | Evaluation script and Metrics page | |
| 12 | Polish: README, tests, demo checklist | |

## Privacy

Phone numbers are stored only as salted SHA-256 hashes (to recognise repeat senders) and are shown masked
(`+91 98XXXXX210`). Data retention policy: to be documented with the data model (phase 2).
