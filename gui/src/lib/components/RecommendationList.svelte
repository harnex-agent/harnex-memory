<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { CircleCheck, CircleSlash, Clock3, FileWarning } from "@lucide/svelte";
  import type { Recommendation } from "$lib/types/harnex-memory";

  export let recommendations: Recommendation[] = [];
  export let selectedId: string | null = null;

  const dispatch = createEventDispatcher<{
    select: Recommendation;
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
</script>

<aside class="list-pane">
  <div class="filter-bar">
    <div class="pane-title compact-title">
      <div>
        <span>Recommendations</span>
        <strong>{recommendations.length} queued</strong>
      </div>
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
          <span>{recommendation.kind.replace("_", " ")}</span>
          <span title={recommendation.target_path}>{recommendation.target_path}</span>
          <strong title={recommendation.title}>{recommendation.title}</strong>
          <span>{recommendation.risk}</span>
        </button>
      {/each}
    {/if}
  </div>
</aside>
