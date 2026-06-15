<script lang="ts">
  import HookSettings from "$lib/components/HookSettings.svelte";
  import ItemDetail from "$lib/components/ItemDetail.svelte";
  import ItemList from "$lib/components/ItemList.svelte";
  import PreviewPanel from "$lib/components/PreviewPanel.svelte";
  import ProjectSelector from "$lib/components/ProjectSelector.svelte";
  import RecommendationDetail from "$lib/components/RecommendationDetail.svelte";
  import RecommendationList from "$lib/components/RecommendationList.svelte";
  import {
    applyRecommendation,
    applyPreview,
    dismissRecommendation,
    listItems,
    listRecommendations,
    previewItemAction,
    selectProjectRoot,
    showRecommendation,
    showItem
  } from "$lib/api/harnexMemory";
  import { createDefaultFilters } from "$lib/stores/itemFilters";
  import { pendingCount, pendingRecommendations } from "$lib/recommendations";
  import type {
    ApplyPayload,
    ApplyRecommendationPayload,
    BridgeError,
    ItemAction,
    MemoryItem,
    PreviewPayload,
    Recommendation,
    RecommendationPreviewPayload
  } from "$lib/types/harnex-memory";

  const lastRootKey = "harnex-memory:last-project-root";

  let projectRoot = localStorage.getItem(lastRootKey) ?? "";
  let includeReadonly = false;
  let activeTab: "items" | "recommendations" | "hooks" = "items";
  let items: MemoryItem[] = [];
  let recommendations: Recommendation[] = [];
  let selectedItem: MemoryItem | null = null;
  let selectedRecommendation: Recommendation | null = null;
  let previewPayload: PreviewPayload | null = null;
  let recommendationPreviewPayload: RecommendationPreviewPayload | null = null;
  let applyResult: ApplyPayload | null = null;
  let applyRecommendationResult: ApplyRecommendationPayload | null = null;
  let filters = createDefaultFilters();
  let loadingItems = false;
  let loadingRecommendationPreview = false;
  let loadingPreview = false;
  let applying = false;
  let applyingRecommendation = false;
  let batchRunning = false;
  let errorMessage = "";

  $: pendingTotal = pendingCount(recommendations);

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
    applyRecommendationResult = null;
    try {
      localStorage.setItem(lastRootKey, root);
      const [itemsPayload, recommendationsPayload] = await Promise.all([
        listItems(root, { includeReadonly }),
        listRecommendations(root)
      ]);
      items = itemsPayload.items;
      recommendations = recommendationsPayload.recommendations;
      const selected = selectedItem ? itemsPayload.items.find((item) => item.id === selectedItem?.id) : null;
      selectedItem = selected ?? itemsPayload.items[0] ?? null;
      const selectedQueued = selectedRecommendation
        ? recommendationsPayload.recommendations.find((item) => item.id === selectedRecommendation?.id)
        : null;
      selectedRecommendation = selectedQueued ?? recommendationsPayload.recommendations[0] ?? null;
      previewPayload = null;
      recommendationPreviewPayload = null;
      if (selectedRecommendation) {
        recommendationPreviewPayload = await showRecommendation(root, selectedRecommendation.id);
      }
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

  async function selectRecommendation(recommendation: Recommendation) {
    selectedRecommendation = recommendation;
    recommendationPreviewPayload = null;
    applyRecommendationResult = null;
    if (!projectRoot.trim()) {
      return;
    }
    loadingRecommendationPreview = true;
    errorMessage = "";
    try {
      recommendationPreviewPayload = await showRecommendation(projectRoot.trim(), recommendation.id);
    } catch (error) {
      errorMessage = bridgeMessage(error);
    } finally {
      loadingRecommendationPreview = false;
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

  async function applySelectedRecommendation(recommendationId: string) {
    if (!projectRoot.trim()) {
      return;
    }
    applyingRecommendation = true;
    errorMessage = "";
    try {
      applyRecommendationResult = await applyRecommendation(projectRoot.trim(), recommendationId);
      const payload = await listRecommendations(projectRoot.trim());
      recommendations = payload.recommendations;
      selectedRecommendation =
        payload.recommendations.find((item) => item.id === recommendationId) ?? selectedRecommendation;
      if (recommendationPreviewPayload) {
        recommendationPreviewPayload = {
          ...recommendationPreviewPayload,
          recommendation: applyRecommendationResult.recommendation
        };
      }
    } catch (error) {
      errorMessage = bridgeMessage(error);
    } finally {
      applyingRecommendation = false;
    }
  }

  async function dismissSelectedRecommendation(recommendationId: string) {
    if (!projectRoot.trim()) {
      return;
    }
    loadingRecommendationPreview = true;
    errorMessage = "";
    try {
      const result = await dismissRecommendation(projectRoot.trim(), recommendationId);
      const payload = await listRecommendations(projectRoot.trim());
      recommendations = payload.recommendations;
      selectedRecommendation = payload.recommendations.find((item) => item.id === recommendationId) ?? null;
      if (recommendationPreviewPayload) {
        recommendationPreviewPayload = {
          ...recommendationPreviewPayload,
          recommendation: result.recommendation
        };
      }
    } catch (error) {
      errorMessage = bridgeMessage(error);
    } finally {
      loadingRecommendationPreview = false;
    }
  }

  async function refreshRecommendationsAfterBatch() {
    const payload = await listRecommendations(projectRoot.trim());
    recommendations = payload.recommendations;
    selectedRecommendation =
      payload.recommendations.find((item) => item.id === selectedRecommendation?.id) ??
      payload.recommendations[0] ??
      null;
  }

  async function applyAllPending() {
    const root = projectRoot.trim();
    if (!root || batchRunning) {
      return;
    }
    const pending = pendingRecommendations(recommendations);
    if (pending.length === 0) {
      return;
    }
    batchRunning = true;
    errorMessage = "";
    const failures: string[] = [];
    try {
      for (const recommendation of pending) {
        try {
          await applyRecommendation(root, recommendation.id);
        } catch (error) {
          failures.push(`${recommendation.title}: ${bridgeMessage(error)}`);
        }
      }
      await refreshRecommendationsAfterBatch();
      if (failures.length > 0) {
        errorMessage = `Some recommendations could not be applied:\n${failures.join("\n")}`;
      }
    } finally {
      batchRunning = false;
    }
  }

  async function dismissAllPending() {
    const root = projectRoot.trim();
    if (!root || batchRunning) {
      return;
    }
    const pending = pendingRecommendations(recommendations);
    if (pending.length === 0) {
      return;
    }
    batchRunning = true;
    errorMessage = "";
    const failures: string[] = [];
    try {
      for (const recommendation of pending) {
        try {
          await dismissRecommendation(root, recommendation.id);
        } catch (error) {
          failures.push(`${recommendation.title}: ${bridgeMessage(error)}`);
        }
      }
      await refreshRecommendationsAfterBatch();
      if (failures.length > 0) {
        errorMessage = `Some recommendations could not be dismissed:\n${failures.join("\n")}`;
      }
    } finally {
      batchRunning = false;
    }
  }
</script>

<main class="app-shell">
  <header class="top-bar">
    <div class="brand">
      <span class="brand-mark">HM</span>
      <div>
        <strong>Harnex Memory</strong>
        <span>{items.length} items · {recommendations.length} recommendations</span>
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

  <nav class="workspace-tabs" aria-label="Workspace views">
    <button type="button" class:active={activeTab === "items"} on:click={() => (activeTab = "items")}>
      Items
    </button>
    <button
      type="button"
      class:active={activeTab === "recommendations"}
      on:click={() => (activeTab = "recommendations")}
    >
      Recommendations
      {#if pendingTotal > 0}
        <span class="tab-badge" title={`${pendingTotal} pending`}>{pendingTotal}</span>
      {/if}
    </button>
    <button type="button" class:active={activeTab === "hooks"} on:click={() => (activeTab = "hooks")}>
      Hooks
    </button>
  </nav>

  <div class="workspace-grid">
    {#if activeTab === "items"}
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
    {:else if activeTab === "recommendations"}
      <RecommendationList
        {recommendations}
        selectedId={selectedRecommendation?.id ?? null}
        pendingCount={pendingTotal}
        {batchRunning}
        on:select={(event) => selectRecommendation(event.detail)}
        on:applyAll={applyAllPending}
        on:dismissAll={dismissAllPending}
      />

      <RecommendationDetail
        payload={recommendationPreviewPayload}
        applyResult={applyRecommendationResult}
        loading={loadingRecommendationPreview || applyingRecommendation}
        on:apply={(event) => applySelectedRecommendation(event.detail)}
        on:dismiss={(event) => dismissSelectedRecommendation(event.detail)}
      />
    {:else}
      <HookSettings />
    {/if}
  </div>
</main>

<style>
  .tab-badge {
    margin-left: 0.4rem;
    padding: 0 0.4rem;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 700;
    background: var(--accent, #6b6bff);
    color: #fff;
  }
</style>
