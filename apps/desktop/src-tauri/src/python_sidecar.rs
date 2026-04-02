use serde::{Deserialize, Serialize};
use serde_json::Value;
use thiserror::Error;
use tokio::process::Command;

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

/// Build the sidecar Command depending on debug vs release.
///
/// - Debug: runs `python <absolute-path>/../../engine/python/scripts/sidecar_entrypoint.py <command>`
///   The path is resolved at compile time from CARGO_MANIFEST_DIR, making it independent of CWD.
/// - Release: runs the bundled `anonymizer_engine-<triple>` binary next to the app exe.
fn get_sidecar_command(command: &str) -> Result<Command, SidecarError> {
    if cfg!(debug_assertions) {
        // env!("CARGO_MANIFEST_DIR") is an absolute path baked in at compile time,
        // so this is not relative to the runtime CWD.
        let script_path = concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../engine/python/scripts/sidecar_entrypoint.py"
        );
        let mut cmd = Command::new("python");
        cmd.arg(script_path).arg(command);
        cmd.env("PYTHONUTF8", "1").env("PYTHONIOENCODING", "utf-8:replace");
        // Suppress console window on Windows
        #[cfg(target_os = "windows")]
        cmd.creation_flags(0x08000000); // CREATE_NO_WINDOW
        Ok(cmd)
    } else {
        let exe_dir = std::env::current_exe()
            .map_err(|e| SidecarError::StartFailed(format!("cannot find app exe: {}", e)))?
            .parent()
            .ok_or_else(|| SidecarError::StartFailed("cannot find app directory".into()))?
            .to_path_buf();

        // Tauri strips the target triple when installing the externalBin,
        // so the installed name is simply "anonymizer_engine[.exe]".
        #[cfg(target_os = "windows")]
        let sidecar_name = "anonymizer_engine.exe";
        #[cfg(not(target_os = "windows"))]
        let sidecar_name = "anonymizer_engine";
        let sidecar_path = exe_dir.join(&sidecar_name);

        if !sidecar_path.exists() {
            return Err(SidecarError::StartFailed(format!(
                "sidecar not found at {:?}",
                sidecar_path
            )));
        }

        let mut cmd = Command::new(sidecar_path);
        cmd.arg(command);
        cmd.env("PYTHONUTF8", "1").env("PYTHONIOENCODING", "utf-8:replace")
           .env("HF_HUB_DISABLE_SYMLINKS_WARNING", "1");
        // Suppress console window on Windows
        #[cfg(target_os = "windows")]
        cmd.creation_flags(0x08000000); // CREATE_NO_WINDOW
        Ok(cmd)
    }
}

/// Write the JSON payload to a uniquely-named temp file and return its path.
///
/// The sidecar reads `--payload-file <path>` instead of stdin, which avoids
/// Windows console-application stdin handle inconsistencies.
fn write_payload_file(payload: &Value) -> Result<std::path::PathBuf, SidecarError> {
    let bytes = serde_json::to_vec(payload)
        .map_err(|e| SidecarError::InvalidOutput(e.to_string()))?;

    // Use full epoch nanos + thread-ID to avoid collisions when multiple commands
    // are spawned concurrently (e.g., during batch processing).
    let nanos = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    let tid = std::thread::current().id();
    let tmp_path = std::env::temp_dir().join(format!("la_payload_{nanos}_{tid:?}.json"));

    std::fs::write(&tmp_path, &bytes)
        .map_err(|e| SidecarError::StartFailed(format!("cannot write payload file: {}", e)))?;

    Ok(tmp_path)
}

