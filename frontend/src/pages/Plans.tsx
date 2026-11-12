import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Check, History, Pencil, RefreshCw, Stamp, X } from "lucide-react";
import { PageHeader } from "../components/Layout";
import MiniMap from "../components/MiniMap";
import { Empty, Panel, PRIORITY_STYLE, simTime } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";
import { SafetyBadge } from "./Dispatch";

const COLORS = ["#141210", "#E6A994", "#B9AE9C", "#D9A27A", "#A9C29A", "#E6D8BC", "#141210"];
const STATUS: Record<string, string> = { pending_approval: "bg-sun-400", approved: "bg-mint-400", rejected: "bg-pink-400", superseded: "bg-white", draft: "bg-white" };

export default function Plans() {
  const { t } = useTranslation();
  const { data, reload } = useApi<any[]>("/api/plans", ["plan", "dispatch"], 400);
  const [who, setWho] = useState("Duty officer");
  const [comment, setComment] = useState("");
  const [remove, setRemove] = useState<number[]>([]);
  const [qty, setQty] = useState<Record<string, number>>({});
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const pending = data?.find((p) => p.status === "pending_approval");
  const lines = useMemo(() => (pending?.assignments ?? []).filter((a: any) => a.kind !== "unmet"), [pending]);
  const unmet = (pending?.assignments ?? []).filter((a: any) => a.kind === "unmet");
  const call = async (path: string, body: any, done: string) => {
    setBusy(true); setMsg(null);
    try { await api(path, { method: "POST", body: JSON.stringify(body) }); setMsg(done); setRemove([]); setQty({}); setComment(""); reload(); }
    catch (e: any) { setMsg(e.message); }
    setBusy(false);
  };
  const edited = remove.length > 0 || Object.keys(qty).length > 0;
  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.plans")} sub={t("pages.plans")} kicker="human in the loop" tone="bg-brand-300" section="plans.page">
        <button className="btn-ghost" disabled={busy} onClick={() => call("/api/plans", { reason: "requested by the duty officer" }, "New plan proposed")}><RefreshCw size={15} aria-hidden />Ask for a fresh plan</button>
      </PageHeader>
      {msg && <p className="sticker w-fit bg-lime-400">{msg}</p>}
      {!pending ? <Empty>No plan is waiting for approval. The Coordination agent proposes one when something changes, or ask for a fresh plan.</Empty> : (
        <div className="grid gap-4 xl:grid-cols-[1.25fr_1fr]">
          <div className="space-y-4">
            <Panel tone="bg-sun-400" title={<span className="flex items-center gap-2">Plan v{pending.version} <span className="badge bg-sun-400">awaiting approval</span></span>}>
              <p className="text-[15px] font-medium leading-relaxed">{pending.rationale}</p>
              <p className="mt-1 text-xs font-bold text-ink/50">proposed {simTime(pending.created_at_sim)} by {pending.created_by_agent}</p>
            </Panel>
            <Panel title={`Deliveries (${lines.length})`} tone="bg-lime-400" section="plans.lines">
              <div className="space-y-2">
                {lines.map((a: any, i: number) => {
                  const off = remove.includes(a.line);
                  const p = PRIORITY_STYLE(a.priority);
                  return (
                    <motion.div key={a.line} layout className={`rounded-2xl border-2 border-ink p-3 ${off ? "bg-paper opacity-50 line-through" : "bg-white shadow-hard-sm"}`}>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="h-3 w-3 rounded-full border-2 border-ink" style={{ background: COLORS[i % COLORS.length] }} />
                        <span className="font-mono text-xs font-bold">#{a.line}</span>
                        <span className={`badge ${a.kind === "shelter" ? "bg-cobalt-300" : p.cls}`}>{a.kind === "shelter" ? "shelter top-up" : `${p.label} ${a.priority}`}</span>
                        <span className="font-extrabold">{a.to_name}</span>
                        <label className="ml-auto flex items-center gap-1 text-xs font-bold"><input type="checkbox" checked={off} onChange={() => setRemove(off ? remove.filter((x) => x !== a.line) : [...remove, a.line])} />remove</label>
                      </div>
                      <p className="mt-1 text-sm font-medium">{a.from_depot} → {a.km} km by {a.vehicle} · ETA {a.eta_h} h{a.eta_reliable === false ? " (unreliable)" : ""} · {a.team}</p>
                      <div className="mt-1 flex flex-wrap items-center gap-1.5 text-[11px]">
                        <SafetyBadge label={a.safety} />
                        {a.recommended_volunteer && <span className="badge bg-lime-200">suggested {a.recommended_volunteer.code} · score {a.recommended_volunteer.score}</span>}
                        {a.precedent && <span className="badge bg-paper" title={a.precedent.signature}>{a.precedent.text}</span>}
                      </div>
                      {a.route_why && <p className="mt-1 text-[11px] text-ink/70"><b>Route:</b> {(a.route_names ?? []).join(" + ") || "in town"} — {a.route_why}</p>}
                      <div className="mt-1.5 flex flex-wrap gap-1.5">
                        {a.resources.map((r: any) => {
                          const k = `${a.line}:${r.resource_type}`;
                          return (
                            <label key={k} className="badge gap-1 bg-paper">
                              <input type="number" min={0} className="w-16 bg-transparent font-mono font-bold outline-none" value={qty[k] ?? r.quantity}
                                onChange={(e) => setQty({ ...qty, [k]: Number(e.target.value) })} aria-label={`${r.resource_type} quantity`} />
                              {r.unit} {r.resource_type.replace("_", " ")}
                            </label>
                          );
                        })}
                      </div>
                      <p className="mt-1.5 text-xs text-ink/70"><b>Why:</b> {a.reason}</p>
                      <p className="text-[11px] font-bold text-ink/50">Evidence: {a.evidence.reports ? <>reports {a.evidence.reports.join(", ")} · {a.evidence.confidence} {Math.round((a.evidence.confidence_score ?? 0) * 100)}%{a.incident_id && <> · <Link className="underline" to={`/incidents?focus=${a.incident_id}`}>open evidence</Link></>}</> : `forecast: ${Math.round(a.evidence.forecast?.hours_left)} h of stock left at ${Math.round(a.evidence.forecast?.rate_per_h)}/h`}</p>
                    </motion.div>
                  );
                })}
              </div>
              {unmet.length > 0 && (
                <div className="mt-3 rounded-2xl border-2 border-dashed border-ink bg-pink-300/40 p-3 text-sm">
                  <p className="font-extrabold">Cannot be fully met ({unmet.length})</p>
                  {unmet.map((u: any, i: number) => <p key={i} className="text-xs font-medium">{u.to_name}: {Object.entries(u.wants).map(([k, v]) => `${v} ${k.replace("_", " ")}`).join(", ")} — {u.why}</p>)}
                </div>
              )}
            </Panel>
          </div>
          <div className="space-y-4 xl:sticky xl:top-28 xl:self-start">
            <Panel title="Previous vs updated" tone="bg-tangerine-300" section="plans.changes">
              {!(pending.changes?.changed?.length || pending.changes?.dropped?.length) ? <p className="text-sm font-medium text-ink/60">First plan, or nothing differs from the previous allocation.</p> : (
                <ul className="space-y-1.5 text-xs">
                  {(pending.changes.changed ?? []).map((c: any, i: number) => (
                    <li key={i} className="rounded-xl border-2 border-ink/20 bg-white p-2"><b>#{c.line} {c.to}</b>: {c.change}
                      {c.previous && <span className="text-ink/60"> (was {c.previous})</span>}<br /><span className="font-bold">Why:</span> {c.why}
                      {c.replaces_dispatch && <span className="badge ml-1 bg-sun-300">replaces D-{c.replaces_dispatch} on approval</span>}
                      <span className="badge ml-1 bg-pink-200">needs approval</span></li>))}
                  {(pending.changes.dropped ?? []).map((c: any, i: number) => <li key={`d${i}`} className="rounded-xl bg-paper p-2">{c.to}: {c.change} ({c.previous})</li>)}
                </ul>
              )}
              {pending.changes?.closed_roads?.length > 0 && <p className="mt-2 text-[11px] font-bold text-ink/60">Closed now: {pending.changes.closed_roads.join("; ")}</p>}
              {pending.changes?.note && <p className="mt-1 text-[11px] font-bold">{pending.changes.note}</p>}
            </Panel>
            <Panel title="Routes" tone="bg-cobalt-300">
              <MiniMap routes={lines.filter((a: any) => !remove.includes(a.line)).map((a: any) => ({ id: a.line, points: a.route_points, color: COLORS[lines.indexOf(a) % COLORS.length], label: `#${a.line} ${a.to_name}` }))} height={340} />
            </Panel>
            <Panel title={<span className="flex items-center gap-2"><Stamp size={18} aria-hidden />Decision</span>} tone="bg-pink-400" section="plans.decision">
              <div className="grid gap-2">
                <input className="input" value={who} onChange={(e) => setWho(e.target.value)} aria-label="Approver name" />
                <textarea className="input" rows={2} value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Comment (kept in the audit log)" />
                <div className="flex flex-wrap gap-2">
                  {edited ? (
                    <button className="btn-primary" disabled={busy} onClick={() => call(`/api/plans/${pending.id}/edit`, { approver_name: who, comment, remove_lines: remove, quantities: qty }, "Edited: new version awaits approval")}><Pencil size={15} aria-hidden />Save edits as v{pending.version + 1}</button>
                  ) : (
                    <button className="btn-approve px-5" disabled={busy} onClick={() => call(`/api/plans/${pending.id}/approve`, { approver_name: who, comment }, "Approved: tasks created and volunteers assigned — verify routes and dispatch on the Tasks page")}><Check size={16} aria-hidden />Approve & assign volunteers</button>
                  )}
                  <button className="btn-reject" disabled={busy} onClick={() => call(`/api/plans/${pending.id}/reject`, { approver_name: who, comment }, "Rejected")}><X size={15} aria-hidden />Reject</button>
                </div>
                <p className="text-xs font-medium text-ink/60">Approval creates tasks and assigns the top-ranked free volunteer. Stock leaves the depot only when a task is dispatched, and dispatch needs a verified route. Only a Duty Officer can approve (the backend returns 403 otherwise). Every decision is in the audit log and in the precedent memory.</p>
              </div>
            </Panel>
          </div>
        </div>
      )}
      <Panel title={<span className="flex items-center gap-2"><History size={18} aria-hidden />Version history</span>} section="plans.history">
        {!data?.length ? <Empty>No plans yet.</Empty> : (
          <ol className="space-y-1.5">
            {data.map((p) => (
              <li key={p.id} className="flex flex-wrap items-center gap-2 rounded-xl border-2 border-ink/15 bg-white px-3 py-2 text-sm">
                <span className="mega text-xl">v{p.version}</span>
                <span className={`badge ${STATUS[p.status] ?? "bg-white"}`}>{p.status.replace("_", " ")}</span>
                <span className="font-mono text-xs text-ink/50">{simTime(p.created_at_sim)}</span>
                <span className="min-w-0 flex-1 truncate text-ink/70">{p.trigger}</span>
                <span className="text-xs font-bold">{p.assignments.filter((a: any) => a.kind !== "unmet").length} deliveries</span>
                {p.approvals.map((a: any) => <span key={a.id} className="badge bg-paper">{a.decision} by {a.approver_name}{a.comment ? `: ${a.comment}` : ""}</span>)}
              </li>
            ))}
          </ol>
        )}
      </Panel>
    </div>
  );
}
