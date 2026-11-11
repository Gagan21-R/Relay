// Minimal motion for the brutalist · minimal UI. Pages and sections appear without entrance animations; the only
// moving thing is the status ticker in the header. Reveal / Stagger / Item are kept as plain wrappers so layouts stay
// the same.
import { ReactNode } from "react";

/** Plain wrapper (no entrance animation). */
export function Reveal({ children, className = "" }: { children: ReactNode; delay?: number; y?: number; className?: string }) {
  return <div className={className}>{children}</div>;
}

/** Plain wrapper (no staggered entrance). */
export function Stagger({ children, className = "" }: { children: ReactNode; className?: string; gap?: number }) {
  return <div className={className}>{children}</div>;
}
export function Item({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={className}>{children}</div>;
}

/** Endless horizontal ticker (used only for the live status line). */
export function Marquee({ children, className = "", fast = false }: { children: ReactNode; className?: string; fast?: boolean }) {
  return (
    <div className={`marquee-mask overflow-hidden ${className}`} aria-hidden>
      <div className={`flex w-max gap-10 ${fast ? "animate-marquee-fast" : "animate-marquee"}`}>
        <div className="flex shrink-0 items-center gap-10">{children}</div>
        <div className="flex shrink-0 items-center gap-10">{children}</div>
      </div>
    </div>
  );
}

/** A number, shown as is (formatted). */
export function CountUp({ value, decimals = 0, className = "" }: { value: number; decimals?: number; className?: string }) {
  return <span className={className}>{value.toFixed(decimals)}</span>;
}
