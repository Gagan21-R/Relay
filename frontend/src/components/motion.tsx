// Motion + surreal primitives for the brutalist · minimal · surreal UI. All respect reduced motion (MotionConfig in
// main.tsx and the CSS media query). Brutalist motion is decisive (hard springs, wipes, letter-by-letter); the surreal
// layer is slow and dreamlike (levitating moons, an eye that follows you, a door in the sky, melting drips).
import { ReactNode, useEffect, useRef, useState } from "react";
import { animate, motion, useInView, useMotionValue, useScroll, useSpring, useTransform } from "framer-motion";

export const spring = { type: "spring", stiffness: 300, damping: 26 } as const;

/** Rise into view once. */
export function Reveal({ children, delay = 0, y = 28, className = "" }: { children: ReactNode; delay?: number; y?: number; className?: string }) {
  return (
    <motion.div className={className} initial={{ opacity: 0, y }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-40px" }}
      transition={{ ...spring, delay }}>
      {children}
    </motion.div>
  );
}

/** Children enter one after another. */
export function Stagger({ children, className = "", gap = 0.07 }: { children: ReactNode; className?: string; gap?: number }) {
  return (
    <motion.div className={className} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-40px" }}
      variants={{ hidden: {}, show: { transition: { staggerChildren: gap } } }}>
      {children}
    </motion.div>
  );
}
export function Item({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <motion.div className={className} variants={{ hidden: { opacity: 0, y: 22, clipPath: "inset(0 0 100% 0)" }, show: { opacity: 1, y: 0, clipPath: "inset(0 0 0% 0)", transition: spring } }}>
      {children}
    </motion.div>
  );
}

/** Headline that assembles letter by letter (brutalist type in motion). Words never break in the middle. */
export function SplitText({ text, className = "", delay = 0 }: { text: string; className?: string; delay?: number }) {
  let i = 0;
  return (
    <span className={className} aria-label={text}>
      {text.split(" ").map((word, w) => (
        <span key={w} aria-hidden className="inline-block whitespace-nowrap">
          {[...word].map((ch) => {
            const k = i++;
            return (
              <motion.span key={k} className="inline-block" initial={{ y: "0.9em", opacity: 0, rotate: 6 }} animate={{ y: 0, opacity: 1, rotate: 0 }}
                transition={{ ...spring, delay: delay + k * 0.028 }}>{ch}</motion.span>
            );
          })}
        </span>
      )).flatMap((el, w) => (w ? [" ", el] : [el]))}
    </span>
  );
}

/** Endless horizontal ticker. */
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

/** A levitating dream sphere (replaces the old colour blob; `color` is ignored on purpose — one surreal tone). */
export function Blob({ className = "" }: { className?: string; color?: string }) {
  return <div aria-hidden className={`pointer-events-none absolute animate-levitate rounded-full orb opacity-90 ${className}`} />;
}

/** A moon that hangs in the page. */
export function Moon({ className = "", size = 160 }: { className?: string; size?: number }) {
  return <div aria-hidden className={`pointer-events-none absolute animate-levitate rounded-full moon ${className}`} style={{ width: size, height: size }} />;
}

/** An eye that follows the pointer and blinks now and then. */
export function Eye({ className = "", size = 120 }: { className?: string; size?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const x = useSpring(0, { stiffness: 120, damping: 14 }), y = useSpring(0, { stiffness: 120, damping: 14 });
  useEffect(() => {
    const move = (e: PointerEvent) => {
      const r = ref.current?.getBoundingClientRect();
      if (!r) return;
      const dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2), d = Math.hypot(dx, dy) || 1, k = Math.min(1, d / 400) * size * 0.16;
      x.set((dx / d) * k); y.set((dy / d) * k * 0.6);
    };
    window.addEventListener("pointermove", move);
    return () => window.removeEventListener("pointermove", move);
  }, [x, y, size]);
  return (
    <div ref={ref} aria-hidden className={`pointer-events-none absolute ${className}`} style={{ width: size, height: size * 0.56 }}>
      <div className="relative h-full w-full animate-blink overflow-hidden border-2 border-ink bg-bone" style={{ borderRadius: "50% / 50%" }}>
        <motion.div className="absolute left-1/2 top-1/2 grid place-items-center rounded-full bg-ink" style={{ width: size * 0.36, height: size * 0.36, marginLeft: -size * 0.18, marginTop: -size * 0.18, x, y }}>
          <div className="rounded-full bg-signal" style={{ width: size * 0.12, height: size * 0.12 }} />
        </motion.div>
      </div>
    </div>
  );
}

/** A melting drip hanging from an edge. */
export function Drip({ className = "", color = "#0B0B0C" }: { className?: string; color?: string }) {
  return (
    <svg aria-hidden viewBox="0 0 120 90" className={`pointer-events-none absolute origin-top animate-drip ${className}`} fill={color}>
      <path d="M0 0h120v18c-8 0-10 10-10 22 0 14-6 22-12 22s-10-8-10-20c0-10-4-16-10-16s-8 8-8 26c0 22-6 34-14 34s-12-12-12-30c0-14-4-22-10-22s-8 6-8 14c0 8-4 12-8 12S8 52 8 44 4 26 0 24z" />
    </svg>
  );
}

/** A door frame standing in the sky, open onto another sky. */
export function Door({ className = "" }: { className?: string }) {
  return (
    <div aria-hidden className={`pointer-events-none absolute animate-floaty ${className}`}>
      <div className="relative h-full w-full border-[6px] border-ink bg-bone">
        <div className="absolute inset-2 sky-night" />
        <div className="absolute left-1/2 top-1/3 h-3 w-3 -translate-x-1/2 rounded-full bg-bone shadow-[0_0_18px_6px_rgba(255,253,246,.7)]" />
      </div>
      <div className="mx-auto mt-2 h-3 w-[80%] rounded-full bg-ink/20 blur-sm" />
    </div>
  );
}

/** A ladder that leads up out of the frame. */
export function Ladder({ className = "", rungs = 9 }: { className?: string; rungs?: number }) {
  return (
    <div aria-hidden className={`pointer-events-none absolute flex flex-col justify-between border-x-[5px] border-ink ${className}`}>
      {Array.from({ length: rungs }, (_, i) => <div key={i} className="h-[5px] bg-ink" />)}
    </div>
  );
}

/** A slow drifting cloud. */
export function Cloud({ className = "", delay = 0 }: { className?: string; delay?: number }) {
  return (
    <div aria-hidden className={`pointer-events-none absolute animate-drift ${className}`} style={{ animationDelay: `${delay}s` }}>
      <div className="relative h-10 w-40">
        <div className="absolute bottom-0 h-8 w-40 rounded-full bg-bone/90" />
        <div className="absolute bottom-3 left-6 h-12 w-16 rounded-full bg-bone/90" />
        <div className="absolute bottom-2 left-20 h-10 w-14 rounded-full bg-bone/90" />
      </div>
    </div>
  );
}

/** Element that leans toward the pointer (buttons, CTAs). */
export function Magnetic({ children, className = "", strength = 0.35 }: { children: ReactNode; className?: string; strength?: number }) {
  const x = useSpring(0, { stiffness: 220, damping: 16 }), y = useSpring(0, { stiffness: 220, damping: 16 });
  return (
    <motion.div className={`inline-block ${className}`} style={{ x, y }}
      onPointerMove={(e) => { const r = e.currentTarget.getBoundingClientRect(); x.set((e.clientX - r.left - r.width / 2) * strength); y.set((e.clientY - r.top - r.height / 2) * strength); }}
      onPointerLeave={() => { x.set(0); y.set(0); }}>
      {children}
    </motion.div>
  );
}

/** Moves with scroll at a different speed (parallax). */
export function Parallax({ children, className = "", speed = 0.3 }: { children: ReactNode; className?: string; speed?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], [120 * speed, -120 * speed]);
  return <motion.div ref={ref} className={className} style={{ y }}>{children}</motion.div>;
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
export function Tilt({ children, className = "", max = 6 }: { children: ReactNode; className?: string; max?: number }) {
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
