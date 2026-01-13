use serde::{Deserialize, Serialize};

use crate::python_sidecar::{run_python_analyze_text, PythonRunResult};

#[derive(Debug, Deserialize)]
pub struct Preset {
  pub preset_id: String,
  pub name: String,
  pub layer: u8,
  pub minimum_confidence: u8, // 0..100
  pub uncertainty_policy: String,
  pub pseudonym_style: String,
  pub language_mode: String,
  pub language: Option<String>,
  pub entities_enabled: std::collections::HashMap<String, bool>,
}

#[derive(Debug, Deserialize)]
pub struct AnalyzeTextRequest {
  pub text: String,
  pub preset: Preset,
}

#[derive(Debug, Serialize)]
pub struct AnalyzeTextResponse {
  pub run_id: String,
  pub redacted_text: String,
  pub run_folder: String,
  pub summary: std::collections::HashMap<String, u32>,
}

#[tauri::command]
pub fn analyze_text(text: String, preset: Preset) -> Result<AnalyzeTextResponse, String> {
  let req = AnalyzeTextRequest { text, preset };
  let res: PythonRunResult = run_python_analyze_text(req).map_err(|e| e.to_string())?;

  Ok(AnalyzeTextResponse {
    run_id: res.run_id,
    redacted_text: res.redacted_text,
    run_folder: res.run_folder,
    summary: res.summary,
  })
}
