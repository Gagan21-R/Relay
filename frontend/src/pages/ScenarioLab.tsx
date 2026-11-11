// Scenario Lab: 50 synthetic scenarios on real places across every Indian state and union territory, nine disaster
// types, three difficulty levels. Launch one and the whole system (map, agents, plans, tasks) switches to it;
// play it stage by stage, then read the final report built from the live database.
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { FileText, FlaskConical, Pause, Play, RotateCcw, Rocket, SkipForward } from "lucide-react";
import { PageHeader } from "../components/Layout";
import { DISASTER_ICON } from "../components/Disaster";
import { Empty, Panel, simTime } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { useLiveEvents } from "../hooks/useLive";
import { api } from "../services/api";
import { startGuide } from "../components/Guide";

const DIFF: Record<string, string> = { beginner: "bg-mint-300", intermediate: "bg-sun-300", advanced: "bg-pink-300" };

export default function ScenarioLab() {
  const list = useApi<any>("/api/lab/scenarios");
  const status = useApi<any>("/api/lab/status", ["sim", "refresh", "plan", "dispatch"], 500);
  const [f, setF] = useState({ q: "", disaster: "", difficulty: "", region: "" });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [report, setReport] = useState<any>(null);
  const [feed, setFeed] = useState<any[]>([]);
  useLiveEvents((e) => setFeed((x) => [{ ...e.data, kind: e.type }, ...x].slice(0, 14)), ["audit"]);
  const items = useMemo(() => (list.data?.scenarios ?? []).filter((s: any) =>
    (!f.disaster || s.disaster === f.disaster) && (!f.difficulty || s.difficulty === f.difficulty) && (!f.region || s.region.includes(f.region)) &&
    (!f.q || `${s.name} ${s.state} ${s.description}`.toLowerCase().includes(f.q.toLowerCase()))), [list.data, f]);
  const cov = list.data?.coverage;
  const regions = useMemo(() => Object.keys(cov?.by_region ?? {}).sort(), [cov]);
  const call = async (path: string, body: any, done: string) => {
    setBusy(true); setMsg(null);
    try { await api(path, { method: "POST", body: JSON.stringify(body) }); setMsg(done); setReport(null); status.reload(); }
    catch (e: any) { setMsg(e.message); }
    setBusy(false);
  };
  const st = status.data;
  const cur = list.data?.scenarios.find((s: any) => s.id === st?.scenario?.id);
  const end = st?.timeline?.end_t ?? 10;
  return (
    <div className="space-y-4">
      <PageHeader title="Scenario Lab" sub="Train on real places across India. Every scenario runs through the real channels, agents and approvals; all people, reports and stock are synthetic." kicker={cov ? `${cov.total_with_kodagu} scenarios · ${cov.states_and_uts.length} states & UTs` : "loading"} tone="bg-brand-300" section="lab.page" />
      {msg && <p className="sticker w-fit bg-lime-400">{msg}</p>}
      {st && cur && (
        <Panel tone="bg-sun-400" title={<span className="flex flex-wrap items-center gap-2">{DISASTER_ICON[cur.disaster]} Now running: {cur.name} <span className={`badge ${DIFF[cur.difficulty]}`}>{cur.difficulty}</span><span className="badge bg-white">T+{st.clock.toFixed(1)} h</span></span>}>
          <div className="flex flex-wrap gap-2">
            <button className="btn-ghost" disabled={busy} onClick={() => call("/api/sim/clock", { action: "step", hours: 1 }, "Advanced 1 h")}><SkipForward size={15} aria-hidden />+1 h</button>
            <button className="btn-ghost" disabled={busy} onClick={() => call("/api/sim/clock", { action: "play", speed: 0.05 }, "Playing (1 h / 20 s)")}><Play size={15} aria-hidden />Play</button>
            <button className="btn-ghost" disabled={busy} onClick={() => call("/api/sim/clock", { action: "pause" }, "Paused")}><Pause size={15} aria-hidden />Pause</button>
            <button className="btn-ghost" disabled={busy} onClick={() => call("/api/lab/reset", {}, "Restarted from T+0")}><RotateCcw size={15} aria-hidden />Reset</button>
            <button className="btn-pop" disabled={busy} onClick={async () => setReport(await api("/api/lab/report"))}><FileText size={15} aria-hidden />Final report</button>
            <Link className="btn-ghost" to="/">Open map</Link><Link className="btn-ghost" to="/plans">Plans</Link><Link className="btn-ghost" to="/dispatch">Tasks</Link>
          </div>
          <div className="mt-3 flex gap-1" aria-label="Stages">
            {st.stages.map((s: any) => {
              const pct = Math.max(0, Math.min(1, (st.clock - s.from_t) / Math.max(0.01, s.to_t - s.from_t)));
              return (
                <div key={s.name} className="flex-1 rounded-xl border-2 border-ink bg-white p-2 text-[11px]">
                  <p className="font-extrabold">{s.name}{st.current_stage === s.name ? " · now" : ""}</p>
                  <div className="my-1 h-2 border border-ink bg-paper"><div className="h-full bg-signal" style={{ width: `${pct * 100}%` }} /></div>
                  <p className="text-ink/70">{simTime(s.from_t)}–{simTime(s.to_t)}: {s.summary}</p>
                </div>);
            })}
          </div>
          <p className="mt-2 text-xs font-bold">{st.counts.reports} reports · {st.counts.incidents} incidents · {st.counts.plans} plans · {st.counts.tasks} tasks · {st.timeline.released}/{st.timeline.total} timeline events (ends T+{end.toFixed(1)} h)</p>
          {cur.events?.length > 0 && <ul className="mt-1 text-[11px] font-medium">{cur.events.map((e: any, i: number) => <li key={i}>{st.clock >= e.t ? "✔" : "◷"} {simTime(e.t)} — {e.what}</li>)}</ul>}
          <div className="mt-2 grid gap-2 md:grid-cols-2">
            <div><p className="text-xs font-extrabold uppercase">Objectives</p><ul className="list-disc pl-5 text-xs">{cur.objectives.map((o: string) => <li key={o}>{o}</li>)}</ul></div>
            <div><p className="text-xs font-extrabold uppercase">Expected outcomes</p><ul className="list-disc pl-5 text-xs">{cur.expected.map((o: string) => <li key={o}>{o}</li>)}</ul></div>
          </div>
        </Panel>
      )}
      {report && (
        <Panel title={`Final report · ${report.scenario?.name} · T+${report.clock.toFixed(1)} h (synthetic)`} tone="bg-mint-400" section="lab.report">
          {report.objectives?.length > 0 && <table className="mb-3 w-full text-xs"><thead><tr className="text-left"><th>Objective</th><th>Status</th></tr></thead>
            <tbody>{report.objectives.map((o: any, i: number) => <tr key={i} className="border-t border-ink/10"><td>{o.objective}</td><td><span className={`badge ${o.met ? "bg-mint-300" : "bg-sun-300"}`}>{o.status}</span></td></tr>)}</tbody></table>}
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4 text-xs">
            {[["Decisions", report.decisions.map((d: any) => `${simTime(d.t)} ${d.who}: ${d.summary}`)], ["Successes", report.successes], ["Failures", report.failures], ["Unresolved", report.unresolved]].map(([t, l]: any) => (
              <div key={t} className="rounded-xl border-2 border-ink bg-white p-2"><p className="font-extrabold">{t} ({l.length})</p>
                <ul className="mt-1 max-h-56 list-disc space-y-0.5 overflow-y-auto pl-4">{l.length ? l.map((x: string, i: number) => <li key={i}>{x}</li>) : <li className="list-none text-ink/50">none</li>}</ul></div>))}
          </div>
          <p className="mt-2 text-[11px] font-bold text-ink/60">{report.note}</p>
        </Panel>
      )}
      <div className="grid gap-4 xl:grid-cols-[1fr_320px]">
        <Panel title={`Scenarios (${items.length})`} tone="bg-lime-400" section="lab.list">
          <div className="mb-3 flex flex-wrap gap-2">
            <input className="input max-w-xs" placeholder="Search place, state…" value={f.q} onChange={(e) => setF({ ...f, q: e.target.value })} aria-label="Search scenarios" />
            <select className="input max-w-[11rem]" value={f.disaster} onChange={(e) => setF({ ...f, disaster: e.target.value })} aria-label="Disaster"><option value="">all disasters</option>{Object.keys(cov?.by_disaster ?? {}).map((d) => <option key={d} value={d}>{DISASTER_ICON[d]} {d} ({cov.by_disaster[d]})</option>)}</select>
            <select className="input max-w-[10rem]" value={f.difficulty} onChange={(e) => setF({ ...f, difficulty: e.target.value })} aria-label="Difficulty"><option value="">all levels</option>{["beginner", "intermediate", "advanced"].map((d) => <option key={d}>{d}</option>)}</select>
            <select className="input max-w-[10rem]" value={f.region} onChange={(e) => setF({ ...f, region: e.target.value })} aria-label="Region type"><option value="">all regions</option>{regions.map((r) => <option key={r}>{r}</option>)}</select>
          </div>
          {!items.length ? <Empty>No scenario matches.</Empty> : (
            <div className="grid gap-2 md:grid-cols-2 2xl:grid-cols-3">
              {items.map((s: any) => (
                <motion.article key={s.id} layout className={`rounded-2xl border-2 border-ink bg-white p-3 text-xs shadow-hard-sm ${st?.scenario?.id === s.id ? "ring-4 ring-brand-400" : ""}`}>
                  <div className="flex flex-wrap items-center gap-1.5"><span className="text-lg">{DISASTER_ICON[s.disaster]}</span><b className="text-sm">{s.name}</b></div>
                  <div className="mt-1 flex flex-wrap gap-1"><span className={`badge ${DIFF[s.difficulty]}`}>{s.difficulty}</span><span className="badge bg-paper">{s.state}</span>{s.region.slice(0, 3).map((r: string) => <span key={r} className="badge bg-white">{r}</span>)}{!s.lab && <span className="badge bg-cobalt-200">hand-built</span>}</div>
                  <p className="mt-1.5 text-ink/75">{s.description}</p>
                  <p className="mt-1 text-[11px] font-bold text-ink/60">{s.stages.length || 1} stage(s) · {s.objectives.length} objectives</p>
                  <div className="mt-2 flex gap-1.5">
                    <button className="btn-pop !px-2 !py-1 !text-[11px]" disabled={busy} onClick={() => startGuide(s.id)}><Rocket size={12} aria-hidden />Run guided</button>
                    <button className="btn-ghost !px-2 !py-1 !text-[11px]" disabled={busy} onClick={() => call("/api/lab/launch", { id: s.id, replay_until: 0 }, `Launched ${s.name} at T+0 — press +1 h or Play`)}><FlaskConical size={12} aria-hidden />Launch only</button>
                  </div>
                </motion.article>
              ))}
            </div>
          )}
        </Panel>
        <div className="space-y-4">
          <Panel title="Coverage" tone="bg-cobalt-300">
            {cov && <div className="space-y-1 text-xs">
              <p><b>Disasters:</b> {Object.entries(cov.by_disaster).map(([k, v]) => `${k} ${v}`).join(" · ")} (+3 Kodagu)</p>
              <p><b>Levels:</b> {Object.entries(cov.by_difficulty).map(([k, v]) => `${k} ${v}`).join(" · ")}</p>
              <p><b>States & UTs:</b> {cov.states_and_uts.length} of 36 (28 states + 8 union territories)</p>
              <p className="text-ink/60">{list.data.note}</p>
            </div>}
          </Panel>
          <Panel title="Live activity" tone="bg-pink-400" section="audit.page">
            {!feed.length ? <p className="text-xs text-ink/60">Agent and human actions appear here as the scenario runs.</p> :
              <ul className="space-y-1 text-[11px]">{feed.map((a, i) => <li key={i} className="rounded-lg bg-paper px-2 py-1"><b>{a.actor}</b> {a.action?.replace(/_/g, " ")} — {a.summary}</li>)}</ul>}
          </Panel>
        </div>
      </div>
    </div>
  );
}
