// One report: original text (never discarded), language badge, English translation with its method and confidence,
// channel, extracted fields, linked incident, and any rumour / clarification flags.
import { Link } from "react-router-dom";
import { AlertTriangle, HelpCircle, LifeBuoy, MapPin, Users, WifiOff } from "lucide-react";
import { Report } from "../services/types";
import { ChannelBadge, LangBadge, Meter, simTime } from "./ui";

export default function ReportCard({ r, compact = false }: { r: Report; compact?: boolean }) {
  const blocked = r.status === "blocked";
  return (
    <article className={`rounded-2xl border-2 bg-white p-3 transition-all hover:-translate-y-0.5 hover:shadow-hard ${blocked ? "border-dashed border-ink/40 opacity-60" : r.life_safety ? "border-ink shadow-hard-pink" : "border-ink shadow-hard-sm"}`}>
      <div className="flex flex-wrap items-center gap-1.5 text-xs">
        <span className="font-mono font-bold text-ink">{r.ref}</span>
        <ChannelBadge channel={r.channel} />
        <LangBadge lang={r.original_language} script={r.script} conf={r.language_confidence} />
        {r.life_safety && <span className="badge bg-pink-400"><LifeBuoy size={12} aria-hidden />life-safety</span>}
        {r.missing_contact && <span className="badge bg-brand-300">missing contact</span>}
        {r.rumour_signals?.length > 0 && <span className="badge bg-tangerine-300" title={r.rumour_signals.map((s) => s.detail || s.phrases?.join(", ")).join("; ")}><AlertTriangle size={12} aria-hidden />rumour signals</span>}
        {r.status === "clarifying" && <span className="badge bg-sun-300"><HelpCircle size={12} aria-hidden />asked for {r.needs_clarification.join(", ")}</span>}
        {blocked && <span className="badge bg-white"><WifiOff size={12} aria-hidden />did not get out: zone internet down</span>}
        <span className="ml-auto font-mono text-ink/50">{simTime(r.received_at)}</span>
      </div>
      <p className="mt-2 text-[15px] font-medium leading-snug text-ink" lang={r.original_language}>{r.raw_text}</p>
      {r.original_language !== "en" && r.translated_text_en && (
        <div className="mt-1.5 rounded-xl border-[1.5px] border-ink/20 bg-paper px-2.5 py-1.5">
          <p className="text-sm text-ink/80"><span className="font-extrabold text-brand-600">EN · </span>{r.translated_text_en}</p>
          <div className="mt-1 flex items-center gap-2 text-[10px] font-bold text-ink/50">
            <span>{r.translation_method}</span><Meter value={r.translation_confidence} label="translation confidence" tone={r.translation_confidence > 0.7 ? "green" : "amber"} />
          </div>
        </div>
      )}
      {!compact && (
        <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-ink/70">
          {r.need_types?.map((n) => <span key={n} className="badge bg-white">{n.replace("_", " ")}</span>)}
          {r.people_count != null && <span className="badge bg-white"><Users size={12} aria-hidden />{r.people_count}</span>}
          {r.vulnerable_groups?.map((v) => <span key={v} className="badge bg-brand-200">{v}</span>)}
          <span className="badge bg-white"><MapPin size={12} aria-hidden />{r.location_text ?? "no location"}{r.location_text ? ` · ${Math.round(r.geocode_confidence * 100)}%` : ""}</span>
          {r.incident_id && <Link to={`/incidents?focus=${r.incident_id}`} className="badge bg-lime-400 hover:bg-lime-300">incident #{r.incident_id}</Link>}
          {r.source && <span className="text-ink/50">· {r.source.name}{r.source.phone_masked ? ` (${r.source.phone_masked})` : ""}</span>}
          <span className="text-ink/50">· {r.extraction_method}</span>
        </div>
      )}
    </article>
  );
}
