// Prevent console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod python_sidecar;

use tauri::Builder;

fn main() {
    Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            commands::analyze_text,
            commands::analyze_file,
            commands::get_supported_extensions,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
