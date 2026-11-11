// Small shared UI pieces: badges, channel icons, confidence bars, panels, empty states.
import { ReactNode } from "react";
import { Globe, MessageSquare, Mic, Newspaper, Radio, Smartphone, Building2, Rss } from "lucide-react";

export const LANG_NAMES: Record<string, string> = {
  en: "English", kn: "ಕನ್ನಡ", hi: "हिंदी", ml: "മലയാളം", ta: "தமிழ்", te: "తెలుగు", mr: "मराठी", bn: "বাংলা",
};

export const CHANNELS: Record<string, { icon: any; label: string; internet: boolean }> = {
  sms: { icon: MessageSquare, label: "SMS", internet: false },
  voice: { icon: Mic, label: "Voice call", internet: false },
  web: { icon: Globe, label: "Web", internet: true },
  field_app: { icon: Smartphone, label: "Field app", internet: true },
  social_feed: { icon: Rss, label: "Social", internet: true },
  news_feed: { icon: Newspaper, label: "News", internet: true },
  official_feed: { icon: Building2, label: "Official", internet: true },
  radio_entry: { icon: Radio, label: "Radio / sat-phone", internet: false },
};

export function ChannelBadge({ channel }: { channel: string }) {
  const c = CHANNELS[channel] ?? { icon: Globe, label: channel, internet: true };
  const I = c.icon;
  return (
    <span className={`badge ${c.internet ? "bg-sky-100 text-sky-800" : "bg-emerald-100 text-emerald-800"}`} title={c.internet ? "needs internet" : "works without internet"}>
      <I size={12} aria-hidden />{c.label}
    </span>
  );
}

export function LangBadge({ lang, script, conf }: { lang?: string; script?: string; conf?: number }) {
  if (!lang) return null;
  return (
    <span className="badge bg-brand-100 text-brand-800" title={conf != null ? `detection confidence ${Math.round(conf * 100)}%` : undefined}>
      {LANG_NAMES[lang] ?? lang}{script && script !== "native" ? ` · ${script}` : ""}
    </span>
  );
}

const LEVEL_STYLE: Record<string, string> = {
  verified: "bg-emerald-100 text-emerald-800", likely: "bg-lime-100 text-lime-800", unverified: "bg-amber-100 text-amber-800",
  disputed: "bg-orange-100 text-orange-800", false: "bg-red-100 text-red-800 line-through",
};
export function ConfidenceBadge({ level, score }: { level: string; score?: number }) {
  return <span className={`badge ${LEVEL_STYLE[level] ?? "bg-slate-100 text-slate-700"}`}>{level}{score != null ? ` · ${Math.round(score * 100)}%` : ""}</span>;
}

export function Meter({ value, label, tone = "brand" }: { value: number; label?: string; tone?: "brand" | "amber" | "red" | "green" }) {
  const pct = Math.max(0, Math.min(100, Math.round(value * 100)));
  const bar = { brand: "bg-brand-500", amber: "bg-amber-500", red: "bg-red-500", green: "bg-emerald-500" }[tone];
  return (
    <div className="min-w-[90px]" title={label}>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200" role="meter" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={label}>
        <div className={`h-full ${bar}`} style={{ width: `${pct}%` }} />
      </div>
      {label && <p className="mt-0.5 text-[10px] text-slate-500">{label} {pct}%</p>}
    </div>
  );
}

export function Panel({ title, actions, children, className = "", explain }: { title?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string; explain?: ReactNode }) {
  return (
    <section className={`card p-4 ${className}`}>
      {(title || actions || explain) && (
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">{title && <h2 className="text-base font-semibold text-ink">{title}</h2>}{explain}</div>
          {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">{children}</p>;
}

export const simTime = (t?: number | null) => (t == null ? "—" : `T+${t.toFixed(1)} h`);

export function Stat({ label, value, tone = "bg-white" }: { label: string; value: ReactNode; tone?: string }) {
  return (
    <div className={`card p-3 ${tone}`}>
      <p className="text-2xl font-bold tabular-nums text-ink">{value}</p>
      <p className="text-xs font-medium text-slate-500">{label}</p>
    </div>
  );
}
