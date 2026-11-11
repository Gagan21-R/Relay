// Shared UI pieces in the maximalist system: badges, channel icons, meters, panels, stats, empty states.
import { ReactNode } from "react";
import { Building2, Globe, MessageSquare, Mic, Newspaper, Radio, Rss, Smartphone } from "lucide-react";
import { CountUp } from "./motion";
import { Explain } from "./Assistant";

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
    <span className={`badge ${c.internet ? "bg-cobalt-300" : "bg-mint-300"}`} title={c.internet ? "needs internet" : "works without internet"}>
      <I size={12} aria-hidden />{c.label}
    </span>
  );
}

export function LangBadge({ lang, script, conf }: { lang?: string; script?: string; conf?: number }) {
  if (!lang) return null;
  return (
    <span className="badge bg-brand-200" title={conf != null ? `detection confidence ${Math.round(conf * 100)}%` : undefined}>
      {LANG_NAMES[lang] ?? lang}{script && script !== "native" ? ` · ${script}` : ""}
    </span>
  );
}

export const LEVEL_STYLE: Record<string, string> = {
  verified: "bg-mint-400", likely: "bg-lime-300", unverified: "bg-sun-300", disputed: "bg-tangerine-300", false: "bg-pink-400 line-through",
};
export function ConfidenceBadge({ level, score }: { level: string; score?: number }) {
  return <span className={`badge ${LEVEL_STYLE[level] ?? "bg-white"}`}>{level}{score != null ? ` · ${Math.round(score * 100)}%` : ""}</span>;
}

export const PRIORITY_STYLE = (score: number) =>
  score >= 70 ? { label: "P1", cls: "bg-p1 text-white" } : score >= 50 ? { label: "P2", cls: "bg-p2 text-white" }
    : score >= 30 ? { label: "P3", cls: "bg-p3 text-ink" } : { label: "P4", cls: "bg-p4 text-white" };

export function Meter({ value, label, tone = "brand" }: { value: number; label?: string; tone?: "brand" | "amber" | "red" | "green" }) {
  const pct = Math.max(0, Math.min(100, Math.round(value * 100)));
  const bar = { brand: "bg-brand-500", amber: "bg-sun-400", red: "bg-pink-500", green: "bg-mint-500" }[tone];
  return (
    <div className="min-w-[90px]" title={label}>
      <div className="h-2 w-full overflow-hidden rounded-full border-[1.5px] border-ink bg-white" role="meter" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={label}>
        <div className={`h-full ${bar} transition-[width] duration-700`} style={{ width: `${pct}%` }} />
      </div>
      {label && <p className="mt-0.5 text-[10px] font-bold text-ink/60">{label} {pct}%</p>}
    </div>
  );
}

export function Panel({ title, actions, children, className = "", explain, tone, section }: { title?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string; explain?: ReactNode; tone?: string; section?: string }) {
  return (
    <section className={`card relative overflow-hidden p-4 ${className}`}>
      {tone && <div className={`absolute inset-x-0 top-0 h-1.5 border-b-2 border-ink ${tone}`} aria-hidden />}
      {(title || actions || explain || section) && (
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">{title && <h2 className="text-[20px] font-extrabold leading-tight">{title}</h2>}{section && <Explain id={section} />}{explain}</div>
          {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="rounded-2xl border-2 border-dashed border-ink/40 bg-paper p-6 text-center text-sm font-medium text-ink/60">{children}</p>;
}

export const simTime = (t?: number | null) => (t == null ? "—" : `T+${t.toFixed(1)} h`);

const STAT_TONES = ["bg-lime-400", "bg-pink-400", "bg-sun-400", "bg-cobalt-300", "bg-tangerine-300", "bg-brand-300", "bg-mint-300"];
export function Stat({ label, value, tone, i = 0, pattern }: { label: string; value: ReactNode; tone?: string; i?: number; pattern?: string }) {
  const t = tone ?? STAT_TONES[i % STAT_TONES.length];
  return (
    <div className={`relative overflow-hidden rounded-2xl border-2 border-ink p-3 shadow-hard transition-transform hover:-translate-y-1 ${t} ${i % 3 === 1 ? "rotate-[0.6deg]" : i % 3 === 2 ? "-rotate-[0.6deg]" : ""}`}>
      {pattern && <div className={`absolute inset-0 opacity-[0.12] ${pattern}`} aria-hidden />}
      <p className="mega relative text-[38px] tabular-nums">{typeof value === "number" ? <CountUp value={value} /> : value}</p>
      <p className="relative text-[11px] font-extrabold uppercase leading-tight tracking-wider">{label}</p>
    </div>
  );
}

/** A weighted score as a stacked breakdown: each component's points, with the reason underneath. */
export function Breakdown({ components, penalties = [], total, unit = "" }: {
  components: Record<string, { value?: number; weight?: number; points: number; why?: string }>; penalties?: { name: string; value: number; why: string }[];
  total?: number; unit?: string;
}) {
  const COLORS = ["bg-brand-400", "bg-lime-400", "bg-pink-400", "bg-sun-400", "bg-cobalt-400", "bg-mint-400", "bg-tangerine-400"];
  const entries = Object.entries(components);
  const max = Math.max(1e-9, entries.reduce((a, [, c]) => a + Math.max(0, c.points), 0), total ?? 0);
  return (
    <div className="space-y-2">
      <div className="flex h-4 overflow-hidden rounded-full border-2 border-ink bg-white" aria-hidden>
        {entries.map(([k, c], i) => <div key={k} className={`${COLORS[i % COLORS.length]} border-r border-ink/40`} style={{ width: `${(Math.max(0, c.points) / max) * 100}%` }} />)}
      </div>
      <ul className="grid gap-1 text-xs sm:grid-cols-2">
        {entries.map(([k, c], i) => (
          <li key={k} className="flex gap-2 rounded-lg bg-paper px-2 py-1">
            <span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-sm border border-ink ${COLORS[i % COLORS.length]}`} />
            <span><b className="capitalize">{k.replace(/_/g, " ")}</b> <span className="font-mono">+{c.points.toFixed(unit ? 1 : 2)}{unit}</span>{c.weight != null && <span className="text-ink/50"> (w {c.weight})</span>}<br /><span className="text-ink/60">{c.why}</span></span>
          </li>
        ))}
        {penalties.map((p) => (
          <li key={p.name} className="flex gap-2 rounded-lg bg-pink-300/40 px-2 py-1">
            <span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-sm border border-ink bg-pink-500" />
            <span><b className="capitalize">{p.name.replace(/_/g, " ")}</b> <span className="font-mono">{p.value.toFixed(2)}</span><br /><span className="text-ink/60">{p.why}</span></span>
          </li>
        ))}
      </ul>
    </div>
  );
}
