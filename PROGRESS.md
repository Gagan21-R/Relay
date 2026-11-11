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
