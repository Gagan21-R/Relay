import { ReactNode, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AnimatePresence, motion } from "framer-motion";
import {
  Activity, AlertTriangle, BarChart3, Box, ClipboardCheck, Database, EyeOff, FlaskConical, Home, Inbox, Map as MapIcon, Menu,
  Package, PhoneCall, RadioTower, ScrollText, ShieldAlert, Smartphone, Sparkles, Truck, X,
} from "lucide-react";
import { setUiLang, UI_LANGS } from "../i18n";
import { useHealth } from "../hooks/useHealth";
import { useLiveStatus } from "../hooks/useLive";
import { useApi } from "../hooks/useApi";
import { Blob, Marquee } from "./motion";
import AssistantDrawer, { Explain } from "./Assistant";

export const NAV = [
  { group: "see", tint: "bg-lime-400", items: [
    { to: "/", key: "map", icon: MapIcon, end: true, chip: "bg-cobalt-400" },
    { to: "/feed", key: "feed", icon: Inbox, chip: "bg-lime-400" },
    { to: "/twin3d", key: "twin3d", icon: Box, chip: "bg-sun-400" },
  ] },
  { group: "decide", tint: "bg-pink-400", items: [
    { to: "/incidents", key: "incidents", icon: Activity, chip: "bg-pink-400" },
    { to: "/fast-verify", key: "fastVerify", icon: ShieldAlert, chip: "bg-tangerine-400" },
    { to: "/plans", key: "plans", icon: ClipboardCheck, chip: "bg-brand-400" },
  ] },
  { group: "act", tint: "bg-tangerine-400", items: [
    { to: "/dispatch", key: "dispatch", icon: Truck, chip: "bg-mint-400" },
    { to: "/resources", key: "resources", icon: Package, chip: "bg-sun-400" },
    { to: "/shelters", key: "shelters", icon: Home, chip: "bg-cobalt-300" },
    { to: "/alerts", key: "alerts", icon: AlertTriangle, chip: "bg-pink-300" },
    { to: "/blackout", key: "blackout", icon: EyeOff, chip: "bg-ink text-white" },
    { to: "/phone", key: "phone", icon: PhoneCall, chip: "bg-lime-300" },
    { to: "/radio", key: "radio", icon: RadioTower, chip: "bg-tangerine-300" },
    { to: "/scenario", key: "scenario", icon: FlaskConical, chip: "bg-brand-300" },
  ] },
  { group: "prove", tint: "bg-cobalt-400", items: [
    { to: "/metrics", key: "metrics", icon: BarChart3, chip: "bg-mint-300" },
    { to: "/audit", key: "audit", icon: ScrollText, chip: "bg-sun-300" },
    { to: "/field", key: "field", icon: Smartphone, chip: "bg-pink-300" },
    { to: "/about", key: "about", icon: Sparkles, chip: "bg-lime-400" },
  ] },
] as const;

type Summary = { clock: number; reports: number; languages: number; incidents: number; fast_verify: number; alerts_open: number;
  plans_pending: number; dispatches_active: number; zones_down: string[]; blackout_zones: string[]; people_affected: number };

function Ticker() {
  const { data: s } = useApi<Summary>("/api/summary", ["report", "incident", "alert", "plan", "dispatch", "network", "sim", "zone"], 800);
  if (!s) return <div className="h-8 border-b-2 border-ink bg-lime-400" />;
  const items = [
    `T+${s.clock.toFixed(1)} h`, `${s.reports} reports`, `${s.languages} languages`, `${s.incidents} incidents`,
    `${s.fast_verify} in Fast Verify`, `${s.plans_pending} plan(s) awaiting approval`, `${s.dispatches_active} deliveries moving`,
    `${s.alerts_open} open alerts`, s.zones_down.length ? `internet DOWN: ${s.zones_down.join(", ")}` : "all zones online",
    s.blackout_zones.length ? `silent zones: ${s.blackout_zones.join(", ")}` : "no silent zones flagged",
    "synthetic scenario · Kodagu, Karnataka", "AI interprets · rules enforce · people decide",
  ];
  return (
    <div className="border-b-2 border-ink bg-lime-400 py-1.5 text-[12px] font-extrabold uppercase tracking-wider">
      <Marquee>{items.map((t, i) => <span key={i} className="flex items-center gap-10 whitespace-nowrap">{t}<span className="text-pink-500">✺</span></span>)}</Marquee>
    </div>
  );
}

