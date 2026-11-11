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
          <div className="h-56"><ResponsiveContainer><BarChart data={dup}><CartesianGrid strokeDasharray="3 3" stroke="#150A2E22" /><XAxis dataKey="lang" fontSize={11} /><YAxis domain={[0, 1]} fontSize={11} />
            <Tooltip contentStyle={{ border: "2px solid #150A2E", borderRadius: 12 }} /><Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="precision" fill="#7C3AED" stroke="#150A2E" radius={[5, 5, 0, 0]} /><Bar dataKey="recall" fill="#C8FF2E" stroke="#150A2E" radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer></div>
        </div>
        <div>
          <p className="label">Extraction accuracy and translation coverage per language</p>
          <div className="h-56"><ResponsiveContainer><BarChart data={ext}><CartesianGrid strokeDasharray="3 3" stroke="#150A2E22" /><XAxis dataKey="lang" fontSize={11} /><YAxis domain={[0, 1]} fontSize={11} />
            <Tooltip contentStyle={{ border: "2px solid #150A2E", borderRadius: 12 }} /><Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="zone" fill="#2E5BFF" stroke="#150A2E" /><Bar dataKey="need" fill="#FF2E86" stroke="#150A2E" /><Bar dataKey="people" fill="#FFD23F" stroke="#150A2E" /><Bar dataKey="translated" fill="#14C48A" stroke="#150A2E" /></BarChart></ResponsiveContainer></div>
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

export default function Metrics() {
  const { t } = useTranslation();
  const { data, reload } = useApi<any>("/api/metrics");
  const [started, setStarted] = useState(false);
  const rerun = async () => { await api("/api/metrics/run", { method: "POST" }); setStarted(true); setTimeout(reload, 60000); };
  const o = data?.operations;
  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.metrics")} sub={t("pages.metrics")} kicker="synthetic data" tone="bg-mint-400" section="metrics.page">
        <button className="btn-ghost" onClick={rerun} disabled={data?.running || started}><RefreshCw size={15} aria-hidden />{data?.running || started ? "Running (≈1 min)…" : "Re-run evaluation"}</button>
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
          <SetBlock s={data.development} label="Development set (rules built on it — optimistic)" tone="bg-white" />
          <p className="text-xs font-medium text-ink/50">{data.mode} · generated in {data.generated_in_seconds} s · {data.notes.join(" · ")}</p>
        </>
      )}
    </div>
  );
}
