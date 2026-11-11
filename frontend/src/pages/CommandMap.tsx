// The Command Map: the live picture. Every layer refetches on WebSocket events; reports pulse where they land;
// trucks move along their routes by the simulated clock; click anything for its evidence.
import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { AnimatePresence, motion } from "framer-motion";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Circle, CircleMarker, MapContainer, Marker, Polygon, Polyline, Popup, TileLayer, Tooltip, useMap } from "react-leaflet";
import { Layers, X } from "lucide-react";
import { PageHeader } from "../components/Layout";
import { Explain } from "../components/Assistant";
import { IncidentDetail } from "./Incidents";
import { Breakdown, ConfidenceBadge, LANG_NAMES, Panel, PRIORITY_STYLE, simTime } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { LiveEvent, useLiveEvents } from "../hooks/useLive";
import { Incident, SimState } from "../services/types";
import { DATA_BADGE, DISASTER_ICON, DisasterProfilePanel, useActiveDisaster, useGdacs } from "../components/Disaster";
import { startGuide } from "../components/Guide";

export const KODAGU_CENTER: [number, number] = [12.42, 75.78];
const PCOL: Record<string, string> = { P1: "#FF3D1F", P2: "#E07A3A", P3: "#C9A94C", P4: "#5A4FD6" };
const SCOL: Record<string, string> = { open: "#5F8F64", full: "#C9A94C", inaccessible: "#FF3D1F", unconfirmed: "#D9895B", closed: "#0B0B0C" };
const LAYERS = ["incidents", "shelters", "depots", "routes", "flood", "blackout", "roads", "pulses", "hospitals", "gdacs", "scenarios"] as const;
type LayerKey = typeof LAYERS[number];
type Sel = { kind: "incident" | "shelter" | "zone" | "depot"; id: number } | null;

const shelterIcon = (status: string, name: string) => L.divIcon({ className: "relay-pin", iconSize: [26, 26], iconAnchor: [13, 13],
  html: `<div title="${name}" style="width:24px;height:24px;border:2.5px solid #0B0B0C;border-radius:0;background:${SCOL[status] ?? "#fff"};box-shadow:2px 2px 0 #0B0B0C;display:grid;place-items:center;font:700 12px 'JetBrains Mono',monospace;color:#0B0B0C">⌂</div>` });
const depotIcon = L.divIcon({ className: "relay-pin", iconSize: [26, 26], iconAnchor: [13, 13],
  html: `<div style="width:20px;height:20px;transform:rotate(45deg);border:2.5px solid #0B0B0C;background:#0B0B0C;box-shadow:2px 2px 0 #0B0B0C"></div>` });
const truckIcon = (overdue: boolean) => L.divIcon({ className: "relay-pin", iconSize: [30, 22], iconAnchor: [15, 11],
  html: `<div style="padding:1px 4px;border:2px solid #0B0B0C;border-radius:0;background:${overdue ? "#FF3D1F" : "#F6F4EF"};font:700 11px 'JetBrains Mono',monospace;box-shadow:2px 2px 0 #0B0B0C">🚚</div>` });

function along(points: number[][], f: number): [number, number] {
  if (points.length < 2) return points[0] as [number, number];
  const seg: number[] = [];
  let total = 0;
  for (let i = 1; i < points.length; i++) { const d = Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]); seg.push(d); total += d; }
  let goal = Math.max(0, Math.min(1, f)) * total;
  for (let i = 0; i < seg.length; i++) {
    if (goal <= seg[i]) { const t = seg[i] ? goal / seg[i] : 0; return [points[i][0] + (points[i + 1][0] - points[i][0]) * t, points[i][1] + (points[i + 1][1] - points[i][1]) * t]; }
    goal -= seg[i];
  }
  return points[points.length - 1] as [number, number];
}

