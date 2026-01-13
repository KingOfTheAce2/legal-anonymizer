use serde::{Deserialize, Serialize};
use std::process::{Command, Stdio};
use std::io::Write;
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

#[derive(Debug, Deserialize)]
pub struct AnalyzeTextRequest {
  pub text: String,
  pub preset: super::commands::Preset,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PythonRunResult {
  pub run_id: String,
  pub redacted_text: String,
  pub run_folder: String,
  pub summary: std::collections::HashMap<String, u32>,
}

pub fn run_python_analyze_text(req: AnalyzeTextRequest) -> Result<PythonRunResult, SidecarError> {
  // In dev we call your system python.
  // Later we bundle a sidecar binary using Tauri externalBin.
  let mut cmd = Command::new("python");
  cmd.arg("../../engine/python/scripts/sidecar_entrypoint.py")
    .arg("analyze_text")
    .stdin(Stdio::piped())
    .stdout(Stdio::piped())
    .stderr(Stdio::piped());

  let mut child = cmd.spawn().map_err(|e| SidecarError::StartFailed(e.to_string()))?;

  {
    let stdin = child.stdin.as_mut().ok_or_else(|| SidecarError::StartFailed("no stdin".into()))?;
    let payload = serde_json::to_vec(&req).map_err(|e| SidecarError::InvalidOutput(e.to_string()))?;
    stdin.write_all(&payload).map_err(|e| SidecarError::StartFailed(e.to_string()))?;
  }

  let output = child.wait_with_output().map_err(|e| SidecarError::StartFailed(e.to_string()))?;

  if !output.status.success() {
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    return Err(SidecarError::NonZero(stderr));
  }

  let stdout = String::from_utf8_lossy(&output.stdout).to_string();
  serde_json::from_str::<PythonRunResult>(&stdout)
    .map_err(|e| SidecarError::InvalidOutput(format!("{e}. stdout={stdout}")))
}
