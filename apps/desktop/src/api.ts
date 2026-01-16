// ============================================================================
// Browser Preview Mode Detection
// ============================================================================

const isTauriAvailable = (): boolean => {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
};

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

// Initialize on module load
loadTauriApis();

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
};

export type AnalyzeTextResponse = {
  run_id: string;
  run_folder: string;
  redacted_text: string;
  summary: Record<string, number>;
  findings_count: number;
  language: string;
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

function mockAnalyzeText(text: string, preset: Preset): AnalyzeTextResponse {
  // Simple regex-based mock anonymization for browser preview
  let redacted = text;
  const summary: Record<string, number> = {};

  // Email pattern
  const emailMatches = text.match(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g);
  if (emailMatches) {
    summary["EMAIL"] = emailMatches.length;
    redacted = redacted.replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g, "[EMAIL_REDACTED]");
  }

  // Phone pattern (international)
  const phoneMatches = text.match(/\+\d{1,4}[\s.-]?\d{1,4}[\s.-]?\d{1,9}/g);
  if (phoneMatches) {
    summary["PHONE_NUMBER"] = phoneMatches.length;
    redacted = redacted.replace(/\+\d{1,4}[\s.-]?\d{1,4}[\s.-]?\d{1,9}/g, "[PHONE_REDACTED]");
  }

  // IBAN pattern
  const ibanMatches = text.match(/\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b/g);
  if (ibanMatches) {
    summary["BANK_ACCOUNT"] = ibanMatches.length;
    redacted = redacted.replace(/\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b/g, "[IBAN_REDACTED]");
  }

  // Simple name pattern (Title Case words)
  const namePattern = /\b(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b/g;
  const nameMatches = text.match(namePattern);
  if (nameMatches) {
    summary["PERSON"] = (summary["PERSON"] || 0) + nameMatches.length;
    redacted = redacted.replace(namePattern, "[PERSON_REDACTED]");
  }

  // Standalone names (John Smith pattern)
  const standaloneNamePattern = /\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b/g;
  const standaloneMatches = text.match(standaloneNamePattern);
  if (standaloneMatches && standaloneMatches.length > 0) {
    // Only count as names if they look like names (not common words)
    const commonWords = ["The", "This", "That", "These", "Those", "Medical", "Center", "Legal", "Amsterdam"];
    const filteredNames = standaloneMatches.filter(m => {
      const parts = m.split(" ");
      return !commonWords.includes(parts[0]) && !commonWords.includes(parts[1]);
    });
    if (filteredNames.length > 0) {
      summary["PERSON"] = (summary["PERSON"] || 0) + filteredNames.length;
      filteredNames.forEach(name => {
        redacted = redacted.replace(name, "[PERSON_REDACTED]");
      });
    }
  }

  // Date pattern
  const dateMatches = text.match(/\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b/g);
  if (dateMatches) {
    summary["DATE"] = dateMatches.length;
    if (preset.entities_enabled.DATE) {
      redacted = redacted.replace(/\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b/g, "[DATE_REDACTED]");
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
  if (!isTauriAvailable() || !tauriInvoke) {
    // Browser preview mode - use mock implementation
    return mockAnalyzeText(text, preset);
  }

  return await tauriInvoke<AnalyzeTextResponse>("analyze_text", {
    text,
    preset,
  });
}

export async function analyzeFile(
  inputPath: string,
  preset: Preset
): Promise<AnalyzeFileResponse> {
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

// ============================================================================
// Supported Languages
// ============================================================================

export const SUPPORTED_LANGUAGES = [
  { code: "auto", name: "Auto-detect" },
  { code: "en", name: "English" },
  { code: "nl", name: "Dutch (Nederlands)" },
  { code: "de", name: "German (Deutsch)" },
  { code: "fr", name: "French (Français)" },
  { code: "es", name: "Spanish (Español)" },
  { code: "it", name: "Italian (Italiano)" },
  { code: "pt", name: "Portuguese (Português)" },
  { code: "pl", name: "Polish (Polski)" },
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