function StatusPills() {
  const { t } = useTranslation();
  const live = useLiveStatus();
  const { health, error } = useHealth();
  const dot = live === "live" ? "bg-mint-500" : live === "connecting" ? "bg-sun-500" : "bg-pink-500";
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="badge bg-white" role="status">
        <span className="relative flex h-2.5 w-2.5"><span className={`absolute inset-0 rounded-full ${dot} ${live === "live" ? "animate-pulsering" : ""}`} /><span className={`relative h-2.5 w-2.5 rounded-full ${dot}`} /></span>
        {t(`status.${live}`)}
      </span>
      {health && <span className={`badge ${health.mock_mode ? "bg-sun-300" : "bg-mint-300"}`}>{health.mock_mode ? t("status.mock") : t("status.keys")}</span>}
      {health && <span className={`badge ${health.database_ok ? "bg-white" : "bg-pink-300"}`}><Database size={11} aria-hidden />{health.database.split(" ")[0]}</span>}
      {error && <span className="badge bg-pink-300">{error}</span>}
    </div>
  );
}

function Logo() {
  return (
    <Link to="/about" className="group relative block overflow-hidden rounded-2xl border-2 border-ink bg-brand-500 p-3 text-white shadow-hard transition-transform hover:-rotate-1" aria-label="About RELAY">
      <div className="pat-dots absolute inset-0 opacity-10" aria-hidden />
      <span className="absolute -right-5 -top-5 h-16 w-16 animate-spinslow rounded-full border-2 border-dashed border-white/70" aria-hidden />
      <p className="mega relative text-[38px]">relay<span className="text-lime-400">.</span></p>
      <p className="relative text-[10px] font-bold uppercase leading-tight tracking-[0.18em] text-brand-100">reports in · relief out</p>
    </Link>
  );
}

