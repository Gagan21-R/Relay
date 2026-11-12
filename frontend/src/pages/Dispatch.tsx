// Task board: created -> approved -> assigned -> dispatched -> delivered -> confirmed (+ failed / cancelled).
// The backend enforces who may do what (403) and which moves are valid (409); this page shows the reason when it refuses.
// Route safety, unverified roads, alternatives and the deterministic volunteer ranking are shown on every task.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { AlarmClock, CheckCircle2, MessageSquare, PackageCheck, Route as RouteIcon, ShieldCheck, Truck, UserCheck, XCircle } from "lucide-react";
import { PageHeader } from "../components/Layout";
import MiniMap from "../components/MiniMap";
import { Empty, Panel, simTime } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api, useRole } from "../services/api";

const COLS = [
  { k: "approved", label: "Approved · needs a volunteer", tone: "bg-white" },
  { k: "assigned", label: "Assigned · verify route", tone: "bg-sun-300" },
  { k: "dispatched", label: "Dispatched", tone: "bg-cobalt-300" },
  { k: "delivered", label: "Delivered · NOT yet confirmed", tone: "bg-tangerine-300" },
  { k: "confirmed", label: "Confirmed by Duty Officer", tone: "bg-mint-300" },
  { k: "failed", label: "Failed / cancelled", tone: "bg-pink-300" },
];
const ROUTE_COLOR: Record<string, string> = { assigned: "#E6D8BC", dispatched: "#B9AE9C", delivered: "#D9A27A", confirmed: "#A9C29A", failed: "#E6A994" };

export function SafetyBadge({ label }: { label?: string }) {
  if (!label) return null;
  const ok = label === "verified passable";
  return <span className={`badge ${ok ? "bg-mint-300" : "bg-sun-400"}`}><ShieldCheck size={11} aria-hidden />{ok ? "route verified passable" : "route unverified — verify before dispatch"}</span>;
}

function TaskCard({ d, act }: { d: any; act: (path: string, body?: any) => void }) {
  const [open, setOpen] = useState(false);
  const ri = d.route_info ?? {};
  const me = useRole();
  const mine = me.role === "volunteer" && d.volunteer?.code === me.actor;
  const officer = me.role === "duty_officer";
  return (
    <motion.article layout animate={{ opacity: 1, scale: 1 }}
      className={`rounded-xl border-2 border-ink bg-white p-2.5 text-xs ${d.overdue ? "shadow-hard-pink ring-2 ring-pink-500" : "shadow-hard-sm"}`}>
      <div className="flex flex-wrap items-center gap-1.5"><Truck size={13} aria-hidden /><b className="font-mono">D-{d.id}</b>
        <span className="badge bg-white">{d.vehicle ?? "vehicle?"}</span>{d.overdue && <span className="badge bg-pink-500 text-ink">overdue</span>}
        {mine && <span className="badge bg-lime-300">your task</span>}</div>
      <p className="mt-1 font-extrabold leading-tight">{d.to_name}</p>
      <p className="font-medium text-ink/60">{d.resource_lines.map((l: any) => `${l.quantity} ${l.resource_type.replace(/_/g, " ")}`).join(" · ")}</p>
      <p className="mt-1 font-bold">{d.volunteer ? `${d.volunteer.code} ${d.volunteer.name} · reliability ${d.volunteer.reliability.toFixed(2)}` : "no volunteer yet"}</p>
      <div className="mt-1 flex flex-wrap gap-1"><SafetyBadge label={ri.safety} />
        {ri.verified && <span className="badge bg-mint-200">checked by {d.route_verified_by}</span>}
        {ri.stale && <span className="badge bg-pink-300">route cut: {ri.stale}</span>}</div>
      <p className="mt-1 font-mono text-[11px]">{(ri.road_names ?? []).join(" + ") || "in-town"} · {ri.km ?? "?"} km · ETA {d.eta ? simTime(d.eta) : `~${ri.eta_h ?? "?"} h`}{ri.eta_reliable === false ? " (unreliable)" : ""}</p>
      {d.recipient_confirmed_at != null && d.status === "delivered" && <p className="mt-1 flex items-center gap-1 text-[11px] font-bold text-brand-600"><MessageSquare size={11} aria-hidden />recipient said YES at {simTime(d.recipient_confirmed_at)} — evidence; officer must confirm</p>}
      {d.status === "delivered" && d.recipient_confirmed_at == null && <p className="mt-1 text-[11px] font-bold text-ink/60">confirmation SMS sent in {d.confirmation_language ?? "—"}; waiting for reply</p>}
      <div className="mt-1.5 flex flex-wrap gap-1">
        {d.status === "approved" && officer && <button className="btn-ghost !px-1.5 !py-0.5 !text-[11px]" onClick={() => act(`/api/dispatches/${d.id}/assign`, {})}><UserCheck size={12} aria-hidden />assign top-ranked</button>}
        {["approved", "assigned"].includes(d.status) && officer && !ri.verified && <button className="btn-ghost !px-1.5 !py-0.5 !text-[11px]" onClick={() => act(`/api/dispatches/${d.id}/verify-route`, {})}><RouteIcon size={12} aria-hidden />verify route</button>}
        {d.status === "assigned" && (officer || mine) && <button className="btn-primary !px-1.5 !py-0.5 !text-[11px]" onClick={() => act(`/api/dispatches/${d.id}/dispatch`)}><Truck size={12} aria-hidden />dispatch</button>}
        {d.status === "dispatched" && (officer || mine) && <button className="btn-ghost !px-1.5 !py-0.5 !text-[11px]" onClick={() => act(`/api/dispatches/${d.id}/deliver`)}><PackageCheck size={12} aria-hidden />mark delivered</button>}
        {d.status === "delivered" && officer && <button className="btn-approve !px-1.5 !py-0.5 !text-[11px]" onClick={() => act(`/api/dispatches/${d.id}/confirm`, { method: d.recipient_confirmed_at != null ? "sms_reply" : "officer_review" })}><CheckCircle2 size={12} aria-hidden />confirm</button>}
        {["approved", "assigned", "dispatched", "delivered"].includes(d.status) && officer && <button className="btn-reject !px-1.5 !py-0.5 !text-[11px]" onClick={() => act(`/api/dispatches/${d.id}/fail`, { reason: "reported by field team" })}><XCircle size={12} aria-hidden />failed</button>}
        <button className="btn-ghost !px-1.5 !py-0.5 !text-[11px]" onClick={() => setOpen(!open)} aria-expanded={open}>{open ? "less" : "why?"}</button>
      </div>
      {open && (
        <div className="mt-2 space-y-1.5 rounded-lg bg-paper p-2 text-[11px]">
          {ri.route_why && <p><b>Route:</b> {ri.route_why}</p>}
          {(ri.unverified_roads ?? []).length > 0 && <p><b>Unverified:</b> {ri.unverified_roads.join("; ")}</p>}
          {ri.shortest && <p><b>Shortest (not chosen):</b> {ri.shortest.road_names.join(" + ")} · {ri.shortest.km} km · {ri.shortest.safety}</p>}
          {(ri.alternatives ?? []).map((a: any, i: number) => <p key={i}><b>Alt {i + 1}:</b> {a.road_names.join(" + ")} · {a.km} km · {a.safety}</p>)}
          {ri.previous_roads && <p><b>Previous route:</b> {ri.previous_roads.join(" + ")}</p>}
          {(ri.volunteer_ranking ?? []).length > 0 && <div><b>Volunteer ranking</b> (skills .40 · reliability .30 · distance .30 · vehicle +.10; ties by ID)
            <ol className="ml-4 list-decimal">{ri.volunteer_ranking.map((v: any) => <li key={v.code}>{v.code} {v.name} — {v.score} · {v.reasons.join("; ")}</li>)}</ol></div>}
          <div><b>History</b><ul className="ml-4 list-disc">{(d.history ?? []).map((h: any, i: number) => <li key={i}>{simTime(h.at)} {h.status} — {h.by} ({h.role}){h.note ? `: ${h.note}` : ""}</li>)}</ul></div>
        </div>
      )}
    </motion.article>
  );
}

