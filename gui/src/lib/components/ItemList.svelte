<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { CircleAlert, CircleCheck, CircleSlash, LockKeyhole, Search, ShieldAlert } from "@lucide/svelte";
  import type { ItemFilters } from "$lib/stores/itemFilters";
  import { filterItems, statusTone } from "$lib/stores/itemFilters";
  import type { MemoryItem } from "$lib/types/harnex-memory";

  export let items: MemoryItem[] = [];
  export let selectedId: string | null = null;
  export let filters: ItemFilters;

  const dispatch = createEventDispatcher<{
    select: MemoryItem;
    filtersChange: ItemFilters;
  }>();

  const kindOptions = ["skill", "rule", "hook"] as const;
  const statusOptions = ["active", "disabled", "shadowed", "conflict", "read_only"] as const;

  $: visibleItems = filterItems(items, filters);

  function setQuery(query: string) {
    dispatch("filtersChange", { ...filters, query });
  }

  function toggleSet(kind: "kinds" | "statuses", value: string) {
    const next = new Set(filters[kind]);
    if (next.has(value)) {
      next.delete(value);
    } else {
      next.add(value);
    }
    dispatch("filtersChange", { ...filters, [kind]: next });
  }

  function statusIcon(status: string) {
    if (status === "active") {
      return CircleCheck;
    }
    if (status === "disabled") {
      return CircleSlash;
    }
    if (status === "read_only") {
      return LockKeyhole;
    }
    if (status === "shadowed") {
      return ShieldAlert;
    }
    return CircleAlert;
  }
</script>

<aside class="list-pane">
  <div class="filter-bar">
    <label class="search-field">
      <Search size={15} />
      <input
        value={filters.query}
        on:input={(event) => setQuery(event.currentTarget.value)}
        placeholder="Filter"
        spellcheck="false"
      />
    </label>

    <div class="filter-groups">
      <div class="segmented" aria-label="Kind filters">
        {#each kindOptions as kind}
          <button
            class:active={filters.kinds.has(kind)}
            type="button"
            title={kind}
            on:click={() => toggleSet("kinds", kind)}
          >
            {kind}
          </button>
        {/each}
      </div>

      <div class="segmented status-filters" aria-label="Status filters">
        {#each statusOptions as status}
          <button
            class:active={filters.statuses.has(status)}
            type="button"
            title={status}
            on:click={() => toggleSet("statuses", status)}
          >
            {status.replace("_", " ")}
          </button>
        {/each}
      </div>
    </div>
  </div>

  <div class="item-table" role="listbox" aria-label="Memory items">
    <div class="item-heading">
      <span>Status</span>
      <span>Kind</span>
      <span>Scope</span>
      <span>Title</span>
      <span>Path</span>
      <span>Lines</span>
    </div>

    {#if visibleItems.length === 0}
      <div class="empty-state">No items</div>
    {:else}
      {#each visibleItems as item (item.id)}
        {@const Icon = statusIcon(item.status)}
        <button
          type="button"
          class="item-row"
          class:selected={item.id === selectedId}
          on:click={() => dispatch("select", item)}
          title={`${item.title}\n${item.path}`}
        >
          <span class={`status-dot ${statusTone(item.status)}`} title={item.status}>
            <Icon size={15} />
          </span>
          <span>{item.document_kind}</span>
          <span title={item.scope}>{item.scope}</span>
          <strong title={item.title}>{item.title}</strong>
          <span title={item.path}>{item.path}</span>
          <span>{item.span ? `${item.span.start_line}-${item.span.end_line}` : "-"}</span>
        </button>
      {/each}
    {/if}
  </div>
</aside>
