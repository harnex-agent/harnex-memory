import { describe, expect, it } from "vitest";

import { pendingCount, pendingRecommendations } from "./recommendations";
import type { Recommendation } from "$lib/types/harnex-memory";

function rec(id: string, status: string): Recommendation {
  return {
    kind: "repeated_prompt",
    title: id,
    reason: "",
    preview_id: "",
    preview_path: "",
    target_path: "",
    target_kind: "",
    risk: "low",
    evidence: [],
    candidate_id: "",
    status,
    dismissed_reason: "",
    origin: "heuristic",
    created_at: "",
    updated_at: "",
    id,
    schema_version: "harnex-memory/v1"
  };
}

describe("pending recommendation helpers", () => {
  const recommendations = [
    rec("a", "pending"),
    rec("b", "applied"),
    rec("c", "pending"),
    rec("d", "dismissed")
  ];

  it("pendingRecommendations keeps only pending entries", () => {
    expect(pendingRecommendations(recommendations).map((item) => item.id)).toEqual(["a", "c"]);
  });

  it("pendingCount counts only pending entries", () => {
    expect(pendingCount(recommendations)).toBe(2);
    expect(pendingCount([])).toBe(0);
  });
});
