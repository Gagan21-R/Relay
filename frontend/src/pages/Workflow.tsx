// How RELAY works: the complete workflow, in order — what happens first, which agent does it, what it tells the
// others, and where a person must decide. During a guided run the steps light up as they happen.
import { Link } from "react-router-dom";
import { ArrowDown, CornerUpLeft, Play } from "lucide-react";
import { PageHeader } from "../components/Layout";
import { startGuide } from "../components/Guide";
import { AGENT_META } from "./Agents";
import { useApi } from "../hooks/useApi";

type W = { id: number; who: string; title: string; does: string[]; tells?: string; gate?: boolean; page: string };
const PHASES: { name: string; tone: string; steps: W[] }[] = [
  { name: "1 · Set up", tone: "bg-cobalt-300", steps: [
    { id: 1, who: "duty_officer", title: "Choose a disaster and a place", page: "/lab",
      does: ["Disaster menu, the India map pins or the Scenario Lab", "RELAY loads that place: roads, shelters, hospitals, depots, stock, volunteers", "The disaster profile sets severity weights, resource standards and overlays"] },
    { id: 2, who: "monitor", title: "Hazard signals arrive", page: "/",
      does: ["Rain, river, wind, quake, fire, heat, gas sensors; satellite footprints; GDACS (live / stale / fallback)", "Roads under the footprint close at once (caution first), marked unverified"] },
  ] },
  { name: "2 · Understand", tone: "bg-lime-400", steps: [
    { id: 3, who: "intake", title: "Reports arrive on any channel", page: "/feed",
      does: ["SMS, voice calls, web, social, news, field app, satellite phone", "When a zone's internet is down, SMS and voice still get through"] },
    { id: 4, who: "intake", title: "Intake reads each report", page: "/feed", tells: "Intake → Trust: “new report R-1012: rescue, 12 people, Napoklu — new or duplicate?”",
      does: ["Language and script (native, romanized, mixed), translation kept beside the original", "Needs, people, urgency, disaster type, location; flags reports a human should check", "Asks the sender for a missing location, in their language"] },
    { id: 5, who: "trust", title: "Trust groups duplicates and scores credibility", page: "/incidents", tells: "Trust → Triage: “R-1012 joins incident #3 (likely 68%)” · Trust ⇄ Coordination: “life-safety but unverified — who can check?” → “V-001, 1 km away”",
      does: ["Same place + same meaning + same time + compatible needs = one incident", "Forwards count once; sensational forwarded claims never join first-hand reports", "Life-safety reports with low confidence go to Fast Verify — never discarded"] },
    { id: 6, who: "triage", title: "Triage decides who needs help first", page: "/incidents", tells: "Triage → Monitor: “re-ranked: #3 → 74/100”",
      does: ["Priority out of 100: life threat, people, vulnerable groups, waiting time, confidence, access", "Every point has a written reason"] },
    { id: 7, who: "resource", title: "Resource compares stock with need", page: "/resources",
      does: ["Shelter burn rates and shortage forecasts (per-person standards of the disaster)", "Only fresh stock that can actually reach counts"] },
    { id: 8, who: "blackout", title: "Blackout looks for silent places", page: "/blackout", tells: "Blackout ⇄ Resource: “Hattihole is silent — what should recon carry?” → quantities · Blackout → Duty Officer: “approve recon?”",
      does: ["Populated places inside the hazard that stopped reporting", "Proposes a recon team carrying supplies"], gate: true },
  ] },
  { name: "3 · Decide", tone: "bg-sun-400", steps: [
    { id: 9, who: "monitor", title: "Monitor notices what changed", page: "/alerts", tells: "Monitor → Coordination: “road blocked / shortage / new P1 / task failed — please re-plan”",
      does: ["New high-priority incident, shortage, shelter cut off, road closed, delivery failed, plan out of date"] },
    { id: 10, who: "coordination", title: "Coordination builds the plan", page: "/plans", tells: "Coordination ⇄ Resource: “short of 2 boats” → “depot B can send 2” → accept / escalate · Coordination ⇄ Trust: “still credible?”",
      does: ["Safest route (not the shortest), right vehicle, unverified roads flagged", "Volunteers ranked by skills, reliability, distance (ties by ID); approval precedents shown", "Previous vs updated allocation, with the reason for every change"] },
    { id: 11, who: "duty_officer", title: "Duty Officer approves the plan", page: "/plans", gate: true,
      does: ["Approve, edit or reject — nothing moves before this", "Tasks: Created → Approved → Assigned (top-ranked free volunteer)"] },
  ] },
  { name: "4 · Act", tone: "bg-pink-300", steps: [
    { id: 12, who: "duty_officer", title: "Route verified, task dispatched", page: "/dispatch", gate: true,
      does: ["A Duty Officer verifies the route (409 otherwise)", "Dispatched by the officer or the assigned volunteer; stock leaves the depot now"] },
    { id: 13, who: "coordination", title: "Tracking on the map", page: "/",
      does: ["Teams move along verified routes", "Route cut on the way → task fails → back to Monitor (step 9)"] },
    { id: 14, who: "coordination", title: "Delivered — evidence collected", page: "/dispatch",
      does: ["The team marks it delivered", "The recipient is asked in their language; “YES” or a shelter check-in is evidence, not confirmation"] },
    { id: 15, who: "duty_officer", title: "Duty Officer confirms", page: "/dispatch", gate: true,
      does: ["Only a Duty Officer confirms (403 for anyone else)", "Stock moves to the shelter; the volunteer's reliability is updated"] },
  ] },
  { name: "5 · Communicate & learn", tone: "bg-mint-400", steps: [
    { id: 16, who: "duty_officer", title: "Tell people in their language", page: "/comms", gate: true,
      does: ["Area updates from templates in the languages spoken there; facts checked; English fallback", "Rumour corrections; nothing sent without approval (mock SMS)"] },
    { id: 17, who: "monitor", title: "Record, measure, debrief", page: "/lab",
      does: ["Audit log of every agent action and human decision", "Precedent memory, metrics, Scenario Lab final report"] },
  ] },
];
const GUIDE_TO_WORKFLOW: Record<number, number[]> = { 1: [1, 2], 2: [3, 4], 3: [4, 5, 6], 4: [5], 5: [6], 6: [7], 7: [9, 10, 11], 8: [11, 12],
  9: [13], 10: [2, 9], 11: [10, 11], 12: [16], 13: [14, 15], 14: [17] };

