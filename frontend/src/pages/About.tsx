// The RELAY landing page, built as a creative-agency portfolio — brutalist (raw grid, index numbers, hard rules),
// minimal (bone, ink, one signal colour, lots of air) and surreal (a dusk sky with a moon, a ladder out of the frame,
// a door that opens onto night, an eye that watches you). Motion: letter-by-letter headline, parallax, magnetic CTAs,
// clip reveals, marquees. Sections: hero · manifesto · live index · case studies · capabilities · team · process ·
// research · contact (files a real report) · footer.
import { useState } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, ArrowUpRight, CheckCircle2, Send } from "lucide-react";
import { Cloud, CountUp, Door, Drip, Eye, Item, Ladder, Magnetic, Marquee, Moon, Parallax, Reveal, Rotator, SplitText, Stagger, Tilt } from "../components/motion";
import { useApi } from "../hooks/useApi";
import { Explain } from "../components/Assistant";
import { startGuide } from "../components/Guide";
import { api } from "../services/api";

const WATER = ["ನೀರು", "पानी", "വെള്ളം", "தண்ணீர்", "నీరు", "पाणी", "জল", "পানী", "ପାଣି", "water"];
const HELP = ["ಸಹಾಯ ಮಾಡಿ", "मदद करो", "സഹായിക്കൂ", "உதவி", "help madi", "madad karo", "help"];

const CASES = [
  { n: "01", title: "The SMS and the tweet", to: "/incidents", obj: "orb",
    claim: "Two reports, two languages, one flooded village.",
    body: "A Kannada SMS and an English post land minutes apart. Same place, same meaning, same hour, compatible needs: one incident — not two boats.",
    stat: "6 reports → 1 incident" },
  { n: "02", title: "The dam that did not burst", to: "/alerts", obj: "door",
    claim: "“Share to all.” In three languages.",
    body: "A forward chain, a catastrophe with no detail, and an official bulletin that says the opposite. It scores false; the correction goes out in every language.",
    stat: "0% credible · 8-language correction" },
  { n: "03", title: "The village that went silent", to: "/blackout", obj: "eye",
    claim: "Zero reports was the alarm.",
    body: "Inside the hazard, towers down, relatives elsewhere who cannot reach anyone. RELAY ranks the silence and asks Resource what a recon team should carry.",
    stat: "2,400 people · 0 reports · 1 recon" },
  { n: "04", title: "Two agents, one boat short", to: "/agents", obj: "moon",
    claim: "“I'm short of 2 boats.” — “Kushalnagar can send 2.”",
    body: "Coordination asks Resource for a second source; the offer becomes a plan line. When nobody has stock, Resource escalates to a person.",
    stat: "propose → accept → plan line" },
  { n: "05", title: "ಹೌದು is not confirmed", to: "/dispatch", obj: "ladder",
    claim: "Arriving is not delivering. Delivering is not confirming.",
    body: "The recipient replies YES in Kannada. That is evidence. A Duty Officer confirms — the backend refuses anyone else.",
    stat: "created → … → confirmed" },
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
  { name: "Intake", role: "reads every report", q: "What is this report saying?", obj: "orb" },
  { name: "Trust", role: "duplicates, credibility", q: "Is it true, and have we seen it before?", obj: "eye" },
  { name: "Triage", role: "who first", q: "Who needs help first?", obj: "moon" },
  { name: "Resource", role: "stock, shortages", q: "Do we have enough, and where?", obj: "ladder" },
  { name: "Blackout", role: "silent places", q: "Which places have gone quiet?", obj: "door" },
  { name: "Monitor", role: "what changed", q: "Has something changed?", obj: "eye" },
  { name: "Coordination", role: "plans, routes, people", q: "Who goes where, with what — and did it arrive?", obj: "moon" },
  { name: "Duty Officer", role: "a person decides", q: "Approve. Verify. Confirm.", obj: "door", human: true },
];

