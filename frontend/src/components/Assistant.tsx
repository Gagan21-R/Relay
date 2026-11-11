// "Explain me": every section of every page has a button that opens this assistant, which explains that part of the
// screen with live facts from the current situation and takes follow-up questions. Read-only.
import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AnimatePresence, motion } from "framer-motion";
import { MessageCircleQuestion, Send, Sparkles, X } from "lucide-react";
import { api } from "../services/api";

type Answer = { section: string; title: string; answer: string; what?: string; read?: string; do?: string; facts: string[]; method: string; note?: string | null };
type Turn = { q?: string; a?: Answer; error?: string };

let opener: ((section: string, context?: any) => void) | null = null;
export const openAssistant = (section: string, context?: any) => opener?.(section, context);

const PAGE_SECTION: Record<string, string> = {
  "": "map.page", feed: "feed.page", incidents: "incidents.page", "fast-verify": "fastverify.page", plans: "plans.page", dispatch: "dispatch.page",
  resources: "resources.page", shelters: "shelters.page", alerts: "alerts.page", blackout: "blackout.page", phone: "phone.page",
  scenario: "scenario.page", agents: "agents.page", workflow: "workflow.page", lab: "lab.page", comms: "comms.page", metrics: "metrics.page", audit: "audit.page", field: "field.page", about: "about.page",
};

/** The "Explain me" button placed on page headers and panels. */
export function Explain({ id, context, label }: { id: string; context?: any; label?: string }) {
  const { t } = useTranslation();
  return (
    <button type="button" onClick={(e) => { e.stopPropagation(); openAssistant(id, context); }}
      className="group inline-flex shrink-0 items-center gap-1 border-[1.5px] border-ink bg-bone px-1.5 py-[1px] font-mono text-[10.5px] font-bold uppercase tracking-[0.06em] text-ink transition-all hover:-translate-y-0.5 hover:bg-ink hover:text-bone"
      aria-label={`${t("assistant.explain")}: ${id}`}>
      <Sparkles size={12} className="transition-transform group-hover:rotate-45" aria-hidden />{label ?? t("assistant.explain")}
    </button>
  );
}

