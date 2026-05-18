<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { Check, FileWarning, ShieldX } from "@lucide/svelte";
  import type { ApplyPayload, PreviewPayload } from "$lib/types/harnex-memory";

  export let payload: PreviewPayload | null = null;
  export let applyResult: ApplyPayload | null = null;
  export let loading = false;

  const dispatch = createEventDispatcher<{
    apply: string;
  }>();

  $: blocked = Boolean(payload?.preview.blocked_reasons.length);
</script>

<section class="preview-pane">
  <header class="pane-title">
    <div>
      <span>Preview</span>
      {#if payload}
        <strong>{payload.preview.action ?? "change"}</strong>
      {/if}
    </div>

    {#if payload}
      <button
        class="primary-button"
        type="button"
        disabled={loading || blocked}
        title={blocked ? "Blocked preview" : "Apply preview"}
        on:click={() => dispatch("apply", payload.preview_path)}
      >
        <Check size={16} />
        <span>{loading ? "Applying" : "Apply"}</span>
      </button>
    {/if}
  </header>

  {#if !payload}
    <div class="empty-state">No preview</div>
  {:else}
    {#if payload.preview.blocked_reasons.length}
      <div class="notice danger">
        <ShieldX size={16} />
        <div>
          {#each payload.preview.blocked_reasons as reason}
            <p>{reason}</p>
          {/each}
        </div>
      </div>
    {/if}

    {#if payload.preview.warnings.length}
      <div class="notice warn">
        <FileWarning size={16} />
        <div>
          {#each payload.preview.warnings as warning}
            <p>{warning}</p>
          {/each}
        </div>
      </div>
    {/if}

    <div class="preview-meta">
      <span title={payload.preview_path}>{payload.preview_path}</span>
      <span>{payload.preview.file_changes.length} files</span>
    </div>

    {#each payload.preview.file_changes as change}
      <article class="diff-block">
        <header>
          <strong title={change.path}>{change.path}</strong>
        </header>
        <pre>{change.diff || "(no diff)"}</pre>
      </article>
    {/each}

    {#if applyResult}
      <div class="notice good">
        <Check size={16} />
        <p title={applyResult.apply_result_path}>{applyResult.apply_result_path}</p>
      </div>
    {/if}
  {/if}
</section>
