// The RELAY landing page, built as a bold creative-agency portfolio in a BRUTALIST style with motion: raw grid, giant
// uppercase type, thick black borders, hard shadows, light warm fills only. Headlines rise word by word, sections slide
// in as they scroll into view, case studies show a live-looking preview, team cards flip, the process line fills as you
// scroll. Sections: hero · languages · manifesto · case studies · capabilities · team · process · research · builders
// (the people of Team Tech Architects, light green) · contact (files a real report) · footer.
import { ReactNode, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, motion, useMotionValue, useScroll, useSpring, useTransform } from "framer-motion";
import { ArrowRight, ArrowUpRight, CheckCircle2, Send } from "lucide-react";
import { useApi } from "../hooks/useApi";
import { Explain } from "../components/Assistant";
import { startGuide } from "../components/Guide";
import { CountUp, Item, Marquee, Reveal, RiseText, ScrollProgress, Stagger, WordCycle } from "../components/motion";
import { api } from "../services/api";

const LANGS = ["ಕನ್ನಡ", "हिंदी", "മലയാളം", "தமிழ்", "తెలుగు", "मराठी", "বাংলা", "অসমীয়া", "ଓଡ଼ିଆ", "ગુજરાતી", "ਪੰਜਾਬੀ", "नेपाली", "Mizo", "Khasi", "English"];
const HELP = ["help madi", "मदद करो", "സഹായിക്കൂ", "உதவி", "సహాయం", "help us", "मदत करा", "সাহায্য"];

type Case = { n: string; title: string; to: string; claim: string; body: string; stat: string; tag: string; fill: string; preview: ReactNode };

const Bubble = ({ children, side = "l", fill = "bg-white" }: { children: ReactNode; side?: "l" | "r"; fill?: string }) => (
  <div className={`max-w-[80%] border-2 border-ink px-2 py-1 font-mono text-[11px] font-bold ${fill} ${side === "r" ? "ml-auto" : ""}`}>{children}</div>
);

