use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::Path;

use crate::python_sidecar::{run_python_command, run_streaming_command, PythonResponse};

#[derive(Debug, Deserialize, Serialize, Clone)]
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
    #[serde(default)]
    pub whitelist: Vec<String>,
    #[serde(default)]
    pub blacklist: Vec<String>,
    #[serde(default)]
    pub language_whitelists: HashMap<String, Vec<String>>,
    #[serde(default)]
    pub language_blacklists: HashMap<String, Vec<String>>,
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

/// A single finding with position information for the highlight feature
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct FindingItem {
    pub entity_type: String,
    pub detected_text: String,
    pub start: Option<u32>,
    pub end: Option<u32>,
    pub confidence: u32,
    pub action: String,
    pub pseudonym: String,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct AnalyzeTextResponse {
    pub run_id: String,
    pub run_folder: String,
    pub redacted_text: String,
    pub summary: HashMap<String, u32>,
    pub findings_count: u32,
    pub language: String,
    #[serde(default)]
    pub findings: Vec<FindingItem>,
}

#[tauri::command]
pub async fn analyze_text(
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
    let res: PythonResponse = run_python_command("analyze_text", payload)
        .await
        .map_err(|e| e.to_string())?;

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
pub async fn analyze_file(
    input_path: String,
    preset: Preset,
) -> Result<AnalyzeFileResponse, String> {
    // Validate the path before passing it to the Python sidecar.
    // Reject path traversal sequences, confirm the path exists and is a regular file.
    if input_path.contains("..") {
        return Err("Invalid file path: path traversal not allowed".to_string());
    }
    let path = Path::new(&input_path);
    if !path.exists() {
        return Err(format!("File not found: {}", input_path));
    }
    if !path.is_file() {
        return Err(format!("Path is not a file: {}", input_path));
    }

    // Reject files larger than 100 MB to prevent the app from hanging.
    let file_size = path
        .metadata()
        .map_err(|e| format!("Cannot read file metadata: {}", e))?
        .len();
    if file_size > MAX_FILE_BYTES {
        return Err(format!(
            "File is too large ({} MB). Maximum supported size is {} MB.",
            file_size / 1024 / 1024,
            MAX_FILE_BYTES / 1024 / 1024
        ));
    }

    let req = AnalyzeFileRequest { input_path, preset };

    let payload = serde_json::to_value(&req).map_err(|e| e.to_string())?;
    let res: PythonResponse = run_python_command("analyze_file", payload)
        .await
        .map_err(|e| e.to_string())?;

    let response: AnalyzeFileResponse = serde_json::from_value(res.data)
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(response)
}

// ============================================================================
// Model Management
// ============================================================================

#[derive(Debug, Deserialize, Serialize)]
pub struct ModelStatusResponse {
    pub spacy_models: HashMap<String, String>,
    pub presidio_available: bool,
    pub transformers_available: bool,
}

#[tauri::command]
pub async fn get_model_status() -> Result<ModelStatusResponse, String> {
    let payload = serde_json::json!({});
    let res: PythonResponse = run_python_command("get_model_status", payload)
        .await
        .map_err(|e| e.to_string())?;

    let response: ModelStatusResponse = serde_json::from_value(res.data)
        .map_err(|e| format!("Failed to parse model status: {}", e))?;

    Ok(response)
}

#[derive(Debug, Deserialize, Serialize)]
pub struct DownloadModelResponse {
    pub status: String,
    pub model_id: String,
}

/// Allowed model type identifiers sent to the Python sidecar.
const ALLOWED_MODEL_TYPES: &[&str] = &["spacy", "huggingface", "presidio"];

#[tauri::command]
pub async fn download_model(
    app: tauri::AppHandle,
    model_type: String,
    model_id: String,
) -> Result<DownloadModelResponse, String> {
    // Validate model_type against a strict allowlist
    if !ALLOWED_MODEL_TYPES.contains(&model_type.as_str()) {
        return Err(format!("Invalid model_type: {}", model_type));
    }

    // Validate model_id: only alphanumeric characters plus the safe set [-_/.]
    if !model_id
        .chars()
        .all(|c| c.is_alphanumeric() || "-_/.".contains(c))
    {
        return Err("Invalid model_id: contains disallowed characters".to_string());
    }

    let payload = serde_json::json!({
        "model_type": model_type,
        "model_id": model_id,
    });
    // Use streaming command so download progress events are emitted in real time
    let res: PythonResponse = run_streaming_command("download_model", payload, &app)
        .await
        .map_err(|e| e.to_string())?;

    let response: DownloadModelResponse = serde_json::from_value(res.data)
        .map_err(|e| format!("Failed to parse download response: {}", e))?;

    Ok(response)
}

// ============================================================================
// Model Uninstall
// ============================================================================

#[derive(Debug, Deserialize, Serialize)]
pub struct UninstallModelResponse {
    pub status: String,
    pub model_id: String,
}

#[tauri::command]
pub async fn uninstall_model(
    model_type: String,
    model_id: String,
) -> Result<UninstallModelResponse, String> {
    // Same validation rules as download_model
    if !ALLOWED_MODEL_TYPES.contains(&model_type.as_str()) {
        return Err(format!("Invalid model_type: {}", model_type));
    }
    if !model_id
        .chars()
        .all(|c| c.is_alphanumeric() || "-_/.".contains(c))
    {
        return Err("Invalid model_id: contains disallowed characters".to_string());
    }

    let payload = serde_json::json!({
        "model_type": model_type,
        "model_id": model_id,
    });
    let res: PythonResponse = run_python_command("uninstall_model", payload)
        .await
        .map_err(|e| e.to_string())?;

    let response: UninstallModelResponse = serde_json::from_value(res.data)
        .map_err(|e| format!("Failed to parse uninstall response: {}", e))?;

    Ok(response)
}

// ============================================================================
// Disk Usage
// ============================================================================

#[derive(Debug, Deserialize, Serialize)]
pub struct DiskUsageResponse {
    pub spacy_models_bytes: u64,
    pub hf_cache_bytes: u64,
    pub spacy_models_path: String,
    pub hf_cache_path: String,
}

#[tauri::command]
pub async fn get_disk_usage() -> Result<DiskUsageResponse, String> {
    let payload = serde_json::json!({});
    let res: PythonResponse = run_python_command("get_disk_usage", payload)
        .await
        .map_err(|e| e.to_string())?;

    let response: DiskUsageResponse = serde_json::from_value(res.data)
        .map_err(|e| format!("Failed to parse disk usage response: {}", e))?;

    Ok(response)
}

// ============================================================================
// File size guard
// ============================================================================

/// Maximum file size accepted for analysis: 100 MB.
const MAX_FILE_BYTES: u64 = 100 * 1024 * 1024;

// ============================================================================
// Browser Access
// ============================================================================

const LOCAL_WEB_URL: &str = "http://localhost:1422";

/// Returns the URL where the desktop app's local web server is accessible.
#[tauri::command]
pub async fn get_local_url() -> Result<String, String> {
    Ok(LOCAL_WEB_URL.to_string())
}

/// Opens the local web server URL in the system default browser.
#[tauri::command]
pub async fn open_in_browser() -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("cmd")
            .args(["/c", "start", "", LOCAL_WEB_URL])
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .arg(LOCAL_WEB_URL)
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    #[cfg(not(any(target_os = "windows", target_os = "macos")))]
    {
        std::process::Command::new("xdg-open")
            .arg(LOCAL_WEB_URL)
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    Ok(())
}

// ============================================================================
// Supported Extensions
// ============================================================================

#[derive(Debug, Deserialize, Serialize)]
pub struct SupportedExtensionsResponse {
    pub extensions: Vec<String>,
}

#[tauri::command]
pub async fn get_supported_extensions() -> Result<SupportedExtensionsResponse, String> {
    let payload = serde_json::json!({});
    let res: PythonResponse = run_python_command("get_supported_extensions", payload)
        .await
        .map_err(|e| e.to_string())?;

    let response: SupportedExtensionsResponse = serde_json::from_value(res.data)
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(response)
}
