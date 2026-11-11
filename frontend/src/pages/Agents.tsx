// Agent conversations: the agents ask, offer, accept, decline and escalate — and the replies change what they do.
// Left: the live network (who talks to whom, how often). Right: every conversation, threaded, as it happens.
import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { PageHeader } from "../components/Layout";
import { Empty, Panel, simTime } from "../components/ui";
import { useApi } from "../hooks/useApi";

export const AGENT_META: Record<string, { label: string; colour: string; role: string }> = {
  intake: { label: "Intake", colour: "#F6F4EF", role: "reads every report" },
  trust: { label: "Trust", colour: "#E2CF98", role: "duplicates, credibility" },
  triage: { label: "Triage", colour: "#C9C3FF", role: "who first" },
  resource: { label: "Resource", colour: "#9FBF9F", role: "stock, shortages" },
  blackout: { label: "Blackout", colour: "#0B0B0C", role: "silent places" },
  monitor: { label: "Monitor", colour: "#D9895B", role: "what changed" },
  coordination: { label: "Coordination", colour: "#5A4FD6", role: "plans, routes, people" },
  duty_officer: { label: "Duty Officer", colour: "#FF3D1F", role: "a person decides" },
};
const ORDER = ["intake", "trust", "triage", "monitor", "coordination", "resource", "blackout", "duty_officer"];
const PERF: Record<string, string> = { inform: "bg-white", request: "bg-sun-300", propose: "bg-lime-300", accept: "bg-mint-300",
  decline: "bg-pink-200", escalate: "bg-pink-400", reply: "bg-cobalt-200" };

function Network({ edges, active }: { edges: any[]; active: Set<string> }) {
  const W = 520, H = 420, cx = W / 2, cy = H / 2, R = 160;
  const pos = Object.fromEntries(ORDER.map((a, i) => [a, [cx + R * Math.cos((i / ORDER.length) * 2 * Math.PI - Math.PI / 2), cy + R * Math.sin((i / ORDER.length) * 2 * Math.PI - Math.PI / 2)]]));
  const pairs = new Map<string, number>();
  for (const e of edges) { const k = `${e.from}>${e.to}`; pairs.set(k, (pairs.get(k) ?? 0) + e.count); }
  const max = Math.max(1, ...pairs.values());
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Agent communication network">
      <defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="11" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#0B0B0C" /></marker></defs>
      {[...pairs].map(([k, n]) => {
        const [a, b] = k.split(">");
        if (!pos[a] || !pos[b]) return null;
        const [x1, y1] = pos[a], [x2, y2] = pos[b];
        const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy) || 1, off = 12;
        const nx = -dy / len * off, ny = dx / len * off;        // offset so a→b and b→a do not overlap
        const sx = x1 + dx / len * 34 + nx, sy = y1 + dy / len * 34 + ny, ex = x2 - dx / len * 38 + nx, ey = y2 - dy / len * 38 + ny;
        const hot = active.has(k);
        return (
          <g key={k}>
            <line x1={sx} y1={sy} x2={ex} y2={ey} stroke={hot ? "#FF3D1F" : "#0B0B0C"} strokeOpacity={hot ? 1 : 0.35} strokeWidth={1 + 4 * (n / max)} markerEnd="url(#arr)" />
            <text x={(sx + ex) / 2 + nx} y={(sy + ey) / 2 + ny} fontSize="10" fontWeight="800" textAnchor="middle" fill="#0B0B0C">{n}</text>
          </g>);
      })}
      {ORDER.map((a) => {
        const [x, y] = pos[a];
        const m = AGENT_META[a];
        return (
          <g key={a}>
            <circle cx={x} cy={y} r={30} fill={m.colour} stroke="#0B0B0C" strokeWidth={2.5} />
            <text x={x} y={y + 3} fontSize="10" fontWeight="900" textAnchor="middle" fill={a === "blackout" || a === "duty_officer" || a === "coordination" ? "#fff" : "#0B0B0C"}>{m.label}</text>
            <text x={x} y={y + 44} fontSize="9" textAnchor="middle" fill="#0B0B0C" opacity={0.6}>{m.role}</text>
          </g>);
      })}
    </svg>
  );
}