export default function Dispatch() {
  const { t } = useTranslation();
  const { data, reload } = useApi<any[]>("/api/dispatches", ["dispatch", "sim"], 300);
  const sim = useApi<any>("/api/state", ["sim"]);
  const [err, setErr] = useState<string | null>(null);
  const act = async (path: string, body: any = {}) => {
    setErr(null);
    try { await api(path, { method: "POST", body: JSON.stringify(body) }); } catch (e: any) { setErr(`${e.status === 403 ? "403 not allowed" : e.status === 409 ? "409 not now" : "error"}: ${e.message}`); }
    reload();
  };
  const all = data ?? [];
  const active = all.filter((d) => ["assigned", "dispatched", "delivered"].includes(d.status));
  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.dispatch")} sub="Every task moves Created → Approved → Assigned → Dispatched → Delivered → Confirmed. Delivered is not Confirmed: only a Duty Officer confirms." kicker={`T+${(sim.data?.clock ?? 0).toFixed(1)} h`} tone="bg-mint-400" section="dispatch.page">
        <button className="btn-ghost" onClick={() => act("/api/dispatches/tick")}><AlarmClock size={15} aria-hidden />Run tracking now</button>
      </PageHeader>
      {err && <p role="alert" className="rounded-xl border-2 border-ink bg-pink-200 p-2 text-sm font-bold">{err}</p>}
      {!all.length ? <Empty>No tasks yet. Approve a plan to create them.</Empty> : (
        <>
          <Panel title="On the move" tone="bg-cobalt-300">
            <MiniMap height={300} routes={active.map((d) => ({ id: d.id, points: d.route, color: ROUTE_COLOR[d.status], dashed: d.route_info?.safety !== "verified passable", label: `D-${d.id} ${d.to_name} · ${d.status} · ${d.route_info?.safety ?? ""}` }))} />
            <p className="mt-1 text-[11px] font-bold text-ink/60">Dashed = route includes unverified roads.</p>
          </Panel>
          <div className="grid gap-3 overflow-x-auto pb-2 md:grid-cols-3 2xl:grid-cols-6">
            {COLS.map((c) => {
              const items = all.filter((d) => c.k === "failed" ? ["failed", "cancelled"].includes(d.status) : d.status === c.k);
              return (
                <section key={c.k} className="min-w-[230px] rounded-2xl border-2 border-ink bg-paper">
                  <h2 className={`flex items-center justify-between border-b-2 border-ink px-3 py-2 text-sm font-extrabold ${c.tone}`}>{c.label}<span className="font-mono">{items.length}</span></h2>
                  <div className="space-y-2 p-2">{items.map((d) => <TaskCard key={d.id} d={d} act={act} />)}</div>
                </section>
              );
            })}
          </div>
          <p className="text-xs font-medium text-ink/60">Permissions (enforced by the backend): Duty Officer — approve, assign, verify routes, dispatch, mark delivered, confirm, fail. Assigned volunteer — dispatch and mark delivered for their own task only. A recipient's SMS "YES" or a shelter check-in is evidence for the officer, not a confirmation.</p>
        </>
      )}
    </div>
  );
}