function HatchDefs() {
  const map = useMap();
  useEffect(() => {
    const svg = map.getPanes().overlayPane.querySelector("svg");
    if (svg && !svg.querySelector("#relay-hatch")) {
      const ns = "http://www.w3.org/2000/svg";
      const defs = document.createElementNS(ns, "defs");
      defs.innerHTML = `<pattern id="relay-hatch" patternUnits="userSpaceOnUse" width="10" height="10" patternTransform="rotate(45)"><rect width="10" height="10" fill="rgba(225,29,72,.12)"/><line x1="0" y1="0" x2="0" y2="10" stroke="#FF3D1F" stroke-width="4"/></pattern>`;
      svg.prepend(defs);
    }
  });
  return null;
}

function ScenarioView({ center, zoom }: { center?: [number, number]; zoom?: number }) {
  // auto-zoom when a scenario (or the Scenario Lab) changes the world
  const map = useMap();
  const key = center ? center.join(",") : "";
  useEffect(() => { if (center) map.flyTo(center, zoom ?? 10, { duration: 0.8 }); }, [key]); // eslint-disable-line react-hooks/exhaustive-deps
  return null;
}

function IndiaView({ go }: { go: number }) {
  const map = useMap();
  useEffect(() => { if (go) map.flyTo([22.6, 80.5], 5, { duration: 0.9 }); }, [go, map]);
  return null;
}

function FlyTo({ target }: { target: [number, number] | null }) {
  const map = useMap();
  useEffect(() => { if (target) map.flyTo(target, Math.max(map.getZoom(), 12), { duration: 0.6 }); }, [target, map]);
  return null;
}

const TABS = [["priorities", "Priorities"], ["arriving", "Arriving"], ["disaster", "Disaster"], ["volunteers", "Volunteers"], ["agents", "Agents"]] as const;

type Pulse = { id: number; lat: number; lng: number; lang?: string; channel: string; born: number };

