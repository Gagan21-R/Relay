// The RELAY landing page, built as a creative-agency portfolio in a BRUTALIST style: raw grid, giant uppercase type,
// thick black borders, heavy shadows, flat red / blue / green / black blocks, no yellow. No entrance animations. Sections: hero ·
// manifesto · live index · case studies · capabilities · team · process · research · contact (files a real report) ·
// footer.
import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, ArrowUpRight, CheckCircle2, Send } from "lucide-react";
import { useApi } from "../hooks/useApi";
import { Explain } from "../components/Assistant";
import { startGuide } from "../components/Guide";
import { api } from "../services/api";

const LANGS = ["ಕನ್ನಡ", "हिंदी", "മലയാളം", "தமிழ்", "తెలుగు", "मराठी", "বাংলা", "অসমীয়া", "ଓଡ଼ିଆ", "ગુજરાતી", "ਪੰਜਾਬੀ", "नेपाली", "Mizo", "Khasi", "English"];

const CASES = [
  { n: "01", title: "The SMS and the tweet", to: "/incidents", claim: "Two reports, two languages, one flooded village.",
    body: "A Kannada SMS and an English post land minutes apart. Same place, same meaning, same hour, compatible needs: one incident — not two boats.",
    stat: "6 reports → 1 incident" },
  { n: "02", title: "The dam that did not burst", to: "/alerts", claim: "“Share to all.” In three languages.",
    body: "A forward chain, a catastrophe with no detail, and an official bulletin that says the opposite. It scores false; the correction goes out in every language.",
    stat: "0% credible · 8-language correction" },
  { n: "03", title: "The village that went silent", to: "/blackout", claim: "Zero reports was the alarm.",
    body: "Inside the hazard, towers down, relatives elsewhere who cannot reach anyone. RELAY ranks the silence and asks Resource what a recon team should carry.",
    stat: "2,400 people · 0 reports · 1 recon" },
  { n: "04", title: "Two agents, one boat short", to: "/agents", claim: "“I'm short of 2 boats.” — “Kushalnagar can send 2.”",
    body: "Coordination asks Resource for a second source; the offer becomes a plan line. When nobody has stock, Resource escalates to a person.",
    stat: "propose → accept → plan line" },
  { n: "05", title: "ಹೌದು is not confirmed", to: "/dispatch", claim: "Arriving is not delivering. Delivering is not confirming.",
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
  { name: "Intake", role: "reads every report", q: "What is this report saying?" },
  { name: "Trust", role: "duplicates, credibility", q: "Is it true, and have we seen it before?" },
  { name: "Triage", role: "who first", q: "Who needs help first?" },
  { name: "Resource", role: "stock, shortages", q: "Do we have enough, and where?" },
  { name: "Blackout", role: "silent places", q: "Which places have gone quiet?" },
  { name: "Monitor", role: "what changed", q: "Has something changed?" },
  { name: "Coordination", role: "plans, routes, people", q: "Who goes where, with what — and did it arrive?" },
  { name: "Duty Officer", role: "a person decides", q: "Approve. Verify. Confirm.", human: true },
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
    <form onSubmit={submit} className="grid border-2 border-ink bg-bone">
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
        <button className="btn-primary px-6 py-3 text-sm" disabled={busy || f.text.trim().length < 3}><Send size={16} aria-hidden />{busy ? "Sending…" : "Send to the control room"}</button>
        <span className="max-w-xs text-xs text-ink/60">Files a real report through every agent. No internet? Text the same words by SMS.</span>
      </div>
      {res && (
        <p className="flex items-center gap-2 border-t-2 border-ink bg-sand p-3 font-mono text-xs uppercase tracking-wider text-ink">
          <CheckCircle2 size={14} className="text-mint-500" aria-hidden />Received · ref {res.ref}{res.lang ? ` · ${res.lang}` : ""}{res.place ? ` · ${res.place}` : " · we'll ask where you are"}
        </p>
      )}
      {err && <p className="border-t-2 border-ink p-3 text-sm font-bold text-brand-600">{err}</p>}
    </form>
  );
}

