<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { CircleCheck, CircleSlash, Clock3, FileWarning } from "@lucide/svelte";
  import type { Recommendation } from "$lib/types/harnex-memory";

  export let recommendations: Recommendation[] = [];
  export let selectedId: string | null = null;
  export let pendingCount = 0;
  export let batchRunning = false;

  const dispatch = createEventDispatcher<{
    select: Recommendation;
    applyAll: void;
    dismissAll: void;
  }>();

  function statusIcon(status: string) {
    if (status === "pending") {
      return Clock3;
    }
    if (status === "applied") {
      return CircleCheck;
    }
    if (status === "dismissed") {
      return CircleSlash;
    }
    return FileWarning;
  }

  function statusTone(status: string): "good" | "muted" | "warn" | "danger" {
    if (status === "applied") {
      return "good";
    }
    if (status === "dismissed") {
      return "muted";
    }
    if (status === "pending") {
      return "warn";
    }
    return "danger";
  }

  // Surface non-heuristic provenance (e.g. an LLM review pass) like hermes-agent's
  // [auto] tag. Heuristic suggestions are the default and stay unlabeled.
  function originLabel(origin: string | undefined): string {
    return origin === "llm_review" ? "LLM" : "";
  }
</script>

<aside class="list-pane">
  <div class="filter-bar">
    <div class="pane-title compact-title">
      <div>
        <span>Recommendations</span>
        <strong>{recommendations.length} queued</strong>
      </div>
    </div>
    <div class="batch-actions">
      <button
        type="button"
        class="batch-button"
        disabled={pendingCount === 0 || batchRunning}
        on:click={() => dispatch("applyAll")}
      >
        Apply all ({pendingCount})
      </button>
      <button
        type="button"
        class="batch-button"
        disabled={pendingCount === 0 || batchRunning}
        on:click={() => dispatch("dismissAll")}
      >
        Dismiss all
      </button>
    </div>
  </div>

  <div class="item-table" role="listbox" aria-label="Memory recommendations">
    <div class="recommendation-heading">
      <span>Status</span>
      <span>Kind</span>
      <span>Target</span>
      <span>Title</span>
      <span>Risk</span>
    </div>

    {#if recommendations.length === 0}
      <div class="empty-state">No recommendations</div>
    {:else}
      {#each recommendations as recommendation (recommendation.id)}
        {@const Icon = statusIcon(recommendation.status)}
        <button
          type="button"
          class="recommendation-row"
          class:selected={recommendation.id === selectedId}
          title={`${recommendation.title}\n${recommendation.target_path}`}
          on:click={() => dispatch("select", recommendation)}
        >
          <span class={`status-dot ${statusTone(recommendation.status)}`} title={recommendation.status}>
            <Icon size={15} />
          </span>
          <span>
            {recommendation.kind.replace("_", " ")}
            {#if originLabel(recommendation.origin)}
              <span class="origin-chip" title={`origin: ${recommendation.origin}`}
                >{originLabel(recommendation.origin)}</span
              >
            {/if}
          </span>
          <span title={recommendation.target_path}>{recommendation.target_path}</span>
          <strong title={recommendation.title}>{recommendation.title}</strong>
          <span>{recommendation.risk}</span>
        </button>
      {/each}
    {/if}
  </div>
</aside>

<style>
  .origin-chip {
    margin-left: 0.35rem;
    padding: 0 0.3rem;
    border-radius: 0.25rem;
    font-size: 0.65rem;
    font-weight: 600;
    background: var(--accent-soft, rgba(120, 120, 255, 0.18));
    color: var(--accent, #6b6bff);
    vertical-align: middle;
  }

  .batch-actions {
    display: flex;
    gap: 0.4rem;
    padding: 0 0.75rem 0.5rem;
  }

  .batch-button {
    flex: 1;
    padding: 0.3rem 0.5rem;
    font-size: 0.75rem;
    border-radius: 0.3rem;
    border: 1px solid var(--border, rgba(120, 120, 140, 0.3));
    background: transparent;
    color: inherit;
    cursor: pointer;
  }

  .batch-button:disabled {
    opacity: 0.45;
    cursor: default;
  }
</style>
