# RELAY demo

## Before you present
- [ ] Start the backend (`python -m uvicorn app.main:app --port 8010` in `backend/`) and the frontend (`npm run dev` in
      `frontend/`). Wait for "Application startup complete". Everything runs offline in mock mode.
- [ ] Open http://localhost:5180 — the header shows **Live**, **Mock mode**, **Disaster: Flood**, **Acting as: Duty Officer**.
- [ ] Projector: zoom the browser to 110–125%.
- [ ] Say once, up front: *"Places are real; every report, person and stock count is synthetic. Docker, Gemini and
      Twilio integrations exist but were not tested — this is the offline mode."*

## Easiest: the guided run
Choose a disaster in the header (or click a pin after **All of India** on the map) → pick a place → the **guided run**
walks all 14 steps and opens each page as the work happens there. It stops where a Duty Officer decides: press the
button in the guide or act on the page. Keep **How RELAY works** open in a second tab — its steps light up as you go.

## The three-minute demo — six beats

**Beat 1 · Disaster selection (0:00–0:25)** — *Scenario Lab*
- Disaster menu → *Cyclone* → **Canning (West Bengal)** → the guided run starts; the map and header switch to the
  Sundarbans. (Or *Scenario Lab* → *Launch only* to drive it yourself.)
- Line: *"Nine disasters, one architecture: the cyclone profile changes severity weights, resource standards, overlays
  and recommendations. 50 scenarios cover every state and UT."*
- Command map → *Disaster* tab: profile and GDACS items labelled **FALLBACK** (*"we never pass samples off as live"*).

**Beat 2 · Reports, evidence and agents talking (0:25–0:55)** — *Live feed*, *Agent conversations*, *Incidents*
- Point at a Bengali SMS, its English duplicate and its romanized/Hindi copy: one incident, counted once.
- *Agent conversations*: Intake → Trust → Triage hand-offs; Coordination asks Resource for boats and accepts a second depot's offer.
- Open the incident: confidence and priority breakdowns, every report behind it.
- Optional: *Phone simulator* → send `Mane olage neeru bandide.` → detected Kannada (romanized), flood, rescue; RELAY
  asks for the location in Kannada.

**Beat 3 · Resources and volunteer assignment (0:55–1:20)** — *Plans*
- Each line: depot → destination by vehicle, **route safety label**, **suggested volunteer** with score, and the
  **precedent count**.
- Line: *"Volunteer choice is a deterministic tool — skills, reliability, distance, vehicle; ties by ID. The LLM never
  picks people, quantities or routes."*

**Beat 4 · Planning and approval (1:20–1:50)** — *Plans* → *Tasks & dispatch*
- Point at **Previous vs updated**: *"the Canning–Gosaba road was reported blocked by a citizen — unverified — so the
  plan reroutes through Kakdwip; every change needs approval."*
- **Approve & assign volunteers.** On *Tasks*, press **dispatch** on a task: **409 — route not verified**. Press
  **verify route**, then switch *Acting as* to the assigned volunteer and **dispatch** their own task. (Another
  volunteer gets 403.)

**Beat 5 · Disruption, rerouting, regional-language communication (1:50–2:30)** — *Scenario Lab*, *Public messages*
- *Scenario Lab* → **+1 h** twice: stage 2 cuts a shelter off; the stage bar moves; a new plan appears with the reason.
- *Public messages* → template *shelter open* → **Draft in each language**: English, Hindi, Bengali, each with
  **facts preserved**; Mizo or Khasi would get English, clearly marked. **Approve**, then **Send (mock SMS)**.
- On *Tasks*: a delivered task shows *recipient said YES — evidence; officer must confirm*. Confirm as Duty Officer.

**Beat 6 · Verification, evaluation and the Lab (2:30–3:00)** — *Scenario Lab* → *Final report*, then *Metrics*
- **Final report**: decisions, successes, failures, unresolved, objective checks.
- *Metrics*: duplicate precision **0.95 (development) / 1.00 (held-out), measured**; per-language and per-input-type
  results (romanized Tamil/Telugu/Marathi/Bengali are the weak spot); verified-only vs all-reports; 0 routes through a
  closed road; 50/50 scenarios ran, 0 rumour-led incidents planned.
- Close: *"Synthetic data, honest numbers, a person decides every action."*

## Longer demo
*Scenario control → Run guided* runs the 14-step guided run on the current scenario; the original Kodagu story (≈ 2 min): reports in five
languages, cross-language duplicates, dam-burst rumour corrected in 8 languages, shortages, a plan, approval, officer-
verified routes and dispatch, the Kannada **ಹೌದು** as evidence then officer confirmation, an internet blackout, a shelter
cut off by flood and a replan, and the silent village found by blackout detection.

## If something goes wrong
- *Offline* pill: the backend is not running on :8010; restart it and refresh.
- A button returns **403**: check *Acting as* in the header (only a Duty Officer can approve, verify routes or confirm).
- **409**: the task is not in the right state (e.g. route not verified yet) — the message says which step is missing.
- Reset a Lab scenario: *Scenario Lab → Reset*. Reset everything: `python -m app.sim.seed --reset` in `backend/`.
