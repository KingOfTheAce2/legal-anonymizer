// ============================================================================
// Browser Preview Mode Detection
// ============================================================================

const isTauriAvailable = (): boolean => {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
};

// Web server URL for browser mode (Python backend)
const WEB_API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8080";

// Check if web API is available
let webApiAvailable = false;

async function checkWebApi(): Promise<boolean> {
  if (isTauriAvailable()) return false;
  try {
    const response = await fetch(`${WEB_API_URL}/health`, { method: "GET" });
    webApiAvailable = response.ok;
    return webApiAvailable;
  } catch {
    webApiAvailable = false;
    return false;
  }
}

// Dynamic imports for Tauri APIs (only when available)
let tauriInvoke: typeof import("@tauri-apps/api/core").invoke | null = null;
let tauriOpen: typeof import("@tauri-apps/plugin-dialog").open | null = null;

async function loadTauriApis() {
  if (isTauriAvailable()) {
    try {
      const core = await import("@tauri-apps/api/core");
      const dialog = await import("@tauri-apps/plugin-dialog");
      tauriInvoke = core.invoke;
      tauriOpen = dialog.open;
    } catch {
      console.warn("Tauri APIs not available, running in browser preview mode");
    }
  }
}

// Single initialization promise — prevents race conditions when callers
// read webApiAvailable or tauriInvoke before the async checks complete.
let _initPromise: Promise<void> | null = null;

function ensureInitialized(): Promise<void> {
  if (!_initPromise) {
    _initPromise = Promise.all([checkWebApi(), loadTauriApis()]).then(() => {});
  }
  return _initPromise;
}

// ============================================================================
// Types
// ============================================================================

export type Layer = 1 | 2 | 3;

export type UncertaintyPolicy = "mask" | "redact" | "leave_intact" | "flag_only";
export type PseudonymStyle = "neutral" | "realistic";
export type LanguageMode = "auto" | "fixed";

export type Preset = {
  preset_id: string;
  name: string;
  layer: Layer;
  minimum_confidence: number;
  uncertainty_policy: UncertaintyPolicy;
  pseudonym_style: PseudonymStyle;
  language_mode: LanguageMode;
  language?: string;
  entities_enabled: Record<string, boolean>;
  whitelist?: string[];
  blacklist?: string[];
  language_whitelists?: Record<string, string[]>;
  language_blacklists?: Record<string, string[]>;
};

// ============================================================================
// Default Language-Specific Whitelists (Common False Positives)
// ============================================================================

