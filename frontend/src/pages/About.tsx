// The RELAY landing page, built like a bold creative-agency portfolio: hero, live numbers, "case studies" (the demo
// stories), the "team" (agents, modules and the people who decide), research grounding and a contact form that files
// a real report into the pipeline.
import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight, ArrowUpRight, Bot, BrainCircuit, CheckCircle2, ClipboardCheck, EyeOff, FlaskConical, Inbox, Megaphone, Package,
  RefreshCw, Scale, Send, ShieldCheck, Siren, Truck, UserRound, Users,
} from "lucide-react";
import { Blob, CountUp, Item, Marquee, Reveal, Rotator, Stagger, Tilt } from "../components/motion";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";

const WATER = ["ನೀರು", "पानी", "വെള്ളം", "தண்ணீர்", "నీరు", "पाणी", "জল", "water"];
const HELP = ["ಸಹಾಯ ಮಾಡಿ", "मदद करो", "സഹായിക്കൂ", "உதவி", "help maadi", "madad karo", "help"];

const CASES = [
  { n: "01", title: "The Kannada SMS and the English tweet", tone: "bg-lime-400", to: "/incidents",
    claim: "Two reports, two languages, one flooded village.", body: "A feature-phone SMS in Kannada and a tweet in English about Karadigodu land minutes apart. RELAY compares meaning, distance and time, and merges them into one incident instead of sending two boats.",
    stat: "1 incident · 6 reports · 3 languages" },
  { n: "02", title: "The dam that did not burst", tone: "bg-pink-400", to: "/alerts",
    claim: "\"Harangi dam has burst, share to all\" — in Kannada, Hindi and English.", body: "Forward-chain phrases, a catastrophic claim with no detail, and an official dam bulletin saying the structure is safe. The rumour scores false and a correction goes out in every language.",
    stat: "confidence 0% · correction in 8 languages" },
  { n: "03", title: "The village that went silent", tone: "bg-ink text-white", to: "/blackout",
    claim: "Hattihole sent zero reports. That was the alarm.", body: "Inside the flood polygon, towers down, power off, and two relatives in other towns who cannot reach their families. RELAY ranks it top of the silent zones and proposes a recon team carrying supplies.",
    stat: "2,400 people · 0 reports · 1 recon task" },
  { n: "04", title: "Water runs out at six in the morning", tone: "bg-cobalt-300", to: "/resources",
    claim: "240 people, 2,700 litres, 15 litres a person a day.", body: "The Resource agent burns the stock forward at Sphere standards and flags the Napoklu camp hours before the tanks run dry, then finds surplus at the district depot.",
    stat: "runs out in ~18 h · transfer proposed" },
  { n: "05", title: "ಹೌದು means delivered", tone: "bg-sun-400", to: "/dispatch",
    claim: "Arriving is not delivering.", body: "When the truck reaches the camp, the recipient gets an SMS in their own language: did you receive it? A one-word Kannada reply closes the loop and moves the stock from in-transit to consumed.",
    stat: "closed loop · recipient-confirmed" },
];

const TEAM = [
  { name: "Intake", q: "What is this report saying?", icon: Inbox, tone: "bg-lime-400", kind: "agent" },
  { name: "Trust & Evidence", q: "Is it true, and have we seen it before?", icon: ShieldCheck, tone: "bg-pink-400", kind: "agent" },
  { name: "Triage", q: "Who needs help first?", icon: Siren, tone: "bg-tangerine-400", kind: "agent" },
  { name: "Resource", q: "Do we have enough, and where?", icon: Package, tone: "bg-sun-400", kind: "agent" },
  { name: "Coordination", q: "Who goes where, with what, and did it arrive?", icon: Truck, tone: "bg-cobalt-300", kind: "agent" },
  { name: "Monitoring & Replanning", q: "Has something changed?", icon: RefreshCw, tone: "bg-mint-300", kind: "module" },
  { name: "Blackout Detection", q: "Which areas have gone silent?", icon: EyeOff, tone: "bg-brand-300", kind: "module" },
  { name: "Rumour Control", q: "What do people need to know is false?", icon: Megaphone, tone: "bg-pink-300", kind: "module" },
  { name: "Digital Twin", q: "What if…?", icon: FlaskConical, tone: "bg-lime-300", kind: "module" },
];
const PEOPLE = [
  { name: "Duty officer", job: "approves every plan, confirms or refutes, publishes corrections", icon: ClipboardCheck },
  { name: "Field teams", job: "check Fast Verify cases, report by app, radio or satellite phone", icon: Users },
  { name: "Citizens", job: "report by SMS, voice, web — in their own language — and confirm deliveries", icon: UserRound },
];

