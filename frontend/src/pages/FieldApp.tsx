// Mobile field reporting that works offline: reports are queued on the device (GPS + time captured when written)
// and synced when the connection returns. Sync is idempotent (client_id), so a retry never duplicates a report.
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { CloudOff, CloudUpload, LocateFixed, Wifi, WifiOff } from "lucide-react";
import { PageHeader } from "../components/Layout";
import { Empty, Panel } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";
import { SimState, Zone } from "../services/types";

type Queued = { client_id: string; text: string; team: string; lat?: number; lng?: number; captured_at: string; captured_sim_time?: number; queued_offline: boolean };
const KEY = "relay.fieldQueue";
const read = (): Queued[] => { try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch { return []; } };
const write = (q: Queued[]) => { try { localStorage.setItem(KEY, JSON.stringify(q)); } catch { /* storage unavailable */ } };

export default function FieldApp() {
  const { t } = useTranslation();
  const zones = useApi<Zone[]>("/api/zones");
  const sim = useApi<SimState>("/api/state", ["sim"]);
  const [queue, setQueue] = useState<Queued[]>(read);
  const [text, setText] = useState("");
  const [team, setTeam] = useState(() => { try { return localStorage.getItem("relay.fieldTeam") || "Volunteer team A"; } catch { return "Volunteer team A"; } });
  const [where, setWhere] = useState<{ lat?: number; lng?: number; label: string }>({ label: "no location yet" });
  const [noSignal, setNoSignal] = useState(false);
  const [online, setOnline] = useState(navigator.onLine);
  const [log, setLog] = useState<string[]>([]);
  useEffect(() => {
    const on = () => setOnline(true), off = () => setOnline(false);
    window.addEventListener("online", on); window.addEventListener("offline", off);
    return () => { window.removeEventListener("online", on); window.removeEventListener("offline", off); };
  }, []);
  const connected = online && !noSignal;

  const sync = useCallback(async () => {
    const left: Queued[] = [];
    for (const q of read()) {
      try {
        const r = await api<any>("/api/intake/field", { method: "POST", body: JSON.stringify(q) });
        setLog((l) => [`${r.duplicate ? "already had" : "synced"} ${r.report.ref}: ${q.text.slice(0, 40)}`, ...l].slice(0, 8));
      } catch { left.push(q); }
    }
    write(left); setQueue(left);
  }, []);
  useEffect(() => { if (connected && read().length) sync(); }, [connected, sync]);

  const gps = () => navigator.geolocation?.getCurrentPosition(
    (p) => setWhere({ lat: p.coords.latitude, lng: p.coords.longitude, label: `GPS ${p.coords.latitude.toFixed(4)}, ${p.coords.longitude.toFixed(4)}` }),
    () => setWhere({ label: "GPS unavailable: pick a zone" }));
  const save = () => {
    const q: Queued = { client_id: `${team.replace(/\W/g, "").slice(0, 10)}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`, text, team,
      lat: where.lat, lng: where.lng, captured_at: new Date().toISOString(), captured_sim_time: sim.data?.clock, queued_offline: !connected };
    const next = [...read(), q];
    write(next); setQueue(next); setText("");
    try { localStorage.setItem("relay.fieldTeam", team); } catch { /* ignore */ }
    if (connected) sync();
  };

  return (
    <div className="mx-auto max-w-xl space-y-4">
      <PageHeader title={t("nav.field")} sub={t("pages.field")} section="field.page" />
      <div className={`flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium ${connected ? "bg-mint-300 text-ink" : "bg-sun-300 text-ink"}`} role="status">
        {connected ? <Wifi size={16} aria-hidden /> : <WifiOff size={16} aria-hidden />}
        {connected ? "Online — reports send immediately" : "No signal — reports are saved on this device"}
        <label className="ml-auto flex items-center gap-1.5 text-xs"><input type="checkbox" checked={noSignal} onChange={(e) => setNoSignal(e.target.checked)} />simulate no signal</label>
      </div>
      <Panel title="New field report">
        <input className="mb-2 w-full input text-sm" value={team} onChange={(e) => setTeam(e.target.value)} aria-label="Team name" />
        <textarea className="input !p-3 text-[15px]" rows={4} value={text} onChange={(e) => setText(e.target.value)} placeholder="What do you see? Any language. e.g. Napoklu camp: 240 people, water for 1 day" />
        <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
          <button className="btn-ghost" onClick={gps}><LocateFixed size={14} aria-hidden />Use GPS</button>
          <select className="input !w-auto !py-1.5" aria-label="Or pick a zone"
            onChange={(e) => { const z = zones.data?.find((x) => x.code === e.target.value); if (z) setWhere({ lat: z.lat, lng: z.lng, label: `${z.name} (zone centre)` }); }}>
            <option value="">or pick a zone…</option>
            {zones.data?.map((z) => <option key={z.code} value={z.code}>{z.name}</option>)}
          </select>
          <span className="text-xs text-ink/60">{where.label}</span>
        </div>
        <button className="btn-primary mt-3 w-full justify-center py-2.5 text-base" disabled={text.trim().length < 3} onClick={save}>
          {connected ? <CloudUpload size={18} aria-hidden /> : <CloudOff size={18} aria-hidden />}{connected ? "Send report" : "Save offline"}
        </button>
      </Panel>
      <Panel title={`Waiting to sync (${queue.length})`} actions={<button className="btn-ghost" disabled={!connected || !queue.length} onClick={sync}>Sync now</button>}>
        {!queue.length ? <Empty>Nothing waiting.</Empty> : (
          <ul className="space-y-1.5 text-sm">{queue.map((q) => <li key={q.client_id} className="rounded-lg bg-sun-300 px-3 py-2">{q.text}<p className="text-[11px] text-ink/60">captured {new Date(q.captured_at).toLocaleTimeString()} · {q.lat ? "with location" : "no location"}</p></li>)}</ul>
        )}
        {!!log.length && <ul className="mt-2 space-y-0.5 text-xs text-ink">{log.map((l, i) => <li key={i}>✓ {l}</li>)}</ul>}
      </Panel>
    </div>
  );
}
