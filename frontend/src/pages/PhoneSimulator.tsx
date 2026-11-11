import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Mic, Send, Square, Upload } from "lucide-react";
import { PageHeader } from "../components/Layout";
import NetworkPanel from "../components/NetworkPanel";
import ReportCard from "../components/ReportCard";
import { Empty, LANG_NAMES, Panel } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { LiveEvent, useLiveEvents } from "../hooks/useLive";
import { api } from "../services/api";
import { Report, SmsMsg } from "../services/types";

type Samples = { messages: { label: string; lang: string; text: string }[]; phones: { label: string; phone: string; lang: string }[] };
const SPEECH_LANG: Record<string, string> = { en: "en-IN", kn: "kn-IN", hi: "hi-IN", ml: "ml-IN", ta: "ta-IN", te: "te-IN", mr: "mr-IN", bn: "bn-IN" };

function MockPhone({ phone, samples }: { phone: string; samples: Samples["messages"] }) {
  const thread = useApi<SmsMsg[]>(`/api/intake/sms/thread?phone=${encodeURIComponent(phone)}`, ["sms"], 150);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ block: "end" }); }, [thread.data]);
  const send = async (body: string) => {
    if (!body.trim()) return;
    setBusy(true); setErr(null);
    try { await api("/api/intake/sms", { method: "POST", body: JSON.stringify({ from: phone, body }) }); setText(""); thread.reload(); }
    catch (e: any) { setErr(e.message); }
    setBusy(false);
  };
  return (
    <div className="mx-auto w-full max-w-[340px]">
      <div className="rounded-[2.2rem] border-[10px] border-ink bg-ink shadow-2xl">
        <div className="flex items-center justify-between rounded-t-[1.6rem] bg-brand-700 px-4 py-2 text-xs text-white">
          <span>RELAY helpline · SMS</span><span className="font-mono">{phone.slice(0, 6)}…{phone.slice(-3)}</span>
        </div>
        <div className="h-[380px] space-y-2 overflow-y-auto bg-paper p-3" aria-live="polite">
          {!thread.data?.length && <p className="pt-10 text-center text-xs text-ink/60">No messages yet. Type in any language, or tap a sample.</p>}
          {thread.data?.map((m) => (
            <div key={m.id} className={`flex ${m.direction === "in" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-2xl px-3 py-1.5 text-sm ${m.direction === "in" ? "rounded-br-sm bg-brand-600 text-white" : "rounded-bl-sm bg-white text-ink shadow"}`} lang={m.language}>
                {m.body}
                <p className={`mt-0.5 text-[10px] ${m.direction === "in" ? "text-brand-100" : "text-ink/50"}`}>{m.kind}{m.language ? ` · ${LANG_NAMES[m.language] ?? m.language}` : ""}</p>
              </div>
            </div>
          ))}
          <div ref={end} />
        </div>
        <form className="flex gap-1.5 rounded-b-[1.6rem] bg-white p-2" onSubmit={(e) => { e.preventDefault(); send(text); }}>
          <input className="min-w-0 flex-1 rounded-full border-2 border-ink px-3 py-1.5 text-sm" value={text} onChange={(e) => setText(e.target.value)} placeholder="Type an SMS in any language" aria-label="SMS text" maxLength={480} />
          <button className="btn-primary !rounded-full !px-2.5" disabled={busy || !text.trim()} aria-label="Send SMS"><Send size={15} /></button>
        </form>
      </div>
      {err && <p className="mt-2 text-xs text-pink-500">{err}</p>}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {samples.map((s) => (
          <button key={s.label} onClick={() => send(s.text)} disabled={busy} className="rounded-full border border-ink bg-lime-300 px-2.5 py-1 text-xs font-bold text-ink shadow-hard-sm transition-transform hover:-translate-y-0.5" title={s.text}>{s.label}</button>
        ))}
      </div>
    </div>
  );
}

