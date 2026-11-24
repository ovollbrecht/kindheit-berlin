<script setup lang="ts">
import TableScroll from '@/components/TableScroll.vue'
/** Plain table: one row per indicator, one numeric column per place (quarter, Berlin, …). */
export interface ValueRow {
  label: string
  /** Optional explanation under the label. */
  hint?: string
  cells: string[]
}

defineProps<{ caption: string; head: string[]; rows: ValueRow[] }>()
</script>

<template>
  <TableScroll :label="caption">
    <table>
      <caption class="visually-hidden">
        {{
          caption
        }}
      </caption>
      <thead>
        <tr>
          <th scope="col">Kennzahl</th>
          <th v-for="cell in head" :key="cell" scope="col" class="number">{{ cell }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.label">
          <th scope="row">
            {{ row.label }}
            <span v-if="row.hint" class="hint">{{ row.hint }}</span>
          </th>
          <td v-for="(cell, index) in row.cells" :key="index" class="number">{{ cell }}</td>
        </tr>
      </tbody>
    </table>
  </TableScroll>
</template>

<style scoped>
tbody th {
  font-weight: 400;
  font-size: inherit;
  color: inherit;
  border-bottom-color: var(--color-rule-soft);
}
.hint {
  display: block;
  font-size: var(--size-small);
  color: var(--color-ink-secondary);
}
td {
  white-space: nowrap;
}
</style>
