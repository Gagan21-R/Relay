// App shell, brutalist · minimal · surreal: a numbered index for navigation (no colour chips), one thin black ticker,
// square controls, a black wipe on every route change, and page headers with big type, a hairline grid and ONE
// surreal object per page (a moon, an orb, an eye, a door) chosen from the page title.
import { ReactNode, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AnimatePresence, motion } from "framer-motion";
import { Database, Menu, X } from "lucide-react";
import { setUiLang, UI_LANGS } from "../i18n";
import { useHealth } from "../hooks/useHealth";
import { useLiveStatus } from "../hooks/useLive";
import { useApi } from "../hooks/useApi";
import { Blob, Door, Drip, Eye, Marquee, Moon } from "./motion";
import AssistantDrawer, { Explain } from "./Assistant";
import GuideOverlay from "./Guide";
import { DisasterSelector } from "./Disaster";
import { RoleSwitcher } from "./Role";

export const NAV = [
  { group: "see", items: [
    { to: "/workflow", key: "workflow" }, { to: "/", key: "map", end: true }, { to: "/agents", key: "agents" }, { to: "/feed", key: "feed" },
  ] },
  { group: "decide", items: [
    { to: "/incidents", key: "incidents" }, { to: "/fast-verify", key: "fastVerify" }, { to: "/plans", key: "plans" },
  ] },
  { group: "act", items: [
    { to: "/dispatch", key: "dispatch" }, { to: "/resources", key: "resources" }, { to: "/shelters", key: "shelters" }, { to: "/alerts", key: "alerts" },
    { to: "/comms", key: "comms" }, { to: "/blackout", key: "blackout" }, { to: "/phone", key: "phone" }, { to: "/lab", key: "lab" },
    { to: "/scenario", key: "scenario" },
  ] },
  { group: "prove", items: [
    { to: "/metrics", key: "metrics" }, { to: "/audit", key: "audit" }, { to: "/field", key: "field" }, { to: "/about", key: "about" },
  ] },
] as const;

type Summary = { clock: number; reports: number; languages: number; incidents: number; fast_verify: number; alerts_open: number;
  plans_pending: number; dispatches_active: number; zones_down: string[]; blackout_zones: string[]; people_affected: number; scenario_name?: string };

function Ticker() {
  const { data: s } = useApi<Summary>("/api/summary", ["report", "incident", "alert", "plan", "dispatch", "network", "sim", "zone"], 800);
  if (!s) return <div className="h-7 bg-ink" />;
  const items = [
    `T+${s.clock.toFixed(1)} h`, `${s.reports} reports`, `${s.languages} languages`, `${s.incidents} incidents`,
    `${s.fast_verify} in fast verify`, `${s.plans_pending} plan(s) awaiting approval`, `${s.dispatches_active} deliveries moving`,
    `${s.alerts_open} open alerts`, s.zones_down.length ? `internet down: ${s.zones_down.join(", ")}` : "all zones online",
    s.blackout_zones.length ? `silent zones: ${s.blackout_zones.join(", ")}` : "no silent zones",
    `synthetic scenario — ${s.scenario_name ?? "Kodagu, Karnataka"}`, "ai interprets / rules enforce / people decide",
  ];
  return (
    <div className="bg-ink py-1.5 font-mono text-[11px] uppercase tracking-[0.14em] text-bone">
      <Marquee>{items.map((t, i) => <span key={i} className="flex items-center gap-10 whitespace-nowrap">{t}<span className="text-signal">■</span></span>)}</Marquee>
    </div>
  );
}

function StatusPills() {
  const { t } = useTranslation();
  const live = useLiveStatus();
  const { health, error } = useHealth();
  const dot = live === "live" ? "bg-mint-500" : live === "connecting" ? "bg-sun-500" : "bg-signal";
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="badge bg-bone" role="status">
        <span className="relative flex h-2 w-2"><span className={`absolute inset-0 rounded-full ${dot} ${live === "live" ? "animate-pulsering" : ""}`} /><span className={`relative h-2 w-2 rounded-full ${dot}`} /></span>
        {t(`status.${live}`)}
      </span>
      {health && <span className={`badge ${health.mock_mode ? "bg-sun-300" : "bg-mint-300"}`}>{health.mock_mode ? t("status.mock") : t("status.keys")}</span>}
      {health && <span className={`badge ${health.database_ok ? "bg-bone" : "bg-pink-300"}`}><Database size={10} aria-hidden />{health.database.split(" ")[0]}</span>}
      {error && <span className="badge bg-pink-300">{error}</span>}
    </div>
  );
}

function Logo() {
  return (
    <Link to="/about" className="group relative block overflow-hidden border-2 border-ink bg-ink p-3 text-bone" aria-label="About RELAY">
      <span className="absolute -right-6 -top-6 h-16 w-16 rounded-full orb transition-transform duration-700 group-hover:translate-y-3 group-hover:scale-110" aria-hidden />
      <p className="mega relative text-[40px] lowercase">relay<span className="text-signal">.</span></p>
      <p className="relative font-mono text-[9.5px] uppercase tracking-[0.22em] text-bone/70">reports in / relief out</p>
    </Link>
  );
}

