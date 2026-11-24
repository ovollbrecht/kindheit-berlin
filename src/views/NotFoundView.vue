<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="page text-column not-found">
    <h1>Diese Seite gibt es nicht</h1>
    <p class="lead">Vielleicht wurde der Link unvollständig kopiert.</p>
    <p><RouterLink class="button" to="/">Zur Startseite</RouterLink></p>
  </div>
</template>

<style scoped>
.not-found {
  padding-top: var(--space-8);
}
h1 {
  margin-bottom: var(--space-4);
}
</style>
