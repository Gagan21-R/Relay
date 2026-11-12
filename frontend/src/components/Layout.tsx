// App shell, BRUTALIST: colour-blocked navigation groups (clay / stone / sage / sand), thick black borders, a sand
// ticker, square controls, and page headers with huge uppercase type next to a giant number block in the section's
// colour. No entrance animations.
import { ReactNode, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AnimatePresence, motion } from "framer-motion";
import { Database, Menu, X } from "lucide-react";
import { setUiLang, UI_LANGS } from "../i18n";
import { useHealth } from "../hooks/useHealth";
import { useLiveStatus } from "../hooks/useLive";
import { useApi } from "../hooks/useApi";
import { Marquee } from "./motion";
import AssistantDrawer, { Explain } from "./Assistant";
import GuideOverlay from "./Guide";
import { DisasterSelector } from "./Disaster";
import { RoleSwitcher } from "./Role";

/** Section colours, all light tones that sit on the cream background: SEE = clay, DECIDE = stone, ACT = sage, PROVE = sand. */
export const GROUP_BG: Record<string, string> = { see: "bg-signal", decide: "bg-blue", act: "bg-go", prove: "bg-sand" };

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
  if (!s) return <div className="h-7 bg-sand" />;
  const items = [
    `T+${s.clock.toFixed(1)} h`, `${s.reports} reports`, `${s.languages} languages`, `${s.incidents} incidents`,
    `${s.fast_verify} in fast verify`, `${s.plans_pending} plan(s) awaiting approval`, `${s.dispatches_active} deliveries moving`,
    `${s.alerts_open} open alerts`, s.zones_down.length ? `internet down: ${s.zones_down.join(", ")}` : "all zones online",
    s.blackout_zones.length ? `silent zones: ${s.blackout_zones.join(", ")}` : "no silent zones",
    `synthetic scenario — ${s.scenario_name ?? "Kodagu, Karnataka"}`, "ai interprets / rules enforce / people decide",
  ];
  return (
    <div className="border-b-2 border-ink bg-sand py-1.5 font-mono text-[12px] font-extrabold uppercase tracking-[0.1em] text-ink">
      <Marquee>{items.map((t, i) => <span key={i} className="flex items-center gap-10 whitespace-nowrap">{t}<span className="text-brand-600">■</span></span>)}</Marquee>
    </div>
  );
}

function StatusPills() {
  const { t } = useTranslation();
  const live = useLiveStatus();
  const { health, error } = useHealth();
  const dot = live === "live" ? "bg-go" : live === "connecting" ? "bg-tangerine-400" : "bg-signal";
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="badge bg-bone" role="status">
        <span className="relative flex h-2 w-2"><span className={`absolute inset-0 rounded-full ${dot} ${live === "live" ? "animate-pulsering" : ""}`} /><span className={`relative h-2 w-2 rounded-full ${dot}`} /></span>
        {t(`status.${live}`)}
      </span>
      {health && <span className={`badge ${health.mock_mode ? "bg-cream" : "bg-mint-300"}`}>{health.mock_mode ? t("status.mock") : t("status.keys")}</span>}
      {health && <span className={`badge ${health.database_ok ? "bg-bone" : "bg-pink-300"}`}><Database size={10} aria-hidden />{health.database.split(" ")[0]}</span>}
      {error && <span className="badge bg-pink-300">{error}</span>}
    </div>
  );
}

function Logo() {
  return (
    <Link to="/about" className="block border-2 border-ink bg-signal px-3 pb-2 pt-2 text-ink shadow-hard" aria-label="About RELAY">
      <p className="whitespace-nowrap font-display text-[44px] uppercase leading-none tracking-[-0.04em]">Relay<span className="text-ink">.</span></p>
      <p className="mt-1 font-mono text-[10px] font-extrabold uppercase tracking-[0.14em] text-ink">reports in / relief out</p>
    </Link>
  );
}

