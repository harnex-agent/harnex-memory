<script lang="ts">
  import { onMount } from "svelte";
  import { hookStatus, installHook, uninstallHook } from "$lib/api/harnexMemory";
  import type { HookStatus } from "$lib/types/harnex-memory";

  const agents = ["codex", "claude"];

  let rows: HookStatus[] = [];
  let busyAgent = "";
  let loading = true;
  let error = "";

  function message(value: unknown): string {
    const bridge = value as { message?: string; stderr?: string };
    if (bridge?.message) {
      return bridge.stderr ? `${bridge.message}\n${bridge.stderr}` : bridge.message;
    }
    return value instanceof Error ? value.message : String(value);
  }

  async function load() {
    loading = true;
    error = "";
    try {
      rows = await Promise.all(agents.map((agent) => hookStatus(agent)));
    } catch (value) {
      error = message(value);
    } finally {
      loading = false;
    }
  }

  async function toggle(row: HookStatus) {
    busyAgent = row.agent;
    error = "";
    try {
      const updated = row.installed ? await uninstallHook(row.agent) : await installHook(row.agent);
      rows = rows.map((item) => (item.agent === updated.agent ? { ...item, ...updated } : item));
    } catch (value) {
      error = message(value);
    } finally {
      busyAgent = "";
    }
  }

  onMount(load);
</script>

<section class="hook-settings">
  <div class="hook-header">
    <h2>Prompt-submit hooks</h2>
    <p class="hook-hint">
      Activate to auto-record each submitted prompt. This adds or removes the
      <code>UserPromptSubmit</code> hook in the agent's user config.
    </p>
  </div>

  {#if error}
    <div class="hook-error"><pre>{error}</pre></div>
  {/if}

  {#if loading}
    <div class="hook-empty">Loading hook status…</div>
  {:else}
    {#each rows as row (row.agent)}
      <div class="hook-row">
        <div class="hook-meta">
          <div class="hook-title">
            <strong>{row.agent}</strong>
            <span class={`hook-badge ${row.installed ? "on" : "off"}`}>
              {row.installed ? "Active" : "Inactive"}
            </span>
          </div>
          <code class="hook-path" title={row.config_path}>{row.config_path}</code>
        </div>
        <button
          type="button"
          class={`hook-button ${row.installed ? "danger" : "primary"}`}
          disabled={busyAgent === row.agent}
          on:click={() => toggle(row)}
        >
          {row.installed ? "Deactivate" : "Activate"}
        </button>
      </div>
    {/each}
  {/if}
</section>

<style>
  .hook-settings {
    grid-column: 1 / -1;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 1rem;
  }

  .hook-header h2 {
    margin: 0 0 0.25rem;
  }

  .hook-hint {
    margin: 0;
    font-size: 0.85rem;
    opacity: 0.75;
  }

  .hook-error {
    border: 1px solid var(--danger, #d9534f);
    border-radius: 0.4rem;
    padding: 0.5rem 0.75rem;
  }

  .hook-error pre {
    margin: 0;
    white-space: pre-wrap;
    font-size: 0.8rem;
  }

  .hook-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.75rem 1rem;
    border: 1px solid var(--border, rgba(120, 120, 140, 0.3));
    border-radius: 0.5rem;
  }

  .hook-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .hook-badge {
    padding: 0 0.4rem;
    border-radius: 0.25rem;
    font-size: 0.7rem;
    font-weight: 700;
  }

  .hook-badge.on {
    background: var(--good-soft, rgba(60, 180, 120, 0.18));
    color: var(--good, #2faa6e);
  }

  .hook-badge.off {
    background: var(--muted-soft, rgba(120, 120, 140, 0.18));
    color: var(--muted, #8a8a98);
  }

  .hook-path {
    display: block;
    margin-top: 0.25rem;
    font-size: 0.75rem;
    opacity: 0.7;
  }

  .hook-button {
    padding: 0.4rem 0.9rem;
    border-radius: 0.4rem;
    border: 1px solid var(--border, rgba(120, 120, 140, 0.3));
    background: transparent;
    color: inherit;
    cursor: pointer;
    white-space: nowrap;
  }

  .hook-button.primary {
    border-color: var(--accent, #6b6bff);
    color: var(--accent, #6b6bff);
  }

  .hook-button:disabled {
    opacity: 0.5;
    cursor: default;
  }
</style>