export default function Layout() {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  let n = 0;
  const nav = (
    <nav aria-label="Main" className="flex h-full flex-col gap-5 overflow-y-auto p-3">
      <Logo />
      {NAV.map((g, gi) => (
        <div key={g.group}>
          <div className="mb-1 flex items-baseline gap-2 border-b-2 border-ink pb-1">
            <span className="index">0{gi + 1}</span>
            <span className="font-display text-[15px] font-extrabold uppercase tracking-tight">{t(`nav.${g.group}`)}</span>
          </div>
          <div>
            {g.items.map((it) => {
              n += 1;
              const num = String(n).padStart(2, "0");
              return (
                <NavLink key={it.to} to={it.to} end={"end" in it} onClick={() => setOpen(false)}
                  className={({ isActive }) => `group relative flex items-baseline gap-2.5 border-b border-ink/15 px-1 py-[7px] text-[13.5px] font-medium transition-colors ${isActive
                    ? "bg-ink text-bone" : "text-ink/80 hover:bg-bone hover:text-ink"}`}>
                  {({ isActive }) => (
                    <>
                      <span className={`font-mono text-[10px] ${isActive ? "text-signal" : "text-ink/40"}`}>{num}</span>
                      <span className="truncate transition-transform duration-200 group-hover:translate-x-1">{t(`nav.${it.key}`)}</span>
                      {isActive && <motion.span layoutId="nav-dot" className="ml-auto h-2 w-2 self-center rounded-full bg-signal" />}
                    </>
                  )}
                </NavLink>
              );
            })}
          </div>
        </div>
      ))}
      <p className="mt-auto border-2 border-dashed border-ink/40 p-2.5 text-[11px] leading-snug text-ink/60">
        <span className="serif-i text-[15px] text-ink">Synthetic.</span> Places are real; every report, person and stock count here is invented.
      </p>
    </nav>
  );
  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 border-r-2 border-ink bg-paper lg:block">{nav}</aside>
      <AnimatePresence>
        {open && (
          <motion.div className="fixed inset-0 z-[1200] lg:hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div className="absolute inset-0 bg-ink/60" onClick={() => setOpen(false)} />
            <motion.aside className="relative h-full w-72 border-r-2 border-ink bg-paper" initial={{ x: -300 }} animate={{ x: 0 }} exit={{ x: -300 }}>
              <button className="btn-ghost absolute right-2 top-2 z-10 !p-1" onClick={() => setOpen(false)} aria-label="Close menu"><X size={16} /></button>
              {nav}
            </motion.aside>
          </motion.div>
        )}
      </AnimatePresence>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-[1000] border-b-2 border-ink bg-paper/95 backdrop-blur">
          <Ticker />
          <div className="flex flex-wrap items-center gap-2 px-4 py-2">
            <button className="btn-ghost !p-1.5 lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu"><Menu size={16} /></button>
            <StatusPills />
            <DisasterSelector />
            <RoleSwitcher />
            <div className="ml-auto flex items-center border-2 border-ink bg-bone" role="group" aria-label={t("common.language")}>
              {UI_LANGS.map((l) => (
                <button key={l.code} onClick={() => setUiLang(l.code)} aria-pressed={i18n.language === l.code}
                  className={`border-r border-ink px-2.5 py-1 font-mono text-[11px] font-bold last:border-r-0 ${i18n.language === l.code ? "bg-ink text-bone" : "text-ink hover:bg-cream"}`}>{l.label}</button>
              ))}
            </div>
          </div>
        </header>
        <main className="relative min-w-0 flex-1 overflow-x-clip p-4 sm:p-6">
          <div key={`wipe-${loc.pathname}`} className="wipe pointer-events-none fixed inset-y-0 left-0 right-0 z-[1100] bg-ink lg:left-60" aria-hidden />
          <motion.div key={loc.pathname} initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ type: "spring", stiffness: 260, damping: 28, delay: 0.25 }}>
            <Outlet />
          </motion.div>
        </main>
      </div>
      <AssistantDrawer />
      <GuideOverlay />
    </div>
  );
}

/** Page header: index number, huge type, hairline grid and one surreal object (picked from the title). */
export function PageHeader({ title, sub, children, kicker, explain, section }: { title: string; sub?: string; children?: ReactNode; kicker?: string; tone?: string; explain?: ReactNode; section?: string }) {
  const h = [...title].reduce((a, c) => a + c.charCodeAt(0), 0);
  const obj = h % 4;
  return (
    <div className="relative mb-6 overflow-hidden border-2 border-ink bg-bone shadow-hard">
      <div className="pat-grid absolute inset-0" aria-hidden />
      <div className="absolute right-0 top-0 hidden h-full w-[34%] border-l-2 border-ink sky sm:block" aria-hidden />
      {obj === 0 && <Moon className="right-[9%] top-6 hidden sm:block" size={110} />}
      {obj === 1 && <Blob className="right-[11%] top-8 hidden h-24 w-24 sm:block" />}
      {obj === 2 && <Eye className="right-[10%] top-10 hidden sm:block" size={130} />}
      {obj === 3 && <Door className="right-[13%] top-6 hidden h-28 w-16 sm:block" />}
      <Drip className="right-[4%] top-0 hidden h-12 w-16 sm:block" />
      <div className="relative flex flex-wrap items-end justify-between gap-4 p-5 sm:p-7 sm:pr-[38%]">
        <div className="min-w-0 max-w-3xl">
          <div className="flex flex-wrap items-center gap-2">
            {kicker && <span className="sticker bg-bone">{kicker}</span>}
            {section && <Explain id={section} />}
            {explain}
          </div>
          <h1 className="mega mt-4 text-[42px] sm:text-[60px]">{title}<span className="text-signal">.</span></h1>
          {sub && <p className="mt-3 max-w-2xl border-l-2 border-ink pl-3 text-[14.5px] text-ink/75">{sub}</p>}
        </div>
        {children && <div className="relative flex flex-wrap gap-2">{children}</div>}
      </div>
    </div>
  );
}
