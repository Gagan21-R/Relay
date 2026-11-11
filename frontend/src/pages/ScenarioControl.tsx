import { useState } from "react";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Clapperboard, FastForward, Flame, Pause, Play, RotateCcw, SkipForward, Zap } from "lucide-react";
import { PageHeader } from "../components/Layout";
import { startGuide } from "../components/Guide";
import { Explain } from "../components/Assistant";
import { Panel } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";

const SPEEDS = [["0.02", "slow · 1 h / 50 s"], ["0.05", "normal · 1 h / 20 s"], ["0.2", "fast · 1 h / 5 s"], ["0.5", "very fast · 1 h / 2 s"]];

export default function ScenarioControl() {
  const { t } = useTranslation();
  const sc = useApi<any>("/api/sim/scenarios", ["sim", "refresh"], 300);
  const zones = useApi<any[]>("/api/zones");
  const roads = useApi<any[]>("/api/roads", ["signal", "sim"]);
  const shelters = useApi<any[]>("/api/shelters");
  const depots = useApi<any[]>("/api/depots");
  const [speed, setSpeed] = useState("0.05");
  const [log, setLog] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [ev, setEv] = useState<Record<string, string>>({ road: "r_mad_kus", shelter: "4", depot: "1", zone: "kushalnagar", silence: "somwarpet", spike: "6" });
  const call = async (path: string, body: any, label: string) => {
    setBusy(true);
    try { const r = await api<any>(path, { method: "POST", body: JSON.stringify(body) }); setLog((l) => [`${label}: ${(r.changes ?? [r.name ?? "ok"]).join("; ")}`, ...l].slice(0, 12)); sc.reload(); }
    catch (e: any) { setLog((l) => [`${label}: ${e.message}`, ...l]); }
    setBusy(false);
  };
  const d = sc.data;
  const running = d?.active?.running;
  const tl = d?.timeline;
  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.scenario")} sub={t("pages.scenario")} kicker={d ? `T+${d.clock.toFixed(1)} h · ${d.active?.name ?? ""}` : "scenario control"} tone="bg-brand-300" section="scenario.page">
        <button className="btn-pop px-5 py-2.5 text-base" onClick={() => startGuide()}><Clapperboard size={18} aria-hidden />Run guided</button>
        <Explain id="scenario.demo" />
      </PageHeader>
      <div className="grid gap-4 md:grid-cols-3">
        {d?.scenarios.map((s: any) => (
          <motion.button key={s.id} whileHover={{ y: -4, rotate: -0.5 }} disabled={busy}
            onClick={() => call("/api/sim/scenario/start", { scenario: s.id, replay_until: 0, speed: Number(speed) }, `Started ${s.name}`)}
            className={`relative overflow-hidden rounded-3xl border-2 border-ink p-4 text-left shadow-hard ${d.active?.id === s.id ? "bg-lime-300" : "bg-white"}`}>
            <span className="absolute right-3 top-3 h-6 w-6 rounded-full border-2 border-ink" style={{ background: s.colour }} />
            <p className="label">{s.hazard}</p>
            <p className="mega text-2xl">{s.name}</p>
            <p className="mt-1 text-sm font-medium text-ink/70">{s.description}</p>
            <p className="mt-2 text-xs font-extrabold">{d.active?.id === s.id ? "● active — click to restart from T+0" : "start from T+0 →"}</p>
          </motion.button>
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-[1fr_1.2fr]">
        <Panel title="Clock" tone="bg-cobalt-300">
          <div className="flex flex-wrap items-center gap-2">
            <span className="mega text-5xl tabular-nums">T+{(d?.clock ?? 0).toFixed(1)}<span className="text-xl text-ink/50"> h</span></span>
            <span className={`badge ${running ? "bg-lime-400" : "bg-white"}`}>{running ? `playing ×${d.active.speed}` : "paused"}</span>
          </div>
          <div className="mt-3 h-3 overflow-hidden rounded-full border-2 border-ink bg-paper"><div className="h-full bg-brand-500 transition-all" style={{ width: `${tl ? (tl.released / Math.max(1, tl.total)) * 100 : 0}%` }} /></div>
          <p className="mt-1 text-xs font-bold text-ink/60">{tl?.released ?? 0} of {tl?.total ?? 0} timeline events released (scenario runs to T+{tl?.end_t ?? 12} h)</p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {running ? <button className="btn-ghost" onClick={() => call("/api/sim/clock", { action: "pause" }, "Paused")}><Pause size={15} aria-hidden />Pause</button>
              : <button className="btn-primary" onClick={() => call("/api/sim/clock", { action: "play", speed: Number(speed) }, "Playing")}><Play size={15} aria-hidden />Play</button>}
            <button className="btn-ghost" disabled={busy} onClick={() => call("/api/sim/clock", { action: "step", hours: 1 }, "+1 h")}><SkipForward size={15} aria-hidden />+1 h</button>
            <button className="btn-ghost" disabled={busy} onClick={() => call("/api/sim/clock", { action: "step", hours: 4 }, "+4 h")}><FastForward size={15} aria-hidden />+4 h</button>
            <select className="input !w-auto !py-1" value={speed} onChange={(e) => { setSpeed(e.target.value); if (running) call("/api/sim/clock", { action: "speed", speed: Number(e.target.value) }, "Speed"); }} aria-label="Speed">
              {SPEEDS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
            <button className="btn-ghost" disabled={busy} onClick={() => call("/api/sim/scenario/start", { scenario: d?.active?.id ?? "kodagu_flood", replay_until: 12 }, "Replayed to T+12")}><RotateCcw size={15} aria-hidden />Reset to full T+12</button>
          </div>
          <p className="label mt-4">Coming next on the timeline</p>
          <ul className="mt-1 space-y-1 text-xs">{(tl?.next ?? []).map((e: any, i: number) => <li key={i} className="rounded-lg bg-paper px-2 py-1"><b className="font-mono">T+{e.t}</b> · {e.kind} · {e.what}</li>)}</ul>
        </Panel>
        <Panel title={<span className="flex items-center gap-2"><Zap size={18} aria-hidden />What if…?</span>} tone="bg-pink-400">
          <div className="grid gap-2 text-sm">
            {[
              ["Close a road", <select key="r" className="input !py-1" value={ev.road} onChange={(e) => setEv({ ...ev, road: e.target.value })}>{roads.data?.map((r) => <option key={r.code} value={r.code}>{r.name} ({r.status})</option>)}</select>,
                () => call("/api/sim/event", { type: "close_road", params: { road: ev.road } }, "Close road"), () => call("/api/sim/event", { type: "reopen_road", params: { road: ev.road } }, "Reopen road"), "reopen"],
              ["Flood a shelter", <select key="s" className="input !py-1" value={ev.shelter} onChange={(e) => setEv({ ...ev, shelter: e.target.value })}>{shelters.data?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select>,
                () => call("/api/sim/event", { type: "flood_shelter", params: { shelter_id: Number(ev.shelter) } }, "Flood shelter")],
              ["Drop inventory 50%", <select key="d" className="input !py-1" value={ev.depot} onChange={(e) => setEv({ ...ev, depot: e.target.value })}>{depots.data?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select>,
                () => call("/api/sim/event", { type: "drop_inventory", params: { depot_id: Number(ev.depot), fraction: 0.5 } }, "Drop inventory")],
              ["Cut internet", <select key="z" className="input !py-1" value={ev.zone} onChange={(e) => setEv({ ...ev, zone: e.target.value })}>{zones.data?.map((z) => <option key={z.code} value={z.code}>{z.name}{z.internet_down ? " (down)" : ""}</option>)}</select>,
                () => call("/api/sim/event", { type: "cut_internet", params: { zone: ev.zone } }, "Cut internet"), () => call("/api/sim/event", { type: "restore_internet", params: { zone: ev.zone } }, "Restore internet"), "restore"],
              ["Spike reports", <input key="n" className="input !py-1" type="number" min={1} max={20} value={ev.spike} onChange={(e) => setEv({ ...ev, spike: e.target.value })} />,
                () => call("/api/sim/event", { type: "spike_reports", params: { count: Number(ev.spike) } }, "Spike reports")],
              ["Silence a village", <select key="v" className="input !py-1" value={ev.silence} onChange={(e) => setEv({ ...ev, silence: e.target.value })}>{zones.data?.map((z) => <option key={z.code} value={z.code}>{z.name}</option>)}</select>,
                () => call("/api/sim/event", { type: "silence_village", params: { zone: ev.silence } }, "Silence village")],
            ].map(([label, control, go, undo, undoLabel]: any) => (
              <div key={label} className="grid grid-cols-[130px_1fr_auto] items-center gap-2">
                <span className="font-extrabold">{label}</span>{control}
                <span className="flex gap-1"><button className="btn-primary !py-1" disabled={busy} onClick={go}><Flame size={13} aria-hidden />go</button>{undo && <button className="btn-ghost !py-1" disabled={busy} onClick={undo}>{undoLabel}</button>}</span>
              </div>
            ))}
          </div>
          {!!log.length && <ul className="mt-3 space-y-1 text-xs">{log.map((l, i) => <li key={i} className="rounded-lg bg-paper px-2 py-1 font-semibold">{l}</li>)}</ul>}
        </Panel>
      </div>
    </div>
  );
}
