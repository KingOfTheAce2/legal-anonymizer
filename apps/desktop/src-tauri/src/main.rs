mod commands;
mod python_sidecar;

use tauri::Builder;

fn main() {
  Builder::default()
    .invoke_handler(tauri::generate_handler![
      commands::analyze_text
    ])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
