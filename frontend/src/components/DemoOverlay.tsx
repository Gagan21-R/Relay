// Run Demo: plays the 12 deck steps on the live system with captions. It survives navigation (mounted in the layout)
// and takes you to the page each step happens on. Steps 7 and 12 stop for a person to approve.
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Check, ChevronRight, Pause, Play, X } from "lucide-react";
import { api } from "../services/api";

type StepOut = { n: number; title: string; page: string; status: string; lines: string[]; focus?: any };
type DemoState = { open: boolean; running: boolean; step: number; results: StepOut[]; busy: boolean; error?: string };

let setter: ((f: (s: DemoState) => DemoState) => void) | null = null;
export const startDemo = () => setter?.(() => ({ open: true, running: true, step: 1, results: [], busy: false }));

export default function DemoOverlay() {
  const nav = useNavigate();
  const [s, setS] = useState<DemoState>({ open: false, running: false, step: 1, results: [], busy: false });
  const timer = useRef<number>();
  useEffect(() => { setter = (f) => setS(f); return () => { setter = null; }; }, []);
  const last = s.results[s.results.length - 1];
  const waiting = last?.status === "waiting_for_approval";

  const run = async (n: number) => {
    setS((x) => ({ ...x, busy: true, error: undefined }));
    try {
      const r = await api<StepOut>(`/api/sim/demo/step/${n}`, { method: "POST", body: JSON.stringify({}) });
      nav(r.focus?.incident_id ? `/incidents?focus=${r.focus.incident_id}` : r.page);
      setS((x) => ({ ...x, busy: false, results: [...x.results.filter((y) => y.n !== n), r], step: r.status === "done" ? n + 1 : n }));
    } catch (e: any) { setS((x) => ({ ...x, busy: false, running: false, error: e.message })); }
  };
  useEffect(() => {
    window.clearTimeout(timer.current);
    if (!s.open || !s.running || s.busy || waiting || s.step > 12) return;
    timer.current = window.setTimeout(() => run(s.step), s.results.length ? 5200 : 300);
    return () => window.clearTimeout(timer.current);
  }); // eslint-disable-line react-hooks/exhaustive-deps

  const approve = async () => {
    if (!last?.focus) return;
    setS((x) => ({ ...x, busy: true }));
    if (last.focus.plan_id) await api(`/api/plans/${last.focus.plan_id}/approve`, { method: "POST", body: JSON.stringify({ approver_name: "Duty officer", comment: "approved during the demo" }) });
    if (last.focus.recon_id) await api(`/api/recon/${last.focus.recon_id}/approve`, { method: "POST", body: JSON.stringify({ who: "Duty officer" }) });
    setS((x) => ({ ...x, busy: false }));
    run(last.n);
  };
  if (!s.open) return null;
  return (
    <motion.aside initial={{ y: 200, opacity: 0 }} animate={{ y: 0, opacity: 1 }} role="region" aria-label="Run Demo"
      className="fixed bottom-4 left-4 z-[1200] w-[min(460px,calc(100vw-2rem))] overflow-hidden rounded-3xl border-2 border-ink bg-white shadow-hard-lg lg:left-72">
      <div className="flex items-center gap-2 border-b-2 border-ink bg-ink px-4 py-2 text-white">
        <span className="mega text-xl text-lime-400">Run Demo</span>
        <span className="font-mono text-xs">step {Math.min(s.step, 12)}/12</span>
        <div className="ml-auto flex gap-1">
          {s.step <= 12 && <button className="rounded-lg border-2 border-white/50 p-1" onClick={() => setS((x) => ({ ...x, running: !x.running }))} aria-label={s.running ? "Pause" : "Play"}>{s.running ? <Pause size={14} /> : <Play size={14} />}</button>}
          {s.step <= 12 && !waiting && <button className="rounded-lg border-2 border-white/50 p-1" disabled={s.busy} onClick={() => run(s.step)} aria-label="Next step"><ChevronRight size={14} /></button>}
          <button className="rounded-lg border-2 border-white/50 p-1" onClick={() => setS((x) => ({ ...x, open: false, running: false }))} aria-label="Close demo"><X size={14} /></button>
        </div>
      </div>
      <div className="flex gap-1 px-4 pt-3" aria-hidden>
        {Array.from({ length: 12 }, (_, i) => <span key={i} className={`h-2 flex-1 rounded-full border border-ink ${i + 1 < s.step ? "bg-lime-400" : i + 1 === s.step ? (waiting ? "bg-pink-400" : "animate-pulse bg-sun-400") : "bg-paper"}`} />)}
      </div>
      <div className="max-h-[42vh] overflow-y-auto p-4">
        {last ? (
          <div key={`${last.n}${last.status}`} className="demo-in">
            <p className="sticker -rotate-1 bg-sun-400">{last.n}. {last.title}</p>
            <ul className="mt-2 space-y-1 text-[13px] leading-snug">{last.lines.map((l, i) => <li key={i} className="rounded-lg bg-paper px-2 py-1">{l}</li>)}</ul>
            {waiting && <button className="btn-pop mt-3 w-full justify-center py-2 text-base" disabled={s.busy} onClick={approve}><Check size={17} aria-hidden />{last.focus?.plan_id ? "Approve plan as Duty officer" : "Approve recon as Duty officer"}</button>}
          </div>
        ) : <p className="text-sm font-bold">{s.busy ? "Resetting the scenario to T+0…" : "Starting…"}</p>}
        {s.step > 12 && <p className="mt-3 sticker bg-lime-400">Demo complete — all 12 steps ran on the live system.</p>}
        {s.error && <p className="mt-2 text-sm font-bold text-pink-500">{s.error}</p>}
      </div>
    </motion.aside>
  );
}