const PROCESS = [
  ["Set up", "choose a disaster and a place"], ["Understand", "intake · trust · triage · resource · blackout"],
  ["Decide", "monitor · coordination · ◆ approval"], ["Act", "◆ route check · dispatch · ◆ confirm"], ["Tell & learn", "◆ public messages · audit · metrics"],
];

const RESEARCH = [
  ["~6%", "of disaster social-media studies handled regional (non-English) languages", "Gopal et al. 2026, NHESS"],
  ["~7%", "addressed resource identification", "Gopal et al. 2026"],
  ["1–3%", "of tweets are geotagged", "Imran et al. 2020"],
  [">75%", "of US emergency agencies won't act on social media without a trusted second source", "Mehta et al. 2017"],
];

type Summary = { reports: number; languages: number; incidents: number; offline_channel_reports: number; fast_verify: number; people_affected: number; scenario_name?: string };

/** A small surreal portrait: one object in a dusk-sky frame. */
function Portrait({ obj, night = false }: { obj: string; night?: boolean }) {
  return (
    <div className={`relative h-40 overflow-hidden border-b-2 border-ink ${night ? "sky-night" : "sky"}`}>
      {obj === "orb" && <div className="absolute left-1/2 top-1/2 h-20 w-20 -translate-x-1/2 -translate-y-1/2 animate-levitate rounded-full orb" />}
      {obj === "moon" && <Moon className="left-1/2 top-6 -ml-12" size={96} />}
      {obj === "eye" && <Eye className="left-1/2 top-1/2 -ml-[60px] -mt-[34px]" size={120} />}
      {obj === "door" && <Door className="left-1/2 top-5 -ml-8 h-28 w-16" />}
      {obj === "ladder" && <Ladder className="left-1/2 top-[-10px] -ml-6 h-[170px] w-12" />}
      <div className="absolute inset-x-0 bottom-0 h-6 bg-gradient-to-t from-ink/15 to-transparent" />
    </div>
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
  return (
    <form onSubmit={submit} className="relative grid gap-0 border-2 border-ink bg-bone">
      <div className="grid sm:grid-cols-2">
        <label className="grid gap-1 border-b-2 border-ink p-4 sm:border-r-2"><span className="label">01 — Name (optional)</span>
          <input className="bg-transparent text-lg outline-none" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} placeholder="—" /></label>
        <label className="grid gap-1 border-b-2 border-ink p-4"><span className="label">02 — Phone (optional, stored masked)</span>
          <input className="bg-transparent text-lg outline-none" value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} placeholder="+91 …" /></label>
      </div>
      <label className="grid gap-1 border-b-2 border-ink p-4"><span className="label">03 — What is happening? Any language.</span>
        <textarea className="min-h-[130px] resize-y bg-transparent text-xl outline-none" required minLength={3} value={f.text} onChange={(e) => setF({ ...f, text: e.target.value })}
          placeholder="ಮನೆ ಒಳಗೆ ನೀರು ಬಂದಿದೆ · House full water ide, help madi · 7 people stuck near the school" /></label>
      <div className="flex flex-wrap items-center gap-4 p-4">
        <Magnetic><button className="btn-pop px-6 py-3 text-sm" disabled={busy || f.text.trim().length < 3}><Send size={16} aria-hidden />{busy ? "Sending…" : "Send to the control room"}</button></Magnetic>
        <span className="max-w-xs text-xs text-ink/60">Files a real report through every agent. No internet? Text the same words by SMS.</span>
      </div>
      <AnimatePresence>
        {res && (
          <motion.p initial={{ clipPath: "inset(0 100% 0 0)" }} animate={{ clipPath: "inset(0 0% 0 0)" }} className="flex items-center gap-2 border-t-2 border-ink bg-ink p-3 font-mono text-xs uppercase tracking-wider text-bone">
            <CheckCircle2 size={14} className="text-signal" aria-hidden />Received · ref {res.ref}{res.lang ? ` · ${res.lang}` : ""}{res.place ? ` · ${res.place}` : " · we'll ask where you are"}
          </motion.p>
        )}
      </AnimatePresence>
      {err && <p className="border-t-2 border-ink p-3 text-sm font-bold text-signal">{err}</p>}
    </form>
  );
}

