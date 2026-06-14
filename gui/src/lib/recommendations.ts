import type { Recommendation } from "$lib/types/harnex-memory";

export function pendingRecommendations(recommendations: Recommendation[]): Recommendation[] {
  return recommendations.filter((recommendation) => recommendation.status === "pending");
}

export function pendingCount(recommendations: Recommendation[]): number {
  return pendingRecommendations(recommendations).length;
}
