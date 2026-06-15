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
            commands::apply_preview,
            commands::list_recommendations,
            commands::show_recommendation,
            commands::apply_recommendation,
            commands::dismiss_recommendation,
            commands::hook_status,
            commands::install_hook,
            commands::uninstall_hook
        ])
        .run(tauri::generate_context!())
        .expect("failed to run Harnex Memory GUI");
}
