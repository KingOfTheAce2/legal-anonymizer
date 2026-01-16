use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use crate::python_sidecar::{run_python_command, PythonResponse};

#[derive(Debug, Deserialize, Clone)]
pub struct Preset {
    pub preset_id: String,
    pub name: String,
    pub layer: u8,
    pub minimum_confidence: u8,
    pub uncertainty_policy: String,
    pub pseudonym_style: String,
    pub language_mode: String,
    pub language: Option<String>,
    pub entities_enabled: HashMap<String, bool>,
}

// ============================================================================
// Text Analysis
// ============================================================================

#[derive(Debug, Serialize)]
struct AnalyzeTextRequest {
    text: String,
    preset: Preset,
    #[serde(skip_serializing_if = "Option::is_none")]
    model_path: Option<String>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct AnalyzeTextResponse {
    pub run_id: String,
    pub run_folder: String,
    pub redacted_text: String,
    pub summary: HashMap<String, u32>,
    pub findings_count: u32,
    pub language: String,
}

#[tauri::command]
pub fn analyze_text(
    text: String,
    preset: Preset,
    model_path: Option<String>,
) -> Result<AnalyzeTextResponse, String> {
    let req = AnalyzeTextRequest {
        text,
        preset,
        model_path,
    };

    let payload = serde_json::to_value(&req).map_err(|e| e.to_string())?;
    let res: PythonResponse = run_python_command("analyze_text", payload).map_err(|e| e.to_string())?;

    // Parse response
    let response: AnalyzeTextResponse = serde_json::from_value(res.data)
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(response)
}

// ============================================================================
// File Analysis
// ============================================================================

#[derive(Debug, Serialize)]
struct AnalyzeFileRequest {
    input_path: String,
    preset: Preset,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct AnalyzeFileResponse {
    pub run_id: String,
    pub run_folder: String,
    pub output_path: String,
    pub summary: HashMap<String, u32>,
    pub findings_count: u32,
}

#[tauri::command]
pub fn analyze_file(input_path: String, preset: Preset) -> Result<AnalyzeFileResponse, String> {
    let req = AnalyzeFileRequest { input_path, preset };

    let payload = serde_json::to_value(&req).map_err(|e| e.to_string())?;
    let res: PythonResponse = run_python_command("analyze_file", payload).map_err(|e| e.to_string())?;

    let response: AnalyzeFileResponse = serde_json::from_value(res.data)
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(response)
}

// ============================================================================
// Supported Extensions
// ============================================================================

#[derive(Debug, Deserialize, Serialize)]
pub struct SupportedExtensionsResponse {
    pub extensions: Vec<String>,
}

#[tauri::command]
pub fn get_supported_extensions() -> Result<SupportedExtensionsResponse, String> {
    let payload = serde_json::json!({});
    let res: PythonResponse = run_python_command("get_supported_extensions", payload)
        .map_err(|e| e.to_string())?;

    let response: SupportedExtensionsResponse = serde_json::from_value(res.data)
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(response)
}
