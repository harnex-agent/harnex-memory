import { describe, expect, it } from "vitest";
import { actionsForItem, createDefaultFilters, filterItems } from "./itemFilters";
import type { MemoryItem } from "$lib/types/harnex-memory";

const baseItem: MemoryItem = {
  document_kind: "rule",
  target_kind: "legacy_rule",
  scope: "project_root",
  path: ".harnex/memory/rules.md",
  title: "Run pytest",
  body: "- Run pytest\n",
  format: "markdown_bullet",
  status: "active",
  span: { start_line: 3, end_line: 3 },
  source_hash: "abc123",
  reason: "",
  agent: "",
  id: "rule-1",
  schema_version: "harnex-memory/v1"
};

describe("item filtering", () => {
  it("matches by query, kind, and status", () => {
    const filters = createDefaultFilters();
    filters.query = "pytest";
    filters.kinds = new Set(["rule"]);
    filters.statuses = new Set(["active"]);

    expect(filterItems([baseItem], filters)).toEqual([baseItem]);

    filters.statuses = new Set(["disabled"]);
    expect(filterItems([baseItem], filters)).toEqual([]);
  });

  it("exposes only safe actions for the current item state", () => {
    expect(actionsForItem(baseItem)).toEqual(["delete", "disable"]);
    expect(actionsForItem({ ...baseItem, status: "disabled" })).toEqual(["enable"]);
    expect(actionsForItem({ ...baseItem, status: "shadowed" })).toEqual([]);
  });

  it("filters by agent while always keeping agent-less legacy items", () => {
    const codexItem: MemoryItem = { ...baseItem, id: "codex-1", agent: "codex" };
    const claudeItem: MemoryItem = { ...baseItem, id: "claude-1", agent: "claude" };
    const items = [baseItem, codexItem, claudeItem];
    const filters = createDefaultFilters();

    // All agents selected by default → everything visible.
    expect(filterItems(items, filters)).toHaveLength(3);

    // Selecting only codex keeps codex items and the agent-less legacy item.
    filters.agents = new Set(["codex"]);
    expect(filterItems(items, filters).map((item) => item.id).sort()).toEqual([
      "codex-1",
      "rule-1"
    ]);

    // Deselecting all agents still keeps the agent-less legacy item.
    filters.agents = new Set();
    expect(filterItems(items, filters).map((item) => item.id)).toEqual(["rule-1"]);
  });

  it("matches an agent name through the query field", () => {
    const claudeItem: MemoryItem = { ...baseItem, id: "claude-1", agent: "claude" };
    const filters = createDefaultFilters();
    filters.query = "claude";

    expect(filterItems([baseItem, claudeItem], filters)).toEqual([claudeItem]);
  });
});
