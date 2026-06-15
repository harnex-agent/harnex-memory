import { invoke } from "@tauri-apps/api/core";
import type {
  ApplyPayload,
  ApplyRecommendationPayload,
  HookStatus,
  ItemAction,
  ItemPayload,
  ItemsPayload,
  PreviewPayload,
  ProjectRootSelection,
  RecommendationPayload,
  RecommendationPreviewPayload,
  RecommendationsPayload,
  RecommendationStatus
} from "$lib/types/harnex-memory";

export function selectProjectRoot(): Promise<ProjectRootSelection> {
  return invoke<ProjectRootSelection>("select_project_root");
}

export function listItems(
  projectRoot: string,
  options: { cwd?: string; includeReadonly?: boolean } = {}
): Promise<ItemsPayload> {
  return invoke<ItemsPayload>("list_items", {
    projectRoot,
    cwd: options.cwd || null,
    includeReadonly: options.includeReadonly ?? false
  });
}

export function showItem(projectRoot: string, itemId: string): Promise<ItemPayload> {
  return invoke<ItemPayload>("show_item", {
    projectRoot,
    itemId
  });
}

export function previewItemAction(
  projectRoot: string,
  itemId: string,
  action: ItemAction,
  expectedSourceHash?: string
): Promise<PreviewPayload> {
  return invoke<PreviewPayload>("preview_item_action", {
    projectRoot,
    itemId,
    action,
    expectedSourceHash: expectedSourceHash || null
  });
}

export function applyPreview(projectRoot: string, previewPath: string): Promise<ApplyPayload> {
  return invoke<ApplyPayload>("apply_preview", {
    projectRoot,
    previewPath
  });
}

export function listRecommendations(
  projectRoot: string,
  status?: RecommendationStatus | string
): Promise<RecommendationsPayload> {
  return invoke<RecommendationsPayload>("list_recommendations", {
    projectRoot,
    status: status || null
  });
}

export function showRecommendation(
  projectRoot: string,
  recommendationId: string
): Promise<RecommendationPreviewPayload> {
  return invoke<RecommendationPreviewPayload>("show_recommendation", {
    projectRoot,
    recommendationId
  });
}

export function applyRecommendation(
  projectRoot: string,
  recommendationId: string
): Promise<ApplyRecommendationPayload> {
  return invoke<ApplyRecommendationPayload>("apply_recommendation", {
    projectRoot,
    recommendationId
  });
}

export function dismissRecommendation(
  projectRoot: string,
  recommendationId: string,
  reason = ""
): Promise<RecommendationPayload> {
  return invoke<RecommendationPayload>("dismiss_recommendation", {
    projectRoot,
    recommendationId,
    reason: reason || null
  });
}

export function hookStatus(agent: string): Promise<HookStatus> {
  return invoke<HookStatus>("hook_status", { agent });
}

export function installHook(agent: string): Promise<HookStatus> {
  return invoke<HookStatus>("install_hook", { agent });
}

export function uninstallHook(agent: string): Promise<HookStatus> {
  return invoke<HookStatus>("uninstall_hook", { agent });
}
