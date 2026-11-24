<script setup lang="ts">
defineProps<{ loading: boolean; error: string | null }>()
defineEmits<{ retry: [] }>()
</script>

<template>
  <p v-if="loading" class="state" role="status">Daten werden geladen …</p>
  <div v-else-if="error" class="state note" role="alert">
    <p><strong>Die Daten konnten nicht geladen werden.</strong> {{ error }}</p>
    <button class="button secondary-button" type="button" @click="$emit('retry')">
      Erneut versuchen
    </button>
  </div>
  <slot v-else />
</template>

<style scoped>
.state {
  margin: var(--space-7) 0;
  color: var(--color-ink-secondary);
}
</style>
