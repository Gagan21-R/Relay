// Silence is a signal: zones ranked by blackout risk, each with its breakdown; recon tasks with pre-positioned
// supplies (approve), the recon team's report (resolves the blackout) and drone images (experimental).
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Camera, Check, EyeOff, Radio, Signal, Users } from "lucide-react";
import { PageHeader } from "../components/Layout";
import { Breakdown, Empty, Meter, Panel, simTime } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";
import { Explain } from "../components/Assistant";

export default function Blackout() {
  const { t } = useTranslation();
  const { data, reload } = useApi<any[]>("/api/zones/blackout", ["zone", "recon", "report", "signal", "alert"], 600);
  const [msg, setMsg] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState(false);
  const approve = async (id: number) => { setBusy(true); await api(`/api/recon/${id}/approve`, { method: "POST", body: JSON.stringify({ who: "Duty officer" }) }); setBusy(false); reload(); };
  const report = async (id: number) => {
    setBusy(true);
    await api(`/api/recon/${id}/report`, { method: "POST", body: JSON.stringify({ callsign: "NDRF-2", message: msg[id] }) });
    setBusy(false); reload();
  };
  const upload = async (id: number, f: File) => {
    const fd = new FormData(); fd.append("image", f); fd.append("note", "aerial pass");
    await fetch(`/api/recon/${id}/image`, { method: "POST", body: fd }); reload();
  };
  const silent = (data ?? []).filter((z) => z.blackout_flag);
  const others = (data ?? []).filter((z) => !z.blackout_flag);
  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.blackout")} sub={t("pages.blackout")} kicker="silence is a signal" tone="bg-ink text-white" section="blackout.page" />
      {!data ? null : !silent.length ? <Empty>No zone is silent right now. Every populated zone inside the hazard footprint has reported recently.</Empty> : silent.map((z, n) => (
        <motion.section key={z.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card overflow-hidden p-0 shadow-hard-pink">
          <div className="hatch-red flex flex-wrap items-center gap-3 border-b-2 border-ink bg-ink px-4 py-3 text-white">
            <span className="mega text-4xl text-pink-400">#{n + 1}</span>
            <EyeOff size={22} aria-hidden />
            <h2 className="mega text-[34px]">{z.name}</h2>
            <span className="sticker bg-pink-500 text-white">risk {Math.round(z.risk.score * 100)}%</span>
            <span className="sticker bg-white text-ink"><Users size={13} aria-hidden />{z.population.toLocaleString()}</span>
            <span className="sticker bg-sun-400 text-ink">silent {z.risk.hours_silent} h</span>
          </div>
          <div className="grid gap-4 p-4 xl:grid-cols-[1.1fr_1fr]">
            <div>
              <p className="label mb-2 flex items-center gap-2">Why RELAY thinks people here need help <Explain id="blackout.risk" context={{ zone: z.code }} /></p>
              <Breakdown components={z.risk.components} />
              <p className="mt-2 text-xs font-bold text-ink/60">Rank value (population × hazard × hours silent): {z.risk.rank_value.toLocaleString()}</p>
            </div>
            {z.recon ? (
              <div className="rounded-2xl border-2 border-ink bg-paper p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="label">Reconnaissance</span><Explain id="blackout.recon" />
                  <span className={`badge ${z.recon.status === "pending_approval" ? "bg-sun-400" : z.recon.status === "completed" ? "bg-mint-400" : "bg-cobalt-300"}`}>{z.recon.status.replace("_", " ")}</span>
                </div>
                <p className="mt-1 text-lg font-extrabold">{z.recon.team}</p>
                <p className="text-sm text-ink/70">{z.recon.rationale}</p>
                <p className="mt-2 text-xs font-bold">Likely needs: {z.recon.estimated_needs.affected_estimate.toLocaleString()} people · {z.recon.estimated_needs.basis}</p>
                <p className="label mt-2">Pre-positioned with the team</p>
                <div className="mt-1 flex flex-wrap gap-1.5">{z.recon.prepositioned.map((p: any) => <span key={p.resource_type} className="badge bg-lime-300">{p.quantity} {p.unit} {p.resource_type.replace("_", " ")}</span>)}</div>
                {z.recon.status === "pending_approval" && <button className="btn-pop mt-3" disabled={busy} onClick={() => approve(z.recon.id)}><Check size={15} aria-hidden />Approve recon + supplies</button>}
                {z.recon.status === "in_progress" && (
                  <div className="mt-3 space-y-2">
                    <p className="label flex items-center gap-1"><Radio size={12} aria-hidden />Team report (satellite phone / radio)</p>
                    <textarea className="input" rows={3} placeholder={`e.g. ${z.name} reached on foot: 40 houses damaged, about 300 people at the temple hall, need food, drinking water and a medical team.`}
                      value={msg[z.recon.id] ?? ""} onChange={(e) => setMsg({ ...msg, [z.recon.id]: e.target.value })} />
                    <div className="flex flex-wrap gap-2">
                      <button className="btn-primary" disabled={busy || (msg[z.recon.id] ?? "").length < 5} onClick={() => report(z.recon.id)}><Signal size={15} aria-hidden />Log team report</button>
                      <label className="btn-ghost cursor-pointer"><Camera size={15} aria-hidden />Drone image<input type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files?.[0] && upload(z.recon.id, e.target.files[0])} /></label>
                    </div>
                    {(z.recon.images ?? []).map((im: any, i: number) => <p key={i} className="text-xs font-bold">image at {simTime(im.t)} · {im.finding.method}{im.finding.sos_detected != null ? ` · SOS ${im.finding.sos_detected ? "seen" : "not seen"}` : ""} <span className="badge bg-tangerine-300">experimental</span></p>)}
                  </div>
                )}
              </div>
            ) : <Empty>Recon task being prepared…</Empty>}
          </div>
        </motion.section>
      ))}
      <Panel title="All zones by blackout risk">
        <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
          {others.map((z) => (
            <div key={z.id} className="rounded-xl border-2 border-ink/20 bg-white p-2.5 text-sm">
              <div className="flex items-center justify-between"><b>{z.name}</b><span className="font-mono text-xs">{z.population.toLocaleString()}</span></div>
              <Meter value={z.risk.score} label="risk" tone={z.risk.score > 0.45 ? "amber" : "green"} />
              <p className="text-[11px] text-ink/60">silent {z.risk.hours_silent} h · towers {z.tower_status} · power {z.power_status}{z.recon?.status === "completed" ? " · recon completed" : ""}</p>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
