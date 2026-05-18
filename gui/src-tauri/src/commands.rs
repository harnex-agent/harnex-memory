use serde::{Deserialize, Serialize};

use crate::harnex_memory::{
    run_cli_json, validate_existing_file, validate_item_id, validate_optional_path,
    validate_project_root, ApplyPayload, BridgeError, CliOperation, ItemPayload, ItemsPayload,
    PreviewPayload,
};

#[derive(Debug, Clone, Serialize)]
pub struct ProjectRootSelection {
    pub path: Option<String>,
    pub cancelled: bool,
}

#[derive(Debug, Clone, Copy, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ItemAction {
    Delete,
    Disable,
    Enable,
}

impl ItemAction {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Delete => "delete",
            Self::Disable => "disable",
            Self::Enable => "enable",
        }
    }
}

#[tauri::command]
pub async fn select_project_root() -> Result<ProjectRootSelection, BridgeError> {
    let selected = tauri::async_runtime::spawn_blocking(|| {
        rfd::FileDialog::new()
            .set_title("Select project root")
            .pick_folder()
    })
    .await
    .map_err(|error| BridgeError::new("dialog", format!("Project picker failed: {error}")))?;

    let cancelled = selected.is_none();
    Ok(ProjectRootSelection {
        path: selected.map(|path| path.to_string_lossy().into_owned()),
        cancelled,
    })
}

#[tauri::command]
pub fn list_items(
    project_root: String,
    cwd: Option<String>,
    include_readonly: Option<bool>,
) -> Result<ItemsPayload, BridgeError> {
    let project_root = validate_project_root(&project_root)?;
    let cwd = validate_optional_path(cwd, "cwd")?;
    run_cli_json(CliOperation::ItemsList {
        project_root,
        cwd,
        include_readonly: include_readonly.unwrap_or(false),
    })
}

#[tauri::command]
pub fn show_item(project_root: String, item_id: String) -> Result<ItemPayload, BridgeError> {
    let project_root = validate_project_root(&project_root)?;
    let item_id = validate_item_id(&item_id)?;
    run_cli_json(CliOperation::ItemsShow {
        project_root,
        item_id,
    })
}

#[tauri::command]
pub fn preview_item_action(
    project_root: String,
    item_id: String,
    action: ItemAction,
    expected_source_hash: Option<String>,
) -> Result<PreviewPayload, BridgeError> {
    let project_root = validate_project_root(&project_root)?;
    let item_id = validate_item_id(&item_id)?;
    let expected_source_hash = validate_optional_hash(expected_source_hash)?;
    run_cli_json(CliOperation::ItemsPreview {
        project_root,
        item_id,
        action: action.as_str().to_string(),
        expected_source_hash,
    })
}

#[tauri::command]
pub fn apply_preview(project_root: String, preview_path: String) -> Result<ApplyPayload, BridgeError> {
    let project_root = validate_project_root(&project_root)?;
    let preview_path = validate_existing_file(&preview_path, "preview_path")?;
    run_cli_json(CliOperation::DocsApply {
        project_root,
        preview_path,
    })
}

fn validate_optional_hash(value: Option<String>) -> Result<Option<String>, BridgeError> {
    match value.map(|item| item.trim().to_string()) {
        None => Ok(None),
        Some(item) if item.is_empty() => Ok(None),
        Some(item) if item.chars().all(|character| character.is_ascii_hexdigit()) => Ok(Some(item)),
        Some(_) => Err(BridgeError::new(
            "invalid_input",
            "expected_source_hash must be hexadecimal",
        )),
    }
}
