import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { FlaskConical, RefreshCw } from "lucide-react";
import { PageHeader } from "../components/Layout";
import { Empty, LANG_NAMES, Panel, Stat } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";

const pct = (x?: number | null) => (x == null ? "—" : `${Math.round(x * 100)}%`);

function SetBlock({ s, label, tone }: { s: any; label: string; tone: string }) {
  const dup = Object.entries(s.duplicates.per_language).map(([l, v]: any) => ({ lang: LANG_NAMES[l] ?? l, precision: v.precision ?? 0, recall: v.recall ?? 0 }));
  const ext = Object.entries(s.extraction.per_language).map(([l, v]: any) => ({ lang: LANG_NAMES[l] ?? l, zone: v.zone.accuracy ?? 0, need: v.need.accuracy ?? 0, people: v.people.accuracy ?? 0, translated: v.translated.accuracy ?? 0 }));
  const cm = s.fake_true_confusion;
  return (
    <Panel title={`${label} · ${s.reports} reports · ${s.languages.length} languages`} tone={tone} section="metrics.page">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat i={0} label="duplicate precision" value={pct(s.duplicates.overall.precision)} />
        <Stat i={1} label="duplicate recall" value={pct(s.duplicates.overall.recall)} />
        <Stat i={2} label="location accuracy" value={pct(s.extraction.overall.zone.accuracy)} />
        <Stat i={3} label="people-count accuracy" value={pct(s.extraction.overall.people.accuracy)} />
      </div>
      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <div>
          <p className="label">Duplicate detection per language</p>
          <div className="h-56"><ResponsiveContainer><BarChart data={dup}><CartesianGrid strokeDasharray="3 3" stroke="#0B0B0C22" /><XAxis dataKey="lang" fontSize={11} /><YAxis domain={[0, 1]} fontSize={11} />
            <Tooltip contentStyle={{ border: "2px solid #0B0B0C", borderRadius: 12 }} /><Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="precision" fill="#0B0B0C" stroke="#0B0B0C" radius={[5, 5, 0, 0]} /><Bar dataKey="recall" fill="#F6F4EF" stroke="#0B0B0C" radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer></div>
        </div>
        <div>
          <p className="label">Extraction accuracy and translation coverage per language</p>
          <div className="h-56"><ResponsiveContainer><BarChart data={ext}><CartesianGrid strokeDasharray="3 3" stroke="#0B0B0C22" /><XAxis dataKey="lang" fontSize={11} /><YAxis domain={[0, 1]} fontSize={11} />
            <Tooltip contentStyle={{ border: "2px solid #0B0B0C", borderRadius: 12 }} /><Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="zone" fill="#5A4FD6" stroke="#0B0B0C" /><Bar dataKey="need" fill="#FF3D1F" stroke="#0B0B0C" /><Bar dataKey="people" fill="#E2CF98" stroke="#0B0B0C" /><Bar dataKey="translated" fill="#5F8F64" stroke="#0B0B0C" /></BarChart></ResponsiveContainer></div>
        </div>
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-[auto_1fr] md:items-center">
        <div>
          <p className="label mb-1">Fake vs true (incident level)</p>
          <table className="text-center text-sm font-bold">
            <thead><tr><th /><th className="px-3 text-xs">predicted fake</th><th className="px-3 text-xs">predicted true</th></tr></thead>
            <tbody>
              <tr><th className="pr-2 text-right text-xs">actually fake</th><td className="rounded-lg border-2 border-ink bg-mint-300 px-5 py-3 text-2xl">{cm.tp}</td><td className="rounded-lg border-2 border-ink bg-pink-300 px-5 py-3 text-2xl">{cm.fn}</td></tr>
              <tr><th className="pr-2 text-right text-xs">actually true</th><td className="rounded-lg border-2 border-ink bg-pink-300 px-5 py-3 text-2xl">{cm.fp}</td><td className="rounded-lg border-2 border-ink bg-mint-300 px-5 py-3 text-2xl">{cm.tn}</td></tr>
            </tbody>
          </table>
        </div>
        <p className="text-sm font-medium text-ink/70">Fake detection is risk scoring, not proof. Clustering is pairwise over report pairs; per-language rows count pairs that involve that language. Need accuracy counts the true need among the extracted needs.</p>
      </div>
    </Panel>
  );
}

function Probes({ p }: { p: any }) {
  const rows = Object.entries(p.per_language).map(([l, v]: any) => ({ lang: l, n: v.n, support: v.support, detect: v.lang.accuracy, need: v.need.accuracy, people: v.people.accuracy }));
  return (
    <Panel title={`Multilingual probe set · ${p.overall.n} messages · ${rows.length} languages`} tone="bg-cobalt-300" section="metrics.page">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat i={1} label="language detected" value={pct(p.overall.lang.accuracy)} />
        <Stat i={2} label="need extracted" value={pct(p.overall.need.accuracy)} />
        <Stat i={3} label="people count" value={pct(p.overall.people.accuracy)} />
        <Stat i={4} label={`disaster type (n=${p.overall.disaster.n})`} value={pct(p.overall.disaster.accuracy)} />
      </div>
      <div className="mt-3 grid gap-4 xl:grid-cols-2">
        <table className="w-full text-xs"><thead><tr className="text-left"><th>Language</th><th>support</th><th>n</th><th>detected</th><th>need</th><th>people</th></tr></thead>
          <tbody>{rows.map((r) => <tr key={r.lang} className="border-t border-ink/10"><td className="font-bold">{LANG_NAMES[r.lang] ?? r.lang}</td><td>{r.support}</td><td>{r.n}</td><td>{pct(r.detect)}</td><td>{pct(r.need)}</td><td>{pct(r.people)}</td></tr>)}</tbody></table>
        <div>
          <table className="w-full text-xs"><thead><tr className="text-left"><th>Input type</th><th>n</th><th>detected</th><th>need</th><th>people</th></tr></thead>
            <tbody>{Object.entries(p.per_input_type).map(([k, v]: any) => <tr key={k} className="border-t border-ink/10"><td className="font-bold">{k}</td><td>{v.n}</td><td>{pct(v.lang.accuracy)}</td><td>{pct(v.need.accuracy)}</td><td>{pct(v.people.accuracy)}</td></tr>)}</tbody></table>
          <p className="mt-2 text-[11px] font-bold">Misses ({p.errors.length}):</p>
          <ul className="text-[11px]">{p.errors.map((e: any, i: number) => <li key={i}>{e.lang}/{e.type}: “{e.text}” → {e.got.language}, {e.got.needs.join(",")}</li>)}</ul>
          <p className="mt-1 text-[11px] text-ink/60">Not evaluated: {p.not_evaluated.join(", ")}. {p.note}</p>
        </div>
      </div>
    </Panel>
  );
}

