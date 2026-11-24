<script setup lang="ts">
import TableScroll from '@/components/TableScroll.vue'
/** Frame around every chart: title, the chart itself, source line and the data as a table. */
defineProps<{
  title: string
  subtitle?: string
  source: string
  /** Column headers and rows of the table alternative. */
  tableHead: string[]
  tableRows: string[][]
}>()
</script>

<template>
  <figure class="chart-figure">
    <figcaption>
      <h3>{{ title }}</h3>
      <p v-if="subtitle" class="secondary small">{{ subtitle }}</p>
    </figcaption>
    <slot />
    <details>
      <summary>Daten als Tabelle</summary>
      <TableScroll class="narrow-table" :label="`Daten zu: ${title}`">
        <table>
          <thead>
            <tr>
              <th
                v-for="(cell, index) in tableHead"
                :key="cell"
                scope="col"
                :class="{ number: index > 0 }"
              >
                {{ cell }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in tableRows" :key="row[0]">
              <template v-for="(cell, index) in row" :key="index">
                <th v-if="index === 0" scope="row">{{ cell }}</th>
                <td v-else class="number">{{ cell }}</td>
              </template>
            </tr>
          </tbody>
        </table>
      </TableScroll>
    </details>
    <p class="source small secondary">{{ source }}</p>
  </figure>
</template>

<style scoped>
.chart-figure {
  margin: var(--space-6) 0;
}
figcaption {
  margin-bottom: var(--space-4);
}
figcaption p {
  margin: var(--space-1) 0 0;
}
details {
  margin-top: var(--space-3);
  font-size: var(--size-small);
}
summary {
  cursor: pointer;
  color: var(--color-accent);
  width: fit-content;
  padding: var(--space-2) 0;
}
.narrow-table {
  max-width: 34rem;
}
tbody th {
  font-weight: 400;
  color: var(--color-ink);
  font-size: inherit;
  border-bottom-color: var(--color-rule-soft);
}
.source {
  margin: var(--space-2) 0 0;
}
</style>
