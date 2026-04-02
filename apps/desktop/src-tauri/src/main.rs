// Prevent console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod python_sidecar;

use tauri::Builder;

/// Spawn the Python web server as a background process so the app is also
/// reachable at http://localhost:1422 in a regular browser tab.
///
/// - Debug:   runs `python <absolute-path>/web_server.py --port 1422`
/// - Release: looks for a bundled `anonymizer_web_server[.exe]` next to the exe.
fn start_web_server() {
    std::thread::spawn(|| {
        #[cfg(debug_assertions)]
        {
            let script = concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/../../engine/python/scripts/web_server.py"
            );
            let _ = std::process::Command::new("python")
                .arg(script)
                .arg("--port")
                .arg("1422")
                .stdout(std::process::Stdio::null())
                .stderr(std::process::Stdio::null())
                .spawn();
        }

        #[cfg(not(debug_assertions))]
        {
            if let Some(exe_dir) = std::env::current_exe()
                .ok()
                .and_then(|p| p.parent().map(|p| p.to_path_buf()))
            {
                #[cfg(target_os = "windows")]
                let binary_name = "anonymizer_web_server.exe";
                #[cfg(not(target_os = "windows"))]
                let binary_name = "anonymizer_web_server";

                let binary_path = exe_dir.join(binary_name);
                if binary_path.exists() {
                    let _ = std::process::Command::new(binary_path)
                        .arg("--port")
                        .arg("1422")
                        .stdout(std::process::Stdio::null())
                        .stderr(std::process::Stdio::null())
                        .spawn();
                }
            }
        }
    });
}

fn main() {
    start_web_server();

    Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            commands::analyze_text,
            commands::analyze_file,
            commands::get_supported_extensions,
            commands::get_model_status,
            commands::download_model,
            commands::uninstall_model,
            commands::get_disk_usage,
            commands::open_in_browser,
            commands::get_local_url,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