export const DEFAULT_LANGUAGE_WHITELISTS: Record<string, string[]> = {
  // Dutch - common words that get falsely flagged
  nl: [
    "terwijl",      // while
    "tijdens",      // during
    "echter",       // however
    "daarom",       // therefore
    "hierbij",      // hereby
    "tevens",       // also
    "namelijk",     // namely
    "derhalve",     // therefore
    "aangezien",    // since
    "mits",         // provided that
    "tenzij",       // unless
    "overeenkomstig", // in accordance with
    "ingevolge",    // pursuant to
    "krachtens",    // by virtue of
    "betreffende",  // concerning
    "inzake",       // regarding
    "alsook",       // as well as
    "alsmede",      // and also
    "dientengevolge", // consequently
    "desalniettemin", // nevertheless
  ],
  // German - common legal/formal words
  de: [
    "gemäß",        // according to
    "hinsichtlich", // regarding
    "bezüglich",    // concerning
    "aufgrund",     // due to
    "infolge",      // as a result of
    "demzufolge",   // consequently
    "diesbezüglich", // in this regard
    "ferner",       // furthermore
    "somit",        // thus
    "hiermit",      // hereby
    "dahingehend",  // to that effect
    "insbesondere", // in particular
    "gegebenenfalls", // if applicable
    "beziehungsweise", // respectively
  ],
  // French - common legal/formal words
  fr: [
    "conformément", // in accordance with
    "notamment",    // in particular
    "néanmoins",    // nevertheless
    "toutefois",    // however
    "ainsi",        // thus
    "également",    // also
    "préalablement", // beforehand
    "ultérieurement", // subsequently
    "dorénavant",   // henceforth
    "nonobstant",   // notwithstanding
    "susmentionné", // above-mentioned
    "ci-dessus",    // above
    "ci-après",     // below/hereafter
  ],
  // Spanish - common legal/formal words
  es: [
    "conforme",     // in accordance with
    "mediante",     // by means of
    "asimismo",     // likewise
    "igualmente",   // equally
    "posteriormente", // subsequently
    "previamente",  // previously
    "actualmente",  // currently
    "respectivamente", // respectively
    "consecuentemente", // consequently
  ],
  // Italian - common legal/formal words
  it: [
    "pertanto",     // therefore
    "tuttavia",     // however
    "altresì",      // also
    "ovvero",       // or rather
    "nonché",       // as well as
    "qualora",      // in case
    "laddove",      // where/whereas
    "giacché",      // since
    "affinché",     // so that
  ],
  // English - common false positives
  en: [
    "whereas",      // legal preamble word
    "hereinafter",  // legal term
    "aforementioned", // legal term
    "notwithstanding", // legal term
    "hereunder",    // legal term
    "hereto",       // legal term
    "thereof",      // legal term
    "whereby",      // legal term
  ],
  // Bulgarian - common legal/formal words
  bg: [
    "настоящото",   // herewith/this
    "съгласно",     // according to
    "съответно",    // accordingly
    "доколкото",    // insofar as
    "независимо",   // regardless
    "вследствие",   // as a result
    "въпреки",      // despite
    "следователно", // therefore
    "предвид",      // in view of
    "относно",      // regarding
  ],
  // Croatian - common legal/formal words
  hr: [
    "sukladno",     // in accordance with
    "temeljem",     // based on
    "navedeno",     // stated/mentioned
    "naime",        // namely
    "međutim",      // however
    "dakle",        // therefore
    "odnosno",      // i.e./or rather
    "stoga",        // therefore
    "budući",       // since/as
    "vezano",       // related to
  ],
  // Czech - common legal/formal words
  cs: [
    "přičemž",      // whereas/while
    "avšak",        // however
    "neboť",        // because
    "ačkoli",       // although
    "nicméně",      // nevertheless
    "tudíž",        // therefore
    "jakožto",      // as/in the capacity of
    "vyjma",        // except
    "přestože",     // even though
    "ohledně",      // regarding
  ],
  // Danish - common legal/formal words
  da: [
    "herunder",     // including/hereunder
    "henholdsvis",  // respectively
    "tillige",      // also/in addition
    "ligeledes",    // likewise
    "idet",         // as/since
    "hvorfor",      // therefore/why
    "således",      // thus/so
    "dermed",       // thereby
    "endvidere",    // furthermore
    "hvorimod",     // whereas/whereas
  ],
  // Estonian - common legal/formal words
  et: [
    "vastavalt",    // according to
    "käesolev",     // present/this
    "sealhulgas",   // including
    "ühtlasi",      // also/simultaneously
    "seetõttu",     // therefore
    "nimelt",       // namely
    "siiski",       // however
    "järelikult",   // consequently
    "kuivõrd",      // insofar as
    "arvestades",   // considering
  ],
  // Finnish - common legal/formal words
  fi: [
    "mikäli",       // if/insofar as
    "siten",        // thus
    "lisäksi",      // in addition
    "kuitenkin",    // however
    "vaikka",       // although
    "jolloin",      // whereupon
    "koska",        // because
    "siinä",        // therein
    "noudattaen",   // in accordance with
    "edellyttäen",  // provided that
  ],
  // Greek - common legal/formal words
  el: [
    "εφόσον",       // provided that
    "πλην",         // however/except
    "ωσαύτως",      // likewise
    "εντούτοις",    // nevertheless
    "ήτοι",         // namely/i.e.
    "ιδίως",        // in particular
    "αντιστοίχως",  // respectively
    "δυνάμει",      // by virtue of
    "κατόπιν",      // following/after
    "εκτός",        // except/unless
  ],
  // Hungarian - common legal/formal words
  hu: [
    "amennyiben",   // insofar as/if
    "azonban",      // however
    "emellett",     // moreover
    "ezáltal",      // thereby
    "következésképpen", // consequently
    "illetve",      // respectively/or
    "tekintettel",  // considering
    "figyelemmel",  // in view of
    "egyebekben",   // otherwise/in other respects
    "mindazonáltal", // nevertheless
  ],
  // Irish - common legal/formal words
  ga: [
    "dá bhrí sin",  // therefore
    "áfach",        // however
    "ina theannta", // in addition
    "faoi réir",    // subject to
    "de réir",      // according to
    "i gcomhréir",  // in accordance with
    "maidir le",    // regarding
    "chomh maith",  // also/as well
  ],
  // Latvian - common legal/formal words
  lv: [
    "atbilstoši",   // accordingly
    "turklāt",      // moreover
    "tomēr",        // however
    "tādēļ",        // therefore
    "proti",        // namely
    "savukārt",     // on the other hand
    "ievērojot",    // considering
    "saskaņā",      // in accordance with
    "tostarp",      // including
    "neatkarīgi",   // regardless
  ],
  // Lithuanian - common legal/formal words
  lt: [
    "atsižvelgiant", // considering
    "tačiau",       // however
    "todėl",        // therefore
    "taigi",        // thus
    "būtent",       // namely
    "laikantis",    // in accordance with
    "vadovaujantis", // pursuant to
    "nepaisant",    // notwithstanding
    "kaip antai",   // such as
    "be to",        // moreover
  ],
  // Maltese - common legal/formal words
  mt: [
    "madankollu",   // however
    "sabiex",       // in order to
    "skont",        // according to
    "minkejja",     // notwithstanding
    "peress li",    // since/whereas
    "b'hekk",       // thus
    "barra minn hekk", // moreover
    "f'konformità", // in conformity with
    "fl-istess waqt", // at the same time
  ],
  // Romanian - common legal/formal words
  ro: [
    "întrucât",     // whereas
    "astfel",       // thus
    "totodată",     // also/simultaneously
    "totuși",       // however
    "prin urmare",  // therefore
    "în temeiul",   // pursuant to
    "respectiv",    // respectively
    "deoarece",     // because
    "potrivit",     // according to
    "referitor",    // regarding
  ],
  // Slovak - common legal/formal words
  sk: [
    "pritom",       // while/at the same time
    "avšak",        // however
    "teda",         // therefore
    "totiž",        // namely
    "hoci",         // although
    "pričom",       // whereas
    "napriek",      // despite
    "podľa",        // according to
    "vzhľadom",     // considering
    "okrem",        // except/besides
  ],
  // Slovenian - common legal/formal words
  sl: [
    "skladno",      // in accordance with
    "vendar",       // however
    "zato",         // therefore
    "namreč",       // namely
    "kljub",        // despite
    "torej",        // thus
    "obenem",       // simultaneously
    "glede na",     // considering
    "v skladu",     // in accordance
    "razen",        // except
  ],
  // Swedish - common legal/formal words
  sv: [
    "varigenom",    // whereby
    "emellertid",   // however
    "däremot",      // on the other hand
    "härutöver",    // moreover/in addition
    "dessutom",     // furthermore
    "enligt",       // according to
    "likväl",       // nevertheless
    "varför",       // therefore/why
    "varvid",       // whereupon
    "oaktat",       // notwithstanding
  ],
};

