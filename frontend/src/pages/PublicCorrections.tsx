// Public view: official rumour corrections only, in every language. No internal data.
import { Link } from "react-router-dom";
import { Megaphone } from "lucide-react";
import { Corrections } from "./Alerts";
import { Blob } from "../components/motion";

export default function PublicCorrections() {
  return (
    <div className="min-h-screen bg-paper">
      <header className="relative overflow-hidden border-b-2 border-ink bg-brand-500 px-5 py-10 text-white">
        <Blob className="-right-16 -top-16 h-64 w-64" color="bg-lime-400" />
        <div className="relative mx-auto max-w-4xl">
          <span className="sticker bg-lime-400 text-ink"><Megaphone size={13} aria-hidden />Official corrections · Kodagu (synthetic scenario)</span>
          <h1 className="mega mt-4 text-[48px] sm:text-[72px]">Is it true?</h1>
          <p className="mt-2 max-w-xl text-lg font-medium text-brand-50">Messages checked by the district control room and found false. Please do not forward them.</p>
        </div>
      </header>
      <main className="mx-auto max-w-4xl p-5"><Corrections /></main>
      <footer className="mx-auto max-w-4xl px-5 pb-8 text-sm font-medium text-ink/60">RELAY · <Link className="underline" to="/about">about</Link> · No internet? These corrections are also sent by SMS.</footer>
    </div>
  );
}
