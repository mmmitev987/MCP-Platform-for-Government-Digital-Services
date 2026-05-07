/**
 * src/locales/index.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Single source of truth for supported languages.
 *
 * TO ADD A NEW LANGUAGE — edit ONLY this file:
 *   1. Create  src/locales/<code>.json  with all translation keys.
 *   2. Add one import line below.
 *   3. Add one entry to LANGUAGES with { code, label, resources }.
 *
 * Nothing else needs to change — i18n.js and Settings.js read from here
 * automatically.
 *
 * Field reference:
 *   code      BCP-47 language code stored in the database (e.g. "en", "mk", "sq")
 *   label     Native name shown in the Settings UI (e.g. "English", "Shqip")
 *   resources The imported JSON translation file
 */

import en from "./en.json";
import mk from "./mk.json";

export const LANGUAGES = [
  { code: "en", label: "English",    resources: en },
  { code: "mk", label: "Македонски", resources: mk },
];

/** Fallback used when no language preference is stored. */
export const DEFAULT_LANGUAGE = "en";