/** A single PII finding with position information for highlighting */
export type FindingItem = {
  entity_type: string;
  detected_text: string;
  start: number | null;
  end: number | null;
  confidence: number;
  action: string;
  pseudonym: string;
};

export type AnalyzeTextResponse = {
  run_id: string;
  run_folder: string;
  redacted_text: string;
  summary: Record<string, number>;
  findings_count: number;
  language: string;
  findings?: FindingItem[];
};

export type AnalyzeFileResponse = {
  run_id: string;
  run_folder: string;
  output_path: string;
  summary: Record<string, number>;
  findings_count: number;
};

// ============================================================================
// Browser Preview Mode - Mock Implementation
// ============================================================================

/** Helper to find all regex matches with positions */
function findAllMatches(text: string, pattern: RegExp, entityType: string, confidence: number, action: string): FindingItem[] {
  const findings: FindingItem[] = [];
  let match;
  const regex = new RegExp(pattern.source, 'g');
  while ((match = regex.exec(text)) !== null) {
    findings.push({
      entity_type: entityType,
      detected_text: match[0],
      start: match.index,
      end: match.index + match[0].length,
      confidence,
      action,
      pseudonym: "",
    });
  }
  return findings;
}

function mockAnalyzeText(text: string, preset: Preset): AnalyzeTextResponse {
  // Simple regex-based mock anonymization for browser preview
  const summary: Record<string, number> = {};
  const allFindings: FindingItem[] = [];

  // Email pattern
  const emailPattern = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g;
  if (preset.entities_enabled.EMAIL !== false) {
    const emailFindings = findAllMatches(text, emailPattern, "EMAIL", 95, "redact");
    allFindings.push(...emailFindings);
    if (emailFindings.length > 0) summary["EMAIL"] = emailFindings.length;
  }

  // Phone pattern (international)
  const phonePattern = /\+\d{1,4}[\s.-]?\d{1,4}[\s.-]?\d{1,9}/g;
  if (preset.entities_enabled.PHONE_NUMBER !== false) {
    const phoneFindings = findAllMatches(text, phonePattern, "PHONE_NUMBER", 90, "redact");
    allFindings.push(...phoneFindings);
    if (phoneFindings.length > 0) summary["PHONE_NUMBER"] = phoneFindings.length;
  }

  // IBAN pattern
  const ibanPattern = /\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b/g;
  if (preset.entities_enabled.BANK_ACCOUNT !== false) {
    const ibanFindings = findAllMatches(text, ibanPattern, "BANK_ACCOUNT", 95, "redact");
    allFindings.push(...ibanFindings);
    if (ibanFindings.length > 0) summary["BANK_ACCOUNT"] = ibanFindings.length;
  }

  // Credit card pattern
  const ccPattern = /\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6011)[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g;
  if (preset.entities_enabled.CREDIT_CARD !== false) {
    const ccFindings = findAllMatches(text, ccPattern, "CREDIT_CARD", 95, "redact");
    allFindings.push(...ccFindings);
    if (ccFindings.length > 0) summary["CREDIT_CARD"] = ccFindings.length;
  }

  // Simple name pattern (Title Case words with prefix)
  const namePattern = /\b(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b/g;
  if (preset.entities_enabled.PERSON !== false) {
    const nameFindings = findAllMatches(text, namePattern, "PERSON", 90, "pseudonymise");
    allFindings.push(...nameFindings);
    if (nameFindings.length > 0) summary["PERSON"] = (summary["PERSON"] || 0) + nameFindings.length;
  }

  // Standalone names (John Smith pattern) - with filtering
  const standaloneNamePattern = /\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b/g;
  if (preset.entities_enabled.PERSON !== false) {
    const commonWords = ["The", "This", "That", "These", "Those", "Medical", "Center", "Legal", "Amsterdam", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    let match;
    while ((match = standaloneNamePattern.exec(text)) !== null) {
      const parts = match[0].split(" ");
      if (!commonWords.includes(parts[0]) && !commonWords.includes(parts[1])) {
        // Check if this overlaps with an existing finding
        const overlaps = allFindings.some(f =>
          f.start !== null && f.end !== null &&
          !(match!.index + match![0].length <= f.start || match!.index >= f.end)
        );
        if (!overlaps) {
          allFindings.push({
            entity_type: "PERSON",
            detected_text: match[0],
            start: match.index,
            end: match.index + match[0].length,
            confidence: 75,
            action: "pseudonymise",
            pseudonym: "",
          });
          summary["PERSON"] = (summary["PERSON"] || 0) + 1;
        }
      }
    }
  }

  // Date pattern
  const datePattern = /\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b/g;
  if (preset.entities_enabled.DATE !== false) {
    const dateFindings = findAllMatches(text, datePattern, "DATE", 85, "redact");
    allFindings.push(...dateFindings);
    if (dateFindings.length > 0) summary["DATE"] = dateFindings.length;
  }

  // Sort findings by position
  allFindings.sort((a, b) => (a.start ?? 0) - (b.start ?? 0));

  // Build redacted text by applying replacements in reverse order
  let redacted = text;
  const sortedByPosDesc = [...allFindings].sort((a, b) => (b.start ?? 0) - (a.start ?? 0));
  for (const f of sortedByPosDesc) {
    if (f.start !== null && f.end !== null) {
      const replacement = f.action === "redact"
        ? "█".repeat(f.end - f.start)
        : `[${f.entity_type}_REDACTED]`;
      redacted = redacted.slice(0, f.start) + replacement + redacted.slice(f.end);
    }
  }

  const findingsCount = Object.values(summary).reduce((a, b) => a + b, 0);

  return {
    run_id: `PREVIEW_${Date.now()}`,
    run_folder: "(Browser Preview Mode)",
    redacted_text: redacted,
    summary,
    findings_count: findingsCount,
    language: preset.language || "auto-detected",
    findings: allFindings,
  };
}

// ============================================================================
// API Functions
// ============================================================================

export async function analyzeText(
  text: string,
  preset: Preset,
  _modelPath?: string
): Promise<AnalyzeTextResponse> {
  await ensureInitialized();
  // Desktop mode - use Tauri
  if (isTauriAvailable() && tauriInvoke) {
    return await tauriInvoke<AnalyzeTextResponse>("analyze_text", {
      text,
      preset,
    });
  }

  // Web mode - try Python backend first
  if (webApiAvailable || (await checkWebApi())) {
    try {
      const response = await fetch(`${WEB_API_URL}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, preset }),
      });

      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.warn("Web API call failed, falling back to mock:", error);
    }
  }

  // Fallback to browser preview mock
  return mockAnalyzeText(text, preset);
}

export async function analyzeFile(
  inputPath: string,
  preset: Preset
): Promise<AnalyzeFileResponse> {
  await ensureInitialized();
  if (!isTauriAvailable() || !tauriInvoke) {
    throw new Error("File analysis requires the desktop app. Please run with 'npm run tauri dev'.");
  }

  return await tauriInvoke<AnalyzeFileResponse>("analyze_file", {
    inputPath,
    preset,
  });
}

export async function selectFile(): Promise<string | null> {
  if (!isTauriAvailable() || !tauriOpen) {
    throw new Error("File selection requires the desktop app. Please run with 'npm run tauri dev'.");
  }

  const selected = await tauriOpen({
    multiple: false,
    filters: [
      {
        name: "Documents",
        extensions: ["docx", "pdf", "txt"],
      },
    ],
  });

  if (typeof selected === "string") {
    return selected;
  }
  return null;
}

export async function selectFiles(): Promise<string[]> {
  if (!isTauriAvailable() || !tauriOpen) {
    throw new Error("File selection requires the desktop app.");
  }

  const selected = await tauriOpen({
    multiple: true,
    filters: [
      {
        name: "Documents",
        extensions: ["docx", "pdf", "txt"],
      },
    ],
  });

  if (Array.isArray(selected)) {
    return selected;
  }
  if (typeof selected === "string") {
    return [selected];
  }
  return [];
}

export function isDesktopApp(): boolean {
  return isTauriAvailable();
}

/**
 * Invoke a Tauri backend command. Waits for initialization to complete so
 * callers do not need to import @tauri-apps/api/core directly.
 */
export async function invokeBackend<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  await ensureInitialized();
  if (!tauriInvoke) {
    throw new Error(`Cannot invoke "${cmd}": Tauri is not available in this environment.`);
  }
  return tauriInvoke<T>(cmd, args);
}

export async function uninstallModel(modelType: string, modelId: string): Promise<{ status: string; model_id: string }> {
  await ensureInitialized();
  if (!isTauriAvailable() || !tauriInvoke) {
    throw new Error("Model management requires the desktop app.");
  }
  return tauriInvoke<{ status: string; model_id: string }>("uninstall_model", {
    modelType,
    modelId,
  });
}

export type DiskUsage = {
  spacy_models_bytes: number;
  hf_cache_bytes: number;
  spacy_models_path: string;
  hf_cache_path: string;
};

export async function getDiskUsage(): Promise<DiskUsage> {
  await ensureInitialized();
  if (!isTauriAvailable() || !tauriInvoke) {
    return { spacy_models_bytes: 0, hf_cache_bytes: 0, spacy_models_path: "", hf_cache_path: "" };
  }
  return tauriInvoke<DiskUsage>("get_disk_usage");
}

export function isWebApiAvailable(): boolean {
  return webApiAvailable;
}

export async function checkWebApiStatus(): Promise<boolean> {
  return await checkWebApi();
}

export function getApiMode(): "desktop" | "web" | "preview" {
  if (isTauriAvailable()) return "desktop";
  if (webApiAvailable) return "web";
  return "preview";
}

/**
 * Open the desktop app's local web server (http://localhost:1422) in the
 * system default browser. Only works in desktop (Tauri) mode.
 */
export async function openInBrowser(): Promise<void> {
  await ensureInitialized();
  if (isTauriAvailable()) {
    await invokeBackend<void>("open_in_browser");
  }
}

// ============================================================================
// Supported Languages
// ============================================================================

export const SUPPORTED_LANGUAGES = [
  { code: "auto", name: "Auto-detect" },
  // EU official languages (alphabetical by English name)
  { code: "bg", name: "Bulgarian (Български)" },
  { code: "hr", name: "Croatian (Hrvatski)" },
  { code: "cs", name: "Czech (Čeština)" },
  { code: "da", name: "Danish (Dansk)" },
  { code: "nl", name: "Dutch (Nederlands)" },
  { code: "en", name: "English" },
  { code: "et", name: "Estonian (Eesti)" },
  { code: "fi", name: "Finnish (Suomi)" },
  { code: "fr", name: "French (Français)" },
  { code: "de", name: "German (Deutsch)" },
  { code: "el", name: "Greek (Ελληνικά)" },
  { code: "hu", name: "Hungarian (Magyar)" },
  { code: "ga", name: "Irish (Gaeilge)" },
  { code: "it", name: "Italian (Italiano)" },
  { code: "lv", name: "Latvian (Latviešu)" },
  { code: "lt", name: "Lithuanian (Lietuvių)" },
  { code: "mt", name: "Maltese (Malti)" },
  { code: "pl", name: "Polish (Polski)" },
  { code: "pt", name: "Portuguese (Português)" },
  { code: "ro", name: "Romanian (Română)" },
  { code: "sk", name: "Slovak (Slovenčina)" },
  { code: "sl", name: "Slovenian (Slovenščina)" },
  { code: "es", name: "Spanish (Español)" },
  { code: "sv", name: "Swedish (Svenska)" },
  // Additional languages
  { code: "ru", name: "Russian (Русский)" },
  { code: "zh", name: "Chinese (中文)" },
  { code: "ja", name: "Japanese (日本語)" },
  { code: "ko", name: "Korean (한국어)" },
  { code: "ar", name: "Arabic (العربية)" },
];

// ============================================================================
// Default Entities
// ============================================================================

export const DEFAULT_ENTITIES: Record<string, boolean> = {
  NATIONAL_ID: true,
  PASSPORT_NUMBER: true,
  MEDICAL_ID: true,
  BANK_ACCOUNT: true,
  CREDIT_CARD: true,
  PERSON: true,
  DATE_OF_BIRTH: true,
  EMAIL: true,
  PHONE_NUMBER: true,
  VEHICLE_ID: true,
  ADDRESS: true,
  IP_ADDRESS: true,
  ORGANIZATION: true,
  LOCATION: true,
  ACCOUNT_USERNAME: true,
  DATE: false, // Optional by default
  MONEY: false, // Optional by default
  URL: false, // Optional by default
};

// ============================================================================
// Preset Templates with Better Confidence Levels
// ============================================================================

export const PRESET_LAYER1_FAST: Preset = {
  preset_id: "layer1_fast_legal_scrub",
  name: "Layer 1: Fast Scrub (spaCy)",
  layer: 1,
  minimum_confidence: 75, // Increased from 60
  uncertainty_policy: "mask",
  pseudonym_style: "neutral",
  language_mode: "auto",
  entities_enabled: { ...DEFAULT_ENTITIES },
};

export const PRESET_LAYER2_ACCURATE: Preset = {
  preset_id: "layer2_accurate_legal_review",
  name: "Layer 2: Accurate (Transformers)",
  layer: 2,
  minimum_confidence: 85, // Increased from 70
  uncertainty_policy: "mask",
  pseudonym_style: "neutral",
  language_mode: "auto",
  entities_enabled: { ...DEFAULT_ENTITIES },
};

export const PRESET_LAYER3_REGULATORY: Preset = {
  preset_id: "layer3_regulatory_standard",
  name: "Layer 3: Regulatory (Presidio)",
  layer: 3,
  minimum_confidence: 90, // Increased from 80
  uncertainty_policy: "redact",
  pseudonym_style: "neutral",
  language_mode: "auto",
  entities_enabled: { ...DEFAULT_ENTITIES },
};

export const ALL_PRESETS: Preset[] = [
  PRESET_LAYER1_FAST,
  PRESET_LAYER2_ACCURATE,
  PRESET_LAYER3_REGULATORY,
];

// ============================================================================
// Confidence Level Explanations
// ============================================================================

export const CONFIDENCE_INFO = {
  description: `Confidence score indicates how certain the system is that detected text is actually PII.

• 90-100%: Very high confidence - Almost certainly PII (e.g., valid IBAN with checksum)
• 80-89%: High confidence - Very likely PII (e.g., email with valid format)
• 70-79%: Medium confidence - Probably PII but needs context
• 60-69%: Low confidence - Might be PII, human review recommended
• Below 60%: Very low confidence - High false positive risk`,

  thresholdGuide: `Recommended minimum confidence by use case:

• 90%+ : Regulatory filings, court submissions (minimize false positives)
• 85%  : Standard legal review (good balance)
• 75%  : Initial document screening (catch more, accept some false positives)
• 70%  : Maximum recall mode (review all flagged items manually)`,
};
