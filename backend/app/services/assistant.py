"""The "Explain me" assistant. Every page and section of the dashboard has an entry: what it is, how to read it, what
you can do there. Answers add live facts from the current state, so the explanation is about *this* situation.
With a Gemini key the model writes the answer (in the UI language) from the same facts; in mock mode a rule-based
answer is assembled. Read-only: it never changes anything."""
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import state
from app.models import Alert, Dispatch, Incident, Plan, ReconTask, Report, Shelter, Zone
from app.services.llm import get_llm

S: dict[str, dict] = {
    # ---- command map ----
    "map.page": {"title": "Command map", "what": "The live picture of the district. Every layer updates over the WebSocket the moment an agent or a person changes something.",
                 "read": "Incident circles are coloured by priority (red P1 → blue P4) and outlined by confidence (solid = verified, dashed = unverified, crossed = false). Shelters are squares coloured by status, depots are purple diamonds, moving trucks follow their dispatch routes, blue areas are the satellite flood extent and hatched red areas are silent (blackout) zones.",
                 "do": "Click anything to open its evidence on the right. Toggle layers at the top. Pulses show reports arriving right now."},
    "map.layers": {"title": "Map layers", "what": "Switches for each kind of thing on the map.", "read": "Turn layers off to declutter: e.g. hide incidents to see only shelters and routes.", "do": "Toggle any layer; the choice is kept while you move around the app."},
    "map.panel": {"title": "Side panel (evidence trail)", "what": "Details of whatever you clicked on the map.", "read": "For an incident: priority and confidence breakdowns plus every report behind it. For a zone: its blackout risk. For a shelter: occupancy, access and stock.", "do": "Confirm or refute an incident, or jump to its full page."},
    # ---- feed / intake ----
    "feed.page": {"title": "Live report feed", "what": "Every report from every channel — SMS, voice, web, social, news, field app, official feeds and radio — as it arrives.",
                  "read": "Each card shows the original text (never discarded), a language badge (with romanized/mixed script), the English translation with its method and confidence, the extracted needs, people, vulnerable groups and place, and the incident it joined.",
                  "do": "Filter by channel or language. Green channel badges work without internet; blue ones need it. Show blocked reports to see what an internet outage stopped."},
    "feed.card": {"title": "Report card", "what": "One report, exactly as received plus what the Intake agent extracted.", "read": "The translation confidence bar says how much to trust the English line: translation memory ≈ 98%, Gemini ≈ 90%, word-by-word glossary lower. Extraction always runs on the original text, never on the translation.", "do": "Open the linked incident to see why this report was grouped with others."},
    "phone.page": {"title": "Phone simulator", "what": "A mock phone that proves RELAY works without internet: SMS and voice calls in any language reach the dashboard and get replies in the sender's language.",
                   "read": "Your messages are on the right in purple; RELAY's replies (acknowledgement with a reference number, clarification questions, delivery confirmation requests) on the left with their language.",
                   "do": "Tap a sample (Kannada, Hindi, Malayalam, Tamil, Telugu, Marathi, Bengali, Kanglish…), type your own, reply to a clarification, or send ಹೌದು / YES to confirm a delivery."},
    "phone.network": {"title": "Network status", "what": "Simulates an internet outage per zone.", "read": "A zone marked DOWN cannot send web, social or field-app reports; SMS, voice and radio still arrive. Blocked reports are counted so you can see what was lost.", "do": "Toggle a zone and send a web report and an SMS from it to compare."},
    "phone.voice": {"title": "Voice call (IVR)", "what": "Language menu → recording → transcription → the same pipeline as SMS.", "read": "With a Gemini key the audio itself is transcribed; in mock mode the browser's speech recognition or a typed transcript is used.", "do": "Pick the caller's language, record or upload a clip, and send."},
    "radio.page": {"title": "Radio console", "what": "Control-room entry for HAM, police wireless, forest/railway radio and satellite-phone messages.", "read": "These channels keep working when towers and power are down. A report from inside a silent zone ends its blackout.", "do": "Choose the channel and callsign, pick the zone if the message names none, and log it."},
    "field.page": {"title": "Field app", "what": "Mobile reporting that works offline: reports are saved on the device with GPS and time, and synced when there is signal.", "read": "The queue shows what is waiting. Sync is idempotent, so retries never duplicate.", "do": "Tick 'simulate no signal', write a report, then untick to watch it sync."},
    # ---- decide ----
    "incidents.page": {"title": "Incidents", "what": "Reports clustered into incidents and ranked by the Triage agent.", "read": "Each incident shows its priority (P1–P4 from a score out of 100), its confidence level and score, people affected and needs. False incidents sink to the bottom with priority 0.", "do": "Click an incident to see why it ranks where it does and every report behind it; confirm or refute it."},
    "incidents.priority": {"title": "Priority breakdown", "what": "Why this incident ranks where it does.", "read": "Points out of 100: life threat (30), people (20, log scale), vulnerable groups (15), waiting time (10), confidence (15) and access difficulty (10). An unverified life-safety report keeps most of its confidence points so it is checked fast instead of pushed down.", "do": "Use it to challenge the ranking: every number has its reason."},
    "incidents.confidence": {"title": "Confidence breakdown", "what": "How sure RELAY is that this is true.", "read": "Seven weighted components (independent sources, source reliability, sensor consistency, field/official support, plausibility, specificity, media check) minus penalties (contradictions, forward chains, sensational claims, old photos). Forwards and copies count as one source. Levels: verified ≥75%, likely ≥55%, else unverified; credible contradictions make it disputed or false.", "do": "Confirming or refuting updates every source's reliability for next time."},
    "incidents.evidence": {"title": "Evidence trail", "what": "Every report in the incident with the clustering tests it passed.", "read": "Each line shows the similarity, distance and time tests with their thresholds and whether the needs matched. ⟂ marks a report that contradicts the claim.", "do": "Check any merge you disagree with."},
    "incidents.analyser": {"title": "Same-report analyser", "what": "Paste two reports in any language and see whether RELAY would treat them as the same incident.", "read": "Four tests: meaning similarity (embeddings of the language-neutral form), distance ≤ 2.5 km, time ≤ 8 h and compatible needs. All four must pass.", "do": "Try a Kannada SMS against an English tweet about the same place."},
    "fastverify.page": {"title": "Fast Verify", "what": "Life-safety reports (people trapped, medical emergencies) with low confidence. They are never discarded.", "read": "Each card shows how long it has waited, the original message, and a masked number to call back in the reporter's language.", "do": "Call back or send the nearest team, then mark Confirmed or Not true."},
    "plans.page": {"title": "Plans & approvals", "what": "Allocation plans from the Coordination agent (deterministic rules, no LLM). Nothing moves until a Duty Officer approves.", "read": "The rationale explains the order (shelter shortages first, then incidents by priority). Each line shows depot → destination by vehicle, quantities, the route safety label (verified passable or unverified — verify before dispatch), the suggested volunteer from the ranking tool, and the precedent count (how similar lines were decided before). 'Previous vs updated' lists what changed since the last allocation and why.", "do": "Approve (creates tasks and assigns volunteers), edit (remove lines or change quantities → new version), or reject with a comment. Only a Duty Officer can; others get 403."},
    "plans.lines": {"title": "Plan lines", "what": "One delivery each.", "read": "Every line uses the nearest depot reachable over open roads that still has stock and a free team after the lines above it. Evidence links go to the reports or the shortage forecast.", "do": "Untick 'remove' or change a quantity to edit."},
    "plans.decision": {"title": "Decision", "what": "Where the human decides.", "read": "Approval creates tasks (Created → Approved) and assigns the top-ranked free volunteer (Assigned). Stock leaves the depot only at dispatch, which needs a verified route. Every decision goes to the audit log and to the precedent memory.", "do": "Add a comment, then approve, save edits or reject."},
    "plans.history": {"title": "Version history", "what": "Every plan version with what triggered it and who decided.", "read": "Superseded plans were replaced by a newer proposal; edited ones point to their new version.", "do": "Use it to see how the plan changed as the situation changed."},
    "dispatch.page": {"title": "Tasks & dispatch", "what": "Every task from approval to confirmation: Created → Approved → Assigned → Dispatched → Delivered → Confirmed (or Failed / Cancelled).", "read": "The backend enforces roles: Duty Officer approves, assigns, verifies routes, confirms and can do everything; the assigned volunteer may dispatch and mark delivered only their own task; others get 403. Invalid moves get 409. Delivered is not Confirmed: a recipient's SMS YES or a shelter check-in is recorded as evidence, then the Duty Officer confirms. 'why?' shows the route reasoning, alternatives, the volunteer ranking and the full history.", "do": "Switch role in the header to see what each role may do. Verify the route, dispatch, mark delivered, confirm."},
    "resources.page": {"title": "Resources", "what": "Supply vs demand, burn rates and shortage forecasts.", "read": "Demand = verified needs + shelter occupancy × per-person standards (15 L water per person per day). Supply = depot stock reachable over open roads; stale stock is not counted.", "do": "Recount stale stock, and watch the transfer proposals the Coordination agent will use."},
    "resources.burn": {"title": "Burn-rate chart", "what": "How long each shelter's stock lasts at current occupancy.", "read": "Each line is one shelter for the chosen item over the next 48 simulated hours; a line reaching zero is a shortage.", "do": "Switch item to see food and medical kits."},
    "resources.transfers": {"title": "Shortages & transfers", "what": "Projected and current shortages with the proposed fix.", "read": "'Runs out in ~N h' = stock ÷ hourly use. The proposal is the nearest reachable depot with enough fresh stock; if none exists the shortage is escalated.", "do": "Approve the plan that carries the transfer."},
    "resources.supply": {"title": "Demand vs supply", "what": "Totals per item.", "read": "Pink bars (demand) above lime bars (supply) mean a current shortage.", "do": "Use it to decide where to request outside help."},
    "resources.depots": {"title": "Depot inventory", "what": "Stock per depot with in-transit amounts.", "read": "Yellow rows are stale (not counted for over 12 h) and excluded from supply.", "do": "Enter a fresh count and press Recount."},
    "shelters.page": {"title": "Shelters", "what": "Capacity, occupancy, access, stock and the last check-in of every shelter.", "read": "Inaccessible = every access road closed. Unconfirmed = no check-in for over 8 h. Stock tiles turn pink when they run out within 24 h.", "do": "Check in on behalf of a manager (resets the clock and confirms deliveries waiting there)."},
    "alerts.page": {"title": "Alerts", "what": "Shortages, blackouts, inaccessible shelters, rumour corrections and overdue deliveries.", "read": "Alerts are raised once per condition and resolve themselves when it clears; the reason is kept.", "do": "Acknowledge, or follow the link to act."},
    "alerts.rumour": {"title": "Rumour control", "what": "Publishing corrections for incidents marked false.", "read": "Corrections use pre-translated templates in 8 languages with the place name in each script, go by SMS to people who reported from the area, and show on the public page.", "do": "Press Publish correction."},
    "blackout.page": {"title": "Blackout & reconnaissance", "what": "Silence is a signal: populated zones inside the hazard footprint that have stopped reporting.", "read": "Risk = hazard + population + silence + infrastructure loss + missing-contact reports + vulnerability. Silent zones are ranked by population × hazard × hours silent.", "do": "Approve the recon task with its pre-positioned supplies, then log the team's report when it arrives."},
    "blackout.risk": {"title": "Blackout risk breakdown", "what": "Why this zone is suspected of being cut off.", "read": "Each component shows its value and reason; missing-contact reports from relatives count even though they come from outside the zone.", "do": "Check the components before approving recon."},
    "blackout.recon": {"title": "Recon task", "what": "A team (satellite phone, helicopter or drone) sent to a silent zone.", "read": "It carries supplies estimated from population × standards so the first visit can deliver, not just assess.", "do": "Approve, then log the team report or upload a drone image (experimental)."},
    # ---- other ----
    "scenario.page": {"title": "Scenario control (digital twin)", "what": "Replays or generates the disaster on a timeline and injects what-if events.", "read": "The clock shows simulated hours since the event started. Speed controls how fast the timeline plays.", "do": "Start a scenario, inject events (close a road, flood a shelter, drop inventory, cut internet, spike reports, silence a village) or press Run Demo."},
    "scenario.demo": {"title": "Run Demo", "what": "The 12-step story from the RELAY deck, played on the live system.", "read": "Each step runs real agents; two steps wait for a person to approve.", "do": "Press Run Demo and follow the captions."},
    "twin3d.page": {"title": "3D twin", "what": "A 3D model of the active scenario that changes with every scenario and event.", "read": "Terrain and river, villages sized by population, water where the satellite flood extent is, dark villages for blackout zones, shelters, depots and delivery trucks moving along their routes.", "do": "Drag to orbit, scroll to zoom, switch scenario."},
    "plans.changes": {"title": "Previous vs updated", "what": "How this plan differs from the allocation already in place.", "read": "Per line: depot, route and quantity changes, the previous source (task or plan version) and why (e.g. a road reported blocked). Lines that replace an existing task cancel it only when this plan is approved.", "do": "Read the reasons before approving a replan."},
    "map.disaster": {"title": "Disaster profile & GDACS", "what": "The active disaster's planning profile and international alerts.", "read": "The selector in the header switches severity weights, per-person resource standards, overlay style and recommendations for all agents. GDACS items are labelled LIVE, STALE (older than 30 min) or FALLBACK (illustrative sample when offline or in mock mode — not real alerts).", "do": "Change the disaster in the header and watch priorities re-rank."},
    "lab.page": {"title": "Scenario Lab", "what": "50 synthetic training scenarios on real places in every Indian state and union territory, across nine disaster types and three difficulty levels.", "read": "Launching resets the world to that scenario's places, roads, shelters, hospitals, depots and volunteers, re-centres the map and the 3D twin, and replays its messages through the real agents. Stages bring disruptions: roads reported blocked, shelters cut off, stock lost, villages going silent.", "do": "Filter, launch, play or step the clock, act as Duty Officer, then open the final report."},
    "lab.list": {"title": "Scenario list", "what": "Every scenario with its disaster, difficulty, state and region type.", "read": "Hand-built ones are the three Kodagu scenarios; the rest are generated from real place coordinates with template-drafted multilingual messages.", "do": "Launch at T+0 to play it yourself, or at T+4.5 h to jump into the disruption."},
    "lab.report": {"title": "Final report", "what": "What happened, computed from the live database.", "read": "Objectives (from the scenario design), human decisions, successes (confirmed deliveries, rumours not acted on, silent zones found), failures (failed tasks, unmet needs) and unresolved issues.", "do": "Use it to debrief; it is a training aid, not an accuracy claim."},
    "comms.page": {"title": "Public messages", "what": "Area-wise public updates drafted from reusable templates in each language the area speaks.", "read": "Place, shelter and road names stay in Latin script and numbers as digits, and a fact check proves every fact survived. Regional templates are machine-drafted and NOT validated by native speakers; languages without one get the English text, clearly marked. Nothing is sent without a Duty Officer's approval, and sending is a mock SMS.", "do": "Pick a template, fill the facts, draft, review each language, approve, send."},
    "comms.languages": {"title": "Language coverage", "what": "The 19 configured languages and how well each is supported.", "read": "full = detection + extraction + outgoing templates; basic = detection + partial vocabulary, a speaker should check; pending = configured but not reliably handled. Accuracy figures on the Metrics page come from small developer-written test sets.", "do": "Treat basic and pending languages as needing human review."},
    "metrics.page": {"title": "Metrics", "what": "Evaluation on labelled synthetic data; real-world validation pending.", "read": "Duplicate precision/recall per language, extraction accuracy per language and per input type (native / romanized / mixed), a developer-written multilingual probe set across 15 languages, verified-only vs all-reports allocation, route-rule checks under simulated road closures, a replay of all 50 scenarios, plan time, shortage detection, traceability and delivery verification. Ground truth is read only by the evaluation script.", "do": "Re-run the evaluation; read the notes under each number."},
    "audit.page": {"title": "Audit log", "what": "Every agent action and human decision with inputs and outputs.", "read": "Agents, people and the system are marked separately; times are simulated hours.", "do": "Filter by who did it, what they did, or free text."},
    "about.page": {"title": "About RELAY", "what": "The story: what RELAY does, who does what, and the evidence behind it.", "read": "Case studies are the demo stories; the team is the five agents, four modules and the people who decide.", "do": "Send a real report with the contact form."},
}


