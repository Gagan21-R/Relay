# Windows without make: run the commands on the right by hand. PY points at the backend's Python.
PY ?= python
.PHONY: up backend frontend test seed eval migrate
up:        ; docker compose up --build
backend:   ; cd backend && $(PY) -m uvicorn app.main:app --reload --port 8010
frontend:  ; cd frontend && npm run dev
migrate:   ; cd backend && $(PY) -m alembic upgrade head
seed:      ; cd backend && $(PY) -m app.sim.seed --reset
test:      ; cd backend && $(PY) -m pytest -q && cd ../frontend && npx vitest run
eval:      ; cd backend && $(PY) -m eval.run_eval