function VoiceCall({ phone }: { phone: string }) {
  const [lang, setLang] = useState("kn");
  const [rec, setRec] = useState<MediaRecorder | null>(null);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [transcript, setTranscript] = useState("");
  const [status, setStatus] = useState<string>("");
  const speech = useRef<any>(null);
  const start = async () => {
    setBlob(null); setStatus("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      const chunks: Blob[] = [];
      mr.ondataavailable = (e) => chunks.push(e.data);
      mr.onstop = () => { setBlob(new Blob(chunks, { type: "audio/webm" })); stream.getTracks().forEach((t) => t.stop()); };
      mr.start(); setRec(mr);
      const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SR) {
        const s = new SR(); s.lang = SPEECH_LANG[lang]; s.continuous = true; s.interimResults = false;
        s.onresult = (e: any) => setTranscript((t) => `${t} ${Array.from(e.results).slice(e.resultIndex).map((r: any) => r[0].transcript).join(" ")}`.trim());
        s.start(); speech.current = s;
      }
    } catch { setStatus("Microphone not available here. Upload a clip or type the transcript instead."); }
  };
  const stop = () => { rec?.stop(); setRec(null); speech.current?.stop?.(); };
  const submit = async () => {
    const fd = new FormData();
    fd.append("phone", phone); fd.append("language", lang);
    if (transcript.trim()) fd.append("transcript", transcript.trim());
    if (blob) fd.append("audio", blob, "call.webm");
    setStatus("Sending…");
    try {
      const r = await fetch("/api/intake/voice/simulate", { method: "POST", body: fd });
      const j = await r.json();
      setStatus(r.ok ? `Report ${j.report.ref} created (${j.transcription}). Auto-reply sent by SMS.` : j.detail);
      if (r.ok) { setTranscript(""); setBlob(null); }
    } catch { setStatus("Backend not reachable."); }
  };
  return (
    <div className="space-y-2 text-sm">
      <p className="text-xs text-ink/60">IVR flow: language menu → record → transcribe → same pipeline as SMS. With a Gemini key the audio itself is transcribed; in mock mode the browser's speech recognition (or your typed transcript) is used.</p>
      <div className="flex flex-wrap items-center gap-2">
        <select className="input !w-auto !py-1" value={lang} onChange={(e) => setLang(e.target.value)} aria-label="Caller language">
          {Object.entries(LANG_NAMES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        {!rec ? <button className="btn-ghost" onClick={start}><Mic size={14} aria-hidden />Record</button>
          : <button className="btn-primary !bg-pink-500" onClick={stop}><Square size={14} aria-hidden />Stop</button>}
        <label className="btn-ghost cursor-pointer"><Upload size={14} aria-hidden />Upload clip<input type="file" accept="audio/*" className="hidden" onChange={(e) => setBlob(e.target.files?.[0] ?? null)} /></label>
        {blob && <audio controls src={URL.createObjectURL(blob)} className="h-8" />}
      </div>
      <textarea className="input" rows={2} value={transcript} onChange={(e) => setTranscript(e.target.value)} placeholder="Transcript (filled by speech recognition, or type it)" lang={lang} />
      <button className="btn-primary" onClick={submit} disabled={!transcript.trim() && !blob}>Send call to RELAY</button>
      {status && <p className="text-xs text-ink/70">{status}</p>}
    </div>
  );
}

export default function PhoneSimulator() {
  const { t } = useTranslation();
  const samples = useApi<Samples>("/api/sim/samples");
  const [phone, setPhone] = useState("+919845500101");
  const [custom, setCustom] = useState("");
  const [arrivals, setArrivals] = useState<Report[]>([]);
  const onReport = useCallback((e: LiveEvent) => setArrivals((x) => [e.data as Report, ...x.filter((r) => r.id !== e.data.id)].slice(0, 6)), []);
  useLiveEvents(onReport, ["report"]);
  return (
    <div className="space-y-4">
      <PageHeader title={t("nav.phone")} sub={t("pages.phone")} />
      <div className="grid gap-4 xl:grid-cols-[380px_1fr]">
        <div className="space-y-3">
          <div className="flex flex-wrap gap-1.5">
            {samples.data?.phones.map((p) => (
              <button key={p.phone} onClick={() => setPhone(p.phone)} className={`rounded-xl border-2 px-2 py-1 text-xs font-bold ${phone === p.phone ? "border-ink bg-brand-500 font-bold text-white shadow-hard-sm" : "border-ink bg-white text-ink/70"}`}>{p.label}</button>
            ))}
            <input className="w-36 input !w-auto !py-1 text-xs" placeholder="+91 other number" value={custom} onChange={(e) => setCustom(e.target.value)} onBlur={() => custom.match(/^\+?\d{10,13}$/) && setPhone(custom.startsWith("+") ? custom : `+91${custom.slice(-10)}`)} aria-label="Other phone number" />
          </div>
          <MockPhone phone={phone} samples={samples.data?.messages ?? []} />
        </div>
        <div className="space-y-4">
          <Panel title="Arriving on the dashboard now">
            {!arrivals.length ? <Empty>Send an SMS or make a call: it appears here within seconds, with its translation and extracted fields.</Empty>
              : <div className="space-y-2">{arrivals.map((r) => <ReportCard key={r.id} r={r} />)}</div>}
          </Panel>
          <div className="grid gap-4 lg:grid-cols-2">
            <Panel title="Voice call (IVR)"><VoiceCall phone={phone} /></Panel>
            <NetworkPanel />
          </div>
        </div>
      </div>
    </div>
  );
}
