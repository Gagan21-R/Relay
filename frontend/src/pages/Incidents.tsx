import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AnimatePresence, motion } from "framer-motion";
import { Check, GitCompare, LifeBuoy, ShieldAlert, Users, X } from "lucide-react";
import { PageHeader } from "../components/Layout";
import ReportCard from "../components/ReportCard";
import { Breakdown, ConfidenceBadge, Empty, LANG_NAMES, Panel, PRIORITY_STYLE, simTime } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";
import { Incident } from "../services/types";

export function IncidentDetail({ id, onClose }: { id: number; onClose?: () => void }) {
  const d = useApi<any>(`/api/incidents/${id}`, ["incident", "report"], 500);
  const [note, setNote] = useState("");
  const verify = async (decision: "confirm" | "refute") => {
    await api(`/api/incidents/${id}/verify`, { method: "POST", body: JSON.stringify({ decision, note: note || null }) });
    setNote(""); d.reload();
  };
  if (!d.data) return <Panel><p className="text-sm">Loading evidence…</p></Panel>;
  const i = d.data;
  const p = PRIORITY_STYLE(i.priority_score);
  return (
    <div className="space-y-4">
      <Panel tone="bg-pink-400" actions={onClose && <button className="btn-ghost !p-1" onClick={onClose} aria-label="Close"><X size={15} /></button>}>
        <div className="flex flex-wrap items-center gap-2">
          <span className={`badge ${p.cls}`}>{p.label} · {i.priority_score.toFixed(0)}</span>
          <ConfidenceBadge level={i.confidence_level} score={i.confidence_score} />
          {i.life_safety && <span className="badge bg-pink-400"><LifeBuoy size={12} aria-hidden />life-safety</span>}
          {i.fast_verify && <span className="badge bg-tangerine-400"><ShieldAlert size={12} aria-hidden />Fast Verify</span>}
          <span className="badge bg-white">{i.status}</span>
        </div>
        <h2 className="mega mt-2 text-[30px]">{i.title}</h2>
        <p className="text-sm font-medium text-ink/70">{i.reports.length} reports · first {simTime(i.first_report_at)} · latest {simTime(i.last_report_at)} · needs: {i.need_types.join(", ")}{i.vulnerable_groups.length ? ` · vulnerable: ${i.vulnerable_groups.join(", ")}` : ""}</p>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <input className="input !w-64" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Note (callback result, team check…)" aria-label="Verification note" />
          <button className="btn-pop" onClick={() => verify("confirm")}><Check size={15} aria-hidden />Confirm</button>
          <button className="btn-danger" onClick={() => verify("refute")}><X size={15} aria-hidden />Refute (false)</button>
        </div>
        {i.official_status && <p className="mt-2 text-xs font-bold">Marked {i.official_status} by a person{i.verification_note ? `: ${i.verification_note}` : ""}. Source reliabilities were updated.</p>}
      </Panel>
      <div className="grid gap-4 2xl:grid-cols-2">
        <Panel title={<>Why priority {i.priority_score.toFixed(0)}<span className="text-ink/40">/100</span></>} tone="bg-lime-400" section="incidents.priority">
          {i.priority_breakdown?.components && Object.keys(i.priority_breakdown.components).length
            ? <Breakdown components={i.priority_breakdown.components} unit=" pts" /> : <p className="text-sm">{i.priority_breakdown?.note}</p>}
        </Panel>
        <Panel title={<>Why {i.confidence_level} ({Math.round(i.confidence_score * 100)}%)</>} tone="bg-cobalt-300" section="incidents.confidence">
          <Breakdown components={i.confidence_breakdown.components} penalties={i.confidence_breakdown.penalties} />
          <p className="mt-2 text-xs font-bold text-ink/60">Level rule: {i.confidence_breakdown.level_reason}</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {i.confidence_breakdown.independent_sources.map((g: any) => (
              <span key={g.name} className="badge bg-paper">{g.name} · {g.type}{g.copies_merged ? ` · +${g.copies_merged} forward(s) counted once` : ""}</span>
            ))}
          </div>
        </Panel>
      </div>
      <Panel title="Evidence trail" tone="bg-sun-400" section="incidents.evidence">
        <div className="space-y-2">
          {i.reports.map((r: any) => (
            <div key={r.id}>
              <ReportCard r={r} />
              <p className="ml-3 mt-1 text-[11px] font-bold text-ink/60">
                {r.refutes ? "⟂ contradicts the claim · " : ""}{r.cluster_evidence?.decision}{r.cluster_evidence?.matched_report ? ` with ${r.cluster_evidence.matched_report}` : ""}
                {r.cluster_evidence?.tests && " · " + Object.entries(r.cluster_evidence.tests).map(([k, t]: any) => `${k} ${t.value ?? "?"}${t.threshold != null ? ` (≤/≥ ${t.threshold})` : ""} ${t.pass ? "✓" : "✗"}`).join(" · ")}
                {r.cluster_evidence?.reason ? ` · ${r.cluster_evidence.reason}` : ""}{r.cluster_evidence?.why ? ` · ${r.cluster_evidence.why}` : ""}
              </p>
            </div>
          ))}
        </div>
        {i.hazard && <p className="mt-3 text-xs font-bold">Sensors for {i.zone?.name}: {i.hazard.in_flood_extent ? "inside flood extent · " : ""}{i.hazard.river_above_danger ? "river above danger · " : ""}{i.hazard.rain_mm_24h ? `${i.hazard.rain_mm_24h} mm rain · ` : ""}towers {i.zone?.tower_status}</p>}
      </Panel>
    </div>
  );
}

