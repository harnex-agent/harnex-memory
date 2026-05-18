<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { FolderOpen, RefreshCcw } from "@lucide/svelte";

  export let projectRoot = "";
  export let includeReadonly = false;
  export let loading = false;

  const dispatch = createEventDispatcher<{
    choose: void;
    load: { projectRoot: string; includeReadonly: boolean };
    includeReadonlyChange: boolean;
    projectRootChange: string;
  }>();

  function submit() {
    dispatch("load", { projectRoot, includeReadonly });
  }

  function updateRoot(value: string) {
    projectRoot = value;
    dispatch("projectRootChange", value);
  }

  function updateReadonly(value: boolean) {
    includeReadonly = value;
    dispatch("includeReadonlyChange", value);
  }
</script>

<form class="project-selector" on:submit|preventDefault={submit}>
  <label class="field project-root-field">
    <span>Project root</span>
    <input
      value={projectRoot}
      on:input={(event) => updateRoot(event.currentTarget.value)}
      placeholder="/Users/minii/mycode/harnex/harnex-memory"
      spellcheck="false"
    />
  </label>

  <button class="icon-button" type="button" title="Choose project root" on:click={() => dispatch("choose")}>
    <FolderOpen size={17} />
  </button>

  <label class="toggle" title="Include read-only items">
    <input
      type="checkbox"
      checked={includeReadonly}
      on:change={(event) => updateReadonly(event.currentTarget.checked)}
    />
    <span>Read-only</span>
  </label>

  <button class="primary-button" type="submit" disabled={loading || !projectRoot.trim()} title="Refresh items">
    <RefreshCcw size={16} />
    <span>{loading ? "Loading" : "Load"}</span>
  </button>
</form>
