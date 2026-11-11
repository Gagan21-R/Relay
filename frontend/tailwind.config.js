/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: { 50: "#f5f1ff", 100: "#ebe3ff", 200: "#d6c8ff", 300: "#b89dff", 400: "#9a6dff", 500: "#7c3aed", 600: "#6a22d6", 700: "#5719b0", 800: "#45168a", 900: "#2e0f5e" },
        ink: "#16112a",
        p1: "#dc2626", p2: "#ea580c", p3: "#ca8a04", p4: "#2563eb",
      },
      fontFamily: { sans: ["Inter", "Noto Sans", "Noto Sans Kannada", "Noto Sans Devanagari", "Noto Sans Malayalam", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
};
