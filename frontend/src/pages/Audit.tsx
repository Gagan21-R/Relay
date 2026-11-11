import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Bot, Cpu, UserRound } from "lucide-react";
import { PageHeader } from "../components/Layout";
import { Empty, simTime } from "../components/ui";
import { useApi } from "../hooks/useApi";

const ACTOR: Record<string, { icon: any; tone: string }> = { agent: { icon: Bot, tone: "bg-brand-300" }, human: { icon: UserRound, tone: "bg-lime-400" }, system: { icon: Cpu, tone: "bg-cobalt-300" } };

export default function Audit() {
  const { t } = useTranslation();
  const { data } = useApi<any[]>("/api/audit?limit=2000", ["audit"], 800);
  const [type, setType] = useState("");
  const [action, setAction] = useState("");
  const [q, setQ] = useState("");
  const [open, setOpen] = useState<number | null>(null);
  const actions = useMemo(() => [...new Set((data ?? []).map((a) => a.action))].sort(), [data]);
  const list = useMemo(() => (data ?? []).filter((a) => (!type || a.actor_type === type) && (!action || a.action === action)
    && (!q || `${a.actor} ${a.action} ${a.summary}`.toLowerCase().includes(q.toLowerCase()))).slice(0, 400), [data, type, action, q]);
  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.audit")} sub={t("pages.audit")} kicker={`${data?.length ?? 0} entries`} tone="bg-sun-400" section="audit.page" />
      <div className="card flex flex-wrap items-center gap-2 p-3">
        <div className="flex rounded-xl border-2 border-ink bg-white p-0.5">
          {["", "agent", "human", "system"].map((k) => <button key={k} onClick={() => setType(k)} className={`rounded-lg px-3 py-1 text-xs font-extrabold ${type === k ? "bg-ink text-white" : ""}`}>{k || "all"}</button>)}
        </div>
        <select className="input !w-auto !py-1" value={action} onChange={(e) => setAction(e.target.value)} aria-label="Action">
          <option value="">every action</option>{actions.map((a) => <option key={a} value={a}>{a.replace(/_/g, " ")}</option>)}
        </select>
        <input className="input !w-64 !py-1" placeholder="search…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search" />
        <span className="ml-auto text-xs font-bold text-ink/60">showing {list.length}</span>
      </div>
      {!list.length ? <Empty>No entries match.</Empty> : (
        <ol className="space-y-1">
          {list.map((a) => {
            const A = ACTOR[a.actor_type] ?? ACTOR.system;
            const I = A.icon;
            return (
              <li key={a.id}>
                <button onClick={() => setOpen(open === a.id ? null : a.id)} className="flex w-full items-start gap-2 rounded-xl border-2 border-ink/15 bg-white px-3 py-2 text-left text-sm hover:border-ink">
                  <span className={`grid h-7 w-7 shrink-0 place-items-center rounded-lg border-2 border-ink ${A.tone}`}><I size={14} aria-hidden /></span>
                  <span className="w-20 shrink-0 font-mono text-xs font-bold text-ink/60">{simTime(a.sim_time)}</span>
                  <span className="w-44 shrink-0 truncate font-extrabold">{a.actor}</span>
                  <span className="badge shrink-0 bg-paper">{a.action.replace(/_/g, " ")}</span>
                  <span className="min-w-0 flex-1 text-ink/80">{a.summary}</span>
                </button>
                {open === a.id && (
                  <pre className="mx-3 mt-1 max-h-72 overflow-auto rounded-xl border-2 border-ink bg-ink p-3 text-[11px] text-lime-300">{JSON.stringify({ object: `${a.object_type ?? "-"} ${a.object_id ?? ""}`, inputs: a.inputs, outputs: a.outputs, at: a.created_at }, null, 2)}</pre>
                )}
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}