const RESEARCH = [
  ["~6%", "of disaster social-media studies handled regional (non-English) languages", "Gopal et al. 2026, NHESS (250 studies)"],
  ["~7%", "addressed resource identification", "Gopal et al. 2026"],
  ["1–3%", "of tweets are geotagged", "Imran et al. 2020"],
  [">75%", "of US emergency agencies will not act on social media unless another trusted source verifies it", "Mehta et al. 2017"],
  ["!", "responders distrust and ignore systems that are hard to use or not explainable", "Bharosa et al. 2010"],
];

type Summary = { reports: number; languages: number; incidents: number; offline_channel_reports: number; fast_verify: number; people_affected: number };

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
    <form onSubmit={submit} className="relative grid gap-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="grid gap-1"><span className="label">Your name (optional)</span><input className="input" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></label>
        <label className="grid gap-1"><span className="label">Phone (optional, stored masked)</span><input className="input" value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} placeholder="+91…" /></label>
      </div>
      <label className="grid gap-1"><span className="label">What is happening? Any language.</span>
        <textarea className="input min-h-[110px] text-base" required minLength={3} value={f.text} onChange={(e) => setF({ ...f, text: e.target.value })} placeholder="e.g. ಸಿದ್ದಾಪುರ ಶಾಲೆ ಹತ್ತಿರ 7 ಜನ ಸಿಲುಕಿದ್ದಾರೆ / 7 people stuck near Siddapura school" /></label>
      <div className="flex flex-wrap items-center gap-3">
        <button className="btn-pop px-5 py-2.5 text-base" disabled={busy || f.text.trim().length < 3}><Send size={17} aria-hidden />{busy ? "Sending…" : "Send to the control room"}</button>
        <span className="text-xs font-medium text-ink/60">Goes through the real pipeline. No internet? Text the same words by SMS.</span>
      </div>
      {res && (
        <motion.p initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="sticker w-fit rotate-1 bg-mint-400">
          <CheckCircle2 size={14} aria-hidden />Received · Ref {res.ref}{res.lang ? ` · ${res.lang}` : ""}{res.place ? ` · ${res.place}` : " · we'll ask where you are"}
        </motion.p>
      )}
      {err && <p className="text-sm font-bold text-pink-500">{err}</p>}
    </form>
  );
}

