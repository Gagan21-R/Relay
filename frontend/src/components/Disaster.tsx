// Disaster selector + profile. One configurable architecture: changing the disaster changes severity factors,
// resource standards, map overlay style and recommendations (all served by /api/disasters).
import { useState } from "react";
import { Play, X } from "lucide-react";
import { api } from "../services/api";
import { startGuide } from "./Guide";
import { useApi } from "../hooks/useApi";

export type DisasterProfile = {
  code: string; name: string; gdacs: string | null; overlay: { label: string; colour: string; fill: number };
  life_threat: Record<string, number>; per_person_day: Record<string, number>; fleet: string[]; recommendations: string[];
  indicators_sample: string[];
};
export type DisasterList = { active: string; items: DisasterProfile[] };

export const DISASTER_ICON: Record<string, string> = {
  flood: "🌊", cyclone: "🌀", earthquake: "🫨", landslide: "⛰️", wildfire: "🔥", drought: "🏜️", heatwave: "🌡️", tsunami: "🌊", industrial: "☣️",
};

export function useDisasters() {
  return useApi<DisasterList>("/api/disasters", ["refresh", "sim"], 300);
}

export function useActiveDisaster(): DisasterProfile | null {
  const { data } = useDisasters();
  return data?.items.find((d) => d.code === data.active) ?? null;
}

export function DisasterSelector() {
  const { data, reload } = useDisasters();
  const [pick, setPick] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  if (!data) return null;
  const profileOnly = async (code: string) => {
    setErr(null);
    try { await api("/api/disasters/active", { method: "POST", body: JSON.stringify({ code }) }); await reload(); setPick(null); }
    catch (e: any) { setErr(e.message); }
  };
  return (
    <>
      <label className="flex items-center gap-1.5 rounded-xl border-2 border-ink bg-white px-2 py-0.5 shadow-hard-sm">
        <span className="text-[11px] font-extrabold uppercase tracking-wider">disaster</span>
        <select value={data.active} onChange={(e) => setPick(e.target.value)} aria-label="Choose a disaster and where to run it"
          className="rounded-lg bg-transparent py-0.5 text-xs font-extrabold focus:outline-none">
          {data.items.map((d) => <option key={d.code} value={d.code}>{DISASTER_ICON[d.code]} {d.name}</option>)}
        </select>
        {err && <span className="badge bg-pink-300">{err}</span>}
      </label>
      {pick && <ScenarioPicker disaster={pick} name={data.items.find((d) => d.code === pick)?.name ?? pick}
        onClose={() => setPick(null)} onProfileOnly={() => profileOnly(pick)} />}
    </>
  );
}

/** Where should this disaster run? Every scenario of that type across India; choosing one runs the full model, guided. */
export function ScenarioPicker({ disaster, name, onClose, onProfileOnly }: { disaster: string; name: string; onClose: () => void; onProfileOnly: () => void }) {
  const { data } = useApi<any>("/api/lab/scenarios");
  const list = (data?.scenarios ?? []).filter((s: any) => s.disaster === disaster);
  const go = (id: string) => { onClose(); startGuide(id); };
  return (
    <div className="fixed inset-0 z-[1300] grid place-items-center bg-ink/50 p-4" role="dialog" aria-modal="true" aria-label={`Run a ${name} scenario`} onClick={onClose}>
      <div className="max-h-[80vh] w-[min(640px,100%)] overflow-y-auto rounded-3xl border-2 border-ink bg-white p-5 shadow-hard-lg" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-2"><span className="text-2xl">{DISASTER_ICON[disaster]}</span>
          <h2 className="mega text-2xl">Run a {name.toLowerCase()} scenario</h2>
          <button className="btn-ghost ml-auto !p-1" onClick={onClose} aria-label="Close"><X size={16} /></button></div>
        <p className="mt-1 text-sm text-ink/70">Pick where it happens. RELAY loads that place (roads, shelters, hospitals, depots, volunteers), centres the map and runs every agent, step by step, stopping where a Duty Officer must decide.</p>
        <ul className="mt-3 space-y-1.5">
          {list.map((s: any) => (
            <li key={s.id}>
              <button onClick={() => go(s.id)} className="flex w-full flex-wrap items-center gap-2 rounded-2xl border-2 border-ink bg-paper px-3 py-2 text-left text-sm hover:-translate-y-0.5 hover:shadow-hard-sm">
                <span className="font-extrabold">{s.name}</span>
                <span className="badge bg-white">{s.state}</span>
                <span className={`badge ${s.difficulty === "advanced" ? "bg-pink-300" : s.difficulty === "intermediate" ? "bg-sun-300" : "bg-mint-300"}`}>{s.difficulty}</span>
                <span className="ml-auto flex items-center gap-1 text-xs font-extrabold text-brand-600"><Play size={13} aria-hidden />Run guided</span>
              </button>
            </li>))}
          {!list.length && <li className="text-sm text-ink/60">Loading scenarios…</li>}
        </ul>
        <button className="btn-ghost mt-3 text-xs" onClick={onProfileOnly}>Only switch the planning profile for the current place</button>
      </div>
    </div>
  );
}

export function DisasterProfilePanel({ compact = false }: { compact?: boolean }) {
  const d = useActiveDisaster();
  if (!d) return null;
  const top = Object.entries(d.life_threat).sort((a, b) => b[1] - a[1]).slice(0, 4);
  return (
    <div className="space-y-2 text-sm">
      <p className="font-bold"><span className="mr-1 text-lg">{DISASTER_ICON[d.code]}</span>{d.name} profile · overlay “{d.overlay.label}”
        <span className="ml-2 inline-block h-3 w-6 rounded border-2 border-ink align-middle" style={{ background: d.overlay.colour, opacity: 0.4 + d.overlay.fill }} /></p>
      <div className="flex flex-wrap gap-1">{top.map(([k, v]) => <span key={k} className="badge bg-white">{k} threat {v.toFixed(2)}</span>)}</div>
      {!compact && <p className="text-xs font-semibold text-ink/70">Per person per day: {Object.entries(d.per_person_day).map(([k, v]) => `${k.replace(/_/g, " ")} ${v}`).join(" · ")}</p>}
      {!compact && <p className="text-xs font-semibold text-ink/70">Fleet: {d.fleet.join(", ")}</p>}
      <ul className="list-disc space-y-0.5 pl-5 text-xs font-semibold">{d.recommendations.slice(0, compact ? 3 : 8).map((r, i) => <li key={i}>{r}</li>)}</ul>
      <p className="text-[11px] text-ink/50">Profiles are planning defaults written for this prototype (based on Sphere-style standards), not official guidance.</p>
    </div>
  );
}

export type GdacsItem = { id: string; type: string; name: string; lat: number; lng: number; level: string; description: string; data: "live" | "stale" | "fallback" };
export function useGdacs() {
  return useApi<{ status: "live" | "stale" | "fallback"; reason?: string; items: GdacsItem[] }>("/api/live/gdacs", [], 0);
}
export const DATA_BADGE: Record<string, string> = { live: "bg-mint-400", stale: "bg-sun-400", fallback: "bg-pink-300", simulated: "bg-cobalt-300" };