function Policy({ a, r, s }: { a: any; r: any; s: any }) {
  return (
    <div className="grid gap-4 xl:grid-cols-3">
      <Panel title="Verified-only vs all reports" tone="bg-pink-300">
        <table className="w-full text-xs"><thead><tr className="text-left"><th /><th>verified-only (RELAY)</th><th>all reports</th></tr></thead>
          <tbody>{["incident_lines", "lines_to_real_incidents", "lines_to_false_incidents", "kit_units_to_false", "unmet_lines"].map((k) =>
            <tr key={k} className="border-t border-ink/10"><td className="font-bold">{k.replace(/_/g, " ")}</td><td>{a.verified_only[k]}</td><td>{a.all_reports[k]}</td></tr>)}</tbody></table>
        <p className="mt-2 text-[11px] text-ink/60">{a.note}</p>
      </Panel>
      <Panel title="Routes under simulated closures" tone="bg-sun-300">
        <ul className="space-y-0.5 text-xs">{Object.entries(r).filter(([k]) => k !== "note").map(([k, v]: any) => <li key={k}><b>{k.replace(/_/g, " ")}:</b> {v}</li>)}</ul>
        <p className="mt-2 text-[11px] text-ink/60">{r.note}</p>
      </Panel>
      <Panel title={`All scenarios replayed (${s.ran})`} tone="bg-mint-300">
        <ul className="space-y-0.5 text-xs">
          <li><b>errors:</b> {s.errors.length}</li><li><b>rumour-led incident ever planned:</b> {s.rumour_ever_planned}</li>
          <li><b>incidents mixing rumour and real reports:</b> {s.incidents_mixing_rumour_and_real ?? "—"}</li>
          <li><b>reports per incident:</b> {s.mean_reports_per_incident}</li>
          {s.lab_incidents_vs_situations && <li><b>lab incidents vs designed situations:</b> {s.lab_incidents_vs_situations.mean_incidents} vs {s.lab_incidents_vs_situations.mean_designed_situations} ({s.lab_incidents_vs_situations.note})</li>}
        </ul>
        <p className="mt-2 text-[11px] text-ink/60">{s.note}</p>
      </Panel>
    </div>
  );
}

export default function Metrics() {
  const { t } = useTranslation();
  const { data, reload } = useApi<any>("/api/metrics");
  const [started, setStarted] = useState(false);
  const rerun = async () => { await api("/api/metrics/run", { method: "POST" }); setStarted(true); setTimeout(reload, 300000); };
  const o = data?.operations;
  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.metrics")} sub={t("pages.metrics")} kicker="synthetic data" tone="bg-mint-400" section="metrics.page">
        <button className="btn-ghost" onClick={rerun} disabled={data?.running || started}><RefreshCw size={15} aria-hidden />{data?.running || started ? "Running (≈5 min)…" : "Re-run evaluation"}</button>
      </PageHeader>
      <div className="flex items-center gap-2 rounded-2xl border-2 border-ink bg-sun-300 p-3 text-sm font-extrabold shadow-hard-sm"><FlaskConical size={18} aria-hidden />Evaluated on synthetic data; real-world validation pending. The held-out set was written after the rules were tuned and never used to tune them — trust it over the development set.</div>
      {!data?.available ? <Empty>No results yet. Run <code>make eval</code> (python -m eval.run_eval) or press Re-run.</Empty> : (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Stat i={4} label="seconds to a feasible plan" value={o.plan_generation_seconds.mean} />
            <Stat i={5} label="plan lines linked to evidence" value={pct(o.evidence_traceability.rate)} />
            <Stat i={6} label={`injected shortages detected (${o.shortage_detection.detected}/${o.shortage_detection.injected})`} value={pct(o.shortage_detection.rate)} />
            <Stat i={0} label={`deliveries verified (${o.delivery_verification.confirmed}/${o.delivery_verification.reached_destination})`} value={pct(o.delivery_verification.rate_of_reached)} />
          </div>
          <p className="text-xs font-medium text-ink/60">{o.delivery_verification.note}.</p>
          <SetBlock s={data.held_out} label="Held-out set (honest)" tone="bg-lime-400" />
          {data.multilingual_probes && <Probes p={data.multilingual_probes} />}
          {data.allocation_policy && <Policy a={data.allocation_policy} r={data.routes} s={data.scenarios} />}
          <SetBlock s={data.development} label="Development set (rules built on it — optimistic)" tone="bg-white" />
          <p className="text-xs font-medium text-ink/50">{data.mode} · generated in {data.generated_in_seconds} s · {data.notes.join(" · ")}</p>
        </>
      )}
    </div>
  );
}