function CaseRow({ c }: { c: typeof CASES[number] }) {
  const [hover, setHover] = useState(false);
  return (
    <Link to={c.to} onPointerEnter={() => setHover(true)} onPointerLeave={() => setHover(false)}
      className="group relative grid grid-cols-[56px_1fr_auto] items-start gap-4 border-b-2 border-ink px-2 py-6 transition-colors hover:bg-ink hover:text-bone sm:grid-cols-[80px_1.2fr_1fr_auto] sm:px-4">
      <span className="font-mono text-sm text-ink/40 group-hover:text-signal">{c.n}</span>
      <div>
        <h3 className="mega text-[30px] sm:text-[44px]">{c.title}</h3>
        <p className="serif-i mt-1 text-xl opacity-80">{c.claim}</p>
      </div>
      <div className="hidden sm:block">
        <p className="text-sm opacity-75">{c.body}</p>
        <p className="mt-3 inline-block border border-current px-2 py-0.5 font-mono text-[10.5px] uppercase tracking-wider">{c.stat}</p>
      </div>
      <span className="grid h-12 w-12 place-items-center border-2 border-current transition-transform duration-300 group-hover:rotate-45"><ArrowUpRight size={22} aria-hidden /></span>
      <AnimatePresence>
        {hover && (
          <motion.div initial={{ opacity: 0, scale: 0.8, rotate: -4 }} animate={{ opacity: 1, scale: 1, rotate: 2 }} exit={{ opacity: 0, scale: 0.8 }}
            className="pointer-events-none absolute right-24 top-1/2 z-10 hidden w-56 -translate-y-1/2 border-2 border-ink bg-bone shadow-hard-pink xl:block">
            <Portrait obj={c.obj} night={c.obj === "door"} />
            <p className="p-2 font-mono text-[10px] uppercase tracking-wider text-ink">Case {c.n} — preview</p>
          </motion.div>
        )}
      </AnimatePresence>
    </Link>
  );
}

