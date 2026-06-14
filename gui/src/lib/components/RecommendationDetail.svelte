<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { Check, X } from "@lucide/svelte";
  import type {
    ApplyRecommendationPayload,
    RecommendationPreviewPayload
  } from "$lib/types/harnex-memory";

  export let payload: RecommendationPreviewPayload | null = null;
  export let applyResult: ApplyRecommendationPayload | null = null;
  export let loading = false;

  const dispatch = createEventDispatcher<{
    apply: string;
    dismiss: string;
  }>();

  $: recommendation = payload?.recommendation ?? null;
  $: preview = payload?.preview ?? null;
  $: canAct = Boolean(recommendation && recommendation.status === "pending");
</script>

<section class="detail-pane recommendation-detail">
  {#if loading}
    <div class="empty-state">Loading recommendation</div>
  {:else if !recommendation || !preview}
    <div class="empty-state">Select a recommendation</div>
  {:else}
    <header class="detail-header">
      <div class="title-stack">
        <div class="eyebrow">
          <span class="status-pill warn">{recommendation.status}</span>
          <span>{recommendation.kind.replace("_", " ")}</span>
          <span>{recommendation.risk}</span>
        </div>
        <h1 title={recommendation.title}>{recommendation.title}</h1>
      </div>

      <div class="actions">
        <button
          class="action-button"
          type="button"
          disabled={!canAct || loading}
          title="Apply recommendation"
          on:click={() => dispatch("apply", recommendation.id)}
        >
          <Check size={16} />
          <span>Apply</span>
        </button>
        <button
          class="action-button danger"
          type="button"
          disabled={!canAct || loading}
          title="Dismiss recommendation"
          on:click={() => dispatch("dismiss", recommendation.id)}
        >
          <X size={16} />
          <span>Dismiss</span>
        </button>
      </div>
    </header>

    <dl class="metadata-grid recommendation-metadata">
      <div>
        <dt>Target</dt>
        <dd title={recommendation.target_path}>{recommendation.target_path}</dd>
      </div>
      <div>
        <dt>Kind</dt>
        <dd>{recommendation.target_kind}</dd>
      </div>
      <div>
        <dt>Evidence</dt>
        <dd>{recommendation.evidence.length}</dd>
      </div>
      <div>
        <dt>Preview</dt>
        <dd title={recommendation.preview_path}>{recommendation.preview_path}</dd>
      </div>
    </dl>

    <p class="reason">{recommendation.reason}</p>

    <div class="preview-meta">
      <span title={recommendation.preview_id}>{recommendation.preview_id}</span>
      <span>{preview.file_changes.length} files</span>
    </div>

    <div class="recommendation-diffs">
      {#each preview.file_changes as change}
        <article class="diff-block">
          <header>
            <strong title={change.path}>{change.path}</strong>
          </header>
          <pre>{change.diff || "(no diff)"}</pre>
        </article>
      {/each}
    </div>

    {#if applyResult}
      <div class="notice good">
        <Check size={16} />
        <p title={applyResult.apply_result_path}>{applyResult.apply_result_path}</p>
      </div>
    {/if}
  {/if}
</section>
