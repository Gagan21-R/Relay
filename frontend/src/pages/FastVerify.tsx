// Life-safety reports with low confidence. Never discarded: call back the reporter (in their language) or send the
// nearest team, then confirm or refute.
import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Check, Phone, ShieldAlert, X } from "lucide-react";
import { PageHeader } from "../components/Layout";
import { ConfidenceBadge, Empty, LANG_NAMES, PRIORITY_STYLE } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";

export default function FastVerify() {
  const { t } = useTranslation();
  const { data, reload } = useApi<any[]>("/api/fast-verify", ["incident"], 400);
  const [notes, setNotes] = useState<Record<number, string>>({});
  const act = async (id: number, decision: string) => {
    await api(`/api/incidents/${id}/verify`, { method: "POST", body: JSON.stringify({ decision, note: notes[id] || (decision === "confirm" ? "callback confirmed" : "callback: not true") }) });
    reload();
  };
  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.fastVerify")} sub={t("pages.fastVerify")} kicker="never discarded" tone="bg-tangerine-400" />
      {!data?.length ? <Empty>Nothing waiting. Every life-safety report is either verified or confirmed false.</Empty> : (
        <div className="grid gap-4 lg:grid-cols-2">
          {data.map((i, n) => {
            const p = PRIORITY_STYLE(i.priority_score);
            return (
              <motion.article key={i.id} initial={{ opacity: 0, y: 20, rotate: n % 2 ? 1 : -1 }} animate={{ opacity: 1, y: 0, rotate: 0 }}
                className="card relative overflow-hidden p-4 shadow-hard-pink">
                <div className="pat-stripes absolute right-0 top-0 h-full w-3 opacity-20" aria-hidden />
                <div className="flex flex-wrap items-center gap-2">
                  <span className="sticker bg-tangerine-400"><ShieldAlert size={13} aria-hidden />waiting {i.waiting_h} h</span>
                  <span className={`badge ${p.cls}`}>{p.label} {i.priority_score.toFixed(0)}</span>
                  <ConfidenceBadge level={i.confidence_level} score={i.confidence_score} />
                </div>
                <h2 className="mega mt-2 text-2xl">{i.title}</h2>
                {i.reports.map((r: any) => (
                  <div key={r.ref} className="mt-2 rounded-xl border-2 border-ink bg-paper p-2.5">
                    <p className="text-[15px] font-semibold" lang={r.original_language}>{r.raw_text}</p>
                    {r.original_language !== "en" && <p className="mt-1 text-sm text-ink/70"><b className="text-brand-600">EN · </b>{r.translated_text_en}</p>}
                    <p className="mt-1 text-[11px] font-bold text-ink/50">{r.ref} · {r.channel} · {LANG_NAMES[r.original_language] ?? r.original_language}</p>
                  </div>
                ))}
                <div className="mt-3 rounded-xl border-2 border-dashed border-ink p-2.5 text-sm">
                  <p className="label">Call back</p>
                  {i.callback.length ? i.callback.map((c: any) => (
                    <p key={c.phone_masked} className="flex items-center gap-2 font-bold"><Phone size={14} aria-hidden />{c.phone_masked} · speak {LANG_NAMES[c.language] ?? c.language}</p>
                  )) : <p className="font-medium text-ink/60">No callable number: send the nearest field team to check.</p>}
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <input className="input !w-56" placeholder="What did you find?" value={notes[i.id] ?? ""} onChange={(e) => setNotes({ ...notes, [i.id]: e.target.value })} aria-label="Result" />
                  <button className="btn-pop" onClick={() => act(i.id, "confirm")}><Check size={15} aria-hidden />Confirmed</button>
                  <button className="btn-danger" onClick={() => act(i.id, "refute")}><X size={15} aria-hidden />Not true</button>
                  <Link className="btn-ghost" to={`/incidents?focus=${i.id}`}>Evidence</Link>
                </div>
              </motion.article>
            );
          })}
        </div>
      )}
    </div>
  );
}
