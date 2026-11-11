// Dispatch tracker: kanban pending -> dispatched -> in transit -> delivered -> confirmed (+ failed), overdue highlighted,
// with the live routes on a map and the three ways to confirm a delivery.
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { AlarmClock, CheckCircle2, MessageSquare, PackageCheck, Truck, XCircle } from "lucide-react";
import { PageHeader } from "../components/Layout";
import MiniMap from "../components/MiniMap";
import { Empty, Panel, simTime } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";

const COLS = [
  { k: "pending", label: "Pending", tone: "bg-white" },
  { k: "dispatched", label: "Dispatched", tone: "bg-sun-300" },
  { k: "in_transit", label: "In transit", tone: "bg-cobalt-300" },
  { k: "delivered", label: "Delivered · awaiting confirmation", tone: "bg-tangerine-300" },
  { k: "confirmed", label: "Confirmed", tone: "bg-mint-300" },
  { k: "failed", label: "Failed", tone: "bg-pink-300" },
];
const ROUTE_COLOR: Record<string, string> = { dispatched: "#F5B800", in_transit: "#2E5BFF", delivered: "#FF6A00", confirmed: "#14C48A", failed: "#E11D48" };

export default function Dispatch() {
  const { t } = useTranslation();
  const { data, reload } = useApi<any[]>("/api/dispatches", ["dispatch", "sim"], 300);
  const sim = useApi<any>("/api/state", ["sim"]);
  const act = async (path: string, method: string, body: any) => { await api(path, { method, body: JSON.stringify(body) }); reload(); };
  const all = data ?? [];
  const active = all.filter((d) => ["dispatched", "in_transit", "delivered"].includes(d.status));
  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.dispatch")} sub={t("pages.dispatch")} kicker={`T+${(sim.data?.clock ?? 0).toFixed(1)} h`} tone="bg-mint-400">
        <button className="btn-ghost" onClick={() => act("/api/dispatches/tick", "POST", {})}><AlarmClock size={15} aria-hidden />Run tracking now</button>
      </PageHeader>
      {!all.length ? <Empty>No dispatches yet. Approve a plan to start.</Empty> : (
        <>
          <Panel title="On the move" tone="bg-cobalt-300">
            <MiniMap height={300} routes={active.map((d) => ({ id: d.id, points: d.route, color: ROUTE_COLOR[d.status], dashed: d.status === "dispatched", label: `D-${d.id} ${d.to_name} · ${d.status}` }))} />
          </Panel>
          <div className="grid gap-3 overflow-x-auto pb-2 md:grid-cols-3 2xl:grid-cols-6">
            {COLS.map((c) => {
              const items = all.filter((d) => d.status === c.k);
              return (
                <section key={c.k} className="min-w-[220px] rounded-2xl border-2 border-ink bg-paper">
                  <h2 className={`flex items-center justify-between rounded-t-[14px] border-b-2 border-ink px-3 py-2 text-sm font-extrabold ${c.tone}`}>{c.label}<span className="font-mono">{items.length}</span></h2>
                  <div className="space-y-2 p-2">
                    {items.map((d) => (
                      <motion.article key={d.id} layout initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                        className={`rounded-xl border-2 border-ink bg-white p-2.5 text-xs ${d.overdue ? "shadow-hard-pink ring-2 ring-pink-500" : "shadow-hard-sm"}`}>
                        <div className="flex items-center gap-1.5"><Truck size={13} aria-hidden /><b className="font-mono">D-{d.id}</b>{d.overdue && <span className="badge bg-pink-500 text-white">overdue</span>}</div>
                        <p className="mt-1 font-extrabold leading-tight">{d.to_name}</p>
                        <p className="font-medium text-ink/60">{d.resource_lines.map((l: any) => `${l.quantity} ${l.resource_type.replace("_", " ")}`).join(" · ")}</p>
                        <p className="font-medium text-ink/60">{d.assigned_team}</p>
                        <p className="font-mono text-[11px]">ETA {simTime(d.eta)}{d.confirmed_at ? ` · confirmed ${simTime(d.confirmed_at)} (${d.confirmation_method})` : ""}</p>
                        {d.status === "delivered" && <p className="mt-1 flex items-center gap-1 text-[11px] font-bold text-brand-600"><MessageSquare size={11} aria-hidden />confirmation SMS sent in {d.confirmation_language ?? "—"}</p>}
                        <div className="mt-1.5 flex flex-wrap gap-1">
                          {["dispatched", "in_transit"].includes(d.status) && <button className="btn-ghost !px-1.5 !py-0.5 !text-[11px]" onClick={() => act(`/api/dispatches/${d.id}`, "PATCH", { status: "delivered" })}><PackageCheck size={12} aria-hidden />arrived</button>}
                          {["dispatched", "in_transit", "delivered"].includes(d.status) && <button className="btn-pop !px-1.5 !py-0.5 !text-[11px]" onClick={() => act(`/api/dispatches/${d.id}/confirm`, "POST", { method: "field_team" })}><CheckCircle2 size={12} aria-hidden />field confirm</button>}
                          {["dispatched", "in_transit"].includes(d.status) && <button className="btn-danger !px-1.5 !py-0.5 !text-[11px]" onClick={() => act(`/api/dispatches/${d.id}`, "PATCH", { status: "failed", note: "reported by field team" })}><XCircle size={12} aria-hidden />failed</button>}
                        </div>
                      </motion.article>
                    ))}
                  </div>
                </section>
              );
            })}
          </div>
          <p className="text-xs font-medium text-ink/60">A delivery is confirmed by the field team, by the shelter manager's check-in, or by the recipient replying YES (in their language) to RELAY's SMS. Unconfirmed deliveries escalate after 2 h; late ones are flagged overdue.</p>
        </>
      )}
    </div>
  );
}
