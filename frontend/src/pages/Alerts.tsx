import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { BellRing, Check, Megaphone } from "lucide-react";
import { PageHeader } from "../components/Layout";
import { Empty, LANG_NAMES, Panel, simTime } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";

const TYPE: Record<string, { label: string; tone: string }> = {
  shortage: { label: "shortage", tone: "bg-sun-400" }, blackout: { label: "blackout", tone: "bg-ink text-white" },
  shelter_inaccessible: { label: "shelter", tone: "bg-pink-400" }, rumour: { label: "rumour correction", tone: "bg-brand-300" },
  delivery_overdue: { label: "delivery", tone: "bg-tangerine-400" }, escalation: { label: "escalation", tone: "bg-pink-500 text-white" },
  stale_stock: { label: "stale stock", tone: "bg-white" },
};
const SEV: Record<string, string> = { critical: "bg-pink-500 text-white", high: "bg-tangerine-400", medium: "bg-sun-300", low: "bg-white" };

export function Corrections({ compact = false }: { compact?: boolean }) {
  const { data } = useApi<any[]>("/api/public/corrections", ["alert"], 500);
  if (!data?.length) return <Empty>No corrections published.</Empty>;
  return (
    <div className="space-y-3">
      {data.map((c) => (
        <div key={c.id} className="rounded-2xl border-2 border-ink bg-white p-3 shadow-hard-sm">
          <p className="font-extrabold">{c.message}</p>
          <div className={`mt-2 grid gap-1.5 ${compact ? "" : "md:grid-cols-2"}`}>
            {Object.entries(c.translations).filter(([k]) => k !== "en").map(([k, v]: any) => (
              <p key={k} className="rounded-xl bg-paper px-2.5 py-1.5 text-sm" lang={k}><span className="badge mr-1 bg-brand-200">{LANG_NAMES[k] ?? k}</span>{v}</p>
            ))}
          </div>
          <p className="mt-1 text-[11px] font-bold text-ink/50">published {simTime(c.t)}</p>
        </div>
      ))}
    </div>
  );
}

export default function Alerts() {
  const { t } = useTranslation();
  const { data, reload } = useApi<any[]>("/api/alerts", ["alert"], 400);
  const incs = useApi<any[]>("/api/incidents", ["incident", "alert"], 600);
  const [show, setShow] = useState<"open" | "all">("open");
  const [msg, setMsg] = useState<string | null>(null);
  const ack = async (id: number) => { await api(`/api/alerts/${id}/ack`, { method: "POST" }); reload(); };
  const publish = async (id: number) => {
    try { const r = await api<any>("/api/alerts/rumour", { method: "POST", body: JSON.stringify({ incident_id: id }) }); setMsg(`Correction published in ${Object.keys(r.translations).length} languages · ${r.sms_sent} SMS sent`); reload(); }
    catch (e: any) { setMsg(e.message); }
  };
  const list = (data ?? []).filter((a) => show === "all" || !a.resolved);
  const published = new Set((data ?? []).filter((a) => a.type === "rumour").map((a) => a.related?.incident_id));
  const falseIncs = (incs.data ?? []).filter((i) => i.confidence_level === "false" || i.official_status === "refuted");
  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.alerts")} sub={t("pages.alerts")} kicker={`${(data ?? []).filter((a) => !a.resolved).length} open`} tone="bg-pink-400" section="alerts.page">
        <div className="flex rounded-xl border-2 border-ink bg-white p-0.5">
          {(["open", "all"] as const).map((k) => <button key={k} onClick={() => setShow(k)} className={`rounded-lg px-3 py-1 text-xs font-extrabold ${show === k ? "bg-ink text-white" : ""}`}>{k}</button>)}
        </div>
      </PageHeader>
      {msg && <p className="sticker w-fit bg-lime-400">{msg}</p>}
      <div className="grid gap-4 xl:grid-cols-[1.3fr_1fr]">
        <div className="space-y-2">
          {!list.length && <Empty>No alerts.</Empty>}
          {list.map((a, n) => (
            <motion.article key={a.id} animate={{ opacity: 1, x: 0 }} transition={{ delay: Math.min(n, 10) * 0.03 }}
              className={`flex flex-wrap items-start gap-2 rounded-2xl border-2 border-ink bg-white p-3 ${a.resolved ? "opacity-50" : a.severity === "critical" ? "shadow-hard-pink" : "shadow-hard-sm"}`}>
              <BellRing size={18} className="mt-0.5" aria-hidden />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className={`badge ${TYPE[a.type]?.tone ?? "bg-white"}`}>{TYPE[a.type]?.label ?? a.type}</span>
                  <span className={`badge ${SEV[a.severity] ?? "bg-white"}`}>{a.severity}</span>
                  {a.resolved && <span className="badge bg-mint-300">resolved</span>}
                  {a.acknowledged && <span className="badge bg-paper">acknowledged</span>}
                  <span className="font-mono text-[11px] text-ink/50">{simTime(a.created_at_sim)}</span>
                </div>
                <p className="mt-1 font-semibold">{a.message}</p>
                {a.details?.why && <p className="text-xs text-ink/60">{a.details.why}</p>}
                {a.details?.resolved_because && <p className="text-xs font-bold text-ink/60">resolved: {a.details.resolved_because}</p>}
                <div className="mt-1 flex gap-2 text-xs font-bold">
                  {a.type === "blackout" && <Link className="underline" to="/blackout">blackout & recon →</Link>}
                  {a.type === "shortage" && <Link className="underline" to="/resources">resources →</Link>}
                  {a.type === "shelter_inaccessible" && <Link className="underline" to="/plans">replan →</Link>}
                  {a.type === "delivery_overdue" && <Link className="underline" to="/dispatch">dispatch →</Link>}
                </div>
              </div>
              {!a.acknowledged && !a.resolved && <button className="btn-ghost !px-2 !py-1 !text-xs" onClick={() => ack(a.id)}><Check size={13} aria-hidden />ack</button>}
            </motion.article>
          ))}
        </div>
        <div className="space-y-4">
          <Panel title={<span className="flex items-center gap-2"><Megaphone size={18} aria-hidden />Rumour control</span>} tone="bg-brand-300" section="alerts.rumour">
            <p className="mb-2 text-xs font-medium text-ink/60">Incidents marked false. Publish a correction: pre-translated into all 8 languages with the place name in each script, sent by SMS to people who reported from the area, and shown on the public page.</p>
            {!falseIncs.length ? <Empty>No false incidents.</Empty> : falseIncs.map((i) => (
              <div key={i.id} className="mb-2 flex items-center gap-2 rounded-xl border-2 border-ink bg-paper p-2">
                <span className="min-w-0 flex-1 text-sm font-bold line-through decoration-pink-500">{i.title}</span>
                {published.has(i.id) ? <span className="badge bg-mint-400">published</span>
                  : <button className="btn-primary !py-1 !text-xs" onClick={() => publish(i.id)}><Megaphone size={13} aria-hidden />Publish correction</button>}
              </div>
            ))}
          </Panel>
          <Panel title="Public corrections" actions={<Link to="/public" className="text-xs font-bold underline">public page →</Link>}><Corrections compact /></Panel>
        </div>
      </div>
    </div>
  );
}
