import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Activity, AlertTriangle, BarChart3, Box, ClipboardCheck, Database, FlaskConical, Home, Inbox, Map as MapIcon, Menu,
  Package, PhoneCall, ScrollText, ShieldAlert, Smartphone, Truck, X,
} from "lucide-react";
import { setUiLang, UI_LANGS } from "../i18n";
import { useHealth } from "../hooks/useHealth";
import { useLiveStatus } from "../hooks/useLive";

export const NAV = [
  { group: "see", items: [
    { to: "/", key: "map", icon: MapIcon, end: true },
    { to: "/feed", key: "feed", icon: Inbox },
    { to: "/twin3d", key: "twin3d", icon: Box },
  ] },
  { group: "decide", items: [
    { to: "/incidents", key: "incidents", icon: Activity },
    { to: "/fast-verify", key: "fastVerify", icon: ShieldAlert },
    { to: "/plans", key: "plans", icon: ClipboardCheck },
  ] },
  { group: "act", items: [
    { to: "/dispatch", key: "dispatch", icon: Truck },
    { to: "/resources", key: "resources", icon: Package },
    { to: "/shelters", key: "shelters", icon: Home },
    { to: "/alerts", key: "alerts", icon: AlertTriangle },
    { to: "/phone", key: "phone", icon: PhoneCall },
    { to: "/scenario", key: "scenario", icon: FlaskConical },
  ] },
  { group: "prove", items: [
    { to: "/metrics", key: "metrics", icon: BarChart3 },
    { to: "/audit", key: "audit", icon: ScrollText },
    { to: "/field", key: "field", icon: Smartphone },
  ] },
] as const;

function StatusPills() {
  const { t } = useTranslation();
  const live = useLiveStatus();
  const { health, error } = useHealth();
  const dot = live === "live" ? "bg-emerald-500" : live === "connecting" ? "bg-amber-400" : "bg-red-500";
  return (
    <div className="flex flex-wrap items-center gap-1.5 text-xs">
      <span className="badge bg-slate-100 text-slate-700" role="status"><span className={`h-2 w-2 rounded-full ${dot}`} />{t(`status.${live}`)}</span>
      {health && <span className={`badge ${health.mock_mode ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800"}`}>{health.mock_mode ? t("status.mock") : t("status.keys")}</span>}
      {health && <span className={`badge ${health.database_ok ? "bg-slate-100 text-slate-700" : "bg-red-100 text-red-700"}`}><Database size={11} aria-hidden />{health.database.split(" ")[0]}</span>}
      {error && <span className="badge bg-red-100 text-red-700">{error}</span>}
    </div>
  );
}

export default function Layout() {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  const nav = (
    <nav aria-label="Main" className="flex h-full flex-col gap-4 overflow-y-auto p-3">
      <div className="rounded-xl bg-gradient-to-br from-brand-600 to-brand-800 p-3 text-white">
        <p className="text-2xl font-bold tracking-tight">{t("brand.name")}</p>
        <p className="text-[11px] leading-tight text-brand-100">{t("brand.tag")}</p>
      </div>
      {NAV.map((g) => (
        <div key={g.group}>
          <p className="mb-1 px-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">{t(`nav.${g.group}`)}</p>
          {g.items.map((it) => {
            const I = it.icon;
            return (
              <NavLink key={it.to} to={it.to} end={"end" in it} onClick={() => setOpen(false)}
                className={({ isActive }) => `flex items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm ${isActive ? "bg-brand-50 font-semibold text-brand-700" : "text-slate-600 hover:bg-slate-100"}`}>
                <I size={16} aria-hidden />{t(`nav.${it.key}`)}
              </NavLink>
            );
          })}
        </div>
      ))}
    </nav>
  );
  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 border-r border-slate-200 bg-white lg:block">{nav}</aside>
      {open && (
        <div className="fixed inset-0 z-[1200] lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} />
          <aside className="relative h-full w-64 bg-white">
            <button className="btn-ghost absolute right-2 top-2 !p-1" onClick={() => setOpen(false)} aria-label="Close menu"><X size={16} /></button>
            {nav}
          </aside>
        </div>
      )}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-[1000] flex flex-wrap items-center gap-2 border-b border-slate-200 bg-white/90 px-4 py-2 backdrop-blur">
          <button className="btn-ghost !p-1.5 lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu"><Menu size={16} /></button>
          <StatusPills />
          <div className="ml-auto flex items-center gap-1" role="group" aria-label={t("common.language")}>
            {UI_LANGS.map((l) => (
              <button key={l.code} onClick={() => setUiLang(l.code)} aria-pressed={i18n.language === l.code}
                className={`rounded-md px-2 py-1 text-xs font-semibold ${i18n.language === l.code ? "bg-brand-600 text-white" : "text-slate-600 hover:bg-slate-100"}`}>{l.label}</button>
            ))}
          </div>
        </header>
        <main key={loc.pathname} className="min-w-0 flex-1 p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function PageHeader({ title, sub, children }: { title: string; sub?: string; children?: React.ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        <h1 className="text-2xl font-bold tracking-tight text-ink sm:text-3xl">{title}</h1>
        {sub && <p className="mt-1 max-w-3xl text-sm text-slate-600">{sub}</p>}
      </div>
      {children && <div className="flex flex-wrap gap-2">{children}</div>}
    </div>
  );
}