export default function About() {
  const { data: s } = useApi<Summary>("/api/summary", ["report", "incident"], 1000);
  const live: [string, number | undefined][] = [["reports", s?.reports], ["languages", s?.languages], ["incidents", s?.incidents],
    ["arrived with no internet", s?.offline_channel_reports], ["in fast verify", s?.fast_verify], ["people affected", s?.people_affected]];
  return (
    <div className="-mx-4 -mt-4 sm:-mx-6 sm:-mt-6">
      {/* HERO */}
      <section className="grid border-b-2 border-ink lg:grid-cols-[1.25fr_1fr]">
        <div className="flex flex-col justify-between border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2">
          <div className="grid grid-cols-2 gap-4 font-mono text-[10.5px] uppercase tracking-[0.16em] text-ink/60 sm:grid-cols-4">
            <span>Relay®<br />index 001</span><span>Studio for<br />disaster response</span><span>AgentX 2026<br />PS-03</span>
            <span className="flex items-start gap-2">Explain<Explain id="about.page" /></span>
          </div>
          <div className="py-10">
            <h1 className="mega text-[50px] sm:text-[86px] xl:text-[104px]">Reports in.<br /><span className="bg-signal px-2 text-ink">Relief</span> out.</h1>
            <p className="mt-8 max-w-xl border-2 border-ink bg-white p-4 text-lg font-medium leading-relaxed shadow-hard">
              Someone texts <span className="border-2 border-ink bg-bone px-1.5 font-bold">ನೀರು</span> and{" "}
              <span className="border-2 border-ink bg-blue px-1.5 font-bold text-ink">help madi</span>. Seven agents read it, check it, rank it,
              negotiate the stock and the route — and then a person decides.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button className="btn-primary px-5 py-3" onClick={() => startGuide()}>Watch it work<ArrowRight size={16} aria-hidden /></button>
            <Link to="/workflow" className="btn-ghost px-5 py-3">How it works</Link>
            <Link to="/" className="btn-ghost px-5 py-3">Command map</Link>
          </div>
        </div>
        {/* brutalist composition: a black block, a signal bar, the live index */}
        <div className="grid grid-rows-[auto_1fr_auto] bg-sand text-ink">
          <div className="flex items-baseline justify-between border-b-2 border-ink/25 px-5 py-3 font-mono text-[10.5px] uppercase tracking-[0.18em] text-ink/60">
            <span>fig. 1 — live index</span><span>{s?.scenario_name ?? "—"}</span>
          </div>
          <div className="grid grid-cols-2">
            {live.map(([l, v], i) => (
              <div key={l} className={`border-b-2 border-ink/25 p-5 ${i % 2 === 0 ? "border-r-2" : ""}`}>
                <p className="font-mono text-[10px] text-brand-600">0{i + 1}</p>
                <p className="font-display text-[52px] font-extrabold leading-none tracking-[-0.04em] tabular-nums">{v ?? "—"}</p>
                <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.14em] text-ink/60">{l}</p>
              </div>))}
          </div>
          <div className="flex items-center gap-3 px-5 py-4">
            <span className="h-4 flex-1 bg-signal" aria-hidden />
            <span className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-ink/70">silence is a signal</span>
          </div>
        </div>
      </section>

      {/* LANGUAGES */}
      <div className="flex flex-wrap border-b-2 border-ink bg-bone">
        {LANGS.map((w) => <span key={w} className="border-r-2 border-ink bg-white px-4 py-3 font-display text-xl odd:bg-cream">{w}</span>)}
        <span className="flex-1 bg-sand px-4 py-3 text-right font-mono text-[10.5px] uppercase tracking-[0.18em] text-ink/70">19 languages configured · support levels declared</span>
      </div>

      {/* MANIFESTO */}
      <section className="grid border-b-2 border-ink lg:grid-cols-[280px_1fr]">
        <div className="border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2"><p className="label">002 — Manifesto</p></div>
        <div className="p-5 sm:p-10">
          <p className="font-display text-[30px] font-extrabold leading-[1.05] tracking-tight sm:text-[52px]">
            We do not trust the loudest report. We trust evidence, we listen for the silence, and we never let a machine{" "}
            <span className="bg-signal px-2 text-ink">press send</span>.</p>
          <div className="mt-10 grid border-2 border-ink sm:grid-cols-3">
            {[["AI interprets", "reads, translates, fills a strict schema"], ["Rules enforce", "priorities, routes, quantities, permissions"], ["People decide", "approve, verify, confirm, send"]].map(([a, b], i) => (
              <div key={a} className={`p-5 text-ink ${["bg-blue", "bg-sand", "bg-go"][i]} ${i < 2 ? "border-b-2 border-ink sm:border-b-0 sm:border-r-2" : ""}`}>
                <p className="font-mono text-[11px] font-extrabold">0{i + 1}</p><p className="mt-2 font-display text-2xl uppercase">{a}</p><p className="mt-1 font-mono text-[12px] uppercase">{b}</p>
              </div>))}
          </div>
        </div>
      </section>

      {/* CASE STUDIES */}
      <section className="border-b-2 border-ink">
        <div className="grid border-b-2 border-ink lg:grid-cols-[280px_1fr]">
          <div className="border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2"><p className="label">003 — Selected work</p><p className="mt-2 text-sm text-ink/60">Every case opens the live page where it happens.</p></div>
          <div className="p-5 sm:p-10"><h2 className="mega text-[48px] sm:text-[84px]">Case studies.</h2></div>
        </div>
        {CASES.map((c) => (
          <Link key={c.n} to={c.to} className="group grid grid-cols-[56px_1fr_auto] items-start gap-4 border-b-2 border-ink px-2 py-6 hover:bg-sand hover:text-ink sm:grid-cols-[80px_1.2fr_1fr_auto] sm:px-4">
            <span className="border-2 border-ink bg-signal px-1 text-center font-mono text-sm font-extrabold text-ink">{c.n}</span>
            <div><h3 className="mega text-[30px] sm:text-[44px]">{c.title}</h3><p className="mt-1 text-lg opacity-75">{c.claim}</p></div>
            <div className="hidden sm:block">
              <p className="text-sm opacity-75">{c.body}</p>
              <p className="mt-3 inline-block border border-current px-2 py-0.5 font-mono text-[10.5px] uppercase tracking-wider">{c.stat}</p>
            </div>
            <span className="grid h-12 w-12 place-items-center border-2 border-current"><ArrowUpRight size={22} aria-hidden /></span>
          </Link>))}
      </section>

      {/* CAPABILITIES */}
      <section className="border-b-2 border-ink">
        <div className="flex items-baseline justify-between border-b-2 border-ink px-5 py-3 sm:px-10"><p className="label">004 — Capabilities</p><Link to="/workflow" className="link-grow font-mono text-[11px] uppercase">full workflow →</Link></div>
        <div className="grid sm:grid-cols-2 xl:grid-cols-3">
          {CAPS.map(([t, d], i) => (
            <div key={t} className={`border-b-2 border-r-2 border-ink p-6 ${i % 2 ? "bg-cream" : "bg-white"} hover:bg-sand hover:text-ink`}>
              <p className="inline-block border-2 border-ink bg-signal px-1.5 font-mono text-[11px] font-extrabold text-ink">{String(i + 1).padStart(2, "0")}</p>
              <p className="mt-3 font-display text-[24px] uppercase leading-tight">{t}</p>
              <p className="mt-2 max-w-sm text-sm font-medium">{d}</p>
            </div>))}
        </div>
      </section>

      {/* TEAM */}
      <section className="border-b-2 border-ink">
        <div className="grid border-b-2 border-ink lg:grid-cols-[280px_1fr]">
          <div className="border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2"><p className="label">005 — The team</p><p className="mt-2 text-sm text-ink/60">Seven agents who talk to each other, and one person who decides. <Link to="/agents" className="link-grow font-bold">See them talk →</Link></p></div>
          <div className="p-5 sm:p-10"><h2 className="mega text-[44px] sm:text-[76px]">Seven agents.<br /><span className="bg-signal px-2 text-ink">One person</span> decides.</h2></div>
        </div>
        <div className="grid sm:grid-cols-2 xl:grid-cols-4">
          {TEAM.map((m, i) => (
            <div key={m.name} className="border-b-2 border-r-2 border-ink bg-white">
              <div className={`flex h-36 items-end justify-between border-b-2 border-ink p-4 text-ink ${m.human ? "bg-signal" : ["bg-sand", "bg-blue", "bg-go", "bg-sand"][i % 4]}`}>
                <span className="font-display text-[96px] leading-[0.8] tracking-[-0.06em]">{m.name[0]}</span>
                <span className="font-mono text-[12px] font-extrabold">{String(i + 1).padStart(2, "0")}</span>
              </div>
              <div className="p-4">
                <p className="font-mono text-[10px] uppercase tracking-[0.16em] opacity-50">{m.human ? "human" : "agent"} · {m.role}</p>
                <p className="mt-1 font-display text-2xl font-extrabold">{m.name}</p>
                <p className="mt-1 text-[15px] leading-snug opacity-75">“{m.q}”</p>
              </div>
            </div>))}
        </div>
      </section>

      {/* PROCESS */}
      <section className="border-b-2 border-ink bg-sand text-ink">
        <div className="flex items-baseline justify-between border-b-2 border-ink/25 px-5 py-3 sm:px-10"><p className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-ink/60">006 — Process</p><Link to="/workflow" className="font-mono text-[11px] uppercase text-brand-600">open the flowchart →</Link></div>
        <div className="grid md:grid-cols-5">
          {PROCESS.map(([a, b], i) => (
            <div key={a} className="border-b-2 border-ink/25 p-6 md:border-b-0 md:border-r-2">
              <p className="font-display text-[64px] font-extrabold leading-none text-ink/20">{i + 1}</p>
              <p className="mt-2 font-display text-2xl font-extrabold">{a}</p>
              <p className="mt-1 font-mono text-[11px] uppercase tracking-wider text-ink/60">{b}</p>
            </div>))}
        </div>
        <p className="border-t-2 border-ink/25 px-5 py-4 font-mono text-[11px] uppercase tracking-wider text-ink/60 sm:px-10">◆ = a person decides · whenever something changes, Monitor sends it back to Coordination to re-plan</p>
      </section>

      {/* RESEARCH */}
      <section className="grid border-b-2 border-ink lg:grid-cols-[280px_1fr]">
        <div className="border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2"><p className="label">007 — Why this, why now</p></div>
        <div className="grid sm:grid-cols-2 xl:grid-cols-4">
          {RESEARCH.map(([big, what, cite]) => (
            <div key={cite + big} className="border-b-2 border-r-2 border-ink p-6">
              <p className="mega text-[58px]">{big}</p><p className="mt-2 text-sm">{what}</p><p className="mt-3 font-mono text-[11px] uppercase tracking-wider text-ink/50">{cite}</p>
            </div>))}
        </div>
      </section>

      {/* CONTACT */}
      <section className="grid border-b-2 border-ink lg:grid-cols-[1fr_1.2fr]">
        <div className="border-b-2 border-ink p-5 sm:p-10 lg:border-b-0 lg:border-r-2">
          <p className="label">008 — Contact the control room</p>
          <h2 className="mega mt-4 text-[40px] sm:text-[56px] xl:text-[62px]">Say it in <span className="bg-blue px-2 text-ink">your</span> language.</h2>
          <p className="mt-6 max-w-md border-l-2 border-ink pl-4 text-[15px]">This form files a real report: language detection, extraction, geocoding, the duplicate check and an evidence score. Leave out where you are and RELAY will ask.</p>
        </div>
        <div className="p-5 sm:p-10"><ContactForm /></div>
      </section>

      {/* FOOTER */}
      <footer className="bg-sand px-5 pb-6 pt-10 text-ink sm:px-10">
        <p className="font-display text-[14vw] uppercase leading-[0.8] tracking-[-0.05em]">Relay<span className="text-brand-600">.</span></p>
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t-2 border-ink/25 pt-4 font-mono text-[10.5px] uppercase tracking-[0.14em] text-ink/60">
          <span>Team Tech Architects · AgentX Hackathon 2026</span>
          <span>Synthetic data · real places · real-world validation pending</span>
        </div>
      </footer>
    </div>
  );
}
