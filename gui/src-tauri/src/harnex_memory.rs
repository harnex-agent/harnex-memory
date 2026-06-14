use std::{
    env,
    ffi::OsString,
    path::{Path, PathBuf},
    process::Command,
};

use serde::{de::DeserializeOwned, Deserialize, Serialize};

#[derive(Debug, Clone, Serialize)]
pub struct BridgeError {
    pub kind: String,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stderr: Option<String>,
}

impl BridgeError {
    pub fn new(kind: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            kind: kind.into(),
            message: message.into(),
            stderr: None,
        }
    }

    fn with_stderr(
        kind: impl Into<String>,
        message: impl Into<String>,
        stderr: impl Into<String>,
    ) -> Self {
        let stderr = stderr.into();
        Self {
            kind: kind.into(),
            message: message.into(),
            stderr: (!stderr.trim().is_empty()).then_some(stderr),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TextSpan {
    pub start_line: u32,
    pub end_line: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryItem {
    pub document_kind: String,
    pub target_kind: String,
    pub scope: String,
    pub path: String,
    pub title: String,
    pub body: String,
    pub format: String,
    pub status: String,
    pub span: Option<TextSpan>,
    pub source_hash: String,
    pub reason: String,
    #[serde(default)]
    pub agent: String,
    pub id: String,
    pub schema_version: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryCandidate {
    pub target: String,
    pub title: String,
    pub content: String,
    pub reason: String,
    #[serde(default)]
    pub evidence: Vec<String>,
    pub risk: String,
    pub target_kind: Option<String>,
    pub target_path: Option<String>,
    pub insertion_strategy: Option<String>,
    pub section: Option<String>,
    pub id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileChange {
    pub path: String,
    pub before: String,
    pub after: String,
    pub diff: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Preview {
    pub project_root: String,
    pub preview_id: String,
    pub source: String,
    #[serde(default)]
    pub candidates: Vec<MemoryCandidate>,
    #[serde(default)]
    pub file_changes: Vec<FileChange>,
    #[serde(default)]
    pub warnings: Vec<String>,
    pub action: Option<String>,
    #[serde(default)]
    pub items: Vec<MemoryItem>,
    #[serde(default)]
    pub blocked_reasons: Vec<String>,
    pub schema_version: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ItemsPayload {
    pub items: Vec<MemoryItem>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ItemPayload {
    pub item: MemoryItem,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PreviewPayload {
    pub preview_path: String,
    pub preview: Preview,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApplyPayload {
    pub apply_result_path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Recommendation {
    pub kind: String,
    pub title: String,
    pub reason: String,
    pub preview_id: String,
    pub preview_path: String,
    pub target_path: String,
    pub target_kind: String,
    pub risk: String,
    #[serde(default)]
    pub evidence: Vec<String>,
    pub candidate_id: String,
    pub status: String,
    pub dismissed_reason: String,
    #[serde(default)]
    pub origin: String,
    pub created_at: String,
    pub updated_at: String,
    pub id: String,
    pub schema_version: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecommendationsPayload {
    pub recommendations: Vec<Recommendation>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecommendationPayload {
    pub recommendation: Recommendation,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecommendationPreviewPayload {
    pub recommendation: Recommendation,
    pub preview: Preview,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApplyRecommendationPayload {
    pub apply_result_path: String,
    pub recommendation: Recommendation,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CliOperation {
    ItemsList {
        project_root: PathBuf,
        cwd: Option<PathBuf>,
        include_readonly: bool,
    },
    ItemsShow {
        project_root: PathBuf,
        item_id: String,
    },
    ItemsPreview {
        project_root: PathBuf,
        item_id: String,
        action: String,
        expected_source_hash: Option<String>,
    },
    DocsApply {
        project_root: PathBuf,
        preview_path: PathBuf,
    },
    RecommendationsList {
        project_root: PathBuf,
        status: Option<String>,
    },
    RecommendationsShow {
        project_root: PathBuf,
        recommendation_id: String,
    },
    RecommendationsApply {
        project_root: PathBuf,
        recommendation_id: String,
    },
    RecommendationsDismiss {
        project_root: PathBuf,
        recommendation_id: String,
        reason: Option<String>,
    },
}

impl CliOperation {
    pub fn args(&self) -> Vec<String> {
        match self {
            Self::ItemsList {
                project_root,
                cwd,
                include_readonly,
            } => {
                let mut args = vec![
                    "items".to_string(),
                    "list".to_string(),
                    "--project-root".to_string(),
                    path_arg(project_root),
                ];
                if let Some(cwd) = cwd {
                    args.push("--cwd".to_string());
                    args.push(path_arg(cwd));
                }
                if *include_readonly {
                    args.push("--include-readonly".to_string());
                }
                args
            }
            Self::ItemsShow {
                project_root,
                item_id,
            } => vec![
                "items".to_string(),
                "show".to_string(),
                "--project-root".to_string(),
                path_arg(project_root),
                "--item-id".to_string(),
                item_id.clone(),
            ],
            Self::ItemsPreview {
                project_root,
                item_id,
                action,
                expected_source_hash,
            } => {
                let mut args = vec![
                    "items".to_string(),
                    "preview".to_string(),
                    "--project-root".to_string(),
                    path_arg(project_root),
                    "--item-id".to_string(),
                    item_id.clone(),
                    "--action".to_string(),
                    action.clone(),
                ];
                if let Some(expected_source_hash) = expected_source_hash {
                    args.push("--expected-source-hash".to_string());
                    args.push(expected_source_hash.clone());
                }
                args
            }
            Self::DocsApply {
                project_root,
                preview_path,
            } => vec![
                "docs".to_string(),
                "apply".to_string(),
                "--project-root".to_string(),
                path_arg(project_root),
                "--preview".to_string(),
                path_arg(preview_path),
            ],
            Self::RecommendationsList {
                project_root,
                status,
            } => {
                let mut args = vec![
                    "recommendations".to_string(),
                    "list".to_string(),
                    "--project-root".to_string(),
                    path_arg(project_root),
                ];
                if let Some(status) = status {
                    args.push("--status".to_string());
                    args.push(status.clone());
                }
                args
            }
            Self::RecommendationsShow {
                project_root,
                recommendation_id,
            } => vec![
                "recommendations".to_string(),
                "show".to_string(),
                "--project-root".to_string(),
                path_arg(project_root),
                "--recommendation-id".to_string(),
                recommendation_id.clone(),
            ],
            Self::RecommendationsApply {
                project_root,
                recommendation_id,
            } => vec![
                "recommendations".to_string(),
                "apply".to_string(),
                "--project-root".to_string(),
                path_arg(project_root),
                "--recommendation-id".to_string(),
                recommendation_id.clone(),
            ],
            Self::RecommendationsDismiss {
                project_root,
                recommendation_id,
                reason,
            } => {
                let mut args = vec![
                    "recommendations".to_string(),
                    "dismiss".to_string(),
                    "--project-root".to_string(),
                    path_arg(project_root),
                    "--recommendation-id".to_string(),
                    recommendation_id.clone(),
                ];
                if let Some(reason) = reason {
                    args.push("--reason".to_string());
                    args.push(reason.clone());
                }
                args
            }
        }
    }
}

pub fn run_cli_json<T: DeserializeOwned>(operation: CliOperation) -> Result<T, BridgeError> {
    let output = python_command()?
        .args(["-m", "harnex_memory.cli"])
        .args(operation.args())
        .env("PYTHONPATH", python_path()?)
        .current_dir(repo_root())
        .output()
        .map_err(|error| {
            BridgeError::new("spawn_failed", format!("Failed to run Python CLI: {error}"))
        })?;

    if !output.status.success() {
        return Err(BridgeError::with_stderr(
            "command_failed",
            format!("harnex-memory exited with {}", output.status),
            String::from_utf8_lossy(&output.stderr),
        ));
    }

    serde_json::from_slice(&output.stdout).map_err(|error| {
        BridgeError::with_stderr(
            "invalid_json",
            format!("harnex-memory returned invalid JSON: {error}"),
            String::from_utf8_lossy(&output.stderr),
        )
    })
}

pub fn validate_project_root(value: &str) -> Result<PathBuf, BridgeError> {
    let path = normalize_path(value, "project_root")?;
    if !path.exists() {
        return Err(BridgeError::new(
            "invalid_project_root",
            format!("Project root does not exist: {}", path.display()),
        ));
    }
    if !path.is_dir() {
        return Err(BridgeError::new(
            "invalid_project_root",
            format!("Project root is not a directory: {}", path.display()),
        ));
    }
    path.canonicalize().map_err(|error| {
        BridgeError::new(
            "invalid_project_root",
            format!("Project root cannot be resolved: {error}"),
        )
    })
}

pub fn validate_optional_path(
    value: Option<String>,
    name: &str,
) -> Result<Option<PathBuf>, BridgeError> {
    value.map(|value| normalize_path(&value, name)).transpose()
}

pub fn validate_existing_file(value: &str, name: &str) -> Result<PathBuf, BridgeError> {
    let path = normalize_path(value, name)?;
    if !path.exists() {
        return Err(BridgeError::new(
            "invalid_input",
            format!("{name} does not exist: {}", path.display()),
        ));
    }
    if !path.is_file() {
        return Err(BridgeError::new(
            "invalid_input",
            format!("{name} is not a file: {}", path.display()),
        ));
    }
    path.canonicalize().map_err(|error| {
        BridgeError::new(
            "invalid_input",
            format!("{name} cannot be resolved: {error}"),
        )
    })
}

pub fn validate_item_id(value: &str) -> Result<String, BridgeError> {
    let trimmed = value.trim();
    if trimmed.is_empty() {
        return Err(BridgeError::new("invalid_input", "item_id is required"));
    }
    if !trimmed
        .chars()
        .all(|character| character.is_ascii_alphanumeric() || character == '-' || character == '_')
    {
        return Err(BridgeError::new(
            "invalid_input",
            "item_id contains unsupported characters",
        ));
    }
    Ok(trimmed.to_string())
}

fn normalize_path(value: &str, name: &str) -> Result<PathBuf, BridgeError> {
    let trimmed = value.trim();
    if trimmed.is_empty() {
        return Err(BridgeError::new(
            "invalid_input",
            format!("{name} is required"),
        ));
    }
    Ok(expand_home(trimmed))
}

fn expand_home(value: &str) -> PathBuf {
    if value == "~" {
        return home_dir().unwrap_or_else(|| PathBuf::from(value));
    }
    if let Some(rest) = value.strip_prefix("~/") {
        if let Some(home) = home_dir() {
            return home.join(rest);
        }
    }
    PathBuf::from(value)
}

fn home_dir() -> Option<PathBuf> {
    env::var_os("HOME").map(PathBuf::from)
}

fn python_command() -> Result<Command, BridgeError> {
    let executable =
        env::var_os("HARNEX_MEMORY_PYTHON").unwrap_or_else(|| OsString::from("python3"));
    let mut command = Command::new(executable);
    command.env_remove("PYTHONHOME");
    Ok(command)
}

fn python_path() -> Result<OsString, BridgeError> {
    let mut entries = vec![repo_root().join("src")];
    if let Some(existing) = env::var_os("PYTHONPATH") {
        entries.extend(env::split_paths(&existing));
    }
    env::join_paths(entries)
        .map_err(|error| BridgeError::new("environment", format!("Invalid PYTHONPATH: {error}")))
}

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("src-tauri must live under gui/src-tauri")
        .to_path_buf()
}

fn path_arg(path: &Path) -> String {
    path.to_string_lossy().into_owned()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn list_items_args_include_readonly_after_fixed_project_root_args() {
        let args = CliOperation::ItemsList {
            project_root: PathBuf::from("/tmp/project"),
            cwd: Some(PathBuf::from("/tmp/project/app")),
            include_readonly: true,
        }
        .args();

        assert_eq!(
            args,
            [
                "items",
                "list",
                "--project-root",
                "/tmp/project",
                "--cwd",
                "/tmp/project/app",
                "--include-readonly"
            ]
        );
    }

    #[test]
    fn preview_args_include_expected_source_hash_when_available() {
        let args = CliOperation::ItemsPreview {
            project_root: PathBuf::from("/tmp/project"),
            item_id: "abc123".to_string(),
            action: "disable".to_string(),
            expected_source_hash: Some("deadbeef".to_string()),
        }
        .args();

        assert_eq!(
            args,
            [
                "items",
                "preview",
                "--project-root",
                "/tmp/project",
                "--item-id",
                "abc123",
                "--action",
                "disable",
                "--expected-source-hash",
                "deadbeef"
            ]
        );
    }

    #[test]
    fn docs_apply_args_are_fixed() {
        let args = CliOperation::DocsApply {
            project_root: PathBuf::from("/tmp/project"),
            preview_path: PathBuf::from("/tmp/project/.harnex/memory/previews/preview.json"),
        }
        .args();

        assert_eq!(
            args,
            [
                "docs",
                "apply",
                "--project-root",
                "/tmp/project",
                "--preview",
                "/tmp/project/.harnex/memory/previews/preview.json"
            ]
        );
    }

    #[test]
    fn recommendations_list_args_include_status_when_available() {
        let args = CliOperation::RecommendationsList {
            project_root: PathBuf::from("/tmp/project"),
            status: Some("pending".to_string()),
        }
        .args();

        assert_eq!(
            args,
            [
                "recommendations",
                "list",
                "--project-root",
                "/tmp/project",
                "--status",
                "pending"
            ]
        );
    }

    #[test]
    fn recommendations_apply_args_are_fixed() {
        let args = CliOperation::RecommendationsApply {
            project_root: PathBuf::from("/tmp/project"),
            recommendation_id: "rec123".to_string(),
        }
        .args();

        assert_eq!(
            args,
            [
                "recommendations",
                "apply",
                "--project-root",
                "/tmp/project",
                "--recommendation-id",
                "rec123"
            ]
        );
    }

    #[test]
    fn recommendations_show_args_are_fixed() {
        let args = CliOperation::RecommendationsShow {
            project_root: PathBuf::from("/tmp/project"),
            recommendation_id: "rec123".to_string(),
        }
        .args();

        assert_eq!(
            args,
            [
                "recommendations",
                "show",
                "--project-root",
                "/tmp/project",
                "--recommendation-id",
                "rec123"
            ]
        );
    }

    #[test]
    fn recommendations_dismiss_args_include_reason_when_available() {
        let args = CliOperation::RecommendationsDismiss {
            project_root: PathBuf::from("/tmp/project"),
            recommendation_id: "rec123".to_string(),
            reason: Some("too noisy".to_string()),
        }
        .args();

        assert_eq!(
            args,
            [
                "recommendations",
                "dismiss",
                "--project-root",
                "/tmp/project",
                "--recommendation-id",
                "rec123",
                "--reason",
                "too noisy"
            ]
        );
    }

    #[test]
    fn recommendations_dismiss_args_omit_reason_when_absent() {
        let args = CliOperation::RecommendationsDismiss {
            project_root: PathBuf::from("/tmp/project"),
            recommendation_id: "rec123".to_string(),
            reason: None,
        }
        .args();

        assert_eq!(
            args,
            [
                "recommendations",
                "dismiss",
                "--project-root",
                "/tmp/project",
                "--recommendation-id",
                "rec123"
            ]
        );
    }

    #[test]
    fn recommendation_defaults_origin_when_missing() {
        // Legacy records written before the `origin` field must still deserialize.
        let json = r#"{
            "kind":"repeated_prompt","title":"t","reason":"r","preview_id":"p",
            "preview_path":"pp","target_path":"AGENTS.md","target_kind":"codex_agents",
            "risk":"low","evidence":[],"candidate_id":"c","status":"pending",
            "dismissed_reason":"","created_at":"","updated_at":"","id":"i",
            "schema_version":"harnex-memory/v1"
        }"#;

        let rec: Recommendation = serde_json::from_str(json).unwrap();

        assert_eq!(rec.origin, "");
    }
}
