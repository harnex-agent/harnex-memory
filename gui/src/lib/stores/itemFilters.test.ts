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
});
