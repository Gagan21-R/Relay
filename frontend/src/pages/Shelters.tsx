import { useState } from "react";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { CheckCircle2, Route } from "lucide-react";
import { PageHeader } from "../components/Layout";
import { Empty, Meter, simTime } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";

const STATUS: Record<string, string> = { open: "bg-mint-400", full: "bg-sun-400", inaccessible: "bg-pink-500 text-white", unconfirmed: "bg-tangerine-300", closed: "bg-ink text-white" };

export default function Shelters() {
  const { t } = useTranslation();
  const ov = useApi<any>("/api/resources/overview", ["shelter", "inventory", "sim", "alert"], 600);
  const sim = useApi<any>("/api/state", ["sim"]);
  const raw = useApi<any[]>("/api/shelters", ["shelter"], 600);
  const [occ, setOcc] = useState<Record<number, string>>({});
  const checkin = async (id: number) => {
    await api(`/api/shelters/${id}/checkin`, { method: "POST", body: JSON.stringify({ occupancy: occ[id] ? Number(occ[id]) : undefined, note: "manager check-in" }) });
    raw.reload(); ov.reload();
  };
  const now = sim.data?.clock ?? 0;
  if (!ov.data || !raw.data) return <PageHeader title={t("nav.shelters")} sub={t("pages.shelters")} />;
  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.shelters")} sub={t("pages.shelters")} kicker="capacity · access · check-ins" tone="bg-cobalt-300" />
      {!raw.data.length && <Empty>No shelters.</Empty>}
      <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
        {ov.data.shelters.map((s: any, n: number) => {
          const r = raw.data!.find((x) => x.id === s.id);
          const since = now - (r?.last_confirmed_at ?? 0);
          return (
            <motion.article key={s.id} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: n * 0.05 }}
              className={`card overflow-hidden p-0 ${s.status === "inaccessible" ? "shadow-hard-pink" : ""}`}>
              <div className={`flex items-center justify-between border-b-2 border-ink px-4 py-2 ${STATUS[s.status] ?? "bg-white"}`}>
                <span className="text-xs font-extrabold uppercase tracking-wider">{s.status}</span>
                <span className="font-mono text-xs font-bold">{s.occupancy}/{s.capacity}</span>
              </div>
              <div className="p-4">
                <h2 className="text-xl font-extrabold leading-tight">{s.name}</h2>
                <Meter value={s.occupancy / Math.max(1, s.capacity)} label="occupancy" tone={s.occupancy >= s.capacity ? "red" : "brand"} />
                <p className={`mt-2 flex items-center gap-1.5 text-xs font-bold ${s.access.accessible ? "" : "text-pink-500"}`}><Route size={13} aria-hidden />{s.access.why}</p>
                {r?.status_reason && <p className="text-xs font-bold text-pink-500">{r.status_reason}</p>}
                <div className="mt-2 grid grid-cols-2 gap-1.5">
                  {s.burn.filter((b: any) => b.rate_per_h > 0).map((b: any) => (
                    <div key={b.resource_type} className={`rounded-xl border-2 border-ink p-1.5 text-xs ${b.hours_left != null && b.hours_left < 24 ? "bg-pink-300" : "bg-paper"}`}>
                      <p className="font-bold">{b.resource_type.replace("_", " ")}</p>
                      <p className="font-mono">{Math.round(b.quantity)} {b.unit} · {b.hours_left == null ? "—" : `${Math.round(b.hours_left)} h`}</p>
                    </div>
                  ))}
                </div>
                <p className={`mt-2 text-xs font-bold ${since > 6 ? "text-pink-500" : "text-ink/60"}`}>last confirmed {simTime(r?.last_confirmed_at)} ({since.toFixed(1)} h ago{since > 6 ? " — stale" : ""})</p>
                <div className="mt-2 flex gap-1.5">
                  <input className="input !py-1" placeholder="occupancy now" value={occ[s.id] ?? ""} onChange={(e) => setOcc({ ...occ, [s.id]: e.target.value })} aria-label="Occupancy" />
                  <button className="btn-pop shrink-0" onClick={() => checkin(s.id)}><CheckCircle2 size={14} aria-hidden />Check in</button>
                </div>
              </div>
            </motion.article>
          );
        })}
      </div>
    </div>
  );
}
