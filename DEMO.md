# RELAY demo rehearsal checklist

## Before you present
- [ ] `docker compose up --build` (or backend + frontend locally) and wait for "Application startup complete".
- [ ] Open http://localhost:5180 — the ticker shows **Live** and **Mock mode**; the Command map shows Kodagu.
- [ ] Projector check: zoom the browser to 110–125%; the layout reflows (the menu collapses below 1024 px).
- [ ] Open a second tab on **/phone** (Phone simulator) and one on **/public** (public corrections).
- [ ] Optional: language switch EN → ಕನ್ನಡ → हिंदी once, then back to EN.

## The 12-step Run Demo (≈ 2 minutes)
Go to **Scenario control → Run Demo**. It resets to T+0 and plays each step on the live system; the caption card
navigates to the page where the step happens. Say one line per step:

1. **Reports arrive** — "web, social and SMS, in Kannada, Hindi, Malayalam, Tamil and English."
2. **Duplicates grouped** — "a Kannada SMS and an English tweet about Karadigodu: one incident, counted once."
3. **Rumour → correction** — "the dam bulletin contradicts the forward; correction in 8 languages, by SMS too."
4. **Prioritised** — open any incident: "every point of the score has a reason."
5. **Shortage** — "water at Napoklu camp runs out in about a day; the nearest depot with fresh stock is proposed."
6. **Plan** — "each line has a reason and its evidence; unmet needs are listed honestly."
7. **You approve** — press *Approve plan as Duty officer*. "Nothing moves without a person."
8. **Tracking** — trucks move on the map along open roads.
9. **ಹೌದು** — "the camp manager replies YES in Kannada; the delivery is confirmed and stock moves."
10. **Internet down** — "web and social from Kushalnagar stop; SMS still gets through; a silent zone is flagged."
11. **Replan** — "flood water cuts the roads to Siddapura camp; a new plan waits for approval."
12. **The village with no phones** — press *Approve recon as Duty officer*. "Silence is a signal: Hattihole sent
    nothing; the recon team carries supplies; its satellite-phone report turns the village into incidents."

## Live extras (if time allows)
- [ ] **Phone simulator**: tap *Kanglish · no location* → RELAY asks where you are, in Kannada → reply "Siddapura school".
- [ ] **Network toggle**: cut Kushalnagar, send a web report (blocked) and an SMS (arrives).
- [ ] **Explain me**: on any panel, press *Explain me* → ask "what should I do next?".
- [ ] **Same-report analyser** (Incidents page): compare a Kannada SMS and an English tweet.
- [ ] **3D twin**: switch scenario (Harangi release / Madikeri landslides) on Scenario control → the twin rebuilds.
- [ ] **Metrics**: point at the held-out column and the "synthetic data" disclaimer.

## If something goes wrong
- Dashboard says *Offline*: the backend is not running on :8010; restart it and refresh.
- Demo caption shows an error: press the **Scenario control → Run Demo** button again (it resets to T+0).
- To reset everything: `python -m app.sim.seed --reset` in `backend/` (or `make seed`).
