// "Internet DOWN in zone X": web, social and field-app reports from that zone stop; SMS, voice and radio continue.
import { Wifi, WifiOff } from "lucide-react";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import { Zone } from "../services/types";
import { Panel } from "./ui";

export default function NetworkPanel({ explain }: { explain?: React.ReactNode }) {
  const { data, reload } = useApi<Zone[]>("/api/zones", ["network", "zone", "signal"]);
  const toggle = async (z: Zone) => {
    await api("/api/sim/network", { method: "POST", body: JSON.stringify({ zone_code: z.code, internet_down: !z.internet_down }) });
    reload();
  };
  return (
    <Panel title="Network status" explain={explain}>
      <p className="mb-2 text-xs text-slate-500">Cut the internet in a zone. Reports needing internet from inside it stop arriving; SMS, voice calls and radio still get through.</p>
      <div className="grid grid-cols-2 gap-1.5">
        {(data ?? []).map((z) => (
          <button key={z.code} onClick={() => toggle(z)} aria-pressed={z.internet_down}
            className={`flex items-center justify-between rounded-lg border px-2.5 py-1.5 text-left text-xs font-medium transition-colors ${z.internet_down ? "border-red-300 bg-red-50 text-red-800" : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"}`}>
            <span>{z.name}{z.tower_status !== "up" && <span className="ml-1 text-[10px] text-red-600">· towers {z.tower_status}</span>}</span>
            {z.internet_down ? <span className="flex items-center gap-1"><WifiOff size={13} aria-hidden />DOWN</span> : <Wifi size={13} className="text-emerald-600" aria-label="internet up" />}
          </button>
        ))}
      </div>
    </Panel>
  );
}
