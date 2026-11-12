import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, ArrowRight, Clock } from "lucide-react";
import { PageHeader } from "../components/Layout";
import { Empty, Panel, Stat } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";

const LINE_COLORS = ["#000000", "#FF2D00", "#1F3BFF", "#E25B00", "#00A33A", "#E6D8BC"];
const nice = (s: string) => s.replace(/_/g, " ");

export default function Resources() {
  const { t } = useTranslation();
  const { data: o, reload } = useApi<any>("/api/resources/overview", ["inventory", "alert", "dispatch", "sim", "shelter"], 700);
  const [rt, setRt] = useState("water_litres");
  const [count, setCount] = useState<Record<number, string>>({});
  const chart = useMemo(() => {
    if (!o) return { rows: [], keys: [] as string[] };
    const series = o.series.filter((s: any) => s.resource_type === rt);
    const rows: any[] = (series[0]?.points ?? []).map((p: any, i: number) => {
      const r: any = { t: `T+${p.t}` };
      series.forEach((s: any) => { r[s.shelter.split(" ")[0]] = s.points[i].level; });
      return r;
    });
    return { rows, keys: series.map((s: any) => s.shelter.split(" ")[0]) };
  }, [o, rt]);
  const dvs = useMemo(() => !o ? [] : Object.keys({ ...o.demand_by_type, ...o.supply_by_type }).filter((k) => k !== "water_litres").map((k) => ({ resource: nice(k), demand: Math.round(o.demand_by_type[k] ?? 0), supply: Math.round(o.supply_by_type[k] ?? 0) })), [o]);
  const recount = async (id: number) => {
    const q = Number(count[id]);
    if (Number.isNaN(q)) return;
    await api(`/api/inventory/${id}`, { method: "PATCH", body: JSON.stringify({ quantity: q, note: "physical recount" }) });
    reload();
  };
  if (!o) return <PageHeader title={t("nav.resources")} sub={t("pages.resources")} />;
  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.resources")} sub={t("pages.resources")} kicker="supply vs demand" tone="bg-sun-400" section="resources.page" />
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat i={0} label="projected shortages (<24 h)" value={o.projected.length} />
        <Stat i={1} label="current shortages" value={o.current.length} />
        <Stat i={2} label="stale stock rows" value={o.stale.length} />
        <Stat i={3} label={`water standard (L / person / day)`} value={o.standards_per_person_day.water_litres} />
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
        <Panel title="Burn-rate projection by shelter" tone="bg-cobalt-300" section="resources.burn"
          actions={<select className="input !w-auto !py-1" value={rt} onChange={(e) => setRt(e.target.value)} aria-label="Resource">
            {["water_litres", "food_kits", "medical_kits"].map((r) => <option key={r} value={r}>{nice(r)}</option>)}</select>}>
          <div className="h-72">
            <ResponsiveContainer>
              <LineChart data={chart.rows} margin={{ left: 0, right: 12, top: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#00000022" />
                <XAxis dataKey="t" fontSize={11} interval={3} />
                <YAxis fontSize={11} />
                <Tooltip contentStyle={{ border: "2px solid #000000", borderRadius: 12 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <ReferenceLine y={0} stroke="#FF2D00" strokeWidth={2} />
                {chart.keys.map((k: string, i: number) => <Line key={k} dataKey={k} stroke={LINE_COLORS[i % LINE_COLORS.length]} strokeWidth={k.startsWith("Napoklu") ? 4 : 2} dot={false} />)}
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs font-medium text-ink/60">Stock at current occupancy × per-person daily standard, next 48 simulated hours. A line hitting zero is a shortage.</p>
        </Panel>
        <Panel title="Projected shortages & transfers" tone="bg-pink-400" section="resources.transfers">
          {!o.transfers.length ? <Empty>No shelter runs out within {o.horizon_h} h.</Empty> : o.transfers.map((t: any) => (
            <div key={t.shelter_id + t.resource_type} className="mb-2 rounded-2xl border-2 border-ink bg-paper p-3">
              <p className="flex items-center gap-2 font-extrabold"><Clock size={16} aria-hidden />{nice(t.resource_type)} at {t.shelter}: runs out in ~{Math.round(t.hours_left)} h</p>
              <p className="text-xs font-medium text-ink/60">{Math.round(t.quantity)} {t.unit} left · using {Math.round(t.rate_per_h)}/h · {t.needed_for_48h} {t.unit} needed for 48 h</p>
              {t.proposal ? (
                <p className="mt-1.5 flex flex-wrap items-center gap-1.5 text-sm font-bold"><span className="badge bg-lime-400">proposed</span>{t.proposal.depot}<ArrowRight size={14} aria-hidden />{t.shelter.split(" ")[0]} · {t.proposal.km} km · ETA {t.proposal.eta_h} h</p>
              ) : <p className="mt-1.5 flex items-center gap-1.5 text-sm font-bold text-pink-500"><AlertTriangle size={14} aria-hidden />no reachable fresh stock: escalated</p>}
              <p className="mt-1 text-[11px] text-ink/60">{t.why}. The Coordination agent turns this into a plan for approval.</p>
            </div>
          ))}
          {o.current.map((c: any) => (
            <p key={c.resource_type} className="mb-1 rounded-xl bg-pink-300/60 px-2 py-1 text-sm font-bold">{nice(c.resource_type)}: demand {c.demand} &gt; reachable supply {c.supply} (gap {c.gap} {c.unit})</p>
          ))}
        </Panel>
      </div>
      <div className="grid gap-4 xl:grid-cols-[1fr_1.4fr]">
        <Panel title="Demand vs reachable supply" tone="bg-lime-400" section="resources.supply">
          <div className="h-64">
            <ResponsiveContainer>
              <BarChart data={dvs}>
                <CartesianGrid strokeDasharray="3 3" stroke="#00000022" />
                <XAxis dataKey="resource" fontSize={11} /><YAxis fontSize={11} />
                <Tooltip contentStyle={{ border: "2px solid #000000", borderRadius: 12 }} /><Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="demand" fill="#FF2D00" stroke="#000000" strokeWidth={1.5} radius={[6, 6, 0, 0]} />
                <Bar dataKey="supply" fill="#FFFFFF" stroke="#000000" strokeWidth={1.5} radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-ink/60">Water (litres) left out for scale: demand {Math.round(o.demand_by_type.water_litres ?? 0)} L vs supply {Math.round(o.supply_by_type.water_litres ?? 0)} L. Stale stock is not counted as supply.</p>
        </Panel>
        <Panel title="Depot inventory" tone="bg-tangerine-400" section="resources.depots">
          <div className="grid gap-3 md:grid-cols-3">
            {o.depots.map((d: any) => (
              <div key={d.id} className="rounded-2xl border-2 border-ink bg-white p-2.5">
                <p className="font-extrabold leading-tight">{d.name}</p>
                <p className="text-[11px] font-bold text-ink/50">{d.owner}</p>
                <table className="mt-1.5 w-full text-xs"><tbody>
                  {d.inventory.map((i: any) => (
                    <tr key={i.id} className={i.stale ? "bg-sun-300/60" : ""}>
                      <td className="py-0.5 pr-1 font-medium">{nice(i.resource_type)}</td>
                      <td className="text-right font-mono font-bold">{Math.round(i.quantity)}{i.in_transit ? <span className="text-brand-600"> +{Math.round(i.in_transit)}↗</span> : ""}</td>
                    </tr>
                  ))}
                </tbody></table>
                {d.inventory.some((i: any) => i.stale) && (
                  <div className="mt-2 rounded-xl border-2 border-dashed border-ink p-1.5 text-[11px] font-bold">
                    stale: not counted for {d.inventory[0].age_h} h
                    {d.inventory.filter((i: any) => i.stale).slice(0, 2).map((i: any) => (
                      <div key={i.id} className="mt-1 flex gap-1">
                        <input className="input !py-0.5 !text-xs" placeholder={`${nice(i.resource_type)} count`} value={count[i.id] ?? ""} onChange={(e) => setCount({ ...count, [i.id]: e.target.value })} />
                        <button className="btn-ghost !px-1.5 !py-0.5 !text-[11px]" onClick={() => recount(i.id)}>Recount</button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
