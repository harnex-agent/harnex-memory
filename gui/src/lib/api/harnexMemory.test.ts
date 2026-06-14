import { beforeEach, describe, expect, it, vi } from "vitest";

const { invokeMock } = vi.hoisted(() => ({ invokeMock: vi.fn() }));

vi.mock("@tauri-apps/api/core", () => ({
  invoke: invokeMock
}));

import {
  applyRecommendation,
  dismissRecommendation,
  listRecommendations,
  showRecommendation
} from "./harnexMemory";

describe("harnexMemory recommendation API contract", () => {
  beforeEach(() => {
    invokeMock.mockReset();
    invokeMock.mockResolvedValue({});
  });

  it("listRecommendations forwards the status filter when provided", async () => {
    await listRecommendations("/tmp/project", "pending");

    expect(invokeMock).toHaveBeenCalledWith("list_recommendations", {
      projectRoot: "/tmp/project",
      status: "pending"
    });
  });

  it("listRecommendations sends a null status when omitted", async () => {
    await listRecommendations("/tmp/project");

    expect(invokeMock).toHaveBeenCalledWith("list_recommendations", {
      projectRoot: "/tmp/project",
      status: null
    });
  });

  it("showRecommendation invokes show_recommendation with the id", async () => {
    await showRecommendation("/tmp/project", "rec123");

    expect(invokeMock).toHaveBeenCalledWith("show_recommendation", {
      projectRoot: "/tmp/project",
      recommendationId: "rec123"
    });
  });

  it("applyRecommendation invokes apply_recommendation with the id", async () => {
    await applyRecommendation("/tmp/project", "rec123");

    expect(invokeMock).toHaveBeenCalledWith("apply_recommendation", {
      projectRoot: "/tmp/project",
      recommendationId: "rec123"
    });
  });

  it("dismissRecommendation forwards the dismissal reason", async () => {
    await dismissRecommendation("/tmp/project", "rec123", "too noisy");

    expect(invokeMock).toHaveBeenCalledWith("dismiss_recommendation", {
      projectRoot: "/tmp/project",
      recommendationId: "rec123",
      reason: "too noisy"
    });
  });

  it("dismissRecommendation sends a null reason when omitted", async () => {
    await dismissRecommendation("/tmp/project", "rec123");

    expect(invokeMock).toHaveBeenCalledWith("dismiss_recommendation", {
      projectRoot: "/tmp/project",
      recommendationId: "rec123",
      reason: null
    });
  });
});
