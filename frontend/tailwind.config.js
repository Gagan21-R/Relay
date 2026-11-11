/** @type {import('tailwindcss').Config} */
// RELAY maximalist system: warm paper, ink outlines, hard offset shadows, RELAY purple + loud accents.
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#FFF7EC",
        cream: "#FFEFD9",
        ink: "#150A2E",
        brand: { 50: "#F4EEFF", 100: "#E9DDFF", 200: "#D4BCFF", 300: "#B68CFF", 400: "#9A5CFF", 500: "#7C3AED", 600: "#6A22D6", 700: "#5718B3", 800: "#40108A", 900: "#2A0A5C" },
        pink: { 300: "#FF9BC6", 400: "#FF5FA2", 500: "#FF2E86" },
        lime: { 300: "#E4FF8A", 400: "#C8FF2E", 500: "#A6E000" },
        tangerine: { 300: "#FFB27A", 400: "#FF8A3D", 500: "#FF6A00" },
        cobalt: { 300: "#9DB2FF", 400: "#5B7BFF", 500: "#2E5BFF" },
        sun: { 300: "#FFE58A", 400: "#FFD23F", 500: "#F5B800" },
        mint: { 300: "#9EF0D0", 400: "#4FE0AE", 500: "#14C48A" },
        p1: "#E11D48", p2: "#F97316", p3: "#EAB308", p4: "#3B82F6",
      },
      fontFamily: {
        display: ["'Bricolage Grotesque'", "'Noto Sans Kannada'", "'Noto Sans Devanagari'", "'Noto Sans Malayalam'", "system-ui", "sans-serif"],
        sans: ["'Bricolage Grotesque'", "'Noto Sans'", "'Noto Sans Kannada'", "'Noto Sans Devanagari'", "'Noto Sans Malayalam'", "'Noto Sans Tamil'", "'Noto Sans Telugu'", "'Noto Sans Bengali'", "system-ui", "sans-serif"],
        serif: ["'Instrument Serif'", "Georgia", "serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        hard: "4px 4px 0 0 #150A2E",
        "hard-sm": "2px 2px 0 0 #150A2E",
        "hard-lg": "8px 8px 0 0 #150A2E",
        "hard-pink": "5px 5px 0 0 #FF2E86",
        "hard-lime": "5px 5px 0 0 #A6E000",
        "hard-violet": "5px 5px 0 0 #7C3AED",
      },
      borderRadius: { blob: "42% 58% 63% 37% / 41% 44% 56% 59%" },
      keyframes: {
        marquee: { from: { transform: "translateX(0)" }, to: { transform: "translateX(-50%)" } },
        floaty: { "0%,100%": { transform: "translateY(0) rotate(0deg)" }, "50%": { transform: "translateY(-14px) rotate(4deg)" } },
        wobble: { "0%,100%": { borderRadius: "42% 58% 63% 37% / 41% 44% 56% 59%" }, "50%": { borderRadius: "58% 42% 37% 63% / 56% 59% 41% 44%" } },
        pulsering: { "0%": { transform: "scale(.6)", opacity: ".9" }, "100%": { transform: "scale(2.4)", opacity: "0" } },
      },
      animation: {
        marquee: "marquee 38s linear infinite",
        "marquee-fast": "marquee 18s linear infinite",
        floaty: "floaty 7s ease-in-out infinite",
        wobble: "wobble 9s ease-in-out infinite",
        spinslow: "spin 24s linear infinite",
        pulsering: "pulsering 1.8s ease-out infinite",
      },
    },
  },
  plugins: [],
};
