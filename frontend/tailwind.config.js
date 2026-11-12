/** @type {import('tailwindcss').Config} */
// RELAY design system v5 — BRUTALISM.
// Raw and loud: cream paper, pure black, thick 3 px borders on everything, heavy offset shadows, square corners, flat
// blocks of red / blue / green, uppercase Archivo Black headings, monospace labels, structure left visible. No yellow
// anywhere (anything that was yellow is cream / beige / white). The colour names from earlier systems are kept as ROLES so
// every page restyles at once:
//   brand → black (primary)          pink → RED (danger, P1, alerts)          lime → cream (neutral highlight)
//   cobalt → BLUE (info, channels)   mint → GREEN (ok, confirmed)             tangerine → ORANGE (warning)
//   sun → beige (attention — replaces yellow)
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F4EEE2",
        cream: "#EDE4D3",
        bone: "#FFFFFF",
        white: "#FFFFFF",
        ink: "#000000",
        signal: "#FF2D00",
        go: "#00A33A",
        stop: "#E10600",
        blue: "#1F3BFF",
        brand: { 50: "#F2F2F2", 100: "#E6E6E6", 200: "#D0D0D0", 300: "#B5B5B5", 400: "#333333", 500: "#000000", 600: "#FF2D00", 700: "#111111", 800: "#0A0A0A", 900: "#000000" },
        pink: { 200: "#FFD3C9", 300: "#FF9C85", 400: "#FF5A36", 500: "#FF2D00" },
        lime: { 200: "#FFFFFF", 300: "#F8F3E9", 400: "#EDE4D3", 500: "#DCCFB6" },
        tangerine: { 300: "#FFB27F", 400: "#FF7A1F", 500: "#E25B00" },
        cobalt: { 200: "#DDE3FF", 300: "#A9B6FF", 400: "#5A72FF", 500: "#1F3BFF" },
        sun: { 200: "#FBF7EF", 300: "#F1E8D6", 400: "#E6D8BC", 500: "#CDBB98" },
        mint: { 200: "#D4F5DF", 300: "#8FE3AE", 400: "#34C46A", 500: "#00A33A" },
        p1: "#FF2D00", p2: "#FF7A1F", p3: "#E6D8BC", p4: "#1F3BFF",
      },
      fontFamily: {
        display: ["'Archivo Black'", "'Noto Sans Kannada'", "'Noto Sans Devanagari'", "'Noto Sans Malayalam'", "Arial Black", "sans-serif"],
        sans: ["'Space Grotesk'", "'Noto Sans'", "'Noto Sans Kannada'", "'Noto Sans Devanagari'", "'Noto Sans Malayalam'", "'Noto Sans Tamil'", "'Noto Sans Telugu'", "'Noto Sans Bengali'", "system-ui", "sans-serif"],
        serif: ["'Archivo Black'", "Arial Black", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      borderWidth: { DEFAULT: "2px", 2: "3px", 4: "5px" },
      borderRadius: { none: "0", sm: "0", DEFAULT: "0", md: "0", lg: "0", xl: "0", "2xl": "0", "3xl": "0", full: "9999px" },
      boxShadow: {
        hard: "6px 6px 0 0 #000000",
        "hard-sm": "4px 4px 0 0 #000000",
        "hard-lg": "12px 12px 0 0 #000000",
        "hard-pink": "6px 6px 0 0 #FF2D00",
        "hard-lime": "6px 6px 0 0 #000000",
        "hard-violet": "5px 5px 0 0 #1F3BFF",
      },
      keyframes: {
        marquee: { from: { transform: "translateX(0)" }, to: { transform: "translateX(-50%)" } },
        pulsering: { "0%": { transform: "scale(.6)", opacity: ".9" }, "100%": { transform: "scale(2.4)", opacity: "0" } },
      },
      animation: {
        marquee: "marquee 42s linear infinite",
        "marquee-fast": "marquee 20s linear infinite",
        pulsering: "pulsering 1.8s ease-out infinite",
      },
    },
  },
  plugins: [],
};