export default function Agents() {
  const msgs = useApi<any[]>("/api/agents/messages?limit=600", ["agent_message"], 400);
  const summary = useApi<any>("/api/agents/summary", ["agent_message"], 1500);
  const [agent, setAgent] = useState("");
  const [topic, setTopic] = useState("");
  const all = msgs.data ?? [];
  const topics = useMemo(() => [...new Set(all.map((m) => m.topic))].sort(), [all]);
  const shown = all.filter((m) => (!agent || m.sender === agent || m.recipient === agent) && (!topic || m.topic === topic));
  const threads = useMemo(() => {
    const by = new Map<string, any[]>();
    for (const m of shown) by.set(m.conversation, [...(by.get(m.conversation) ?? []), m]);
    return [...by.values()].map((t) => t.sort((a, b) => a.id - b.id)).slice(0, 60);
  }, [shown]);
  const active = useMemo(() => new Set(all.slice(0, 6).map((m) => `${m.sender}>${m.recipient}`)), [all]);
  return (
    <div className="space-y-4">
      <PageHeader title="Agent conversations" sub="The agents do not just run one after another: they ask each other for help, make offers, accept or decline them, and escalate to a person. Every message is shown here as it happens." kicker={`${summary.data?.total ?? 0} messages`} tone="bg-pink-300" section="agents.page" />
      <div className="grid gap-4 xl:grid-cols-[540px_1fr]">
        <div className="space-y-4">
          <Panel title="Who talks to whom" tone="bg-lime-400" section="agents.network">
            <Network edges={summary.data?.edges ?? []} active={active} />
            <p className="text-[11px] font-bold text-ink/60">Arrow thickness = number of messages; pink = the latest exchanges.</p>
          </Panel>
          <Panel title="The conversations that change outcomes" tone="bg-sun-300">
            <ul className="space-y-1.5 text-xs">
              <li><b>Intake → Trust → Triage → Monitor:</b> hand-offs — "new report", "it joins incident #3", "re-ranked".</li>
              <li><b>Coordination ⇄ Resource:</b> "I'm short of 2 boats for Bhagamandala" → "Kushalnagar depot can send 2" → <i>accept</i> (a new plan line) — or <i>escalate</i> to the Duty Officer.</li>
              <li><b>Coordination ⇄ Trust:</b> "is #9 still credible before I send a team?" → "unverified, no contradictions: verify on arrival".</li>
              <li><b>Trust ⇄ Coordination:</b> "life-safety but unverified — who can check on the ground?" → "V-001 is free, 1 km away".</li>
              <li><b>Blackout ⇄ Resource:</b> "Hattihole is silent: what should recon carry?" → quantities from the nearest depot.</li>
              <li><b>Monitor → Coordination → Duty Officer:</b> "road blocked, re-plan" → "plan v5 ready" → "needs your approval".</li>
            </ul>
            <p className="mt-2 text-[11px] text-ink/60">Messages carry facts and numbers, not prompts; no LLM decides anything here.</p>
          </Panel>
        </div>
        <Panel title={`Conversations (${threads.length})`} tone="bg-cobalt-300">
          <div className="mb-3 flex flex-wrap gap-2">
            <select className="input max-w-[12rem]" value={agent} onChange={(e) => setAgent(e.target.value)} aria-label="Filter by agent">
              <option value="">all agents</option>{ORDER.map((a) => <option key={a} value={a}>{AGENT_META[a].label}</option>)}</select>
            <select className="input max-w-[14rem]" value={topic} onChange={(e) => setTopic(e.target.value)} aria-label="Filter by topic">
              <option value="">all topics</option>{topics.map((t) => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}</select>
          </div>
          {!threads.length ? <Empty>No messages yet. Start a guided run from the disaster menu, the map or the Scenario Lab.</Empty> : (
            <div className="space-y-3">
              {threads.map((t) => (
                <motion.div key={t[0].conversation} layout animate={{ opacity: 1, y: 0 }} className="rounded-2xl border-2 border-ink bg-white p-2.5">
                  <p className="mb-1 text-[10px] font-extrabold uppercase tracking-wider text-ink/50">{t[0].topic.replace(/_/g, " ")} · {simTime(t[0].sim_time)}</p>
                  <ul className="space-y-1">
                    {t.map((m: any) => {
                      const s = AGENT_META[m.sender] ?? { label: m.sender, colour: "#fff" }, r = AGENT_META[m.recipient] ?? { label: m.recipient, colour: "#fff" };
                      return (
                        <li key={m.id} className={`flex gap-2 ${m.in_reply_to ? "pl-6" : ""}`}>
                          <span className="mt-0.5 h-3 w-3 shrink-0 rounded-full border-2 border-ink" style={{ background: s.colour }} />
                          <div className="min-w-0 text-xs">
                            <p className="font-extrabold">{s.label} → {r.label} <span className={`badge ml-1 ${PERF[m.performative] ?? "bg-white"}`}>{m.performative}</span></p>
                            <p className="text-ink/80">{m.summary}</p>
                          </div>
                        </li>);
                    })}
                  </ul>
                </motion.div>))}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