const CASES: Case[] = [
  { n: "01", title: "The SMS and the tweet", to: "/incidents", tag: "Trust agent", fill: "bg-cream", claim: "Two reports, two languages, one flooded village.",
    body: "A Kannada SMS and an English post land minutes apart. Same place, same meaning, same hour, compatible needs: one incident — not two boats.",
    stat: "6 reports → 1 incident",
    preview: (<div className="space-y-2"><Bubble>ಮನೆ ಒಳಗೆ ನೀರು · Karadigodu</Bubble><Bubble side="r" fill="bg-sand">Karadigodu flooded, 7 stuck</Bubble>
      <div className="border-2 border-dashed border-ink bg-go px-2 py-1 text-center font-mono text-[11px] font-extrabold uppercase">merged → incident #4</div></div>) },
  { n: "02", title: "The dam that did not burst", to: "/alerts", tag: "Trust agent", fill: "bg-stop", claim: "“Share to all.” In three languages.",
    body: "A forward chain, a catastrophe with no detail, and an official bulletin that says the opposite. It scores false; the correction goes out in every language.",
    stat: "0% credible · 8-language correction",
    preview: (<div className="relative space-y-2"><Bubble>DAM BURST!!! share to all 🙏</Bubble><Bubble>ಡ್ಯಾಮ್ ಒಡೆದಿದೆ forward</Bubble>
      <span className="absolute right-1 top-6 rotate-[-12deg] border-4 border-ink bg-white px-3 py-1 font-display text-2xl uppercase">False</span></div>) },
  { n: "03", title: "The village that went silent", to: "/blackout", tag: "Blackout agent", fill: "bg-taupe", claim: "Zero reports was the alarm.",
    body: "Inside the hazard, towers down, relatives elsewhere who cannot reach anyone. RELAY ranks the silence and asks Resource what a recon team should carry.",
    stat: "2,400 people · 0 reports · 1 recon",
    preview: (<div className="grid grid-cols-4 gap-1">{Array.from({ length: 12 }).map((_, i) => (
      <div key={i} className={`h-7 border-2 border-ink ${i === 6 ? "hatch-red bg-white" : i % 3 ? "bg-white" : "bg-cream"}`}>{i === 6 && <span className="block text-center font-mono text-[10px] font-extrabold">0</span>}</div>))}</div>) },
  { n: "04", title: "Two agents, one boat short", to: "/agents", tag: "Resource ↔ Coordination", fill: "bg-go", claim: "“I'm short of 2 boats.” — “Kushalnagar can send 2.”",
    body: "Coordination asks Resource for a second source; the offer becomes a plan line. When nobody has stock, Resource escalates to a person.",
    stat: "propose → accept → plan line",
    preview: (<div className="space-y-2"><Bubble>Coordination → short of 2 boats</Bubble><Bubble side="r" fill="bg-go">Resource → Kushalnagar can send 2</Bubble><Bubble>Coordination → accepted ✓</Bubble></div>) },
  { n: "05", title: "ಹೌದು is not confirmed", to: "/dispatch", tag: "A person decides", fill: "bg-blue", claim: "Arriving is not delivering. Delivering is not confirming.",
    body: "The recipient replies YES in Kannada. That is evidence. A Duty Officer confirms — the backend refuses anyone else.",
    stat: "created → … → confirmed",
    preview: (<div className="flex flex-wrap gap-1">{["created", "approved", "dispatched", "delivered", "confirmed"].map((s, i) => (
      <span key={s} className={`border-2 border-ink px-1.5 py-0.5 font-mono text-[10px] font-extrabold uppercase ${i === 4 ? "bg-go" : "bg-white"}`}>{s}</span>))}</div>) },
];

const CAPS = [
  ["Multilingual intake", "19 languages, native script, romanized, mixed, noisy voice — with honest support levels."],
  ["Evidence & rumours", "Duplicates across languages count once; sensational forwards never borrow credibility."],
  ["Triage with reasons", "Priority out of 100, every point explained, nine disaster profiles."],
  ["Safe routes", "Safest, not shortest. Unverified roads flagged; a person verifies before dispatch."],
  ["Agents that negotiate", "Requests, offers, accepts, escalations — deterministic and logged."],
  ["People decide", "Approve, verify, confirm, send. 403 for the wrong role, 409 for the wrong moment."],
];

const TEAM = [
  { name: "Intake", role: "reads every report", q: "What is this report saying?", asks: "Asks Trust: new or a duplicate?" },
  { name: "Trust", role: "duplicates, credibility", q: "Is it true, and have we seen it before?", asks: "Tells Triage what to re-rank." },
  { name: "Triage", role: "who first", q: "Who needs help first?", asks: "Tells Monitor what to watch." },
  { name: "Resource", role: "stock, shortages", q: "Do we have enough, and where?", asks: "Offers stock to Coordination." },
  { name: "Blackout", role: "silent places", q: "Which places have gone quiet?", asks: "Asks Resource what recon needs." },
  { name: "Monitor", role: "what changed", q: "Has something changed?", asks: "Asks Coordination to re-plan." },
  { name: "Coordination", role: "plans, routes, people", q: "Who goes where, with what — and did it arrive?", asks: "Escalates to the Duty Officer." },
  { name: "Duty Officer", role: "a person decides", q: "Approve. Verify. Confirm.", asks: "Nothing moves without me.", human: true },
];
const TEAM_FILL = ["bg-sand", "bg-blue", "bg-go", "bg-taupe", "bg-cream", "bg-stop", "bg-sand", "bg-signal"];

const PROCESS = [
  ["Set up", "choose a disaster and a place"], ["Understand", "intake · trust · triage · resource · blackout"],
  ["Decide", "monitor · coordination · ◆ approval"], ["Act", "◆ route check · dispatch · ◆ confirm"], ["Tell & learn", "◆ public messages · audit · metrics"],
];

const RESEARCH: [number, string, string, string, string][] = [
  [6, "~", "%", "of disaster social-media studies handled regional (non-English) languages", "Gopal et al. 2026, NHESS"],
  [7, "~", "%", "addressed resource identification", "Gopal et al. 2026"],
  [3, "1–", "%", "of tweets are geotagged", "Imran et al. 2020"],
  [75, ">", "%", "of US emergency agencies won't act on social media without a trusted second source", "Mehta et al. 2017"],
];

// The people who built RELAY. Names are taken from their GitHub handles; avatars come from GitHub.
const BUILDERS = [
  { name: "Gagan R", gh: "Gagan21-R", avatar: "https://avatars.githubusercontent.com/u/228348284?v=4" },
  { name: "Chiranjeevi Sathya", gh: "chiranjeevisathya78-design", avatar: "https://avatars.githubusercontent.com/u/272247768?v=4" },
  { name: "Pranav Angadi", gh: "pranavangadi77-dot", avatar: "https://avatars.githubusercontent.com/u/276653253?v=4" },
  { name: "Amogh Ravi", gh: "amogh-ravi1979", avatar: "https://avatars.githubusercontent.com/u/226490141?v=4" },
];

function BuilderCard({ b, i }: { b: (typeof BUILDERS)[number]; i: number }) {
  const [broken, setBroken] = useState(false);
  return (
    <Item>
      <motion.a href={`https://github.com/${b.gh}`} target="_blank" rel="noreferrer" whileHover={{ x: -6, y: -6 }}
        transition={{ type: "spring", stiffness: 500, damping: 30 }}
        className="group block border-2 border-ink bg-mint-200 shadow-hard transition-shadow duration-150 hover:shadow-hard-lg">
        <div className="flex items-end justify-between border-b-2 border-ink bg-mint-300 p-4">
          {broken ? (
            <span className="grid h-24 w-24 place-items-center border-2 border-ink bg-mint-200 font-display text-[56px] leading-none">{b.name[0]}</span>
          ) : (
            <img src={b.avatar} alt={`${b.name}'s GitHub avatar`} onError={() => setBroken(true)} loading="lazy"
              className="h-24 w-24 border-2 border-ink bg-mint-200 object-cover grayscale transition duration-300 group-hover:grayscale-0" />
          )}
          <span className="font-mono text-[12px] font-extrabold">{String(i + 1).padStart(2, "0")}</span>
        </div>
        <div className="p-4">
          <p className="font-mono text-[10px] font-extrabold uppercase tracking-[0.16em] text-ink/60">Team Tech Architects</p>
          <p className="mt-1 font-display text-[22px] uppercase leading-tight">{b.name}</p>
          <p className="mt-3 inline-flex items-center gap-1 border-2 border-ink bg-white px-2 py-0.5 font-mono text-[10.5px] font-extrabold">
            @{b.gh}<ArrowUpRight size={12} aria-hidden className="transition-transform group-hover:rotate-45" /></p>
        </div>
      </motion.a>
    </Item>
  );
}

type Summary = { reports: number; languages: number; incidents: number; offline_channel_reports: number; fast_verify: number; people_affected: number; scenario_name?: string };

/** A card that tilts a little toward the pointer (hard, small angles). */
function Tilt({ children, className = "" }: { children: ReactNode; className?: string }) {
  const x = useMotionValue(0), y = useMotionValue(0);
  const rx = useSpring(useTransform(y, [-0.5, 0.5], [5, -5]), { stiffness: 300, damping: 20 });
  const ry = useSpring(useTransform(x, [-0.5, 0.5], [-5, 5]), { stiffness: 300, damping: 20 });
  return (
    <motion.div className={className} style={{ rotateX: rx, rotateY: ry, transformPerspective: 900 }}
      onPointerMove={(e) => { const r = e.currentTarget.getBoundingClientRect(); x.set((e.clientX - r.left) / r.width - 0.5); y.set((e.clientY - r.top) / r.height - 0.5); }}
      onPointerLeave={() => { x.set(0); y.set(0); }}>
      {children}
    </motion.div>
  );
}

function SectionHead({ n, label, title, note }: { n: string; label: string; title: ReactNode; note?: ReactNode }) {
  return (
    <div className="grid border-b-2 border-ink lg:grid-cols-[280px_1fr]">
      <div className="border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2">
        <p className="label">{n} — {label}</p>{note && <div className="mt-2 text-sm text-ink/60">{note}</div>}
      </div>
      <Reveal className="p-5 sm:p-10"><h2 className="mega text-[44px] sm:text-[80px]">{title}</h2></Reveal>
    </div>
  );
}

function CaseCard({ c }: { c: Case }) {
  return (
    <Item>
      <Link to={c.to} className="group block h-full">
        <motion.article whileHover={{ x: -6, y: -6 }} transition={{ type: "spring", stiffness: 500, damping: 30 }}
          className="flex h-full flex-col border-2 border-ink bg-white shadow-hard transition-shadow duration-150 group-hover:shadow-hard-lg">
          {/* preview window */}
          <div className={`border-b-2 border-ink ${c.fill}`}>
            <div className="flex items-center gap-1.5 border-b-2 border-ink bg-white px-2 py-1">
              {[0, 1, 2].map((i) => <span key={i} className="h-2.5 w-2.5 border-2 border-ink bg-cream" />)}
              <span className="ml-2 truncate font-mono text-[10px] font-extrabold uppercase text-ink/60">relay{c.to === "/" ? "" : c.to}</span>
            </div>
            <div className="h-40 overflow-hidden p-4 transition-transform duration-300 group-hover:scale-[1.04]">{c.preview}</div>
          </div>
          <div className="flex flex-1 flex-col p-5">
            <div className="flex items-center justify-between gap-2">
              <span className="border-2 border-ink bg-signal px-1.5 font-mono text-[11px] font-extrabold">{c.n}</span>
              <span className="font-mono text-[10px] font-extrabold uppercase tracking-[0.12em] text-ink/60">{c.tag}</span>
            </div>
            <h3 className="mega mt-3 text-[28px]">{c.title}</h3>
            <p className="mt-1 font-medium">{c.claim}</p>
            <p className="mt-2 text-sm text-ink/70">{c.body}</p>
            <div className="mt-auto flex items-center justify-between gap-2 pt-4">
              <span className="border-2 border-ink bg-cream px-2 py-0.5 font-mono text-[10.5px] font-extrabold uppercase">{c.stat}</span>
              <span className="grid h-10 w-10 place-items-center border-2 border-ink bg-sand transition-transform duration-200 group-hover:rotate-45"><ArrowUpRight size={20} aria-hidden /></span>
            </div>
          </div>
        </motion.article>
      </Link>
    </Item>
  );
}

function TeamCard({ m, i }: { m: (typeof TEAM)[number]; i: number }) {
  return (
    <Item className="group h-64 [perspective:1000px]">
      <div tabIndex={0} aria-label={`${m.name}: ${m.q} ${m.asks}`}
        className="relative h-full w-full outline-none transition-transform duration-500 [transform-style:preserve-3d] group-hover:[transform:rotateY(180deg)] group-focus-within:[transform:rotateY(180deg)]">
        {/* front */}
        <div className="absolute inset-0 flex flex-col border-2 border-ink bg-white shadow-hard [backface-visibility:hidden]">
          <div className={`flex flex-1 items-end justify-between border-b-2 border-ink p-4 ${TEAM_FILL[i]}`}>
            <span className="font-display text-[110px] leading-[0.78] tracking-[-0.06em]">{m.name[0]}</span>
            <span className="font-mono text-[12px] font-extrabold">{String(i + 1).padStart(2, "0")}</span>
          </div>
          <div className="p-4">
            <p className="font-mono text-[10px] font-extrabold uppercase tracking-[0.16em] text-ink/60">{m.human ? "human" : "agent"} · {m.role}</p>
            <p className="mt-1 font-display text-2xl uppercase">{m.name}</p>
          </div>
        </div>
        {/* back */}
        <div className={`absolute inset-0 flex flex-col justify-between border-2 border-ink p-5 shadow-hard [backface-visibility:hidden] [transform:rotateY(180deg)] ${TEAM_FILL[i]}`}>
          <p className="font-mono text-[11px] font-extrabold uppercase tracking-[0.14em]">{m.name} asks</p>
          <p className="font-display text-[26px] uppercase leading-[1]">“{m.q}”</p>
          <p className="border-t-2 border-ink pt-2 font-mono text-[11px] font-extrabold uppercase">{m.asks}</p>
        </div>
      </div>
    </Item>
  );
}

function Process() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start 85%", "end 55%"] });
  const fill = useSpring(scrollYProgress, { stiffness: 200, damping: 30 });
  return (
    <section ref={ref} className="border-b-2 border-ink bg-sand">
      <div className="flex items-baseline justify-between border-b-2 border-ink px-5 py-3 sm:px-10">
        <p className="label">006 — Process</p><Link to="/workflow" className="link-grow font-mono text-[11px] font-extrabold uppercase">open the flowchart →</Link>
      </div>
      <div className="h-3 border-b-2 border-ink bg-white"><motion.div className="h-full origin-left bg-taupe" style={{ scaleX: fill }} /></div>
      <Stagger className="grid md:grid-cols-5" gap={0.1}>
        {PROCESS.map(([a, b], i) => (
          <Item key={a} className="border-b-2 border-ink p-6 md:border-b-0 md:border-r-2 md:last:border-r-0">
            <p className="font-display text-[72px] leading-none text-ink/25">{i + 1}</p>
            <p className="mt-2 font-display text-2xl uppercase">{a}</p>
            <p className="mt-1 font-mono text-[11px] font-bold uppercase tracking-wider text-ink/60">{b}</p>
          </Item>))}
      </Stagger>
      <p className="border-t-2 border-ink px-5 py-4 font-mono text-[11px] font-bold uppercase tracking-wider text-ink/60 sm:px-10">◆ = a person decides · whenever something changes, Monitor sends it back to Coordination to re-plan</p>
    </section>
  );
}

function ContactForm() {
  const [f, setF] = useState({ name: "", phone: "", text: "" });
  const [res, setRes] = useState<{ ref: string; lang?: string; place?: string } | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setErr(null);
    try {
      const r = await api<any>("/api/intake/web", { method: "POST", body: JSON.stringify({ text: f.text, name: f.name || undefined, phone: f.phone || undefined }) });
      setRes({ ref: r.report.ref, lang: r.report.original_language, place: r.report.location_text }); setF({ ...f, text: "" });
    } catch (e: any) { setErr(e.message); }
    setBusy(false);
  };
  const field = "grid gap-1 border-b-2 border-ink p-4 transition-colors duration-150 focus-within:bg-cream";
  return (
    <form onSubmit={submit} className="relative grid border-2 border-ink bg-white shadow-hard-lg">
      <div className="grid sm:grid-cols-2">
        <label className={`${field} sm:border-r-2`}><span className="label">01 — Name (optional)</span>
          <input className="bg-transparent text-lg outline-none" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} placeholder="—" /></label>
        <label className={field}><span className="label">02 — Phone (optional, stored masked)</span>
          <input className="bg-transparent text-lg outline-none" value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} placeholder="+91 …" /></label>
      </div>
      <label className={field}><span className="label">03 — What is happening? Any language.</span>
        <textarea className="min-h-[130px] resize-y bg-transparent text-xl outline-none" required minLength={3} value={f.text} onChange={(e) => setF({ ...f, text: e.target.value })}
          placeholder="ಮನೆ ಒಳಗೆ ನೀರು ಬಂದಿದೆ · House full water ide, help madi · 7 people stuck near the school" /></label>
      <div className="flex flex-wrap items-center gap-4 p-4">
        <button className="btn-primary px-6 py-3 text-sm" disabled={busy || f.text.trim().length < 3}>
          <motion.span animate={busy ? { x: [0, 6, 0] } : { x: 0 }} transition={busy ? { repeat: Infinity, duration: 0.6 } : {}}><Send size={16} aria-hidden /></motion.span>
          {busy ? "Sending…" : "Send to the control room"}
        </button>
        <span className="max-w-xs text-xs text-ink/60">Files a real report through every agent. No internet? Text the same words by SMS.</span>
      </div>
      <AnimatePresence>
        {res && (
          <motion.div key={res.ref} initial={{ opacity: 0, scale: 1.6, rotate: -14 }} animate={{ opacity: 1, scale: 1, rotate: -4 }} exit={{ opacity: 0 }}
            transition={{ type: "spring", stiffness: 400, damping: 18 }}
            className="absolute -right-3 -top-6 flex items-center gap-2 border-4 border-ink bg-go px-3 py-2 font-mono text-xs font-extrabold uppercase shadow-hard">
            <CheckCircle2 size={16} aria-hidden />Received · ref {res.ref}{res.lang ? ` · ${res.lang}` : ""}
          </motion.div>
        )}
      </AnimatePresence>
      {res && <p className="border-t-2 border-ink bg-sand p-3 font-mono text-xs font-bold uppercase tracking-wider">{res.place ? `Place understood: ${res.place}` : "No place given — RELAY will ask where you are"}</p>}
      {err && <p className="border-t-2 border-ink bg-stop p-3 text-sm font-bold">{err}</p>}
    </form>
  );
}

