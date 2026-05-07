/**
 * src/i18n.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Initialises react-i18next from the central language registry.
 *
 * DO NOT add language-specific imports here.
 * To add a new language, edit src/locales/index.js only.
 */

import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import { LANGUAGES, DEFAULT_LANGUAGE } from "./locales/index";

const resources = Object.fromEntries(
  LANGUAGES.map(({ code, resources }) => [code, { translation: resources }])
);

i18n.use(initReactI18next).init({
  resources,
  lng: localStorage.getItem("language") || DEFAULT_LANGUAGE,
  fallbackLng: DEFAULT_LANGUAGE,
  interpolation: { escapeValue: false },
});

export default i18n;
