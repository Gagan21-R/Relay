// Disaster selector + profile. One configurable architecture: changing the disaster changes severity factors,
// resource standards, map overlay style and recommendations (all served by /api/disasters).
import { useState } from "react";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";

export type DisasterProfile = {
  code: string; name: string; gdacs: string | null; overlay: { label: string; colour: string; fill: string };
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
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  if (!data) return null;
  const change = async (code: string) => {
    setBusy(true); setErr(null);
    try { await api("/api/disasters/active", { method: "POST", body: JSON.stringify({ code }) }); await reload(); }
    catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  };
  return (
    <label className="flex items-center gap-1.5 rounded-xl border-2 border-ink bg-white px-2 py-0.5 shadow-hard-sm">
      <span className="text-[11px] font-extrabold uppercase tracking-wider">disaster</span>
      <select value={data.active} disabled={busy} onChange={(e) => change(e.target.value)} aria-label="Active disaster type"
        className="rounded-lg bg-transparent py-0.5 text-xs font-extrabold focus:outline-none">
        {data.items.map((d) => <option key={d.code} value={d.code}>{DISASTER_ICON[d.code]} {d.name}</option>)}
      </select>
      {err && <span className="badge bg-pink-300">{err}</span>}
    </label>
  );
}

export function DisasterProfilePanel({ compact = false }: { compact?: boolean }) {
  const d = useActiveDisaster();
  if (!d) return null;
  const top = Object.entries(d.life_threat).sort((a, b) => b[1] - a[1]).slice(0, 4);
  return (
    <div className="space-y-2 text-sm">
      <p className="font-bold"><span className="mr-1 text-lg">{DISASTER_ICON[d.code]}</span>{d.name} profile · overlay “{d.overlay.label}”
        <span className="ml-2 inline-block h-3 w-6 rounded border-2 border-ink align-middle" style={{ background: d.overlay.fill }} /></p>
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
