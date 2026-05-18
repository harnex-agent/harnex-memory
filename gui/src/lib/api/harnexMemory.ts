import { invoke } from "@tauri-apps/api/core";
import type {
  ApplyPayload,
  ItemAction,
  ItemPayload,
  ItemsPayload,
  PreviewPayload,
  ProjectRootSelection
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
