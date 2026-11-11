/** @type {import('tailwindcss').Config} */
// RELAY design system v4 — brutalist · minimal.
// Bone paper, black ink, ONE signal colour (vermilion), green for approve and red for reject, square corners, hard
// offset shadows, a visible grid and monospace structure. The colour names from the earlier system are kept as ROLES so
// every page restyles at once; each role maps to a restrained tone:
//   brand → ink (primary actions)      pink → signal vermilion (danger, P1, alerts)
//   lime → bone highlight / done       sun → sand (waiting, attention)      cobalt → dream lilac (info, maps)
//   tangerine → rust (warning)         mint → sage (ok, confirmed)
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#EFECE6",
        cream: "#E7E3DB",
        bone: "#F6F4EF",
        white: "#F6F4EF",
        ink: "#0B0B0C",
        signal: "#FF3D1F",
        go: "#15803D",
        stop: "#DC2626",
        dusk: { 1: "#C9C3FF", 2: "#F3C8D8", 3: "#FFD9B8" },
        brand: { 50: "#F4F4F4", 100: "#E9E9E9", 200: "#D6D6D6", 300: "#BDBDBD", 400: "#4A4A4A", 500: "#0B0B0C", 600: "#FF3D1F", 700: "#1A1A1A", 800: "#111111", 900: "#000000" },
        pink: { 200: "#FFD6CE", 300: "#FFB3A6", 400: "#FF6B52", 500: "#FF3D1F" },
        lime: { 200: "#F6F4EF", 300: "#F2EFE8", 400: "#E2DED4", 500: "#CFC9BC" },
        tangerine: { 300: "#E9B99A", 400: "#D9895B", 500: "#B85A27" },
        cobalt: { 200: "#E3E0FF", 300: "#C9C3FF", 400: "#8F86F0", 500: "#5A4FD6" },
        sun: { 200: "#F5EDDA", 300: "#EEE2C2", 400: "#E2CF98", 500: "#C9A94C" },
        mint: { 200: "#E1EBE1", 300: "#C7DAC7", 400: "#9FBF9F", 500: "#5F8F64" },
        p1: "#FF3D1F", p2: "#E07A3A", p3: "#C9A94C", p4: "#5A4FD6",
      },
      fontFamily: {
        display: ["'Syne'", "'Noto Sans Kannada'", "'Noto Sans Devanagari'", "'Noto Sans Malayalam'", "system-ui", "sans-serif"],
        sans: ["'Space Grotesk'", "'Noto Sans'", "'Noto Sans Kannada'", "'Noto Sans Devanagari'", "'Noto Sans Malayalam'", "'Noto Sans Tamil'", "'Noto Sans Telugu'", "'Noto Sans Bengali'", "system-ui", "sans-serif"],
        serif: ["'Instrument Serif'", "Georgia", "serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      // brutalism: square everything; only true circles (dots, the moon, the eye) stay round
      borderRadius: { none: "0", sm: "0", DEFAULT: "0", md: "0", lg: "0", xl: "0", "2xl": "0", "3xl": "0", full: "9999px",
        blob: "42% 58% 63% 37% / 41% 44% 56% 59%" },
      boxShadow: {
        hard: "5px 5px 0 0 #0B0B0C",
        "hard-sm": "3px 3px 0 0 #0B0B0C",
        "hard-lg": "10px 10px 0 0 #0B0B0C",
        "hard-pink": "5px 5px 0 0 #FF3D1F",
        "hard-lime": "5px 5px 0 0 #0B0B0C",
        "hard-violet": "4px 4px 0 0 #FF3D1F",
      },
      keyframes: {
        marquee: { from: { transform: "translateX(0)" }, to: { transform: "translateX(-50%)" } },
        floaty: { "0%,100%": { transform: "translateY(0) rotate(0deg)" }, "50%": { transform: "translateY(-16px) rotate(2deg)" } },
        levitate: { "0%,100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-22px)" } },
        wobble: { "0%,100%": { borderRadius: "42% 58% 63% 37% / 41% 44% 56% 59%" }, "50%": { borderRadius: "58% 42% 37% 63% / 56% 59% 41% 44%" } },
        drip: { "0%,100%": { transform: "scaleY(1)" }, "50%": { transform: "scaleY(1.18)" } },
        drift: { from: { transform: "translateX(-10%)" }, to: { transform: "translateX(110%)" } },
        pulsering: { "0%": { transform: "scale(.6)", opacity: ".9" }, "100%": { transform: "scale(2.4)", opacity: "0" } },
        blink: { "0%,92%,100%": { transform: "scaleY(1)" }, "95%": { transform: "scaleY(0.08)" } },
      },
      animation: {
        marquee: "marquee 42s linear infinite",
        "marquee-fast": "marquee 20s linear infinite",
        floaty: "floaty 8s ease-in-out infinite",
        levitate: "levitate 6s ease-in-out infinite",
        wobble: "wobble 11s ease-in-out infinite",
        drip: "drip 5s ease-in-out infinite",
        drift: "drift 60s linear infinite",
        spinslow: "spin 40s linear infinite",
        pulsering: "pulsering 1.8s ease-out infinite",
        blink: "blink 6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
