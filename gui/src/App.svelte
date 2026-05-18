<script lang="ts">
  import ItemDetail from "$lib/components/ItemDetail.svelte";
  import ItemList from "$lib/components/ItemList.svelte";
  import PreviewPanel from "$lib/components/PreviewPanel.svelte";
  import ProjectSelector from "$lib/components/ProjectSelector.svelte";
  import {
    applyPreview,
    listItems,
    previewItemAction,
    selectProjectRoot,
    showItem
  } from "$lib/api/harnexMemory";
  import { createDefaultFilters } from "$lib/stores/itemFilters";
  import type {
    ApplyPayload,
    BridgeError,
    ItemAction,
    MemoryItem,
    PreviewPayload
  } from "$lib/types/harnex-memory";

  const lastRootKey = "harnex-memory:last-project-root";

  let projectRoot = localStorage.getItem(lastRootKey) ?? "";
  let includeReadonly = false;
  let items: MemoryItem[] = [];
  let selectedItem: MemoryItem | null = null;
  let previewPayload: PreviewPayload | null = null;
  let applyResult: ApplyPayload | null = null;
  let filters = createDefaultFilters();
  let loadingItems = false;
  let loadingPreview = false;
  let applying = false;
  let errorMessage = "";

  function bridgeMessage(error: unknown): string {
    const bridgeError = error as Partial<BridgeError>;
    if (bridgeError?.message) {
      return bridgeError.stderr ? `${bridgeError.message}\n${bridgeError.stderr}` : bridgeError.message;
    }
    return error instanceof Error ? error.message : String(error);
  }

  async function chooseProjectRoot() {
    errorMessage = "";
    try {
      const selection = await selectProjectRoot();
      if (!selection.cancelled && selection.path) {
        projectRoot = selection.path;
        await loadProject();
      }
    } catch (error) {
      errorMessage = bridgeMessage(error);
    }
  }

  async function loadProject() {
    const root = projectRoot.trim();
    if (!root) {
      return;
    }
    loadingItems = true;
    errorMessage = "";
    applyResult = null;
    try {
      localStorage.setItem(lastRootKey, root);
      const payload = await listItems(root, { includeReadonly });
      items = payload.items;
      const selected = selectedItem ? payload.items.find((item) => item.id === selectedItem?.id) : null;
      selectedItem = selected ?? payload.items[0] ?? null;
      previewPayload = null;
    } catch (error) {
      errorMessage = bridgeMessage(error);
    } finally {
      loadingItems = false;
    }
  }

  async function selectItem(item: MemoryItem) {
    if (!projectRoot.trim()) {
      selectedItem = item;
      return;
    }
    errorMessage = "";
    try {
      const payload = await showItem(projectRoot.trim(), item.id);
      selectedItem = payload.item;
      previewPayload = null;
      applyResult = null;
    } catch (error) {
      selectedItem = item;
      errorMessage = bridgeMessage(error);
    }
  }

  async function previewAction(action: ItemAction) {
    if (!selectedItem || !projectRoot.trim()) {
      return;
    }
    loadingPreview = true;
    errorMessage = "";
    applyResult = null;
    try {
      previewPayload = await previewItemAction(
        projectRoot.trim(),
        selectedItem.id,
        action,
        selectedItem.source_hash
      );
    } catch (error) {
      errorMessage = bridgeMessage(error);
    } finally {
      loadingPreview = false;
    }
  }

  async function applyCurrentPreview(previewPath: string) {
    if (!projectRoot.trim()) {
      return;
    }
    applying = true;
    errorMessage = "";
    try {
      applyResult = await applyPreview(projectRoot.trim(), previewPath);
      const payload = await listItems(projectRoot.trim(), { includeReadonly });
      items = payload.items;
      selectedItem = selectedItem
        ? payload.items.find((item) => item.id === selectedItem?.id) ?? payload.items[0] ?? null
        : payload.items[0] ?? null;
    } catch (error) {
      errorMessage = bridgeMessage(error);
    } finally {
      applying = false;
    }
  }
</script>

<main class="app-shell">
  <header class="top-bar">
    <div class="brand">
      <span class="brand-mark">HM</span>
      <div>
        <strong>Harnex Memory</strong>
        <span>{items.length} items</span>
      </div>
    </div>

    <ProjectSelector
      bind:projectRoot
      bind:includeReadonly
      loading={loadingItems}
      on:choose={chooseProjectRoot}
      on:load={loadProject}
      on:projectRootChange={(event) => (projectRoot = event.detail)}
      on:includeReadonlyChange={(event) => (includeReadonly = event.detail)}
    />
  </header>

  {#if errorMessage}
    <div class="error-banner">
      <pre>{errorMessage}</pre>
    </div>
  {/if}

  <div class="workspace-grid">
    <ItemList
      {items}
      selectedId={selectedItem?.id ?? null}
      {filters}
      on:select={(event) => selectItem(event.detail)}
      on:filtersChange={(event) => (filters = event.detail)}
    />

    <div class="right-column">
      <ItemDetail item={selectedItem} loading={loadingPreview} on:preview={(event) => previewAction(event.detail)} />
      <PreviewPanel payload={previewPayload} {applyResult} loading={applying} on:apply={(event) => applyCurrentPreview(event.detail)} />
    </div>
  </div>
</main>
