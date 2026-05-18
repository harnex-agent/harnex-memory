import type { ItemAction, ItemStatus, MemoryItem } from "$lib/types/harnex-memory";

export interface ItemFilters {
  query: string;
  kinds: Set<string>;
  statuses: Set<string>;
}

export const KIND_FILTERS = ["skill", "rule", "hook"] as const;
export const STATUS_FILTERS = ["active", "disabled", "shadowed", "conflict", "read_only"] as const;

export function createDefaultFilters(): ItemFilters {
  return {
    query: "",
    kinds: new Set(KIND_FILTERS),
    statuses: new Set(STATUS_FILTERS)
  };
}

export function filterItems(items: MemoryItem[], filters: ItemFilters): MemoryItem[] {
  const query = filters.query.trim().toLowerCase();
  return items.filter((item) => {
    const kindMatch = filters.kinds.has(item.document_kind);
    const statusMatch = filters.statuses.has(item.status);
    const queryMatch =
      !query ||
      [item.title, item.path, item.scope, item.target_kind, item.reason]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(query));
    return kindMatch && statusMatch && queryMatch;
  });
}

export function actionsForItem(item: MemoryItem | null): ItemAction[] {
  if (!item) {
    return [];
  }
  if (item.status === "active") {
    return ["delete", "disable"];
  }
  if (item.status === "disabled") {
    return ["enable"];
  }
  return [];
}

export function statusTone(status: ItemStatus | string): "good" | "muted" | "warn" | "danger" {
  if (status === "active") {
    return "good";
  }
  if (status === "disabled" || status === "read_only") {
    return "muted";
  }
  if (status === "shadowed") {
    return "warn";
  }
  return "danger";
}
