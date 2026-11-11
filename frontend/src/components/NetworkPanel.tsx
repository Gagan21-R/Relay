// "Internet DOWN in zone X": web, social and field-app reports from that zone stop; SMS, voice and satellite phones continue.
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
    <Panel title="Network status" explain={explain} section="phone.network">
      <p className="mb-2 text-xs text-ink/60">Cut the internet in a zone. Reports needing internet from inside it stop arriving; SMS and voice calls still get through.</p>
      <div className="grid grid-cols-2 gap-1.5">
        {(data ?? []).map((z) => (
          <button key={z.code} onClick={() => toggle(z)} aria-pressed={z.internet_down}
            className={`flex items-center justify-between rounded-xl border-2 border-ink px-2.5 py-1.5 text-left text-xs font-bold transition-all ${z.internet_down ? "-rotate-1 bg-pink-500 text-white shadow-hard-sm" : "bg-white text-ink hover:-translate-y-0.5 hover:bg-lime-300"}`}>
            <span>{z.name}{z.tower_status !== "up" && <span className="ml-1 text-[10px] opacity-80">· towers {z.tower_status}</span>}</span>
            {z.internet_down ? <span className="flex items-center gap-1"><WifiOff size={13} aria-hidden />DOWN</span> : <Wifi size={13} className="text-ink" aria-label="internet up" />}
          </button>
        ))}
      </div>
    </Panel>
  );
}
