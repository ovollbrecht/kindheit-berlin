<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { NAVIGATION } from '@/router'
</script>

<template>
  <header class="site-header">
    <div class="page bar">
      <RouterLink class="brand" to="/">Kindheit in Berlin</RouterLink>
      <nav aria-label="Hauptnavigation">
        <ul>
          <li v-for="item in NAVIGATION" :key="item.name">
            <RouterLink :to="item.path">{{ item.label }}</RouterLink>
          </li>
        </ul>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.site-header {
  border-bottom: 1px solid var(--color-rule);
  background: var(--color-paper);
}
.bar {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-2) var(--space-6);
  padding-top: var(--space-4);
  padding-bottom: var(--space-3);
}
.brand {
  font-family: var(--font-display);
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--color-ink);
  text-decoration: none;
}
ul {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1) var(--space-5);
  margin: 0;
  padding: 0;
  list-style: none;
}
nav a {
  display: inline-block;
  padding: var(--space-2) 0;
  color: var(--color-ink-secondary);
  text-decoration: none;
  border-bottom: 2px solid transparent;
}
nav a:hover {
  color: var(--color-ink);
}
nav a.router-link-exact-active {
  color: var(--color-ink);
  font-weight: 600;
  border-bottom-color: var(--color-highlight);
}
</style>