function SameReportAnalyser() {
  const [a, setA] = useState("ಕರಡಿಗೋಡು ಗ್ರಾಮದಲ್ಲಿ 30 ಕುಟುಂಬಗಳ ಮನೆಗಳಿಗೆ ನೀರು ನುಗ್ಗಿದೆ, ಊಟ ಮತ್ತು ಕುಡಿಯುವ ನೀರು ಬೇಕು");
  const [b, setB] = useState("Karadigodu village near Siddapura: around 30 families' houses flooded by Cauvery. They need food and drinking water.");
  const [hours, setHours] = useState(0.3);
  const [res, setRes] = useState<any>(null);
  const run = async () => setRes(await api("/api/trust/compare", { method: "POST", body: JSON.stringify({ texts: [a, b], hours_apart: [0, hours] }) }));
  const p = res?.pairs?.[0];
  return (
    <Panel title={<span className="flex items-center gap-2"><GitCompare size={18} aria-hidden />Same-report analyser</span>} tone="bg-brand-300" section="incidents.analyser">
      <p className="mb-2 text-xs font-medium text-ink/60">Paste two reports in any language. RELAY runs the real Intake and Trust logic (nothing is stored) and shows every test.</p>
      <div className="grid gap-2 md:grid-cols-2">
        <textarea className="input" rows={3} value={a} onChange={(e) => setA(e.target.value)} aria-label="Report A" />
        <textarea className="input" rows={3} value={b} onChange={(e) => setB(e.target.value)} aria-label="Report B" />
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
        <label className="flex items-center gap-1.5 font-bold">hours apart <input type="number" step="0.5" min="0" className="input !w-20 !py-1" value={hours} onChange={(e) => setHours(Number(e.target.value))} /></label>
        <button className="btn-primary" onClick={run}>Compare</button>
      </div>
      <AnimatePresence>{res && p && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-3 space-y-2">
          <p className={`sticker w-fit ${p.same ? "bg-mint-400" : "bg-pink-400"}`}>{res.verdict}</p>
          <div className="grid gap-2 md:grid-cols-2">
            {res.items.map((it: any, n: number) => (
              <div key={n} className="rounded-xl border-2 border-ink bg-paper p-2 text-xs">
                <b>{LANG_NAMES[it.language] ?? it.language} · {it.script}</b> · {it.location ?? "no location"} · {it.need_types.join(", ")} · {it.people ?? "?"} people
                <p className="mt-1 text-ink/70">EN: {it.translation}</p>
              </div>
            ))}
          </div>
          <ul className="grid gap-1.5 text-xs sm:grid-cols-4">
            {Object.entries(p.tests).map(([k, t]: any) => (
              <li key={k} className={`rounded-xl border-2 border-ink p-2 font-bold ${t.pass ? "bg-mint-300" : "bg-pink-300"}`}>
                {t.pass ? "✓" : "✗"} {k.replace("_", " ")}<br /><span className="font-mono font-medium">{String(t.value)}{t.threshold != null ? ` vs ${t.threshold}` : ""}</span>
              </li>
            ))}
          </ul>
          {p.copy_of_same_text && <p className="text-xs font-bold">Near-identical text: would count as one source (forward/copy).</p>}
        </motion.div>
      )}</AnimatePresence>
    </Panel>
  );
}

