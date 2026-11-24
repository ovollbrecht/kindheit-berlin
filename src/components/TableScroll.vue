<script setup lang="ts">
/** Wrapper for wide tables: scrolls sideways on small screens and is reachable by keyboard. */
defineProps<{ label: string }>()
</script>

<template>
  <div
    class="table-scroll"
    tabindex="0"
    role="region"
    :aria-label="`${label} (seitlich scrollbar)`"
  >
    <slot />
  </div>
</template>

<style scoped>
.table-scroll {
  overflow-x: auto;
}
</style>
