<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppFooter from './components/AppFooter.vue'
import AppHeader from './components/AppHeader.vue'

const route = useRoute()
const main = ref<HTMLElement | null>(null)

// After navigating to another page, move keyboard and screen-reader focus to the new content.
watch(
  () => route.path,
  async (path, previous) => {
    if (previous === undefined) return
    await nextTick()
    main.value?.focus({ preventScroll: true })
  },
)
</script>

<template>
  <a class="skip-link" href="#inhalt" @click.prevent="main?.focus()">Zum Inhalt springen</a>
  <AppHeader />
  <main id="inhalt" ref="main" tabindex="-1">
    <RouterView />
  </main>
  <AppFooter />
</template>

<style scoped>
.skip-link {
  position: absolute;
  left: var(--space-4);
  top: -4rem;
  z-index: 10;
  padding: var(--space-3) var(--space-4);
  background: var(--color-ink);
  color: #fff;
}
.skip-link:focus {
  top: var(--space-3);
}
main {
  min-height: 60vh;
}
main:focus {
  outline: none;
}
</style>