export default function Workflow() {
  const g = useApi<any>("/api/lab/guide", ["sim", "refresh", "plan", "dispatch", "agent_message"], 800);
  const done: number[] = g.data?.done ?? [];
  const current = done.length ? Math.max(...done) : 0;
  const lit = new Set((GUIDE_TO_WORKFLOW[current] ?? []));
  const past = new Set(done.flatMap((n) => GUIDE_TO_WORKFLOW[n] ?? []));
  return (
    <div className="space-y-4">
      <PageHeader title="How RELAY works" sub="The complete workflow, in order: what happens first, which agent does it, what it tells the other agents, and where a person must decide. Steps light up during a guided run." kicker="workflow" tone="bg-lime-400" section="workflow.page">
        <button className="btn-pop" onClick={() => startGuide()}><Play size={15} aria-hidden />Run it guided</button>
      </PageHeader>
      <div className="flex flex-wrap gap-2 text-xs font-bold">
        {Object.entries(AGENT_META).map(([k, m]) => <span key={k} className="badge bg-white"><span className="h-3 w-3 rounded-full border-2 border-ink" style={{ background: m.colour }} />{m.label}</span>)}
        <span className="badge bg-pink-400">◆ = a person decides</span><span className="badge bg-sun-300">⇄ = agents talk</span>
      </div>
      <div className="grid gap-4 xl:grid-cols-[1fr_260px]">
        <div className="space-y-2">
          {PHASES.map((ph) => (
            <section key={ph.name} className="rounded-3xl border-2 border-ink bg-paper p-3">
              <h2 className={`mb-2 inline-block rounded-xl border-2 border-ink px-3 py-1 text-sm font-extrabold ${ph.tone}`}>{ph.name}</h2>
              <div className="space-y-1">
                {ph.steps.map((st, i) => {
                  const m = AGENT_META[st.who];
                  const on = lit.has(st.id), was = past.has(st.id) && !on;
                  return (
                    <div key={st.id}>
                      <Link to={st.page} className={`block rounded-2xl border-2 border-ink bg-white p-3 transition-all hover:-translate-y-0.5 hover:shadow-hard-sm ${on ? "ring-4 ring-pink-400" : ""} ${st.gate ? "border-dashed" : ""}`}>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={`grid h-8 w-8 place-items-center rounded-full border-2 border-ink text-sm font-black ${was ? "bg-lime-400" : on ? "bg-pink-400 text-white" : "bg-white"}`}>{was ? "✔" : st.id}</span>
                          <span className="font-extrabold">{st.gate ? "◆ " : ""}{st.title}</span>
                          <span className="badge" style={{ background: m.colour, color: ["blackout", "duty_officer", "coordination"].includes(st.who) ? "#fff" : "#0B0B0C" }}>{m.label}</span>
                          {on && <span className="badge bg-pink-400 text-white">happening now</span>}
                          <span className="ml-auto font-mono text-[11px] text-ink/50">{st.page}</span>
                        </div>
                        <ul className="mt-1.5 list-disc space-y-0.5 pl-12 text-xs text-ink/80">{st.does.map((d) => <li key={d}>{d}</li>)}</ul>
                        {st.tells && <p className="ml-10 mt-1.5 rounded-lg bg-sun-200 px-2 py-1 text-[11px] font-bold">⇄ {st.tells}</p>}
                      </Link>
                      {i < ph.steps.length - 1 && <div className="flex justify-center py-0.5 text-ink/50"><ArrowDown size={16} aria-hidden /></div>}
                    </div>);
                })}
              </div>
            </section>))}
        </div>
        <aside className="space-y-3 xl:sticky xl:top-28 xl:self-start">
          <div className="rounded-3xl border-2 border-ink bg-white p-3 text-xs shadow-hard-sm">
            <p className="flex items-center gap-1 text-sm font-extrabold"><CornerUpLeft size={15} aria-hidden />The loop</p>
            <p className="mt-1">Whenever something changes — a new report, a sensor signal, a road reported blocked, a shelter cut off, a task that fails — the <b>Monitor</b> asks <b>Coordination</b> to re-plan (step 9 → 10), and the Duty Officer approves the change (step 11). RELAY keeps cycling until every need is met or escalated.</p>
          </div>
          <div className="rounded-3xl border-2 border-ink bg-white p-3 text-xs shadow-hard-sm">
            <p className="text-sm font-extrabold">Task lifecycle</p>
            <p className="mt-1 font-mono text-[11px]">Created → Approved → Assigned → Dispatched → Delivered → Confirmed</p>
            <p className="mt-1">Failed / Cancelled end a task. 403 = not your role; 409 = not this step yet.</p>
          </div>
          <div className="rounded-3xl border-2 border-ink bg-white p-3 text-xs shadow-hard-sm">
            <p className="text-sm font-extrabold">What the AI may do</p>
            <p className="mt-1">Read and translate text, fill a strict schema, draft translations that must pass a fact check. It never sets priorities, quantities, routes, assignments, approvals or dispatch.</p>
          </div>
          <Link to="/agents" className="btn-ghost w-full justify-center">See the agents talking →</Link>
        </aside>
      </div>
    </div>
  );
}