export default function CommandMap() {
  const { t } = useTranslation();
  const [on, setOn] = useState<Record<LayerKey, boolean>>(() => {
    try { return { ...Object.fromEntries(LAYERS.map((l) => [l, true])), ...JSON.parse(localStorage.getItem("relay.layers") || "{}") }; }
    catch { return Object.fromEntries(LAYERS.map((l) => [l, true])) as any; }
  });
  useEffect(() => { try { localStorage.setItem("relay.layers", JSON.stringify(on)); } catch { /* ignore */ } }, [on]);
  const incidents = useApi<Incident[]>("/api/incidents", ["incident"], 500);
  const shelters = useApi<any[]>("/api/shelters", ["shelter", "inventory"], 600);
  const depots = useApi<any[]>("/api/depots", ["inventory"], 800);
  const dispatches = useApi<any[]>("/api/dispatches", ["dispatch"], 400);
  const sim = useApi<SimState>("/api/state", ["sim", "signal", "network"], 300);
  const zones = useApi<any[]>("/api/zones/blackout", ["zone", "signal", "recon"], 800);
  const roads = useApi<any[]>("/api/roads", ["signal", "sim"], 600);
  const hospitals = useApi<any[]>("/api/hospitals", ["sim"], 800);
  const gdacs = useGdacs();
  const lab = useApi<any>("/api/lab/scenarios");
  const [india, setIndia] = useState(0);
  const dis = useActiveDisaster();
  const ov = dis?.overlay ?? { label: "flood extent", colour: "#5A4FD6", fill: 0.35 };
  const [sel, setSel] = useState<Sel>(null);
  const [fly, setFly] = useState<[number, number] | null>(null);
  const [pulses, setPulses] = useState<Pulse[]>([]);
  const [feed, setFeed] = useState<any[]>([]);
  const [tab, setTab] = useState<string>("priorities");
  const [agentLog, setAgentLog] = useState<any[]>([]);
  useLiveEvents(useCallback((e: LiveEvent) => setAgentLog((l) => [e.data, ...l].slice(0, 12)), []), ["agent_message"]);
  const vols = useApi<any[]>("/api/volunteers", ["dispatch", "refresh"], 800);
  const onReport = useCallback((e: LiveEvent) => {
    const r = e.data;
    setFeed((f) => [r, ...f.filter((x) => x.id !== r.id)].slice(0, 6));
    if (r.lat != null && r.status !== "blocked") setPulses((p) => [...p.filter((x) => Date.now() - x.born < 9000), { id: r.id, lat: r.lat, lng: r.lng, lang: r.original_language, channel: r.channel, born: Date.now() }]);
  }, []);
  useLiveEvents(onReport, ["report"]);
  const [, tick] = useState(0);
  useEffect(() => { const i = window.setInterval(() => tick((n) => n + 1), 1500); return () => window.clearInterval(i); }, []);
  const clock = sim.data?.clock ?? 0;
  const active = (dispatches.data ?? []).filter((d) => ["dispatched", "delivered"].includes(d.status));
  const silent = (zones.data ?? []).filter((z) => z.blackout_flag);
  const counts = useMemo(() => {
    const inc = incidents.data ?? [];
    return { p1: inc.filter((i) => i.priority_score >= 70).length, fv: inc.filter((i) => i.fast_verify).length, incidents: inc.filter((i) => i.confidence_level !== "false").length };
  }, [incidents.data]);
  const pick = (s: Sel, at?: [number, number]) => { setSel(s); if (at) setFly(at); };

  return (
    <div className="space-y-4">
      <PageHeader title={t("map.title")} sub={sim.data?.scenario?.world && sim.data.scenario.world !== "kodagu" ? `${sim.data.scenario.name} · ${sim.data.scenario.state}. Real OpenStreetMap basemap; every report, shelter, hospital and stock count is synthetic.` : t("map.sub")} kicker={`T+${clock.toFixed(1)} h · live`} tone="bg-cobalt-300" section="map.page">
        <span className="sticker bg-sun-300">{t("common.synthetic")}</span>
      </PageHeader>
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="flex items-center gap-1 text-xs font-extrabold uppercase tracking-wider"><Layers size={14} aria-hidden />layers</span>
        {LAYERS.map((l) => (
          <button key={l} onClick={() => setOn({ ...on, [l]: !on[l] })} aria-pressed={on[l]}
            className={`border-[1.5px] border-ink px-2 py-0.5 font-mono text-[10.5px] font-bold uppercase transition-all ${on[l] ? "bg-ink text-bone" : "bg-bone text-ink/50 line-through"}`}>{l}</button>
        ))}
        <Explain id="map.layers" />
        <span className="ml-auto flex flex-wrap gap-1.5">
          <span className="badge bg-pink-400">{counts.p1} P1</span>
          <span className="badge bg-tangerine-300">{counts.fv} fast verify</span>
          <span className="badge bg-lime-300">{active.length} trucks moving</span>
          <span className={`badge ${silent.length ? "bg-ink text-white" : "bg-white"}`}>{silent.length} silent zone(s)</span>
          {sim.data?.network_down?.length ? <span className="badge bg-pink-500 text-white">internet down: {sim.data.network_down.join(", ")}</span> : null}
        </span>
      </div>
      <div className="grid gap-4 xl:grid-cols-[1fr_400px]">
        <div className="relative h-[72vh] min-h-[460px] overflow-hidden rounded-3xl border-2 border-ink shadow-hard-lg">
          <MapContainer center={(sim.data?.scenario?.center as [number, number]) ?? KODAGU_CENTER} zoom={sim.data?.scenario?.zoom ?? 10} style={{ height: "100%", width: "100%" }}>
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" maxZoom={18} attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors · synthetic scenario overlay' />
            <HatchDefs />
            <FlyTo target={fly} />
            <ScenarioView center={sim.data?.scenario?.center} zoom={sim.data?.scenario?.zoom} />
            <IndiaView go={india} />
            {on.scenarios && (lab.data?.scenarios ?? []).filter((sc: any) => Array.isArray(sc.center) && sc.center.length === 2).map((sc: any) => {
              const current = sim.data?.scenario?.id === sc.id;
              return (
                <CircleMarker key={`sc-${sc.id}`} center={sc.center} radius={current ? 13 : 10}
                  pathOptions={{ color: "#0B0B0C", weight: current ? 4 : 2, fillColor: sc.colour ?? "#0B0B0C", fillOpacity: current ? 0.35 : 0.8 }}>
                  <Tooltip>{DISASTER_ICON[sc.disaster]} {sc.name} · {sc.difficulty}{current ? " · running now" : " · click to run"}</Tooltip>
                  <Popup>
                    <div className="space-y-1 text-xs">
                      <p className="text-sm font-extrabold">{DISASTER_ICON[sc.disaster]} {sc.name}</p>
                      <p>{sc.state} · {sc.difficulty} · {sc.region.slice(0, 3).join(", ")}</p>
                      <p className="text-ink/70">{sc.description}</p>
                      <button className="btn-pop !px-2 !py-1 !text-xs" onClick={() => startGuide(sc.id)}>{current ? "Restart guided run" : "Run this scenario (guided)"}</button>
                    </div>
                  </Popup>
                </CircleMarker>);
            })}
            {on.flood && (sim.data?.flood_extent ?? []).map((p, i) => (
              <Polygon key={`f${i}`} positions={p as [number, number][]} pathOptions={{ color: ov.colour, weight: 1.5, fillColor: ov.colour, fillOpacity: ov.fill, className: "flood-poly" }}>
                <Tooltip sticky>{dis?.name ?? "Hazard"} · {ov.label} v{sim.data?.flood_version} (simulated satellite-style product)</Tooltip>
              </Polygon>
            ))}
            {on.blackout && silent.map((z) => (
              <Polygon key={`b${z.id}`} positions={z.polygon} eventHandlers={{ click: () => pick({ kind: "zone", id: z.id }) }}
                pathOptions={{ color: "#FF3D1F", weight: 3, dashArray: "8 6", fillOpacity: 1, className: "blackout-hatch" }}>
                <Tooltip sticky>SILENT · {z.name} · risk {Math.round(z.blackout_score * 100)}% · click for the breakdown</Tooltip>
              </Polygon>
            ))}
            {on.roads && (roads.data ?? []).map((r) => (
              <Polyline key={r.code} positions={r.points} pathOptions={{ color: r.status === "open" ? "#0B0B0C" : "#FF3D1F", weight: r.status === "open" ? 2 : 4, opacity: r.status === "open" ? 0.35 : 0.9, dashArray: r.status === "open" ? undefined : "4 6" }}>
                <Tooltip sticky>{r.name} · {r.status}{r.status !== "open" ? ` (${r.status_source})` : ""}</Tooltip>
              </Polyline>
            ))}
            {on.routes && active.map((d) => {
              const f = (clock - (d.dispatched_at ?? clock)) / Math.max(0.01, (d.eta ?? clock) - (d.dispatched_at ?? clock));
              const pos = d.status === "delivered" ? d.route[d.route.length - 1] : along(d.route, f);
              return (
                <span key={`d${d.id}`}>
                  <Polyline positions={d.route} pathOptions={{ color: "#0B0B0C", weight: 4, opacity: 0.8, dashArray: d.status === "dispatched" ? "8 8" : undefined }} />
                  <Marker position={pos} icon={truckIcon(d.overdue)}><Tooltip>D-{d.id} → {d.to_name} · {d.status.replace("_", " ")} · ETA {simTime(d.eta)}</Tooltip></Marker>
                </span>
              );
            })}
            {on.depots && (depots.data ?? []).map((d) => (
              <Marker key={`dp${d.id}`} position={[d.lat, d.lng]} icon={depotIcon} eventHandlers={{ click: () => pick({ kind: "depot", id: d.id }) }}><Tooltip>{d.name}</Tooltip></Marker>
            ))}
            {on.shelters && (shelters.data ?? []).map((s) => (
              <Marker key={`s${s.id}`} position={[s.lat, s.lng]} icon={shelterIcon(s.status, s.name)} eventHandlers={{ click: () => pick({ kind: "shelter", id: s.id }, [s.lat, s.lng]) }}>
                <Tooltip>{s.name} · {s.status} · {s.occupancy}/{s.capacity}</Tooltip>
              </Marker>
            ))}
            {on.incidents && (incidents.data ?? []).filter((i) => i.lat != null).map((i) => {
              const p = PRIORITY_STYLE(i.priority_score);
              const isFalse = i.confidence_level === "false";
              return (
                <CircleMarker key={`i${i.id}`} center={[i.lat!, i.lng!]} radius={7 + Math.min(10, Math.log2((i.people_affected || 1) + 1) * 1.6)}
                  eventHandlers={{ click: () => pick({ kind: "incident", id: i.id }, [i.lat!, i.lng!]) }}
                  pathOptions={{ color: "#0B0B0C", weight: i.confidence_level === "verified" ? 3 : 2, dashArray: ["unverified", "disputed"].includes(i.confidence_level) ? "3 4" : undefined,
                    fillColor: isFalse ? "#9CA3AF" : PCOL[p.label], fillOpacity: isFalse ? 0.4 : 0.85 }}>
                  <Tooltip>{p.label} · {i.title} · {i.confidence_level}{i.fast_verify ? " · FAST VERIFY" : ""}</Tooltip>
                </CircleMarker>
              );
            })}
            {on.hospitals && (hospitals.data ?? []).map((h) => (
              <CircleMarker key={`h${h.id}`} center={[h.lat, h.lng]} radius={7} pathOptions={{ color: "#0B0B0C", weight: 2, fillColor: "#fff", fillOpacity: 1 }}>
                <Tooltip>✚ {h.name} · {h.beds ?? "?"} beds · {h.status} (synthetic)</Tooltip>
              </CircleMarker>
            ))}
            {on.gdacs && (gdacs.data?.items ?? []).filter((g) => g.lat != null).map((g) => (
              <CircleMarker key={g.id} center={[g.lat, g.lng]} radius={11} pathOptions={{ color: "#0B0B0C", weight: 2, dashArray: g.data === "live" ? undefined : "2 4", fillColor: g.level === "Red" ? "#FF3D1F" : g.level === "Orange" ? "#E07A3A" : "#5F8F64", fillOpacity: 0.55 }}>
                <Tooltip>GDACS {g.type} · {g.name} · {g.level} · <b>{g.data.toUpperCase()}</b>{g.data === "fallback" ? " (illustrative sample, not a real alert)" : ""}</Tooltip>
              </CircleMarker>
            ))}
            {on.pulses && pulses.filter((p) => Date.now() - p.born < 9000).map((p) => (
              <Circle key={`p${p.id}-${p.born}`} center={[p.lat, p.lng]} radius={900} pathOptions={{ color: "#FF3D1F", weight: 3, fillOpacity: 0.15, className: "pulse-ring" }}>
                <Tooltip permanent direction="top">{p.channel} · {LANG_NAMES[p.lang ?? ""] ?? p.lang}</Tooltip>
              </Circle>
            ))}
          </MapContainer>
          <button className="btn-pop absolute right-3 top-3 z-[500] !px-3 !py-1.5 !text-xs" onClick={() => { setOn({ ...on, scenarios: true }); setIndia((x) => x + 1); }}>
            🇮🇳 All of India · pick a scenario
          </button>
          <div className="pointer-events-none absolute bottom-3 left-3 z-[500] rounded-2xl border-2 border-ink bg-white/95 p-2.5 text-[11px] font-bold shadow-hard-sm">
            <p className="mb-1 font-extrabold uppercase tracking-wider">legend</p>
            <p><span style={{ color: PCOL.P1 }}>●</span> P1 <span style={{ color: PCOL.P2 }}>●</span> P2 <span style={{ color: PCOL.P3 }}>●</span> P3 <span style={{ color: PCOL.P4 }}>●</span> P4 · thick = verified · dashed = unverified · grey = false</p>
            <p>⌂ shelter (green open · amber full · red inaccessible) · ◆ depot · 🚚 delivery · <span style={{ color: ov.colour }}>▬</span> {ov.label} · ✚ hospital · ◯ GDACS ({gdacs.data?.status ?? "…"}) · <span className="text-p1">▨</span> silent zone</p>
          </div>
        </div>
        <div className="space-y-4">
          <AnimatePresence mode="wait">
            {sel ? (
              <motion.div key={`${sel.kind}${sel.id}`} initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 30 }}>
                <div className="mb-2 flex items-center gap-2"><Explain id="map.panel" /><button className="btn-ghost ml-auto !p-1" onClick={() => setSel(null)} aria-label="Close"><X size={15} /></button></div>
                {sel.kind === "incident" && <IncidentDetail id={sel.id} />}
                {sel.kind === "zone" && (() => { const z = (zones.data ?? []).find((x) => x.id === sel.id); return z && (
                  <Panel title={`${z.name}: silent ${z.risk.hours_silent} h`} tone="bg-pink-500" section="blackout.risk">
                    <Breakdown components={z.risk.components} />
                    {z.recon && <p className="mt-2 text-sm font-bold">Recon: {z.recon.team} · {z.recon.status.replace("_", " ")}</p>}
                  </Panel>); })()}
                {sel.kind === "shelter" && (() => { const s = (shelters.data ?? []).find((x) => x.id === sel.id); return s && (
                  <Panel title={s.name} tone="bg-mint-400" section="shelters.page">
                    <p className="text-sm font-bold">{s.status}{s.status_reason ? ` — ${s.status_reason}` : ""} · {s.occupancy}/{s.capacity} people · last check-in {simTime(s.last_confirmed_at)}</p>
                    <ul className="mt-2 grid grid-cols-2 gap-1 text-xs">{s.inventory.map((i: any) => <li key={i.id} className="rounded-lg bg-paper px-2 py-1 font-bold">{i.resource_type.replace("_", " ")}: {Math.round(i.quantity)}{i.in_transit ? ` (+${Math.round(i.in_transit)} coming)` : ""}</li>)}</ul>
                  </Panel>); })()}
                {sel.kind === "depot" && (() => { const d = (depots.data ?? []).find((x) => x.id === sel.id); return d && (
                  <Panel title={d.name} tone="bg-brand-300" section="resources.depots">
                    <p className="text-xs font-bold text-ink/60">{d.owner}</p>
                    <ul className="mt-2 grid grid-cols-2 gap-1 text-xs">{d.inventory.map((i: any) => <li key={i.id} className="rounded-lg bg-paper px-2 py-1 font-bold">{i.resource_type.replace("_", " ")}: {Math.round(i.quantity)}</li>)}</ul>
                  </Panel>); })()}
              </motion.div>
            ) : (
              <motion.div key="tabs" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <div className="mb-2 flex flex-wrap gap-1" role="tablist" aria-label="Side panel">
                  {TABS.map(([k, label]) => <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)}
                    className={`border-[1.5px] border-ink px-2 py-0.5 font-mono text-[10.5px] font-bold uppercase ${tab === k ? "bg-ink text-bone" : "bg-bone"}`}>{label}</button>)}
                </div>
                {tab === "arriving" && <Panel title="Arriving now" section="feed.page" tone="bg-pink-400">
                  {!feed.length ? <p className="text-sm font-medium text-ink/60">Reports pulse on the map as they arrive. Send one from the phone simulator, or click any marker for its evidence.</p> : (
                    <ul className="space-y-1.5">{feed.map((r) => (
                      <li key={r.id} className="rounded-xl border-2 border-ink/20 bg-paper p-2 text-xs">
                        <b className="font-mono">{r.ref}</b> · {r.channel} · {LANG_NAMES[r.original_language] ?? r.original_language}
                        <p className="mt-0.5 text-sm font-semibold" lang={r.original_language}>{r.raw_text}</p>
                      </li>))}</ul>
                  )}
                </Panel>}
                {tab === "priorities" && <Panel title="Top priorities" section="incidents.priority" tone="bg-lime-400">
                  <ul className="space-y-1.5">
                    {(incidents.data ?? []).slice(0, 8).map((i) => { const p = PRIORITY_STYLE(i.priority_score); return (
                      <li key={i.id}><button className="flex w-full items-center gap-2 rounded-xl border-2 border-ink/15 bg-white px-2 py-1.5 text-left text-sm hover:border-ink" onClick={() => i.lat && pick({ kind: "incident", id: i.id }, [i.lat, i.lng!])}>
                        <span className={`badge ${p.cls}`}>{p.label}</span><span className="min-w-0 flex-1 truncate font-bold">{i.title}</span><ConfidenceBadge level={i.confidence_level} />
                      </button></li>); })}
                  </ul>
                </Panel>}
                {tab === "disaster" && <Panel title={`Disaster profile · GDACS ${gdacs.data?.status ?? ""}`} section="map.disaster" tone="bg-cobalt-300">
                  <DisasterProfilePanel />
                  {gdacs.data && <p className="mt-2 text-xs font-bold"><span className={`badge ${DATA_BADGE[gdacs.data.status]}`}>{gdacs.data.status}</span> {gdacs.data.items.length} GDACS item(s){gdacs.data.reason ? ` · ${gdacs.data.reason}` : ""}</p>}
                </Panel>}
                {tab === "volunteers" && <Panel title={`Volunteers (${vols.data?.length ?? 0})`} section="dispatch.page" tone="bg-mint-400">
                  <ul className="space-y-1 text-xs">{(vols.data ?? []).map((v) => (
                    <li key={v.code} className="flex flex-wrap items-center gap-1.5 rounded-lg bg-paper px-2 py-1">
                      <b className="font-mono">{v.code}</b><span className="font-bold">{v.name}</span>
                      <span className={`badge ${v.busy ? "bg-sun-300" : v.available ? "bg-mint-300" : "bg-white"}`}>{v.busy ? "on a task" : v.available ? "free" : "unavailable"}</span>
                      <span className="badge bg-white" title={v.reliability_formula}>reliability {v.reliability.toFixed(2)}</span>
                      <span className="text-ink/60">{v.skills.join(", ")} · {v.vehicle ?? "no vehicle"}</span></li>))}</ul>
                  <p className="mt-2 text-[11px] text-ink/60">Reliability = (on-time confirmations + 1) / (assigned tasks + 2). Separate from reporter reliability and approval precedents.</p>
                </Panel>}
                {tab === "agents" && <Panel title="Agent activity" section="audit.page" tone="bg-sun-400">
                  {!agentLog.length ? <p className="text-sm text-ink/60">Messages between agents appear here as they happen.</p> :
                    <ul className="space-y-1 text-[11px]">{agentLog.map((a, i) => <li key={i} className="rounded-lg bg-paper px-2 py-1"><span className="badge mr-1 bg-cobalt-200">{a.sender} → {a.recipient?.replace("_", " ")} · {a.performative}</span>{a.summary}</li>)}</ul>}
                  <a href="/agents" className="mt-2 block text-xs font-extrabold underline">All conversations →</a>
                </Panel>}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
