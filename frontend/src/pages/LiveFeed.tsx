import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { PageHeader } from "../components/Layout";
import ReportCard from "../components/ReportCard";
import { CHANNELS, Empty, LANG_NAMES, Stat } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { Report } from "../services/types";

export default function LiveFeed() {
  const { t } = useTranslation();
  const { data } = useApi<Report[]>("/api/reports?limit=500", ["report", "incident"], 250);
  const [channel, setChannel] = useState("");
  const [lang, setLang] = useState("");
  const [showBlocked, setShowBlocked] = useState(false);
  const all = data ?? [];
  const blocked = all.filter((r) => r.status === "blocked");
  const list = useMemo(() => all.filter((r) => (!channel || r.channel === channel) && (!lang || r.original_language === lang) && (showBlocked || r.status !== "blocked")), [all, channel, lang, showBlocked]);
  const langs = useMemo(() => [...new Set(all.map((r) => r.original_language).filter(Boolean))] as string[], [all]);
  const offline = all.filter((r) => !CHANNELS[r.channel]?.internet).length;
  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.feed")} sub={t("pages.feed")} section="feed.page" />
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="reports" value={all.length} />
        <Stat label="languages" value={langs.length} />
        <Stat label="arrived without internet (SMS, voice, radio)" value={offline} />
        <Stat label="could not get out (zone internet down)" value={blocked.length} tone={blocked.length ? "bg-paper" : "bg-white"} />
      </div>
      <div className="card flex flex-wrap items-center gap-2 p-3 text-sm">
        <select className="input !w-auto !py-1" value={channel} onChange={(e) => setChannel(e.target.value)} aria-label="Channel">
          <option value="">All channels</option>
          {Object.entries(CHANNELS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
        <select className="input !w-auto !py-1" value={lang} onChange={(e) => setLang(e.target.value)} aria-label="Language">
          <option value="">All languages</option>
          {langs.map((l) => <option key={l} value={l}>{LANG_NAMES[l] ?? l}</option>)}
        </select>
        <label className="flex items-center gap-1.5 text-ink/70"><input type="checkbox" checked={showBlocked} onChange={(e) => setShowBlocked(e.target.checked)} />show reports blocked by internet outage</label>
        <span className="ml-auto text-xs text-ink/60">updates live over WebSocket</span>
      </div>
      {!list.length ? <Empty>No reports match.</Empty> : (
        <div className="grid gap-3 lg:grid-cols-2">{list.map((r) => <ReportCard key={r.id} r={r} />)}</div>
      )}
    </div>
  );
}
