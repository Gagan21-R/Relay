// Public messages: area-wise updates from reusable templates, one draft per language, each fact-checked; English
// fallback where no drafted template exists; nothing is sent (mock SMS) without a Duty Officer's approval.
import { useEffect, useState } from "react";
import { CheckCircle2, Megaphone, Send, XCircle } from "lucide-react";
import { PageHeader } from "../components/Layout";
import { Empty, Panel } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";

const TS: Record<string, string> = { source: "bg-mint-300", "drafted-unreviewed": "bg-sun-300", "machine-translated-unreviewed": "bg-sun-400", "english-fallback": "bg-pink-200" };
const SUP: Record<string, string> = { full: "bg-mint-300", basic: "bg-sun-300", pending: "bg-pink-200" };

export default function Communications() {
  const tpl = useApi<any>("/api/communications/templates");
  const list = useApi<any[]>("/api/communications", ["communication"], 300);
  const zones = useApi<any[]>("/api/zones", ["refresh"]);
  const shelters = useApi<any[]>("/api/shelters", ["refresh"]);
  const [tid, setTid] = useState("shelter_open");
  const [zone, setZone] = useState<string>("");
  const [facts, setFacts] = useState<Record<string, string>>({ phone: "1077" });
  const [langs, setLangs] = useState<string[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const t = tpl.data?.templates?.[tid];
  useEffect(() => {   // sensible defaults from the live world
    const z = zones.data?.find((x) => String(x.id) === zone) ?? zones.data?.[0];
    const s = shelters.data?.find((x) => x.zone_id === z?.id) ?? shelters.data?.[0];
    if (z) setFacts((f) => ({ phone: f.phone ?? "1077", time: f.time ?? "10:00", items: f.items ?? "food kits, drinking water", ...f, area: z.name, shelter: s?.name ?? f.shelter ?? "", place: s?.name ?? f.place ?? "" }));
  }, [zone, zones.data, shelters.data]);
  const act = async (path: string, body?: any, done?: string) => {
    setMsg(null);
    try { await api(path, { method: "POST", body: JSON.stringify(body ?? {}) }); if (done) setMsg(done); list.reload(); }
    catch (e: any) { setMsg(`${e.status ?? ""} ${e.message}`); }
  };
  const draft = () => act("/api/communications/draft", { template_id: tid, zone_id: zone ? Number(zone) : null, languages: langs.length ? langs : null,
    facts: Object.fromEntries((t?.fields ?? []).map((k: string) => [k, facts[k] ?? ""])) }, "Drafted — review each language below");
  return (
    <div className="space-y-4">
      <PageHeader title="Public messages" sub="Area-wise updates in the languages people actually use. Facts are preserved and checked; nothing goes out without approval." kicker="human approval before send" tone="bg-tangerine-400" section="comms.page" />
      {msg && <p className="sticker w-fit bg-lime-400">{msg}</p>}
      <div className="grid gap-4 xl:grid-cols-[420px_1fr]">
        <div className="space-y-4">
          <Panel title={<span className="flex items-center gap-2"><Megaphone size={18} aria-hidden />New update</span>} tone="bg-sun-400">
            <div className="grid gap-2 text-sm">
              <label className="font-bold">Template<select className="input" value={tid} onChange={(e) => setTid(e.target.value)}>{Object.keys(tpl.data?.templates ?? {}).map((k) => <option key={k} value={k}>{k.replace(/_/g, " ")}</option>)}</select></label>
              <label className="font-bold">Area<select className="input" value={zone} onChange={(e) => setZone(e.target.value)}><option value="">all areas</option>{(zones.data ?? []).map((z) => <option key={z.id} value={z.id}>{z.name}</option>)}</select></label>
              {(t?.fields ?? []).map((k: string) => <label key={k} className="font-bold">{k.replace("_", " ")}<input className="input" value={facts[k] ?? ""} onChange={(e) => setFacts({ ...facts, [k]: e.target.value })} /></label>)}
              <p className="rounded-lg bg-paper p-2 text-xs"><b>English source:</b> {t?.english}</p>
              <fieldset className="text-xs"><legend className="font-bold">Languages (empty = the area's languages)</legend>
                <div className="mt-1 flex flex-wrap gap-1">{(tpl.data?.languages ?? []).map((l: any) => (
                  <label key={l.code} className={`badge cursor-pointer ${langs.includes(l.code) ? "bg-ink text-white" : "bg-white"}`}>
                    <input type="checkbox" className="sr-only" checked={langs.includes(l.code)} onChange={() => setLangs(langs.includes(l.code) ? langs.filter((x) => x !== l.code) : [...langs, l.code])} />{l.name}</label>))}</div></fieldset>
              <button className="btn-pop" onClick={draft}>Draft in each language</button>
            </div>
          </Panel>
          <Panel title="Language coverage" tone="bg-cobalt-300" section="comms.languages">
            <table className="w-full text-xs"><thead><tr className="text-left"><th>Language</th><th>Understanding</th><th>Outgoing template</th></tr></thead>
              <tbody>{(tpl.data?.languages ?? []).map((l: any) => <tr key={l.code} className="border-t border-ink/10"><td className="py-0.5 font-bold">{l.name}</td>
                <td><span className={`badge ${SUP[l.support]}`}>{l.support}</span></td><td>{l.templates === "none" ? "English fallback" : l.templates}</td></tr>)}</tbody></table>
            <p className="mt-2 text-[11px] font-bold text-ink/60">{tpl.data?.note}</p>
          </Panel>
        </div>
        <Panel title={`Drafts and sent messages (${list.data?.length ?? 0})`} tone="bg-lime-400">
          {!list.data?.length ? <Empty>No messages yet. Draft one on the left.</Empty> : (
            <div className="space-y-2">{list.data.map((c) => (
              <article key={c.id} className="rounded-2xl border-2 border-ink bg-white p-3 text-sm shadow-hard-sm">
                <div className="flex flex-wrap items-center gap-1.5 text-xs"><b className="font-mono">#{c.id}</b><span className="badge bg-white">{c.language_name}</span>
                  <span className={`badge ${TS[c.translation_status] ?? "bg-white"}`}>{c.translation_status}</span><span className="badge bg-paper">{c.template_id.replace(/_/g, " ")} · {c.zone}</span>
                  <span className={`badge ${c.fact_check.ok ? "bg-mint-300" : "bg-pink-400"}`}>facts {c.fact_check.ok ? "preserved" : `MISSING ${[...c.fact_check.missing_fields, ...c.fact_check.missing_numbers].join(", ")}`}</span>
                  <span className="badge bg-ink text-white">{c.status}{c.status === "sent" ? ` · ${c.recipients} phone(s), mock SMS` : ""}</span></div>
                <p className="mt-2 text-[15px] font-medium" lang={c.language}>{c.text}</p>
                {c.language !== "en" && c.translation_status !== "english-fallback" && <p className="mt-1 text-xs text-ink/60">EN: {c.english_text}</p>}
                <div className="mt-2 flex gap-1.5">
                  {c.status === "draft" && <button className="btn-pop !px-2 !py-1 !text-xs" onClick={() => act(`/api/communications/${c.id}/approve`)}><CheckCircle2 size={13} aria-hidden />Approve</button>}
                  {c.status === "draft" && <button className="btn-danger !px-2 !py-1 !text-xs" onClick={() => act(`/api/communications/${c.id}/reject`)}><XCircle size={13} aria-hidden />Reject</button>}
                  {c.status === "approved" && <button className="btn-pop !px-2 !py-1 !text-xs" onClick={() => act(`/api/communications/${c.id}/send`, {}, `Sent #${c.id} (mock SMS)`)}><Send size={13} aria-hidden />Send (mock SMS)</button>}
                </div>
              </article>))}</div>
          )}
        </Panel>
      </div>
    </div>
  );
}
