export type DocumentKind = "skill" | "rule" | "hook";
export type ItemAction = "delete" | "disable" | "enable";
export type ItemStatus = "active" | "disabled" | "shadowed" | "conflict" | "read_only" | "deleted";
export type RecommendationStatus = "pending" | "applied" | "dismissed" | "stale";
export type RecommendationOrigin = "heuristic" | "llm_review";
export type ItemFormat =
  | "markdown_section"
  | "markdown_bullet"
  | "starlark_rule"
  | "toml_config"
  | "json_hook"
  | "skill_document";

export interface TextSpan {
  start_line: number;
  end_line: number;
}

export interface MemoryItem {
  document_kind: DocumentKind;
  target_kind: string;
  scope: string;
  path: string;
  title: string;
  body: string;
  format: ItemFormat | string;
  status: ItemStatus | string;
  span: TextSpan | null;
  source_hash: string;
  reason: string;
  agent: string;
  id: string;
  schema_version: string;
}

export interface MemoryCandidate {
  target: DocumentKind;
  title: string;
  content: string;
  reason: string;
  evidence: string[];
  risk: "low" | "medium" | "high";
  target_kind: string | null;
  target_path: string | null;
  insertion_strategy: string | null;
  section: string | null;
  id: string;
}

export interface FileChange {
  path: string;
  before: string;
  after: string;
  diff: string;
}

export interface Preview {
  project_root: string;
  preview_id: string;
  source: string;
  candidates: MemoryCandidate[];
  file_changes: FileChange[];
  warnings: string[];
  action: ItemAction | string | null;
  items: MemoryItem[];
  blocked_reasons: string[];
  schema_version: string;
}

export interface ItemsPayload {
  items: MemoryItem[];
}

export interface ItemPayload {
  item: MemoryItem;
}

export interface PreviewPayload {
  preview_path: string;
  preview: Preview;
}

export interface ApplyPayload {
  apply_result_path: string;
}

export interface Recommendation {
  kind: string;
  title: string;
  reason: string;
  preview_id: string;
  preview_path: string;
  target_path: string;
  target_kind: string;
  risk: "low" | "medium" | "high" | string;
  evidence: string[];
  candidate_id: string;
  status: RecommendationStatus | string;
  dismissed_reason: string;
  origin: RecommendationOrigin | string;
  created_at: string;
  updated_at: string;
  id: string;
  schema_version: string;
}

export interface RecommendationsPayload {
  recommendations: Recommendation[];
}

export interface RecommendationPreviewPayload {
  recommendation: Recommendation;
  preview: Preview;
}

export interface RecommendationPayload {
  recommendation: Recommendation;
}

export interface ApplyRecommendationPayload {
  apply_result_path: string;
  recommendation: Recommendation;
}

export interface ProjectRootSelection {
  path: string | null;
  cancelled: boolean;
}

export interface BridgeError {
  kind: string;
  message: string;
  stderr?: string | null;
}