export default function About() {
  const { data: s } = useApi<Summary>("/api/summary", ["report", "incident"], 1000);
  const live: [string, number | undefined][] = [["reports", s?.reports], ["languages", s?.languages], ["incidents", s?.incidents],
    ["arrived with no internet", s?.offline_channel_reports], ["in fast verify", s?.fast_verify], ["people affected", s?.people_affected]];
  const LIVE_FILL = ["bg-white", "bg-cream", "bg-cream", "bg-white", "bg-white", "bg-cream"];
  return (
    <div className="-mx-4 -mt-4 sm:-mx-6 sm:-mt-6">
      <ScrollProgress />

      {/* HERO */}
      <section className="grid border-b-2 border-ink lg:grid-cols-[1.25fr_1fr]">
        <div className="flex flex-col justify-between border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2">
          <div className="grid grid-cols-2 gap-4 font-mono text-[10.5px] font-bold uppercase tracking-[0.16em] text-ink/60 sm:grid-cols-4">
            <span>Relay®<br />index 001</span><span>Studio for<br />disaster response</span><span>AgentX 2026<br />PS-03</span>
            <span className="flex items-start gap-2">Explain<Explain id="about.page" /></span>
          </div>
          <div className="py-10">
            <h1 className="mega text-[50px] sm:text-[86px] xl:text-[104px]">
              <RiseText text="Reports in." /><br />
              <span className="inline-block bg-signal px-2"><RiseText text="Relief" delay={0.15} /></span> <RiseText text="out." delay={0.25} />
            </h1>
            <motion.div initial={{ opacity: 0, x: -24 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.45, duration: 0.4 }}
              className="mt-8 max-w-xl border-2 border-ink bg-white p-4 text-lg font-medium leading-relaxed shadow-hard">
              Someone texts <span className="border-2 border-ink bg-cream px-1.5 font-bold">ನೀರು</span> and{" "}
              <WordCycle words={HELP} className="border-2 border-ink bg-sand px-1.5 font-bold" />. Seven agents read it, check it, rank it,
              negotiate the stock and the route — and then a person decides.
            </motion.div>
          </div>
          <motion.div className="flex flex-wrap gap-3" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6, duration: 0.35 }}>
            <button className="btn-primary px-5 py-3" onClick={() => startGuide()}>Watch it work<ArrowRight size={16} aria-hidden /></button>
            <Link to="/workflow" className="btn-ghost px-5 py-3">How it works</Link>
            <Link to="/" className="btn-ghost px-5 py-3">Command map</Link>
          </motion.div>
        </div>
        {/* live index: tilt cards with counting numbers */}
        <div className="grid grid-rows-[auto_1fr_auto] bg-sand">
          <div className="flex items-baseline justify-between border-b-2 border-ink px-5 py-3 font-mono text-[10.5px] font-bold uppercase tracking-[0.18em] text-ink/60">
            <span>fig. 1 — live index</span><span>{s?.scenario_name ?? "—"}</span>
          </div>
          <Stagger className="grid grid-cols-2 gap-3 p-4" gap={0.08}>
            {live.map(([l, v], i) => (
              <Item key={l}>
                <Tilt className={`h-full border-2 border-ink p-4 shadow-hard ${LIVE_FILL[i]}`}>
                  <p className="font-mono text-[10px] font-extrabold text-brand-600">0{i + 1}</p>
                  <p className="font-display text-[48px] leading-none tracking-[-0.04em] tabular-nums">{v == null ? "—" : <CountUp value={v} />}</p>
                  <p className="mt-1 font-mono text-[10px] font-bold uppercase tracking-[0.14em] text-ink/60">{l}</p>
                </Tilt>
              </Item>))}
          </Stagger>
          <div className="flex items-center gap-3 border-t-2 border-ink px-5 py-4">
            <span className="relative h-4 flex-1 overflow-hidden border-2 border-ink bg-white" aria-hidden>
              <motion.span className="absolute inset-y-0 left-0 w-1/3 bg-signal" animate={{ x: ["-100%", "300%"] }} transition={{ repeat: Infinity, duration: 3.2, ease: "linear" }} />
            </span>
            <span className="font-mono text-[10.5px] font-extrabold uppercase tracking-[0.18em] text-ink/70">silence is a signal</span>
          </div>
        </div>
      </section>

      {/* LANGUAGES */}
      <div className="border-b-2 border-ink bg-white py-3"><Marquee>{LANGS.map((w) => <span key={w} className="font-display text-3xl">{w} <span className="text-ink/30">✱</span></span>)}</Marquee></div>
      <div className="border-b-2 border-ink bg-cream py-2"><Marquee fast reverse>{["19 languages configured", "native script", "romanized", "code-mixed", "noisy voice", "support levels declared"].map((w) => <span key={w} className="font-mono text-[12px] font-extrabold uppercase tracking-[0.16em]">{w} ■</span>)}</Marquee></div>

      {/* MANIFESTO */}
      <section className="grid border-b-2 border-ink lg:grid-cols-[280px_1fr]">
        <div className="border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2"><p className="label">002 — Manifesto</p></div>
        <div className="p-5 sm:p-10">
          <Reveal>
            <p className="font-display text-[30px] uppercase leading-[1.02] tracking-tight sm:text-[52px]">
              We do not trust the loudest report. We trust evidence, we listen for the silence, and we never let a machine{" "}
              <span className="bg-signal px-2">press send</span>.</p>
          </Reveal>
          <Stagger className="mt-10 grid gap-4 sm:grid-cols-3">
            {[["AI interprets", "reads, translates, fills a strict schema"], ["Rules enforce", "priorities, routes, quantities, permissions"], ["People decide", "approve, verify, confirm, send"]].map(([a, b], i) => (
              <Item key={a}>
                <motion.div whileHover={{ x: -5, y: -5 }} className={`h-full border-2 border-ink p-5 shadow-hard ${["bg-blue", "bg-sand", "bg-go"][i]}`}>
                  <p className="font-mono text-[11px] font-extrabold">0{i + 1}</p><p className="mt-2 font-display text-2xl uppercase">{a}</p><p className="mt-1 font-mono text-[12px] font-bold uppercase">{b}</p>
                </motion.div>
              </Item>))}
          </Stagger>
        </div>
      </section>

      {/* CASE STUDIES */}
      <section className="border-b-2 border-ink">
        <SectionHead n="003" label="Selected work" title="Case studies." note="Every case opens the live page where it happens." />
        <Stagger className="grid gap-6 p-5 sm:grid-cols-2 sm:p-10 xl:grid-cols-3">
          {CASES.map((c) => <CaseCard key={c.n} c={c} />)}
          <Item>
            <Link to="/lab" className="group flex h-full min-h-[300px] flex-col justify-between border-2 border-dashed border-ink bg-cream p-6 transition-colors hover:bg-sand">
              <p className="label">+ 50 more</p>
              <p className="mega text-[40px]">Run any scenario in the lab.</p>
              <span className="grid h-12 w-12 place-items-center border-2 border-ink bg-white transition-transform duration-200 group-hover:translate-x-2"><ArrowRight size={22} aria-hidden /></span>
            </Link>
          </Item>
        </Stagger>
      </section>

      {/* CAPABILITIES */}
      <section className="border-b-2 border-ink">
        <div className="flex items-baseline justify-between border-b-2 border-ink px-5 py-3 sm:px-10"><p className="label">004 — Capabilities</p><Link to="/workflow" className="link-grow font-mono text-[11px] font-extrabold uppercase">full workflow →</Link></div>
        <Stagger className="grid sm:grid-cols-2 xl:grid-cols-3">
          {CAPS.map(([t, d], i) => (
            <Item key={t} className={`group relative overflow-hidden border-b-2 border-r-2 border-ink p-6 ${i % 2 ? "bg-cream" : "bg-white"}`}>
              <span className="absolute inset-0 origin-bottom scale-y-0 bg-sand transition-transform duration-300 group-hover:scale-y-100" aria-hidden />
              <div className="relative">
                <p className="inline-block border-2 border-ink bg-signal px-1.5 font-mono text-[11px] font-extrabold transition-transform duration-300 group-hover:rotate-[-6deg]">{String(i + 1).padStart(2, "0")}</p>
                <p className="mt-3 font-display text-[24px] uppercase leading-tight">{t}</p>
                <p className="mt-2 max-w-sm text-sm font-medium">{d}</p>
              </div>
            </Item>))}
        </Stagger>
      </section>

      {/* TEAM */}
      <section className="border-b-2 border-ink">
        <SectionHead n="005" label="The team" title={<>Seven agents.<br /><span className="bg-signal px-2">One person</span> decides.</>}
          note={<>Seven agents who talk to each other, and one person who decides. Hover a card to hear them. <Link to="/agents" className="link-grow font-bold">See them talk →</Link></>} />
        <Stagger className="grid gap-5 p-5 sm:grid-cols-2 sm:p-10 xl:grid-cols-4">
          {TEAM.map((m, i) => <TeamCard key={m.name} m={m} i={i} />)}
        </Stagger>
      </section>

      <Process />

      {/* RESEARCH */}
      <section className="grid border-b-2 border-ink lg:grid-cols-[280px_1fr]">
        <div className="border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2"><p className="label">007 — Why this, why now</p></div>
        <Stagger className="grid sm:grid-cols-2 xl:grid-cols-4">
          {RESEARCH.map(([num, pre, post, what, cite]) => (
            <Item key={cite + num} className="border-b-2 border-r-2 border-ink p-6">
              <p className="mega text-[58px]">{pre}<CountUp value={num} />{post}</p><p className="mt-2 text-sm">{what}</p><p className="mt-3 font-mono text-[11px] font-bold uppercase tracking-wider text-ink/50">{cite}</p>
            </Item>))}
        </Stagger>
      </section>

      {/* BUILDERS */}
      <section className="border-b-2 border-ink bg-mint-200/60">
        <SectionHead n="008" label="The builders" title={<>Built by <span className="bg-mint-300 px-2">four people</span>.</>}
          note="Team Tech Architects · AgentX Hackathon 2026. Click a card to open their GitHub." />
        <Stagger className="grid gap-5 p-5 sm:grid-cols-2 sm:p-10 xl:grid-cols-4">
          {BUILDERS.map((b, i) => <BuilderCard key={b.gh} b={b} i={i} />)}
        </Stagger>
      </section>

      {/* CONTACT */}
      <section className="grid border-b-2 border-ink lg:grid-cols-[1fr_1.2fr]">
        <div className="border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2">
          <p className="label">009 — Contact the control room</p>
          <Reveal><h2 className="mega mt-4 text-[40px] sm:text-[56px] xl:text-[62px]">Say it in <span className="bg-blue px-2">your</span> language.</h2></Reveal>
          <p className="mt-6 max-w-md border-l-4 border-ink pl-4 text-[15px]">This form files a real report: language detection, extraction, geocoding, the duplicate check and an evidence score. Leave out where you are and RELAY will ask.</p>
        </div>
        <Reveal className="p-5 sm:p-10"><ContactForm /></Reveal>
      </section>

      {/* FOOTER */}
      <footer className="bg-sand pb-6 pt-8">
        <Marquee className="border-y-2 border-ink bg-white py-2">{["Reports in", "Relief out", "People decide"].map((w) => <span key={w} className="font-display text-[64px] uppercase leading-none">{w} <span className="text-ink/25">✱</span></span>)}</Marquee>
        <p className="px-5 pt-8 font-display text-[14vw] uppercase leading-[0.8] tracking-[-0.05em] sm:px-10">Relay<span className="text-brand-600">.</span></p>
        <div className="mx-5 mt-6 flex flex-wrap items-center justify-between gap-3 border-t-2 border-ink pt-4 font-mono text-[10.5px] font-bold uppercase tracking-[0.14em] text-ink/60 sm:mx-10">
          <span>Team Tech Architects · AgentX Hackathon 2026</span>
          <span>Synthetic data · real places · real-world validation pending</span>
        </div>
      </footer>
    </div>
  );
}