/// Run a Python sidecar command with streaming stdout support.
///
/// Reads stdout line-by-line. Lines matching `{"__progress__": ...}` are emitted
/// as Tauri `download-progress` events; the last non-progress line is the result.
/// Payload is delivered via a temp file to avoid Windows stdin pipe issues.
pub async fn run_streaming_command<R: tauri::Runtime>(
    command: &str,
    payload: Value,
    app: &tauri::AppHandle<R>,
) -> Result<PythonResponse, SidecarError> {
    use std::process::Stdio;
    use tauri::Emitter;
    use tokio::io::{AsyncBufReadExt, AsyncReadExt, BufReader};

    let payload_path = write_payload_file(&payload)?;

    let mut cmd = get_sidecar_command(command)?;
    cmd.arg("--payload-file")
        .arg(&payload_path)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    let mut child = cmd
        .spawn()
        .map_err(|e| SidecarError::StartFailed(e.to_string()))?;

    // Stream stdout line by line
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| SidecarError::StartFailed("no stdout".into()))?;
    let stderr_handle = child.stderr.take();
    let mut lines = BufReader::new(stdout).lines();

    let mut final_line = String::new();
    while let Some(line) = lines
        .next_line()
        .await
        .map_err(|e| SidecarError::InvalidOutput(e.to_string()))?
    {
        let trimmed = line.trim().to_string();
        if trimmed.is_empty() {
            continue;
        }
        // Emit progress events without buffering them as the final result
        if trimmed.contains("\"__progress__\"") {
            if let Ok(v) = serde_json::from_str::<Value>(&trimmed) {
                if let Some(progress) = v.get("__progress__") {
                    let _ = app.emit("download-progress", progress.clone());
                    continue;
                }
            }
        }
        final_line = trimmed;
    }

    let _ = child.wait().await;
    let _ = std::fs::remove_file(&payload_path); // clean up temp file

    if final_line.is_empty() {
        // Capture stderr for diagnostics (e.g. import errors before main() runs)
        let stderr_text = if let Some(mut se) = stderr_handle {
            let mut buf = String::new();
            let _ = se.read_to_string(&mut buf).await;
            buf
        } else {
            String::new()
        };
        let detail = if stderr_text.trim().is_empty() {
            String::new()
        } else {
            format!(". stderr={}", stderr_text.trim())
        };
        return Err(SidecarError::InvalidOutput(format!("empty output from process{detail}")));
    }

    let data: Value = serde_json::from_str(&final_line)
        .map_err(|e| SidecarError::InvalidOutput(format!("{e}. stdout={final_line}")))?;

    if let Some(error) = data.get("error") {
        let msg = error
            .as_str()
            .map(|s| s.to_owned())
            .unwrap_or_else(|| error.to_string());
        return Err(SidecarError::NonZero(msg));
    }

    Ok(PythonResponse { data })
}

/// Run a Python sidecar command with the given payload.
///
/// Payload is delivered via a temp file (`--payload-file <path>`) to avoid
/// Windows console-application stdin pipe issues.
pub async fn run_python_command(
    command: &str,
    payload: Value,
) -> Result<PythonResponse, SidecarError> {
    use std::process::Stdio;

    let payload_path = write_payload_file(&payload)?;

    let mut cmd = get_sidecar_command(command)?;
    cmd.arg("--payload-file")
        .arg(&payload_path)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    let child = cmd
        .spawn()
        .map_err(|e| SidecarError::StartFailed(e.to_string()))?;

    let output = child
        .wait_with_output()
        .await
        .map_err(|e| SidecarError::StartFailed(e.to_string()))?;

    let _ = std::fs::remove_file(&payload_path); // clean up temp file

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        return Err(SidecarError::NonZero(stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();

    // Presidio and spaCy may emit non-JSON diagnostic lines before the result.
    // Take the last line that starts with '{'.
    let final_line = stdout
        .lines()
        .rev()
        .map(str::trim)
        .find(|l| !l.is_empty() && l.starts_with('{'))
        .unwrap_or("");

    if final_line.is_empty() {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        return Err(SidecarError::InvalidOutput(format!(
            "empty output from process. stderr={stderr}"
        )));
    }

    let data: Value = serde_json::from_str(final_line)
        .map_err(|e| SidecarError::InvalidOutput(format!("{e}. stdout={stdout}")))?;

    if let Some(error) = data.get("error") {
        let msg = error
            .as_str()
            .map(|s| s.to_owned())
            .unwrap_or_else(|| error.to_string());
        return Err(SidecarError::NonZero(msg));
    }

    Ok(PythonResponse { data })
}