export default function Incidents() {
  const { t } = useTranslation();
  const [params, setParams] = useSearchParams();
  const { data } = useApi<Incident[]>("/api/incidents", ["incident"], 500);
  const [level, setLevel] = useState("");
  const focus = Number(params.get("focus")) || null;
  const list = useMemo(() => (data ?? []).filter((i) => !level || i.confidence_level === level), [data, level]);
  useEffect(() => { if (!focus && list.length) setParams({ focus: String(list[0].id) }, { replace: true }); }, [focus, list, setParams]);
  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.incidents")} sub={t("pages.incidents")} kicker="ranked by danger" tone="bg-pink-400" section="incidents.page" />
      <div className="flex flex-wrap gap-1.5">
        {["", "verified", "likely", "unverified", "disputed", "false"].map((l) => (
          <button key={l} onClick={() => setLevel(l)} className={`badge !px-3 !py-1 text-xs ${level === l ? "bg-ink text-white" : "bg-white hover:bg-lime-300"}`}>{l || "all"} {l ? `(${(data ?? []).filter((i) => i.confidence_level === l).length})` : `(${data?.length ?? 0})`}</button>
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(320px,420px)_1fr]">
        <div className="space-y-2">
          {!list.length && <Empty>No incidents.</Empty>}
          {list.map((i, n) => {
            const p = PRIORITY_STYLE(i.priority_score);
            return (
              <motion.button key={i.id} layout onClick={() => setParams({ focus: String(i.id) })}
                className={`w-full rounded-2xl border-2 border-ink p-3 text-left transition-all ${focus === i.id ? "bg-lime-300 shadow-hard" : "bg-white shadow-hard-sm hover:-translate-y-0.5"} ${i.confidence_level === "false" ? "opacity-60" : ""}`}>
                <div className="flex items-center gap-2">
                  <span className="mega w-8 text-2xl text-ink/30">{n + 1}</span>
                  <span className={`badge ${p.cls}`}>{p.label} {i.priority_score.toFixed(0)}</span>
                  <ConfidenceBadge level={i.confidence_level} />
                  {i.fast_verify && <span className="badge bg-tangerine-400">fast verify</span>}
                </div>
                <p className="mt-1 font-extrabold leading-tight">{i.title}</p>
                <p className="text-xs font-medium text-ink/60"><Users size={11} className="inline" aria-hidden /> {i.people_affected} · {i.need_types.join(", ")} · {simTime(i.last_report_at)}</p>
              </motion.button>
            );
          })}
        </div>
        <div className="space-y-4">
          {focus ? <IncidentDetail key={focus} id={focus} /> : <Empty>Pick an incident.</Empty>}
          <SameReportAnalyser />
        </div>
      </div>
    </div>
  );
}
