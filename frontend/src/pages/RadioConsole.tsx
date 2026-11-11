// Control-room operators type in reports received by HAM radio, police wireless, forest/railway radio or satellite phone.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Radio } from "lucide-react";
import { PageHeader } from "../components/Layout";
import ReportCard from "../components/ReportCard";
import { Empty, Panel } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";
import { Report, Zone } from "../services/types";

const KINDS = [
  ["satphone", "Satellite phone (NDRF/SDRF)"], ["police_wireless", "Police wireless"], ["forest_radio", "Forest radio"],
  ["railway_radio", "Railway radio"], ["ham", "HAM radio"],
];

export default function RadioConsole() {
  const { t } = useTranslation();
  const zones = useApi<Zone[]>("/api/zones");
  const recent = useApi<Report[]>("/api/reports?channel=radio_entry&limit=20", ["report"]);
  const [f, setF] = useState({ kind: "satphone", callsign: "NDRF-2", zone_code: "", message: "", operator: "Operator 1" });
  const [err, setErr] = useState<string | null>(null);
  const submit = async () => {
    setErr(null);
    try {
      await api("/api/intake/radio", { method: "POST", body: JSON.stringify({ ...f, zone_code: f.zone_code || null }) });
      setF({ ...f, message: "" }); recent.reload();
    } catch (e: any) { setErr(e.message); }
  };
  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.radio")} sub={t("pages.radio")} section="radio.page" />
      <div className="grid gap-4 xl:grid-cols-[440px_1fr]">
        <Panel title="Log a radio / sat-phone message">
          <div className="grid gap-2 text-sm">
            <div className="grid grid-cols-2 gap-2">
              <select className="input" value={f.kind} onChange={(e) => setF({ ...f, kind: e.target.value })} aria-label="Channel">
                {KINDS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
              </select>
              <input className="input" value={f.callsign} onChange={(e) => setF({ ...f, callsign: e.target.value })} placeholder="Callsign / team" aria-label="Callsign or team" />
            </div>
            <select className="input" value={f.zone_code} onChange={(e) => setF({ ...f, zone_code: e.target.value })} aria-label="Zone">
              <option value="">Zone (if the message does not name a place)</option>
              {zones.data?.map((z) => <option key={z.code} value={z.code}>{z.name}</option>)}
            </select>
            <textarea className="input" rows={5} value={f.message} onChange={(e) => setF({ ...f, message: e.target.value })} placeholder="Message as received, in any language" />
            <input className="input" value={f.operator} onChange={(e) => setF({ ...f, operator: e.target.value })} aria-label="Operator name" />
            <button className="btn-primary justify-center py-2" disabled={f.message.trim().length < 3 || !f.callsign} onClick={submit}><Radio size={15} aria-hidden />Log message</button>
            {err && <p className="text-xs text-pink-500">{err}</p>}
            <p className="text-xs text-ink/60">Radio and satellite phones keep working when towers and power are down. A team report from a silent zone resolves its blackout alert and turns into normal incidents.</p>
          </div>
        </Panel>
        <Panel title="Recent radio entries">
          {!recent.data?.length ? <Empty>No radio entries yet.</Empty> : <div className="space-y-2">{recent.data.map((r) => <ReportCard key={r.id} r={r} />)}</div>}
        </Panel>
      </div>
    </div>
  );
}