def facts(db: Session, section: str) -> list[str]:
    """Live facts relevant to a section."""
    p = section.split(".")[0]
    now = state.now(db)
    out = [f"Simulated time T+{now:.1f} h."]
    n_rep = db.scalar(select(func.count()).select_from(Report)) or 0
    if p in ("map", "feed", "phone", "radio", "field", "about"):
        langs = db.scalar(select(func.count(func.distinct(Report.original_language)))) or 0
        offline = db.scalar(select(func.count()).select_from(Report).where(Report.channel.in_(["sms", "voice", "radio_entry"]))) or 0
        blocked = db.scalar(select(func.count()).select_from(Report).where(Report.status == "blocked")) or 0
        down = [z.name for z in db.scalars(select(Zone).where(Zone.internet_down))]
        out.append(f"{n_rep} reports in {langs} languages; {offline} arrived over SMS, voice or radio; {blocked} blocked by internet outages.")
        out.append(f"Internet down in: {', '.join(down)}." if down else "No zone has its internet cut.")
    if p in ("map", "incidents", "fastverify", "about"):
        top = db.scalars(select(Incident).where(Incident.status != "resolved").order_by(Incident.priority_score.desc()).limit(3)).all()
        if top:
            out.append("Top incidents: " + "; ".join(f"{i.title} (priority {i.priority_score:.0f}, {i.confidence_level})" for i in top) + ".")
        fv = db.scalar(select(func.count()).select_from(Incident).where(Incident.fast_verify.is_(True))) or 0
        false = db.scalar(select(func.count()).select_from(Incident).where(Incident.confidence_level == "false")) or 0
        out.append(f"{fv} incident(s) wait in Fast Verify; {false} judged false.")
    if p in ("plans", "dispatch", "map"):
        pend = db.scalar(select(Plan).where(Plan.status == "pending_approval"))
        if pend:
            lines = [a for a in pend.assignments if a.get("kind") != "unmet"]
            out.append(f"Plan v{pend.version} awaits approval: {len(lines)} deliveries (trigger: {pend.trigger}).")
        counts = {s_: c for s_, c in db.execute(select(Dispatch.status, func.count()).group_by(Dispatch.status))}
        if counts:
            out.append("Dispatches: " + ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in counts.items()) + ".")
    if p in ("resources", "shelters", "map", "alerts"):
        sh = db.scalars(select(Alert).where(Alert.type == "shortage", Alert.resolved.is_(False))).all()
        if sh:
            out.append("Shortages: " + "; ".join(a.message for a in sh[:3]) + ".")
        bad = db.scalars(select(Shelter).where(Shelter.status != "open")).all()
        if bad:
            out.append("Shelters not open: " + "; ".join(f"{s.name} ({s.status})" for s in bad) + ".")
    if p in ("blackout", "map", "alerts"):
        sil = db.scalars(select(Zone).where(Zone.blackout_flag)).all()
        out.append(("Silent zones: " + "; ".join(f"{z.name} (risk {z.blackout_score:.2f}, {z.population:,} people)" for z in sil) + ".") if sil else "No zone is flagged silent right now.")
        rt = db.scalars(select(ReconTask).where(ReconTask.status.in_(["pending_approval", "in_progress"]))).all()
        if rt:
            out.append("Recon: " + "; ".join(f"{t.team} ({t.status.replace('_', ' ')})" for t in rt) + ".")
    if p == "alerts":
        n = db.scalar(select(func.count()).select_from(Alert).where(Alert.resolved.is_(False))) or 0
        out.append(f"{n} open alert(s).")
    return out


