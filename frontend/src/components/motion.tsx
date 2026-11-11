// Motion primitives for the maximalist UI. All respect the user's reduced-motion setting (MotionConfig in main.tsx).
import { ReactNode, useEffect, useRef, useState } from "react";
import { animate, motion, useInView, useMotionValue, useSpring, useTransform } from "framer-motion";

export const spring = { type: "spring", stiffness: 260, damping: 22 } as const;

/** Fade and rise into view once. */
export function Reveal({ children, delay = 0, y = 24, className = "" }: { children: ReactNode; delay?: number; y?: number; className?: string }) {
  return (
    <motion.div className={className} initial={{ opacity: 0, y }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-40px" }}
      transition={{ ...spring, delay }}>
      {children}
    </motion.div>
  );
}

/** Children enter one after another. */
export function Stagger({ children, className = "", gap = 0.06 }: { children: ReactNode; className?: string; gap?: number }) {
  return (
    <motion.div className={className} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-40px" }}
      variants={{ hidden: {}, show: { transition: { staggerChildren: gap } } }}>
      {children}
    </motion.div>
  );
}
export function Item({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <motion.div className={className} variants={{ hidden: { opacity: 0, y: 18, rotate: -1.5 }, show: { opacity: 1, y: 0, rotate: 0, transition: spring } }}>
      {children}
    </motion.div>
  );
}

/** Endless horizontal ticker. Content is duplicated for a seamless loop. */
export function Marquee({ children, className = "", fast = false, reverse = false }: { children: ReactNode; className?: string; fast?: boolean; reverse?: boolean }) {
  return (
    <div className={`marquee-mask overflow-hidden ${className}`} aria-hidden>
      <div className={`flex w-max gap-10 ${fast ? "animate-marquee-fast" : "animate-marquee"}`} style={reverse ? { animationDirection: "reverse" } : undefined}>
        <div className="flex shrink-0 items-center gap-10">{children}</div>
        <div className="flex shrink-0 items-center gap-10">{children}</div>
      </div>
    </div>
  );
}

/** Morphing colour blob for backgrounds. */
export function Blob({ className = "", color = "bg-pink-400" }: { className?: string; color?: string }) {
  return <div aria-hidden className={`pointer-events-none absolute animate-wobble rounded-blob opacity-80 blur-[1px] ${color} ${className}`} />;
}

/** Number that counts up when it first appears and glides to new values. */
export function CountUp({ value, decimals = 0, className = "" }: { value: number; decimals?: number; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const seen = useInView(ref, { once: true });
  const [shown, setShown] = useState(0);
  useEffect(() => {
    if (!seen) return;
    const c = animate(shown, value, { duration: 0.9, ease: "easeOut", onUpdate: (v) => setShown(v) });
    return () => c.stop();
  }, [value, seen]); // eslint-disable-line react-hooks/exhaustive-deps
  return <span ref={ref} className={className}>{shown.toFixed(decimals)}</span>;
}

/** Card that tilts toward the pointer. */
export function Tilt({ children, className = "", max = 7 }: { children: ReactNode; className?: string; max?: number }) {
  const x = useMotionValue(0), y = useMotionValue(0);
  const rx = useSpring(useTransform(y, [-0.5, 0.5], [max, -max]), { stiffness: 200, damping: 18 });
  const ry = useSpring(useTransform(x, [-0.5, 0.5], [-max, max]), { stiffness: 200, damping: 18 });
  return (
    <motion.div className={className} style={{ rotateX: rx, rotateY: ry, transformPerspective: 900 }}
      onPointerMove={(e) => { const r = e.currentTarget.getBoundingClientRect(); x.set((e.clientX - r.left) / r.width - 0.5); y.set((e.clientY - r.top) / r.height - 0.5); }}
      onPointerLeave={() => { x.set(0); y.set(0); }}>
      {children}
    </motion.div>
  );
}

/** Words that swap in place (e.g. "water" in eight languages). */
export function Rotator({ words, className = "", every = 1800 }: { words: string[]; className?: string; every?: number }) {
  const [i, setI] = useState(0);
  useEffect(() => { const t = window.setInterval(() => setI((n) => (n + 1) % words.length), every); return () => window.clearInterval(t); }, [words.length, every]);
  return (
    <span className={`relative inline-grid ${className}`}>
      {words.map((w, n) => (
        <motion.span key={w} className="col-start-1 row-start-1" initial={false} aria-hidden={n !== i}
          animate={{ opacity: n === i ? 1 : 0, y: n === i ? 0 : n < i ? -30 : 30, rotateX: n === i ? 0 : 70 }} transition={spring}>
          {w}
        </motion.span>
      ))}
    </span>
  );
}
