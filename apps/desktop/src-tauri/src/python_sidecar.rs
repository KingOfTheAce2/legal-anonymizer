use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::io::Write;
use std::process::{Command, Stdio};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum SidecarError {
    #[error("failed to start python: {0}")]
    StartFailed(String),
    #[error("python returned non-zero exit code: {0}")]
    NonZero(String),
    #[error("invalid python output: {0}")]
    InvalidOutput(String),
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PythonResponse {
    #[serde(flatten)]
    pub data: Value,
}

/// Run a Python sidecar command with the given payload.
///
/// # Arguments
/// * `command` - The command name (e.g., "analyze_text", "analyze_file")
/// * `payload` - JSON payload to send to the Python script
///
/// # Returns
/// * `PythonResponse` containing the JSON response from Python
pub fn run_python_command(command: &str, payload: Value) -> Result<PythonResponse, SidecarError> {
    // In development, use system Python
    // In production, this would use Tauri's externalBin
    let mut cmd = Command::new("python");
    cmd.arg("../../engine/python/scripts/sidecar_entrypoint.py")
        .arg(command)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    let mut child = cmd
        .spawn()
        .map_err(|e| SidecarError::StartFailed(e.to_string()))?;

    // Write payload to stdin
    {
        let stdin = child
            .stdin
            .as_mut()
            .ok_or_else(|| SidecarError::StartFailed("no stdin".into()))?;
        let payload_bytes =
            serde_json::to_vec(&payload).map_err(|e| SidecarError::InvalidOutput(e.to_string()))?;
        stdin
            .write_all(&payload_bytes)
            .map_err(|e| SidecarError::StartFailed(e.to_string()))?;
    }

    let output = child
        .wait_with_output()
        .map_err(|e| SidecarError::StartFailed(e.to_string()))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        return Err(SidecarError::NonZero(stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();

    // Check for error in response
    let data: Value = serde_json::from_str(&stdout)
        .map_err(|e| SidecarError::InvalidOutput(format!("{e}. stdout={stdout}")))?;

    if let Some(error) = data.get("error") {
        return Err(SidecarError::NonZero(error.to_string()));
    }

    Ok(PythonResponse { data })
}

// Legacy function for backwards compatibility
pub fn run_python_analyze_text(
    req: crate::commands::Preset,
    text: String,
) -> Result<PythonResponse, SidecarError> {
    let payload = serde_json::json!({
        "text": text,
        "preset": req
    });
    run_python_command("analyze_text", payload)
}
