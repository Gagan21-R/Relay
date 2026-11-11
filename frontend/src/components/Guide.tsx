// Guided run: one scenario, step by step, on the live system. It takes you to the page where the work is happening,
// explains what just happened, moves on by itself when a step is done, and waits when a Duty Officer must decide
// (approve, verify routes and dispatch, send a public message, confirm deliveries) — do it here or on the page.
import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Check, ChevronDown, ChevronRight, ChevronUp, Loader2, Pause, Play, RotateCcw, X } from "lucide-react";
import { api } from "../services/api";

type Step = { n: number; title: string; page: string; what: string };
type Out = { n: number; total: number; title: string; page: string; what: string; status: "done" | "waiting"; lines: string[];
  action: { label: string; kind: string; plan_id?: number } | null; focus?: any };
type GuideState = { open: boolean; running: boolean; step: number; steps: Step[]; last?: Out; busy: boolean; error?: string;
  scenario?: string; countdown: number; finished: boolean; collapsed: boolean };

const AUTO_NEXT_S = 6;
const INIT: GuideState = { open: false, running: false, step: 1, steps: [], busy: false, countdown: 0, finished: false, collapsed: false };
let setter: ((f: (s: GuideState) => GuideState) => void) | null = null;
let startFn: ((scenario?: string) => void) | null = null;

/** Launch a scenario at T+0 and walk through it. Without an id: restart the current scenario. */
export const startGuide = (scenario?: string) => startFn?.(scenario);
export const guideOpen = () => setter?.((s) => ({ ...s, open: true }));

