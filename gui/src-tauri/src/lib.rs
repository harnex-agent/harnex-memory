mod commands;
mod harnex_memory;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            commands::select_project_root,
            commands::list_items,
            commands::show_item,
            commands::preview_item_action,
            commands::apply_preview
        ])
        .run(tauri::generate_context!())
        .expect("failed to run Harnex Memory GUI");
}