export default function About() {
  const { data: s } = useApi<Summary>("/api/summary", ["report", "incident"], 1000);
  return (
    <div className="-mx-4 -mt-4 space-y-0 sm:-mx-6 sm:-mt-6">
      {/* HERO */}
      <section className="grain relative overflow-hidden border-b-2 border-ink bg-brand-500 px-5 pb-14 pt-12 text-white sm:px-10 sm:pt-16">
        <Blob className="-left-24 top-10 h-72 w-72" color="bg-pink-400" />
        <Blob className="right-[-60px] top-[-40px] h-80 w-80" color="bg-lime-400" />
        <Blob className="bottom-[-90px] left-1/3 h-64 w-64" color="bg-sun-400" />
        <div className="pat-dots absolute inset-0 opacity-[0.08]" aria-hidden />
        <div className="relative max-w-6xl">
          <motion.span initial={{ rotate: -12, scale: 0 }} animate={{ rotate: -4, scale: 1 }} transition={{ type: "spring", stiffness: 300, damping: 14 }}
            className="sticker bg-lime-400 text-ink">AgentX Hackathon 2026 · PS-03 · Agentic AI</motion.span>
          <motion.h1 initial={{ y: 40, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ type: "spring", stiffness: 160, damping: 18, delay: 0.1 }}
            className="mega mt-6 text-[56px] sm:text-[92px] lg:text-[120px]">
            Reports in.<br /><span className="serif-i text-lime-400">Relief</span> out.
          </motion.h1>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.35 }} className="mt-6 max-w-2xl text-lg font-medium text-brand-50 sm:text-xl">
            Someone texts <Rotator words={WATER} className="mx-1 rounded-lg border-2 border-ink bg-white px-2 font-extrabold text-ink" /> and{" "}
            <Rotator words={HELP} className="mx-1 rounded-lg border-2 border-ink bg-pink-400 px-2 font-extrabold text-ink" every={2100} />. RELAY turns fragmented,
            duplicate, unverified, multilingual reports — over the internet <i>and</i> over SMS and voice — into evidence-backed, human-approved relief plans,
            then follows every delivery until someone says it arrived.
          </motion.p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/" className="btn-pop px-5 py-3 text-base">Open the command map<ArrowRight size={18} aria-hidden /></Link>
            <Link to="/scenario" className="btn bg-white px-5 py-3 text-base text-ink shadow-hard">Run the demo<FlaskConical size={18} aria-hidden /></Link>
            <Link to="/phone" className="btn bg-pink-400 px-5 py-3 text-base text-ink shadow-hard">Send an SMS<Send size={18} aria-hidden /></Link>
          </div>
        </div>
        <motion.div aria-hidden className="absolute bottom-6 right-6 hidden h-40 w-40 place-items-center rounded-full border-2 border-white/80 lg:grid"
          animate={{ rotate: 360 }} transition={{ duration: 30, repeat: Infinity, ease: "linear" }}>
          <svg viewBox="0 0 100 100" className="h-full w-full"><defs><path id="c" d="M50,50 m-38,0 a38,38 0 1,1 76,0 a38,38 0 1,1 -76,0" /></defs>
            <text fontSize="9.5" fontWeight="800" fill="#fff" letterSpacing="2"><textPath href="#c">SILENCE IS A SIGNAL ✺ PEOPLE DECIDE ✺ </textPath></text></svg>
        </motion.div>
      </section>

      {/* LANGUAGE MARQUEE */}
      <div className="border-b-2 border-ink bg-ink py-3 text-2xl font-extrabold text-white">
        <Marquee fast>{["ಕನ್ನಡ", "हिंदी", "മലയാളം", "தமிழ்", "తెలుగు", "मराठी", "বাংলা", "English", "Kanglish", "Hinglish", "Manglish", "SMS", "Voice", "Radio", "Sat-phone"].map((w, i) =>
          <span key={w} className={`flex items-center gap-10 ${i % 3 === 0 ? "text-lime-400" : i % 3 === 1 ? "text-pink-400" : "text-white"}`}>{w}<span className="text-sun-400">✦</span></span>)}</Marquee>
      </div>

      {/* LIVE NUMBERS */}
      <section className="relative border-b-2 border-ink bg-paper px-5 py-12 sm:px-10">
        <Reveal><p className="label">Right now, in the synthetic Kodagu scenario</p></Reveal>
        <Stagger className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
          {[["reports", s?.reports, "bg-lime-400"], ["languages", s?.languages, "bg-pink-400"], ["incidents", s?.incidents, "bg-sun-400"],
            ["arrived with no internet", s?.offline_channel_reports, "bg-cobalt-300"], ["in Fast Verify", s?.fast_verify, "bg-tangerine-400"],
            ["people affected", s?.people_affected, "bg-mint-300"]].map(([l, v, c], i) => (
            <Item key={l as string}>
              <div className={`rounded-3xl border-2 border-ink p-4 shadow-hard ${c} ${i % 2 ? "rotate-1" : "-rotate-1"}`}>
                <p className="mega text-[48px]">{v == null ? "—" : <CountUp value={v as number} />}</p>
                <p className="text-xs font-extrabold uppercase tracking-wider">{l as string}</p>
              </div>
            </Item>
          ))}
        </Stagger>
      </section>

      {/* CASE STUDIES */}
      <section className="relative overflow-hidden border-b-2 border-ink bg-cream px-5 py-14 sm:px-10">
        <div className="pat-grid absolute inset-0 opacity-50" aria-hidden />
        <Reveal className="relative">
          <p className="label">Case studies</p>
          <h2 className="mega mt-2 text-[44px] sm:text-[72px]">Five stories, <span className="serif-i text-brand-500">one</span> loop.</h2>
        </Reveal>
        <div className="relative mt-8 grid gap-6 lg:grid-cols-2">
          {CASES.map((c, i) => (
            <Reveal key={c.n} delay={i * 0.05} className={i === 0 ? "lg:col-span-2" : ""}>
              <Tilt>
                <Link to={c.to} className={`group relative block overflow-hidden rounded-3xl border-2 border-ink p-6 shadow-hard-lg transition-shadow hover:shadow-hard-pink ${c.tone}`}>
                  <span className="absolute -right-4 -top-8 select-none font-display text-[150px] font-extrabold leading-none opacity-15">{c.n}</span>
                  <div className="relative flex items-start justify-between gap-4">
                    <div className="max-w-3xl">
                      <span className="sticker bg-white text-ink">Case {c.n}</span>
                      <h3 className="mega mt-3 text-[30px] sm:text-[40px]">{c.title}</h3>
                      <p className="serif-i mt-2 text-xl">{c.claim}</p>
                      <p className="mt-3 text-[15px] font-medium opacity-85">{c.body}</p>
                      <p className="mt-4 inline-block rounded-full border-2 border-current px-3 py-1 text-xs font-extrabold uppercase tracking-wider">{c.stat}</p>
                    </div>
                    <span className="grid h-12 w-12 shrink-0 place-items-center rounded-full border-2 border-ink bg-white text-ink transition-transform group-hover:rotate-45"><ArrowUpRight size={22} aria-hidden /></span>
                  </div>
                </Link>
              </Tilt>
            </Reveal>
          ))}
        </div>
      </section>

      {/* TEAM */}
      <section className="relative overflow-hidden border-b-2 border-ink bg-paper px-5 py-14 sm:px-10">
        <Blob className="-right-24 top-20 h-72 w-72 opacity-60" color="bg-brand-300" />
        <Reveal className="relative">
          <p className="label">The team</p>
          <h2 className="mega mt-2 text-[44px] sm:text-[72px]">Five agents. Four modules.<br /><span className="serif-i text-pink-500">People decide.</span></h2>
        </Reveal>
        <Stagger className="relative mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {TEAM.map((m, i) => {
            const I = m.icon;
            return (
              <Item key={m.name}>
                <motion.div whileHover={{ y: -6, rotate: i % 2 ? 1.5 : -1.5 }} className="flex h-full gap-3 rounded-3xl border-2 border-ink bg-white p-4 shadow-hard">
                  <span className={`grid h-16 w-16 shrink-0 place-items-center rounded-2xl border-2 border-ink ${m.tone}`}><I size={28} aria-hidden /></span>
                  <div>
                    <p className="text-[11px] font-extrabold uppercase tracking-widest text-ink/50">{m.kind === "agent" ? <><Bot size={11} className="inline" aria-hidden /> agent</> : <><BrainCircuit size={11} className="inline" aria-hidden /> module</>}</p>
                    <p className="text-xl font-extrabold">{m.name}</p>
                    <p className="serif-i text-lg leading-tight">“{m.q}”</p>
                  </div>
                </motion.div>
              </Item>
            );
          })}
        </Stagger>
        <Reveal className="relative mt-8">
          <div className="grid gap-4 rounded-3xl border-2 border-ink bg-ink p-5 text-white shadow-hard-lime md:grid-cols-3">
            {PEOPLE.map((p) => { const I = p.icon; return (
              <div key={p.name} className="flex gap-3"><span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border-2 border-white bg-lime-400 text-ink"><I size={20} aria-hidden /></span>
                <div><p className="text-lg font-extrabold">{p.name}</p><p className="text-sm text-white/75">{p.job}</p></div></div>
            ); })}
          </div>
          <p className="mt-4 flex items-center gap-2 text-sm font-medium text-ink/70"><Scale size={16} aria-hidden />AI interprets, deterministic rules enforce, people keep authority: nothing is dispatched without approval, and every decision is in the audit log.</p>
          <p className="mt-1 text-sm font-bold">Built by Team Tech Architects for AgentX Hackathon 2026.</p>
        </Reveal>
      </section>

      {/* RESEARCH */}
      <section className="border-b-2 border-ink bg-lime-400 px-5 py-12 sm:px-10">
        <Reveal><h2 className="mega text-[40px] sm:text-[60px]">Why this, why now.</h2></Reveal>
        <Stagger className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {RESEARCH.map(([big, what, cite]) => (
            <Item key={cite + big}><div className="h-full rounded-3xl border-2 border-ink bg-white p-4 shadow-hard">
              <p className="mega text-[46px] text-brand-500">{big}</p><p className="mt-1 text-sm font-bold">{what}</p><p className="serif-i mt-2 text-sm text-ink/60">{cite}</p>
            </div></Item>
          ))}
        </Stagger>
      </section>

      {/* CONTACT */}
      <section className="relative overflow-hidden bg-pink-400 px-5 py-14 sm:px-10">
        <div className="pat-stripes absolute inset-0 opacity-[0.07]" aria-hidden />
        <div className="relative grid gap-8 lg:grid-cols-[1fr_1.2fr]">
          <Reveal>
            <p className="label !text-ink/70">Contact the control room</p>
            <h2 className="mega mt-2 text-[48px] sm:text-[80px]">Say it in <span className="serif-i">your</span> language.</h2>
            <p className="mt-4 max-w-md text-[15px] font-medium">This form files a real web report: language detection, extraction, geocoding, duplicate check and an evidence score. If you leave out where you are, RELAY will ask.</p>
          </Reveal>
          <Reveal delay={0.1}><div className="rounded-3xl border-2 border-ink bg-paper p-5 shadow-hard-lg"><ContactForm /></div></Reveal>
        </div>
      </section>
      <footer className="flex flex-wrap items-center justify-between gap-3 border-t-2 border-ink bg-ink px-5 py-5 text-sm text-white sm:px-10">
        <span className="mega text-2xl">relay<span className="text-lime-400">.</span></span>
        <span className="text-white/70">Synthetic scenario data · real-world validation pending · Kodagu, Karnataka is used only to place the scenario.</span>
      </footer>
    </div>
  );
}
