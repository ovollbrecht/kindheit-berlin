<script setup lang="ts">
defineProps<{ value: string; caption: string }>()
</script>

<template>
  <div class="key-figure">
    <p class="value">{{ value }}</p>
    <p class="caption">{{ caption }}</p>
  </div>
</template>

<style scoped>
.key-figure {
  border-top: 2px solid var(--color-ink);
  padding-top: var(--space-3);
}
.value {
  font-family: var(--font-display);
  font-size: var(--size-figure);
  font-weight: 600;
  line-height: 1;
  margin: 0 0 var(--space-2);
  font-variant-numeric: lining-nums;
}
.caption {
  margin: 0;
  color: var(--color-ink-secondary);
  font-size: var(--size-small);
  max-width: 22rem;
}
</style>
