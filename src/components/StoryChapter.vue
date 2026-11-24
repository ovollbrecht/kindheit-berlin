<script setup lang="ts">
/** One chapter of the story: numbered heading, text column, a wide slot for the figure. */
defineProps<{ number: number; title: string }>()
</script>

<template>
  <section class="chapter page" :aria-labelledby="`kapitel-${number}`">
    <div class="text-column">
      <p class="eyebrow">Erkenntnis {{ number }}</p>
      <h2 :id="`kapitel-${number}`">{{ title }}</h2>
      <div class="body"><slot /></div>
    </div>
    <div class="figure-column"><slot name="figure" /></div>
    <div class="text-column"><slot name="after" /></div>
  </section>
</template>

<style scoped>
.chapter {
  padding-top: var(--space-8);
  padding-bottom: var(--space-6);
  border-top: 1px solid var(--color-rule);
}
.body {
  margin-top: var(--space-5);
}
.figure-column {
  max-width: 54rem;
}
</style>