export default function About() {
  const { data: s } = useApi<Summary>("/api/summary", ["report", "incident"], 1000);
  return (
    <div className="-mx-4 -mt-4 sm:-mx-6 sm:-mt-6">
      {/* HERO */}
      <section className="relative grid min-h-[86vh] border-b-2 border-ink lg:grid-cols-[1.15fr_1fr]">
        <div className="relative flex flex-col justify-between border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2">
          <div className="grid grid-cols-2 gap-4 font-mono text-[10.5px] uppercase tracking-[0.16em] text-ink/60 sm:grid-cols-4">
            <span>Relay®<br />index 001</span><span>Studio for<br />disaster response</span><span>AgentX 2026<br />PS-03</span>
            <span className="flex items-start gap-2">Explain<Explain id="about.page" /></span>
          </div>
          <div className="py-10">
            <h1 className="mega text-[52px] sm:text-[92px] xl:text-[112px] 2xl:text-[132px]">
              <SplitText text="Reports in." /><br />
              <span className="serif-i font-normal tracking-normal"><SplitText text="Relief" delay={0.35} /></span> <SplitText text="out" delay={0.55} /><span className="text-signal">.</span>
            </h1>
            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.9 }} className="mt-8 max-w-xl border-l-2 border-ink pl-4 text-lg leading-relaxed">
              Someone texts <Rotator words={WATER} className="mx-1 border-2 border-ink bg-bone px-1.5 font-bold" /> and{" "}
              <Rotator words={HELP} className="mx-1 border-2 border-ink bg-ink px-1.5 font-bold text-bone" every={2100} />. Seven agents read it, check it,
              rank it, negotiate the stock and the route — and then a person decides.
            </motion.p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Magnetic><button className="btn-pop px-5 py-3" onClick={() => startGuide()}>Watch it work<ArrowRight size={16} aria-hidden /></button></Magnetic>
            <Magnetic><Link to="/workflow" className="btn-ghost px-5 py-3">How it works</Link></Magnetic>
            <Magnetic><Link to="/" className="btn-ghost px-5 py-3">Command map</Link></Magnetic>
          </div>
        </div>
        {/* the surreal scene */}
        <div className="relative min-h-[420px] overflow-hidden sky">
          <Parallax speed={0.6} className="absolute inset-0"><Moon className="right-[14%] top-[12%]" size={190} /></Parallax>
          <Cloud className="top-[18%]" /><Cloud className="top-[46%]" delay={-25} /><Cloud className="top-[70%]" delay={-45} />
          <Ladder className="bottom-[-20px] left-[18%] h-[78%] w-14" rungs={12} />
          <Door className="bottom-[16%] right-[18%] h-44 w-24" />
          <Eye className="left-[34%] top-[22%]" size={140} />
          <Drip className="left-0 top-0 h-16 w-28" />
          <div className="absolute inset-x-0 bottom-0 h-[16%] border-t-2 border-ink bg-paper" />
          <div className="absolute bottom-[16%] left-0 right-0 h-[2px] bg-ink" />
          <p className="absolute bottom-4 left-4 font-mono text-[10px] uppercase tracking-[0.2em]">fig. 1 — silence is a signal</p>
          <motion.div aria-hidden className="absolute bottom-[20%] left-[52%] h-28 w-28" animate={{ rotate: 360 }} transition={{ duration: 40, repeat: Infinity, ease: "linear" }}>
            <svg viewBox="0 0 100 100" className="h-full w-full"><defs><path id="c" d="M50,50 m-38,0 a38,38 0 1,1 76,0 a38,38 0 1,1 -76,0" /></defs>
              <text fontSize="8.2" fontWeight="700" fill="#0B0B0C" letterSpacing="1.2" fontFamily="JetBrains Mono"><textPath href="#c">PEOPLE DECIDE ■ AGENTS NEGOTIATE ■ </textPath></text></svg>
          </motion.div>
        </div>
      </section>

      {/* MARQUEE */}
      <div className="border-b-2 border-ink bg-ink py-3 font-display text-3xl font-extrabold uppercase text-bone">
        <Marquee fast>{["ಕನ್ನಡ", "हिंदी", "മലയാളം", "தமிழ்", "తెలుగు", "मराठी", "বাংলা", "অসমীয়া", "ଓଡ଼ିଆ", "ગુજરાતી", "ਪੰਜਾਬੀ", "नेपाली", "Mizo", "Khasi", "English", "SMS", "Voice", "Sat-phone"].map((w) =>
          <span key={w} className="flex items-center gap-10">{w}<span className="text-signal">■</span></span>)}</Marquee>
      </div>

      {/* MANIFESTO */}
      <section className="grid border-b-2 border-ink lg:grid-cols-[280px_1fr]">
        <div className="border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2"><p className="label">002 — Manifesto</p></div>
        <div className="p-5 sm:p-10">
          <Reveal><p className="font-display text-[30px] font-extrabold leading-[1.05] tracking-tight sm:text-[52px]">
            We do not trust the loudest report. We trust <span className="serif-i font-normal">evidence</span>, we listen for the <span className="serif-i font-normal">silence</span>,
            and we never let a machine <span className="bg-ink px-2 text-bone">press send</span><span className="text-signal">.</span></p></Reveal>
          <Stagger className="mt-10 grid border-2 border-ink sm:grid-cols-3">
            {[["AI interprets", "reads, translates, fills a strict schema"], ["Rules enforce", "priorities, routes, quantities, permissions"], ["People decide", "approve, verify, confirm, send"]].map(([a, b], i) => (
              <Item key={a} className={`p-5 ${i < 2 ? "border-b-2 border-ink sm:border-b-0 sm:border-r-2" : ""}`}>
                <p className="font-mono text-[10px] text-signal">0{i + 1}</p><p className="mt-2 font-display text-2xl font-extrabold">{a}</p><p className="mt-1 text-sm text-ink/60">{b}</p>
              </Item>))}
          </Stagger>
        </div>
      </section>

      {/* LIVE INDEX */}
      <section className="border-b-2 border-ink">
        <div className="flex items-baseline justify-between border-b-2 border-ink px-5 py-3 sm:px-10"><p className="label">003 — Live index</p><p className="font-mono text-[10.5px] uppercase text-ink/50">{s?.scenario_name ?? "—"} · synthetic</p></div>
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6">
          {[["reports", s?.reports], ["languages", s?.languages], ["incidents", s?.incidents], ["arrived with no internet", s?.offline_channel_reports],
            ["in fast verify", s?.fast_verify], ["people affected", s?.people_affected]].map(([l, v], i) => (
            <div key={l as string} className={`group border-b-2 border-r-2 border-ink p-5 transition-colors hover:bg-ink hover:text-bone ${i === 5 ? "border-r-0" : ""}`}>
              <p className="font-mono text-[10px] text-ink/40 group-hover:text-signal">0{i + 1}</p>
              <p className="mega mt-2 text-[56px] tabular-nums">{v == null ? "—" : <CountUp value={v as number} />}</p>
              <p className="font-mono text-[10.5px] uppercase tracking-[0.14em] opacity-60">{l as string}</p>
            </div>))}
        </div>
      </section>

      {/* CASE STUDIES */}
      <section className="border-b-2 border-ink">
        <div className="grid border-b-2 border-ink lg:grid-cols-[280px_1fr]">
          <div className="border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2"><p className="label">004 — Selected work</p><p className="mt-2 text-sm text-ink/60">Hover a case for a preview. Every case opens the live page where it happens.</p></div>
          <div className="p-5 sm:p-10"><Reveal><h2 className="mega text-[48px] sm:text-[88px]">Case studies<span className="text-signal">.</span></h2></Reveal></div>
        </div>
        <div>{CASES.map((c) => <CaseRow key={c.n} c={c} />)}</div>
      </section>

      {/* CAPABILITIES */}
      <section className="border-b-2 border-ink">
        <div className="flex items-baseline justify-between border-b-2 border-ink px-5 py-3 sm:px-10"><p className="label">005 — Capabilities</p><Link to="/workflow" className="link-grow font-mono text-[11px] uppercase">full workflow →</Link></div>
        <Stagger className="grid sm:grid-cols-2 xl:grid-cols-3">
          {CAPS.map(([t, d], i) => (
            <Item key={t} className="group relative overflow-hidden border-b-2 border-r-2 border-ink p-6">
              <span className="absolute -right-6 -top-6 h-20 w-20 rounded-full orb opacity-0 transition-all duration-500 group-hover:translate-y-4 group-hover:opacity-100" aria-hidden />
              <p className="font-mono text-[10px] text-ink/40">{String(i + 1).padStart(2, "0")}</p>
              <p className="mt-3 font-display text-[26px] font-extrabold leading-tight">{t}</p>
              <p className="mt-2 max-w-sm text-sm text-ink/65">{d}</p>
            </Item>))}
        </Stagger>
      </section>

      {/* TEAM */}
      <section className="border-b-2 border-ink">
        <div className="grid border-b-2 border-ink lg:grid-cols-[280px_1fr]">
          <div className="border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2"><p className="label">006 — The team</p><p className="mt-2 text-sm text-ink/60">Seven agents who talk to each other, and one person who decides. <Link to="/agents" className="link-grow font-bold">Watch them talk →</Link></p></div>
          <div className="p-5 sm:p-10"><Reveal><h2 className="mega text-[48px] sm:text-[88px]">Seven agents.<br /><span className="serif-i font-normal">One</span> person decides<span className="text-signal">.</span></h2></Reveal></div>
        </div>
        <Stagger className="grid sm:grid-cols-2 xl:grid-cols-4">
          {TEAM.map((m, i) => (
            <Item key={m.name} className="border-b-2 border-r-2 border-ink">
              <Tilt className="h-full">
                <div className={`group h-full ${m.human ? "bg-ink text-bone" : "bg-bone"}`}>
                  <Portrait obj={m.obj} night={!!m.human} />
                  <div className="p-4">
                    <p className="font-mono text-[10px] uppercase tracking-[0.16em] opacity-50">{String(i + 1).padStart(2, "0")} — {m.human ? "human" : "agent"} · {m.role}</p>
                    <p className="mt-1 font-display text-2xl font-extrabold">{m.name}</p>
                    <p className="serif-i mt-1 text-lg leading-tight opacity-80">“{m.q}”</p>
                  </div>
                </div>
              </Tilt>
            </Item>))}
        </Stagger>
      </section>

      {/* PROCESS */}
      <section className="border-b-2 border-ink bg-ink text-bone">
        <div className="flex items-baseline justify-between border-b-2 border-bone/20 px-5 py-3 sm:px-10"><p className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-bone/60">007 — Process</p><Link to="/workflow" className="font-mono text-[11px] uppercase text-signal">open the flowchart →</Link></div>
        <div className="grid md:grid-cols-5">
          {PROCESS.map(([a, b], i) => (
            <Reveal key={a} delay={i * 0.06} className="border-b-2 border-bone/20 p-6 md:border-b-0 md:border-r-2">
              <p className="font-display text-[64px] font-extrabold leading-none text-bone/15">{i + 1}</p>
              <p className="mt-2 font-display text-2xl font-extrabold">{a}</p>
              <p className="mt-1 font-mono text-[11px] uppercase tracking-wider text-bone/60">{b}</p>
            </Reveal>))}
        </div>
        <p className="border-t-2 border-bone/20 px-5 py-4 font-mono text-[11px] uppercase tracking-wider text-bone/60 sm:px-10">◆ = a person decides · whenever something changes, Monitor sends it back to Coordination to re-plan</p>
      </section>

      {/* RESEARCH */}
      <section className="grid border-b-2 border-ink lg:grid-cols-[280px_1fr]">
        <div className="border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2"><p className="label">008 — Why this, why now</p></div>
        <div className="grid sm:grid-cols-2 xl:grid-cols-4">
          {RESEARCH.map(([big, what, cite], i) => (
            <Reveal key={cite + big} delay={i * 0.05} className="border-b-2 border-r-2 border-ink p-6">
              <p className="mega text-[58px]">{big}</p><p className="mt-2 text-sm">{what}</p><p className="serif-i mt-3 text-base text-ink/55">{cite}</p>
            </Reveal>))}
        </div>
      </section>

      {/* CONTACT */}
      <section className="relative grid overflow-hidden border-b-2 border-ink lg:grid-cols-[1fr_1.2fr]">
        <div className="relative overflow-hidden border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2">
          <div className="absolute inset-0 sky opacity-70" aria-hidden />
          <Moon className="-bottom-16 -right-10" size={240} />
          <div className="relative">
            <p className="label">009 — Contact the control room</p>
            <h2 className="mega mt-4 text-[44px] sm:text-[60px] xl:text-[68px]">Say it in <span className="serif-i font-normal">your</span> language<span className="text-signal">.</span></h2>
            <p className="mt-6 max-w-md border-l-2 border-ink pl-4 text-[15px]">This form files a real report: language detection, extraction, geocoding, the duplicate check and an evidence score. Leave out where you are and RELAY will ask.</p>
          </div>
        </div>
        <div className="p-5 sm:p-10"><Reveal><ContactForm /></Reveal></div>
      </section>

      {/* FOOTER */}
      <footer className="relative overflow-hidden bg-ink px-5 pb-6 pt-14 text-bone sm:px-10">
        <Drip className="left-[10%] top-0 h-14 w-24" color="#EFECE6" />
        <Drip className="right-[22%] top-0 h-10 w-20" color="#EFECE6" />
        <p className="mega select-none text-[15vw] leading-[0.8] lowercase">relay<span className="text-signal">.</span></p>
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t-2 border-bone/20 pt-4 font-mono text-[10.5px] uppercase tracking-[0.14em] text-bone/60">
          <span>Team Tech Architects · AgentX Hackathon 2026</span>
          <span>Synthetic data · real places · real-world validation pending</span>
        </div>
      </footer>
    </div>
  );
}
