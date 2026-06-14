import type { ItemAction, ItemStatus, MemoryItem } from "$lib/types/harnex-memory";

export interface ItemFilters {
  query: string;
  kinds: Set<string>;
  statuses: Set<string>;
  agents: Set<string>;
}

export const KIND_FILTERS = ["skill", "rule", "hook"] as const;
export const STATUS_FILTERS = ["active", "disabled", "shadowed", "conflict", "read_only"] as const;
export const AGENT_FILTERS = ["codex", "claude"] as const;

export function createDefaultFilters(): ItemFilters {
  return {
    query: "",
    kinds: new Set(KIND_FILTERS),
    statuses: new Set(STATUS_FILTERS),
    agents: new Set(AGENT_FILTERS)
  };
}

export function filterItems(items: MemoryItem[], filters: ItemFilters): MemoryItem[] {
  const query = filters.query.trim().toLowerCase();
  return items.filter((item) => {
    const kindMatch = filters.kinds.has(item.document_kind);
    const statusMatch = filters.statuses.has(item.status);
    // Legacy items carry no agent; keep them visible regardless of the agent filter.
    const agentMatch = !item.agent || filters.agents.has(item.agent);
    const queryMatch =
      !query ||
      [item.title, item.path, item.scope, item.target_kind, item.reason, item.agent]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(query));
    return kindMatch && statusMatch && agentMatch && queryMatch;
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
