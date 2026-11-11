import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./en.json";
import kn from "./kn.json";
import hi from "./hi.json";

export const UI_LANGS = [
  { code: "en", label: "EN" },
  { code: "kn", label: "ಕನ್ನಡ" },
  { code: "hi", label: "हिंदी" },
] as const;

function saved(): string {
  try { return localStorage.getItem("relay.uiLang") || "en"; } catch { return "en"; }
}

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, kn: { translation: kn }, hi: { translation: hi } },
  lng: saved(),
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export function setUiLang(code: string) {
  i18n.changeLanguage(code);
  document.documentElement.lang = code;
  try { localStorage.setItem("relay.uiLang", code); } catch { /* storage unavailable */ }
}

export default i18n;
