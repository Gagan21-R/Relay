// Motion for the brutalist agency UI: hard, snappy movement (short distances, quick springs, no blur or float).
// Sections slide in once as they scroll into view, lists stagger, numbers count, headlines rise word by word, and the
// status ticker scrolls. Everything respects prefers-reduced-motion.
import { ReactNode, useEffect, useRef, useState } from "react";
import { animate, motion, useInView, useReducedMotion, useScroll, useSpring } from "framer-motion";

const SNAP = [0.2, 0.9, 0.25, 1] as const;

/** Slides its children up into place the first time they scroll into view. */
export function Reveal({ children, delay = 0, y = 28, className = "" }: { children: ReactNode; delay?: number; y?: number; className?: string }) {
  const reduce = useReducedMotion();
  return (
    <motion.div className={className} initial={reduce ? false : { opacity: 0, y }} whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.05 }} transition={{ duration: 0.45, delay, ease: SNAP }}>
      {children}
    </motion.div>
  );
}

/** A container whose <Item> children arrive one after another. */
export function Stagger({ children, className = "", gap = 0.07 }: { children: ReactNode; className?: string; gap?: number }) {
  const reduce = useReducedMotion();
  return (
    <motion.div className={className} initial={reduce ? false : "hidden"} whileInView="show" viewport={{ once: true, amount: 0.05 }}
      variants={{ hidden: {}, show: { transition: { staggerChildren: gap } } }}>
      {children}
    </motion.div>
  );
}
export function Item({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <motion.div className={className} variants={{ hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: SNAP } } }}>
      {children}
    </motion.div>
  );
}

/** A headline whose words rise out of a clipping mask one after another (words never break mid-word). */
export function RiseText({ text, className = "", delay = 0 }: { text: string; className?: string; delay?: number }) {
  const reduce = useReducedMotion();
  const words = text.split(" ");
  return (
    <span className={className} aria-label={text}>
      {words.map((w, i) => (
        <span key={i} className="inline-block overflow-hidden pb-[0.06em] align-bottom" aria-hidden>
          <motion.span className="inline-block" initial={reduce ? false : { y: "105%" }} animate={{ y: 0 }}
            transition={{ duration: 0.55, delay: delay + i * 0.06, ease: SNAP }}>{w}</motion.span>
          {i < words.length - 1 ? " " : ""}
        </span>
      ))}
    </span>
  );
}

/** Cycles through words, sliding each new one up from below. */
export function WordCycle({ words, className = "", every = 1800 }: { words: string[]; className?: string; every?: number }) {
  const [i, setI] = useState(0);
  const reduce = useReducedMotion();
  useEffect(() => {
    if (reduce) return;
    const t = setInterval(() => setI((x) => (x + 1) % words.length), every);
    return () => clearInterval(t);
  }, [words.length, every, reduce]);
  return (
    <span className={`relative inline-grid overflow-hidden align-bottom ${className}`}>
      <motion.span key={i} className="inline-block whitespace-nowrap" initial={{ y: "100%" }} animate={{ y: 0 }} transition={{ duration: 0.4, ease: SNAP }}>
        {words[i]}
      </motion.span>
    </span>
  );
}

/** A hard bar across the top of the page that fills as you scroll. */
export function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 300, damping: 40 });
  return <motion.div className="fixed left-0 right-0 top-0 z-[1300] h-[5px] origin-left border-b border-ink bg-taupe" style={{ scaleX }} aria-hidden />;
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

/** A number that counts up to its value when it first appears, and to each new value after that. */
export function CountUp({ value, decimals = 0, className = "" }: { value: number; decimals?: number; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const reduce = useReducedMotion();
  const from = useRef(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (reduce) { el.textContent = value.toFixed(decimals); from.current = value; return; }
    if (!inView) return;
    const ctl = animate(from.current, value, { duration: 0.9, ease: SNAP, onUpdate: (v) => { el.textContent = v.toFixed(decimals); } });
    from.current = value;
    return () => ctl.stop();
  }, [value, decimals, inView, reduce]);
  return <span ref={ref} className={className}>{(reduce ? value : 0).toFixed(decimals)}</span>;
}
