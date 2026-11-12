/** @type {import('tailwindcss').Config} */
// RELAY design system v6 — brutalism in a light, warm palette.
// Structure stays brutalist (thick black borders, hard shadows, square corners, uppercase Archivo Black, monospace
// labels) but every FILL is a light tone that belongs to the cream background: sand, beige, taupe, stone, pale clay and
// pale sage. No bright red, blue or green, and no yellow. Black is used only for text, borders and shadows.
// The colour names from earlier systems are kept as ROLES so every page restyles at once:
//   brand → greys / warm brown text     pink → pale clay (danger, P1, alerts)     lime → cream (neutral highlight)
//   cobalt → stone (info, channels)     mint → pale sage (ok, confirmed)          tangerine → peach (warning)
//   sun → beige (attention)             signal → clay accent   go → sage (approve)   stop → clay rose (reject)
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F4EEE2",
        cream: "#EDE4D3",
        bone: "#FBF8F2",
        white: "#FBF8F2",
        sand: "#E6DCC8",
        taupe: "#D6C7AE",
        stone: "#DDD6CA",
        ink: "#141210",
        signal: "#DFA58E",
        go: "#CADDBB",
        stop: "#EDC0B1",
        blue: "#DCD5C8",
        brand: { 50: "#F7F3EC", 100: "#EFE8DC", 200: "#E4DACA", 300: "#D6C7AE", 400: "#8C7A62", 500: "#E6DCC8", 600: "#8A5F46", 700: "#5C4A39", 800: "#3B3128", 900: "#141210" },
        pink: { 200: "#F6E4DC", 300: "#EFD0C3", 400: "#E8BEAD", 500: "#B9775D" },
        lime: { 200: "#FBF8F2", 300: "#F6F0E5", 400: "#EDE4D3", 500: "#DFD3BC" },
        tangerine: { 300: "#F3DCC8", 400: "#EAC6A6", 500: "#C98F66" },
        cobalt: { 200: "#F0ECE5", 300: "#E3DDD2", 400: "#D1C8B9", 500: "#9C8F7B" },
        sun: { 200: "#FBF7EF", 300: "#F3EBDB", 400: "#E8DCC4", 500: "#CDBB98" },
        mint: { 200: "#E8EFE0", 300: "#D7E3CA", 400: "#C2D4B1", 500: "#8DAA7A" },
        p1: "#E6A994", p2: "#EDC9A9", p3: "#E8DCC4", p4: "#D5CDC0",
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
        hard: "6px 6px 0 0 #141210",
        "hard-sm": "4px 4px 0 0 #141210",
        "hard-lg": "10px 10px 0 0 #141210",
        "hard-pink": "6px 6px 0 0 #141210",
        "hard-lime": "6px 6px 0 0 #141210",
        "hard-violet": "5px 5px 0 0 #8C7A62",
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