export default function Layout() {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  const nav = (
    <nav aria-label="Main" className="flex h-full flex-col gap-4 overflow-y-auto p-3">
      <Logo />
      {NAV.map((g) => (
        <div key={g.group}>
          <div className="mb-1.5 flex items-center gap-2 px-1">
            <span className="serif-i text-[17px] text-ink">{t(`nav.${g.group}`)}</span>
            <span className={`h-[3px] flex-1 rounded-full border border-ink ${g.tint}`} />
          </div>
          <div className="space-y-1">
            {g.items.map((it) => {
              const I = it.icon;
              return (
                <NavLink key={it.to} to={it.to} end={"end" in it} onClick={() => setOpen(false)}
                  className={({ isActive }) => `group flex items-center gap-2.5 rounded-xl border-2 px-2 py-1.5 text-[13.5px] font-bold transition-all ${isActive
                    ? "translate-x-1 border-ink bg-ink text-white shadow-hard-pink" : "border-transparent text-ink/75 hover:border-ink hover:bg-white hover:text-ink"}`}>
                  <span className={`grid h-7 w-7 shrink-0 place-items-center rounded-lg border-2 border-ink ${it.chip} text-ink transition-transform group-hover:-rotate-12 group-hover:scale-110`}><I size={15} aria-hidden /></span>
                  <span className="truncate">{t(`nav.${it.key}`)}</span>
                </NavLink>
              );
            })}
          </div>
        </div>
      ))}
      <p className="mt-auto rounded-xl border-2 border-dashed border-ink/40 p-2.5 text-[11px] leading-snug text-ink/60">
        <span className="serif-i text-[14px] text-ink">Synthetic scenario.</span> Kodagu is real; every report, person and stock count here is invented.
      </p>
    </nav>
  );
  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 border-r-2 border-ink bg-cream lg:block">{nav}</aside>
      <AnimatePresence>
        {open && (
          <motion.div className="fixed inset-0 z-[1200] lg:hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div className="absolute inset-0 bg-ink/50" onClick={() => setOpen(false)} />
            <motion.aside className="relative h-full w-72 border-r-2 border-ink bg-cream" initial={{ x: -300 }} animate={{ x: 0 }} exit={{ x: -300 }}>
              <button className="btn-ghost absolute right-2 top-2 z-10 !p-1" onClick={() => setOpen(false)} aria-label="Close menu"><X size={16} /></button>
              {nav}
            </motion.aside>
          </motion.div>
        )}
      </AnimatePresence>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-[1000] border-b-2 border-ink bg-paper/90 backdrop-blur">
          <Ticker />
          <div className="flex flex-wrap items-center gap-2 px-4 py-2">
            <button className="btn-ghost !p-1.5 lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu"><Menu size={16} /></button>
            <StatusPills />
            <div className="ml-auto flex items-center gap-1 rounded-xl border-2 border-ink bg-white p-0.5 shadow-hard-sm" role="group" aria-label={t("common.language")}>
              {UI_LANGS.map((l) => (
                <button key={l.code} onClick={() => setUiLang(l.code)} aria-pressed={i18n.language === l.code}
                  className={`rounded-lg px-2.5 py-1 text-xs font-extrabold transition-colors ${i18n.language === l.code ? "bg-brand-500 text-white" : "text-ink hover:bg-lime-300"}`}>{l.label}</button>
              ))}
            </div>
          </div>
        </header>
        <main className="min-w-0 flex-1 p-4 sm:p-6">
          <motion.div key={loc.pathname} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ type: "spring", stiffness: 240, damping: 26 }}>
            <Outlet />
          </motion.div>
        </main>
      </div>
      <AssistantDrawer />
    </div>
  );
}

const ORNAMENTS = ["✺", "✦", "❋", "✿", "☀", "❖"];
const TONES = ["bg-lime-400", "bg-pink-400", "bg-sun-400", "bg-cobalt-300", "bg-tangerine-400", "bg-brand-300"];

export function PageHeader({ title, sub, children, kicker, tone, explain, section }: { title: string; sub?: string; children?: ReactNode; kicker?: string; tone?: string; explain?: ReactNode; section?: string }) {
  const h = [...title].reduce((a, c) => a + c.charCodeAt(0), 0);
  const tn = tone ?? TONES[h % TONES.length];
  return (
    <div className="relative mb-6 overflow-hidden rounded-3xl border-2 border-ink bg-white p-5 shadow-hard sm:p-7">
      <div className="pat-grid absolute inset-0 opacity-60" aria-hidden />
      <Blob className="-right-16 -top-20 h-56 w-56" color={tn} />
      <span className="pointer-events-none absolute bottom-[-30px] right-6 select-none text-[130px] leading-none text-ink/10" aria-hidden>{ORNAMENTS[h % ORNAMENTS.length]}</span>
      <div className="relative flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0 max-w-3xl">
          <div className="flex flex-wrap items-center gap-2">
            {kicker && <span className={`sticker -rotate-2 ${tn}`}>{kicker}</span>}
            {section && <Explain id={section} />}
            {explain}
          </div>
          <h1 className="mega mt-3 text-[40px] sm:text-[56px]">{title}</h1>
          {sub && <p className="mt-2 text-[15px] font-medium text-ink/70">{sub}</p>}
        </div>
        {children && <div className="relative flex flex-wrap gap-2">{children}</div>}
      </div>
    </div>
  );
}
