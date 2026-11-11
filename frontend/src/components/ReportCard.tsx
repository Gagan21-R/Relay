// One report: original text (never discarded), language badge, English translation with its method and confidence,
// channel, extracted fields, linked incident, and any rumour / clarification flags.
import { Link } from "react-router-dom";
import { AlertTriangle, HelpCircle, LifeBuoy, MapPin, Users, WifiOff } from "lucide-react";
import { Report } from "../services/types";
import { ChannelBadge, LangBadge, Meter, simTime } from "./ui";

export default function ReportCard({ r, compact = false }: { r: Report; compact?: boolean }) {
  const blocked = r.status === "blocked";
  return (
    <article className={`rounded-xl border bg-white p-3 transition-shadow hover:shadow-md ${blocked ? "border-dashed border-slate-300 opacity-60" : r.life_safety ? "border-red-200" : "border-slate-200"}`}>
      <div className="flex flex-wrap items-center gap-1.5 text-xs">
        <span className="font-mono font-semibold text-slate-700">{r.ref}</span>
        <ChannelBadge channel={r.channel} />
        <LangBadge lang={r.original_language} script={r.script} conf={r.language_confidence} />
        {r.life_safety && <span className="badge bg-red-100 text-red-700"><LifeBuoy size={12} aria-hidden />life-safety</span>}
        {r.missing_contact && <span className="badge bg-fuchsia-100 text-fuchsia-800">missing contact</span>}
        {r.rumour_signals?.length > 0 && <span className="badge bg-orange-100 text-orange-800" title={r.rumour_signals.map((s) => s.detail || s.phrases?.join(", ")).join("; ")}><AlertTriangle size={12} aria-hidden />rumour signals</span>}
        {r.status === "clarifying" && <span className="badge bg-amber-100 text-amber-800"><HelpCircle size={12} aria-hidden />asked for {r.needs_clarification.join(", ")}</span>}
        {blocked && <span className="badge bg-slate-200 text-slate-700"><WifiOff size={12} aria-hidden />did not get out: zone internet down</span>}
        <span className="ml-auto text-slate-400">{simTime(r.received_at)}</span>
      </div>
      <p className="mt-2 text-[15px] leading-snug text-ink" lang={r.original_language}>{r.raw_text}</p>
      {r.original_language !== "en" && r.translated_text_en && (
        <div className="mt-1.5 rounded-lg bg-slate-50 px-2.5 py-1.5">
          <p className="text-sm text-slate-700"><span className="font-semibold text-slate-500">EN · </span>{r.translated_text_en}</p>
          <div className="mt-1 flex items-center gap-2 text-[10px] text-slate-500">
            <span>{r.translation_method}</span><Meter value={r.translation_confidence} label="translation confidence" tone={r.translation_confidence > 0.7 ? "green" : "amber"} />
          </div>
        </div>
      )}
      {!compact && (
        <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-slate-600">
          {r.need_types?.map((n) => <span key={n} className="badge bg-slate-100 text-slate-700">{n.replace("_", " ")}</span>)}
          {r.people_count != null && <span className="badge bg-slate-100 text-slate-700"><Users size={12} aria-hidden />{r.people_count}</span>}
          {r.vulnerable_groups?.map((v) => <span key={v} className="badge bg-violet-100 text-violet-800">{v}</span>)}
          <span className="badge bg-slate-100 text-slate-700"><MapPin size={12} aria-hidden />{r.location_text ?? "no location"}{r.location_text ? ` · ${Math.round(r.geocode_confidence * 100)}%` : ""}</span>
          {r.incident_id && <Link to={`/incidents?focus=${r.incident_id}`} className="badge bg-brand-100 text-brand-800 hover:bg-brand-200">incident #{r.incident_id}</Link>}
          {r.source && <span className="text-slate-400">· {r.source.name}{r.source.phone_masked ? ` (${r.source.phone_masked})` : ""}</span>}
          <span className="text-slate-400">· {r.extraction_method}</span>
        </div>
      )}
    </article>
  );
}