export default function AssistantDrawer() {
  const { t, i18n } = useTranslation();
  const loc = useLocation();
  const [open, setOpen] = useState(false);
  const [section, setSection] = useState("map.page");
  const [context, setContext] = useState<any>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const end = useRef<HTMLDivElement>(null);
  const ask = async (sec: string, question?: string, ctx?: any) => {
    setBusy(true);
    setTurns((x) => [...x, { q: question }]);
    try {
      const a = await api<Answer>("/api/assistant", { method: "POST", body: JSON.stringify({ section: sec, question: question || null, lang: i18n.language, context: ctx ?? null }) });
      setTurns((x) => [...x.slice(0, -1), { q: question, a }]);
    } catch (e: any) { setTurns((x) => [...x.slice(0, -1), { q: question, error: e.message }]); }
    setBusy(false);
  };
  useEffect(() => {
    opener = (sec, ctx) => { setOpen(true); setSection(sec); setContext(ctx ?? null); setTurns([]); ask(sec, undefined, ctx); };
    return () => { opener = null; };
  });
  useEffect(() => { end.current?.scrollIntoView({ block: "end", behavior: "smooth" }); }, [turns]);
  const pageSection = PAGE_SECTION[loc.pathname.replace(/^\//, "").split("/")[0]] ?? "map.page";
  return (
    <>
      {!open && (
        <motion.button initial={{ scale: 0 }} animate={{ scale: 1 }} whileHover={{ x: -3, y: -3 }}
          onClick={() => opener?.(pageSection)} aria-label={t("assistant.ask")}
          className="fixed bottom-4 right-4 z-[1100] flex items-center gap-2 border-2 border-ink bg-ink px-4 py-3 font-mono text-[12px] font-bold uppercase tracking-[0.08em] text-bone shadow-hard-pink">
          <MessageCircleQuestion size={18} aria-hidden />{t("assistant.ask")}
        </motion.button>
      )}
      <AnimatePresence>
        {open && (
          <motion.aside role="dialog" aria-label={t("assistant.title")} initial={{ x: 480, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: 480, opacity: 0 }}
            transition={{ type: "spring", stiffness: 260, damping: 28 }}
            className="fixed bottom-0 right-0 top-0 z-[1300] flex w-[min(440px,100vw)] flex-col border-l-2 border-ink bg-paper shadow-hard-lg">
            <header className="relative overflow-hidden border-b-2 border-ink bg-ink p-4 text-bone">
              <span className="absolute -right-6 -top-8 h-24 w-24 animate-levitate rounded-full orb" aria-hidden />
              <div className="relative flex items-center gap-2">
                <span className="grid h-9 w-9 place-items-center rounded-xl border-2 border-ink bg-lime-400 text-ink"><Sparkles size={18} aria-hidden /></span>
                <div className="flex-1"><p className="mega text-2xl">{t("assistant.title")}</p><p className="text-[11px] font-bold text-brand-100">{t("assistant.sub")}</p></div>
                <button className="rounded-lg border-2 border-white/60 p-1" onClick={() => setOpen(false)} aria-label={t("assistant.close")}><X size={16} /></button>
              </div>
            </header>
            <div className="flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
              {turns.map((tn, i) => (
                <div key={i} className="space-y-2">
                  {tn.q && <p className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-sm border-2 border-ink bg-lime-300 px-3 py-1.5 text-sm font-semibold">{tn.q}</p>}
                  {!tn.a && !tn.error && <p className="text-sm font-bold text-ink/60">{t("assistant.thinking")}</p>}
                  {tn.error && <p className="text-sm font-bold text-pink-500">{tn.error}</p>}
                  {tn.a && (
                    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl rounded-bl-sm border-2 border-ink bg-white p-3 shadow-hard-sm">
                      <p className="sticker mb-2 w-fit -rotate-1 bg-sun-400">{tn.a.title}</p>
                      {tn.a.what ? (
                        <dl className="space-y-2 text-[14px] leading-relaxed">
                          <div><dt className="label">{t("assistant.what")}</dt><dd>{tn.a.what}</dd></div>
                          <div><dt className="label">{t("assistant.read")}</dt><dd>{tn.a.read}</dd></div>
                          <div><dt className="label">{t("assistant.do")}</dt><dd>{tn.a.do}</dd></div>
                        </dl>
                      ) : <p className="whitespace-pre-line text-[14px] leading-relaxed">{tn.a.answer}</p>}
                      <div className="mt-3 rounded-xl border-2 border-dashed border-ink/30 bg-paper p-2">
                        <p className="label">{t("assistant.now")}</p>
                        <ul className="mt-1 space-y-0.5 text-[13px]">{tn.a.facts.map((f, k) => <li key={k}>• {f}</li>)}</ul>
                      </div>
                      <p className="mt-2 text-[10px] font-bold uppercase tracking-wider text-ink/40">{tn.a.method}{tn.a.note ? ` · ${tn.a.note}` : ""}</p>
                    </motion.div>
                  )}
                </div>
              ))}
              <div ref={end} />
            </div>
            <div className="border-t-2 border-ink p-3">
              <div className="mb-2 flex flex-wrap gap-1">
                {[t("assistant.s1"), t("assistant.s2"), t("assistant.s3")].map((s) => (
                  <button key={s} className="border-[1.5px] border-ink bg-bone px-2 py-0.5 font-mono text-[10.5px] font-bold uppercase hover:bg-ink hover:text-bone" onClick={() => ask(section, s, context)}>{s}</button>
                ))}
              </div>
              <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); if (q.trim()) { ask(section, q.trim(), context); setQ(""); } }}>
                <input className="input" value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("assistant.placeholder")} aria-label={t("assistant.placeholder")} maxLength={500} />
                <button className="btn-primary" disabled={busy || !q.trim()} aria-label={t("assistant.send")}><Send size={15} /></button>
              </form>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>
    </>
  );
}
