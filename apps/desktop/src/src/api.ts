import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";

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
};

// ============================================================================
// Text Analysis
// ============================================================================

export type AnalyzeTextResponse = {
  run_id: string;
  run_folder: string;
  redacted_text: string;
  summary: Record<string, number>;
  findings_count: number;
  language: string;
};

export async function analyzeText(
  text: string,
  preset: Preset,
  modelPath?: string
): Promise<AnalyzeTextResponse> {
  return await invoke<AnalyzeTextResponse>("analyze_text", {
    text,
    preset,
    modelPath,
  });
}

// ============================================================================
// File Analysis
// ============================================================================

export type AnalyzeFileResponse = {
  run_id: string;
  run_folder: string;
  output_path: string;
  summary: Record<string, number>;
  findings_count: number;
};

export async function analyzeFile(
  inputPath: string,
  preset: Preset
): Promise<AnalyzeFileResponse> {
  return await invoke<AnalyzeFileResponse>("analyze_file", {
    inputPath,
    preset,
  });
}

// ============================================================================
// File Dialog
// ============================================================================

export async function selectFile(): Promise<string | null> {
  const selected = await open({
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
  const selected = await open({
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

// ============================================================================
// Supported Extensions
// ============================================================================

export type SupportedExtensionsResponse = {
  extensions: string[];
};

export async function getSupportedExtensions(): Promise<string[]> {
  const res = await invoke<SupportedExtensionsResponse>("get_supported_extensions");
  return res.extensions;
}

// ============================================================================
// Preset Templates
// ============================================================================

const DEFAULT_ENTITIES: Record<string, boolean> = {
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
};

export const PRESET_LAYER1_FAST: Preset = {
  preset_id: "layer1_fast_legal_scrub",
  name: "Layer 1: Fast Legal Scrub",
  layer: 1,
  minimum_confidence: 60,
  uncertainty_policy: "mask",
  pseudonym_style: "neutral",
  language_mode: "auto",
  entities_enabled: { ...DEFAULT_ENTITIES },
};

export const PRESET_LAYER2_ACCURATE: Preset = {
  preset_id: "layer2_accurate_legal_review",
  name: "Layer 2: Accurate Legal Review",
  layer: 2,
  minimum_confidence: 70,
  uncertainty_policy: "mask",
  pseudonym_style: "neutral",
  language_mode: "auto",
  entities_enabled: { ...DEFAULT_ENTITIES },
};

export const PRESET_LAYER3_REGULATORY: Preset = {
  preset_id: "layer3_regulatory_standard",
  name: "Layer 3: Regulatory Standard",
  layer: 3,
  minimum_confidence: 80,
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
