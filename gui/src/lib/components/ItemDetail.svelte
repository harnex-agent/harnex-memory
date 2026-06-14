<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { EyeOff, RotateCcw, Trash2 } from "@lucide/svelte";
  import { actionsForItem, statusTone } from "$lib/stores/itemFilters";
  import type { ItemAction, MemoryItem } from "$lib/types/harnex-memory";

  export let item: MemoryItem | null = null;
  export let loading = false;

  const dispatch = createEventDispatcher<{
    preview: ItemAction;
  }>();

  $: actions = actionsForItem(item);

  function actionLabel(action: ItemAction): string {
    if (action === "delete") {
      return "Delete";
    }
    if (action === "disable") {
      return "Disable";
    }
    return "Enable";
  }

  function actionIcon(action: ItemAction) {
    if (action === "delete") {
      return Trash2;
    }
    if (action === "disable") {
      return EyeOff;
    }
    return RotateCcw;
  }
</script>

<section class="detail-pane">
  {#if !item}
    <div class="empty-state">Select an item</div>
  {:else}
    <header class="detail-header">
      <div class="title-stack">
        <div class="eyebrow">
          <span class={`status-pill ${statusTone(item.status)}`}>{item.status.replace("_", " ")}</span>
          <span>{item.document_kind}</span>
          <span>{item.format}</span>
        </div>
        <h1 title={item.title}>{item.title}</h1>
      </div>

      <div class="actions">
        {#each actions as action}
          {@const Icon = actionIcon(action)}
          <button
            class:danger={action === "delete"}
            class="action-button"
            type="button"
            disabled={loading}
            title={`${actionLabel(action)} preview`}
            on:click={() => dispatch("preview", action)}
          >
            <Icon size={16} />
            <span>{actionLabel(action)}</span>
          </button>
        {/each}
      </div>
    </header>

    <dl class="metadata-grid">
      <div>
        <dt>Path</dt>
        <dd title={item.path}>{item.path}</dd>
      </div>
      <div>
        <dt>Scope</dt>
        <dd>{item.scope}</dd>
      </div>
      <div>
        <dt>Agent</dt>
        <dd>{item.agent || "—"}</dd>
      </div>
      <div>
        <dt>Target</dt>
        <dd>{item.target_kind}</dd>
      </div>
      <div>
        <dt>Hash</dt>
        <dd>{item.source_hash}</dd>
      </div>
      <div>
        <dt>Lines</dt>
        <dd>{item.span ? `${item.span.start_line}-${item.span.end_line}` : "-"}</dd>
      </div>
    </dl>

    {#if item.reason}
      <p class="reason">{item.reason}</p>
    {/if}

    <pre class="body-preview">{item.body}</pre>
  {/if}
</section>
