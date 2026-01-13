import { invoke } from "@tauri-apps/api/core";

export type Layer = 1 | 2 | 3;

export type Preset = {
  preset_id: string;
  name: string;
  layer: Layer;
  minimum_confidence: number; // 0..100
  uncertainty_policy: "mask" | "redact" | "leave_intact" | "flag_only";
  pseudonym_style: "neutral" | "realistic";
  language_mode: "auto" | "fixed";
  language?: string;
  entities_enabled: Record<string, boolean>;
};

export type AnalyzeTextResponse = {
  run_id: string;
  redacted_text: string;
  run_folder: string;
  summary: Record<string, number>;
};

export async function analyzeText(text: string, preset: Preset): Promise<AnalyzeTextResponse> {
  return await invoke<AnalyzeTextResponse>("analyze_text", { text, preset });
}