export default function GuideOverlay() {
  const nav = useNavigate();
  const loc = useLocation();
  const [s, setS] = useState<GuideState>(INIT);
  const timer = useRef<number>();
  const poll = useRef<number>();

  const goto = (o: Out) => { const p = o.focus?.plan_id && o.page === "/plans" ? "/plans" : o.page; if (loc.pathname !== p) nav(p); };
  const run = async (n: number) => {
    setS((x) => ({ ...x, busy: true, error: undefined }));
    try {
      const o = await api<Out>(`/api/lab/guide/step/${n}`, { method: "POST" });
      goto(o);
      setS((x) => ({ ...x, busy: false, last: o, step: n, countdown: o.status === "done" ? AUTO_NEXT_S : 0, finished: o.status === "done" && n >= o.total }));
    } catch (e: any) { setS((x) => ({ ...x, busy: false, running: false, error: e.message })); }
  };
  const start = async (scenario?: string) => {
    setS({ ...INIT, open: true, running: true, busy: true });
    try {
      const g = await api<any>("/api/lab/guide/start", { method: "POST", body: JSON.stringify({ scenario: scenario ?? null }) });
      setS((x) => ({ ...x, steps: g.steps, scenario: g.scenario?.name }));
      await run(1);
    } catch (e: any) { setS((x) => ({ ...x, busy: false, running: false, error: e.message })); }
  };
  const startRef = useRef(start);
  startRef.current = start;
  // registered in an effect (not during render) so React's dev double-mount cannot leave it unset
  useEffect(() => {
    setter = (f) => setS(f);
    startFn = (scenario?: string) => { startRef.current(scenario); };
    return () => { setter = null; startFn = null; };
  }, []);

  // done → count down, then the next step (and its page)
  useEffect(() => {
    window.clearTimeout(timer.current);
    if (!s.open || !s.running || s.busy || !s.last || s.last.status !== "done" || s.finished) return;
    if (s.countdown > 0) { timer.current = window.setTimeout(() => setS((x) => ({ ...x, countdown: x.countdown - 1 })), 1000); return; }
    run(s.step + 1);
  }); // eslint-disable-line react-hooks/exhaustive-deps

  // waiting → re-check every 3 s, so acting on the page itself also moves the guide on
  useEffect(() => {
    window.clearInterval(poll.current);
    if (!s.open || !s.last || s.last.status !== "waiting") return;
    poll.current = window.setInterval(() => { if (!s.busy) run(s.step); }, 3000);
    return () => window.clearInterval(poll.current);
  }); // eslint-disable-line react-hooks/exhaustive-deps

  const act = async () => {
    if (!s.last?.action) return;
    setS((x) => ({ ...x, busy: true, error: undefined }));
    try {
      const o = await api<Out>(`/api/lab/guide/act/${s.step}`, { method: "POST", body: JSON.stringify({ kind: s.last.action.kind, plan_id: s.last.action.plan_id ?? null }) });
      goto(o);
      setS((x) => ({ ...x, busy: false, last: o, countdown: o.status === "done" ? AUTO_NEXT_S : 0, finished: o.status === "done" && x.step >= o.total }));
    } catch (e: any) {
      setS((x) => ({ ...x, busy: false, error: e.status === 403 ? "Only a Duty Officer can do this: switch 'Acting as' to Duty Officer in the header." : e.message }));
    }
  };

  if (!s.open) return null;
  const o = s.last;
  const total = o?.total ?? (s.steps.length || 14);
  return (
    <motion.aside initial={{ y: 200, opacity: 0 }} animate={{ y: 0, opacity: 1 }} role="region" aria-label="Guided run"
      className="fixed bottom-4 left-4 z-[1200] w-[min(500px,calc(100vw-2rem))] overflow-hidden rounded-3xl border-2 border-ink bg-white shadow-hard-lg lg:left-72">
      <div className="flex items-center gap-2 border-b-2 border-ink bg-ink px-4 py-2 text-white">
        <span className="mega text-lg text-lime-400">Guided run</span>
        <span className="min-w-0 flex-1 truncate font-mono text-[11px]">{s.scenario ?? ""} · step {Math.min(s.step, total)}/{total}</span>
        <button className="rounded-lg border-2 border-white/50 p-1" onClick={() => setS((x) => ({ ...x, running: !x.running }))} aria-label={s.running ? "Pause" : "Play"}>{s.running ? <Pause size={14} /> : <Play size={14} />}</button>
        {o?.status === "done" && !s.finished && <button className="rounded-lg border-2 border-white/50 p-1" disabled={s.busy} onClick={() => run(s.step + 1)} aria-label="Next step"><ChevronRight size={14} /></button>}
        <button className="rounded-lg border-2 border-white/50 p-1" onClick={() => startGuide()} aria-label="Restart this scenario"><RotateCcw size={14} /></button>
        <button className="rounded-lg border-2 border-white/50 p-1" onClick={() => setS((x) => ({ ...x, collapsed: !x.collapsed }))} aria-label={s.collapsed ? "Expand" : "Collapse"}>{s.collapsed ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</button>
        <button className="rounded-lg border-2 border-white/50 p-1" onClick={() => setS((x) => ({ ...x, open: false, running: false }))} aria-label="Close guided run"><X size={14} /></button>
      </div>
      <div className="flex gap-1 px-4 pt-3" aria-hidden>
        {Array.from({ length: total }, (_, i) => <span key={i} className={`h-2 flex-1 border border-ink ${i + 1 < s.step || (i + 1 === s.step && o?.status === "done") ? "bg-lime-400" : i + 1 === s.step ? (o?.status === "waiting" ? "bg-pink-400" : "animate-pulse bg-sun-400") : "bg-paper"}`} />)}
      </div>
      {!s.collapsed && (
        <div className="grid max-h-[46vh] grid-cols-[150px_1fr] gap-3 overflow-y-auto p-4">
          <ol className="space-y-0.5 text-[11px]" aria-label="Sequence">
            {(s.steps.length ? s.steps : []).map((st) => (
              <li key={st.n} className={`flex items-start gap-1 rounded px-1 ${st.n === s.step ? "bg-sun-300 font-extrabold" : st.n < s.step ? "text-ink/50" : ""}`}>
                <span className="w-4 shrink-0 text-right font-mono">{st.n < s.step || (st.n === s.step && o?.status === "done") ? "✔" : st.n}</span><span>{st.title}</span>
              </li>))}
          </ol>
          <div>
            {o ? (
              <div key={`${o.n}${o.status}`} className="demo-in">
                <p className="sticker -rotate-1 bg-sun-400">{o.n}. {o.title}</p>
                <p className="mt-1 text-[11px] font-bold text-ink/60">Now on: <span className="font-mono">{o.page}</span> — {o.what}</p>
                <ul className="mt-2 space-y-1 text-[12.5px] leading-snug">{o.lines.map((l, i) => <li key={i} className="rounded-lg bg-paper px-2 py-1">{l}</li>)}</ul>
                {o.status === "waiting" && o.action && (
                  <>
                    <button className="btn-pop mt-3 w-full justify-center py-2 text-sm" disabled={s.busy} onClick={act}><Check size={16} aria-hidden />{o.action.label}</button>
                    <p className="mt-1 text-[11px] text-ink/60">…or do it yourself on this page — the guide continues as soon as it is done.</p>
                  </>
                )}
                {o.status === "done" && !s.finished && s.running && <p className="mt-2 text-[11px] font-bold text-brand-600">Next step in {s.countdown} s…</p>}
              </div>
            ) : <p className="flex items-center gap-2 text-sm font-bold"><Loader2 size={15} className="animate-spin" aria-hidden />Starting the scenario at T+0…</p>}
            {s.finished && <p className="mt-3 sticker bg-lime-400">Done — the whole scenario ran on the live system. Open Scenario Lab → Final report for the debrief.</p>}
            {s.error && <p className="mt-2 text-sm font-bold text-pink-500">{s.error}</p>}
          </div>
        </div>
      )}
    </motion.aside>
  );
}