export default function Layout() {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  let n = 0;
  const nav = (
    <nav aria-label="Main" className="flex h-full flex-col gap-4 overflow-y-auto p-3">
      <Logo />
      {NAV.map((g, gi) => (
        <div key={g.group}>
          <div className={`flex items-baseline gap-2 border-2 border-ink px-2 py-1 text-ink ${GROUP_BG[g.group]}`}>
            <span className="font-mono text-[11px] font-extrabold">0{gi + 1}</span>
            <span className="font-display text-[16px] uppercase">{t(`nav.${g.group}`)}</span>
          </div>
          <div className="border-x-2 border-b-2 border-ink bg-white">
            {g.items.map((it) => {
              n += 1;
              const num = String(n).padStart(2, "0");
              return (
                <NavLink key={it.to} to={it.to} end={"end" in it} onClick={() => setOpen(false)}
                  className={({ isActive }) => `group relative flex items-baseline gap-2.5 border-b-2 border-ink px-2 py-[6px] font-mono text-[12px] font-extrabold uppercase last:border-b-0 ${isActive
                    ? "bg-sand text-ink" : "text-ink hover:bg-cream"}`}>
                  {({ isActive }) => (
                    <>
                      <span className={`text-[10px] ${isActive ? "text-brand-600" : "text-ink/50"}`}>{num}</span>
                      <span className="truncate">{t(`nav.${it.key}`)}</span>
                      {isActive && <span className="ml-auto h-3 w-3 self-center border-2 border-ink bg-signal" />}
                    </>
                  )}
                </NavLink>
              );
            })}
          </div>
        </div>
      ))}
      <p className="mt-auto border-2 border-ink bg-sand p-2.5 font-mono text-[10.5px] font-bold uppercase leading-snug text-ink">
        <span className="text-brand-600">Synthetic.</span> Places are real; every report, person and stock count here is invented.
      </p>
    </nav>
  );
  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 border-r-2 border-ink bg-cream lg:block">{nav}</aside>
      <AnimatePresence>
        {open && (
          <motion.div className="fixed inset-0 z-[1200] lg:hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div className="absolute inset-0 bg-sand/60" onClick={() => setOpen(false)} />
            <motion.aside className="relative h-full w-72 border-r-2 border-ink bg-paper" initial={{ x: -300 }} animate={{ x: 0 }} exit={{ x: -300 }}>
              <button className="btn-ghost absolute right-2 top-2 z-10 !p-1" onClick={() => setOpen(false)} aria-label="Close menu"><X size={16} /></button>
              {nav}
            </motion.aside>
          </motion.div>
        )}
      </AnimatePresence>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-[1000] border-b-2 border-ink bg-white">
          <Ticker />
          <div className="flex flex-wrap items-center gap-2 px-4 py-2">
            <button className="btn-ghost !p-1.5 lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu"><Menu size={16} /></button>
            <StatusPills />
            <DisasterSelector />
            <RoleSwitcher />
            <div className="ml-auto flex items-center border-2 border-ink bg-bone" role="group" aria-label={t("common.language")}>
              {UI_LANGS.map((l) => (
                <button key={l.code} onClick={() => setUiLang(l.code)} aria-pressed={i18n.language === l.code}
                  className={`border-r-2 border-ink px-2.5 py-1 font-mono text-[12px] font-extrabold last:border-r-0 ${i18n.language === l.code ? "bg-blue text-ink" : "text-ink hover:bg-cream"}`}>{l.label}</button>
              ))}
            </div>
          </div>
        </header>
        <main className="relative min-w-0 flex-1 overflow-x-clip p-4 sm:p-6">
          <Outlet key={loc.pathname} />
        </main>
      </div>
      <AssistantDrawer />
      <GuideOverlay />
    </div>
  );
}

/** Page header: huge uppercase title on white, and a giant number block in the section's colour. */
export function PageHeader({ title, sub, children, kicker, explain, section }: { title: string; sub?: string; children?: ReactNode; kicker?: string; tone?: string; explain?: ReactNode; section?: string }) {
  const loc = useLocation();
  const flat = NAV.flatMap((g) => (g.items as readonly { to: string }[]).map((it) => ({ to: it.to, group: g.group })));
  const idx = flat.findIndex((it) => it.to === loc.pathname);
  const num = String(idx >= 0 ? idx + 1 : 0).padStart(2, "0");
  const bg = GROUP_BG[idx >= 0 ? flat[idx].group : "prove"];
  return (
    <div className="relative mb-6 grid border-2 border-ink bg-white shadow-hard-lg sm:grid-cols-[1fr_220px]">
      <div className="flex flex-wrap items-end justify-between gap-4 p-5 sm:p-7">
        <div className="min-w-0 max-w-3xl">
          <div className="flex flex-wrap items-center gap-2">
            {kicker && <span className="sticker bg-sand text-ink">{kicker}</span>}
            {section && <Explain id={section} />}
            {explain}
          </div>
          <h1 className="mega mt-4 text-[40px] sm:text-[58px]">{title}</h1>
          {sub && <p className="mt-3 max-w-2xl border-2 border-ink bg-cream px-3 py-2 text-[14px] font-medium">{sub}</p>}
        </div>
        {children && <div className="relative flex flex-wrap gap-2">{children}</div>}
      </div>
      <div className={`hidden flex-col justify-between border-l-2 border-ink p-4 text-ink sm:flex ${bg}`} aria-hidden>
        <span className="font-mono text-[11px] font-extrabold uppercase tracking-[0.14em]">relay / {num}</span>
        <span className="font-display text-[110px] leading-none tracking-[-0.06em]">{num}</span>
        <span className="h-4 w-full border-2 border-ink bg-white" />
      </div>
    </div>
  );
}