_STOP = {"the", "is", "and", "what", "why", "this", "that", "to", "of", "a", "an", "i", "should", "do", "about", "how", "it", "in",
         "for", "with", "are", "be", "can", "you", "my", "me", "on", "does", "next", "here", "there", "or", "who", "where", "when"}


def _stem(w: str) -> str:
    return w[:-1] if w.endswith("s") and len(w) > 4 else w


def _match(question: str) -> str:
    q = {_stem(w) for w in re.findall(r"[a-z]+", question.lower()) if w not in _STOP}
    best, score = "map.page", 0
    for k, v in S.items():
        title = {_stem(w) for w in re.findall(r"[a-z]+", v["title"].lower()) if w not in _STOP}
        body = {_stem(w) for w in re.findall(r"[a-z]+", (v["what"] + " " + v["read"]).lower()) if w not in _STOP}
        sc = 3 * len(q & title) + len(q & body) + (2 if _stem(k.split(".")[0]) in q else 0)
        if sc > score:
            best, score = k, sc
    return best


def explain(db: Session, section: str, question: str | None = None, lang: str = "en", context: dict | None = None) -> dict:
    key = section if section in S else (_match(question) if question else "map.page")
    if question and section in S:
        # a follow-up about another part of the app
        guess = _match(question)
        if guess.split(".")[0] != section.split(".")[0] and len(question.split()) > 2:
            key = guess
    s = S[key]
    live = facts(db, key)
    llm = get_llm().generate_text(
        f"You are RELAY's explain-me assistant for a disaster-response dashboard. Answer in language code '{lang}', in 4-7 short "
        f"sentences, plainly. Section: {s['title']}. What it is: {s['what']} How to read it: {s['read']} What the user can do: {s['do']} "
        f"Live facts: {' '.join(live)} Extra context: {context or {}}. User question: {question or 'Explain this section.'}"
    )
    if llm:
        return {"section": key, "title": s["title"], "answer": llm, "facts": live, "method": "gemini"}
    return {"section": key, "title": s["title"], "what": s["what"], "read": s["read"], "do": s["do"], "facts": live,
            "answer": f"{s['what']} {s['read']} {s['do']}", "method": "rule-based (mock mode)",
            "note": None if lang == "en" else "Detailed explanations are in English in mock mode; with a Gemini key they are written in your UI language."}
