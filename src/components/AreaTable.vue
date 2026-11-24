<script setup lang="ts">
import TableScroll from '@/components/TableScroll.vue'
/** Sortable table of planning areas: the text alternative to the map. */
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { formatCount, formatValue, type ValueFormat } from '@/domain/format'

export interface AreaRow {
  id: string
  name: string
  district: string
  children: number
  value: number | null
}

const props = defineProps<{
  rows: AreaRow[]
  valueLabel: string
  format: ValueFormat
  selectedId?: string | null
}>()

type SortKey = 'name' | 'district' | 'children' | 'value'
const INITIAL_ROWS = 12

const sortKey = ref<SortKey>('value')
const ascending = ref(true)
const showAll = ref(false)

const columns: { key: SortKey; label: () => string; numeric: boolean }[] = [
  { key: 'name', label: () => 'Planungsraum', numeric: false },
  { key: 'district', label: () => 'Bezirk', numeric: false },
  { key: 'children', label: () => 'Kinder unter 18', numeric: true },
  { key: 'value', label: () => props.valueLabel, numeric: true },
]

function sortBy(key: SortKey): void {
  if (sortKey.value === key) ascending.value = !ascending.value
  else {
    sortKey.value = key
    ascending.value = true
  }
}

const sorted = computed(() => {
  const direction = ascending.value ? 1 : -1
  const key = sortKey.value
  return [...props.rows].sort((a, b) => {
    const left = a[key]
    const right = b[key]
    // Rows without a value always go last, whatever the direction.
    if (left === null) return right === null ? 0 : 1
    if (right === null) return -1
    if (typeof left === 'string' || typeof right === 'string')
      return direction * String(left).localeCompare(String(right), 'de')
    return direction * (left - right)
  })
})
const visible = computed(() => (showAll.value ? sorted.value : sorted.value.slice(0, INITIAL_ROWS)))
const ariaSort = (key: SortKey) =>
  sortKey.value !== key ? 'none' : ascending.value ? 'ascending' : 'descending'
</script>

<template>
  <div>
    <TableScroll :label="`Tabelle der Planungsräume: ${valueLabel}`">
      <table>
        <caption class="visually-hidden">
          Planungsräume mit
          {{
            valueLabel
          }}, sortierbar über die Spaltenköpfe
        </caption>
        <thead>
          <tr>
            <th
              v-for="column in columns"
              :key="column.key"
              scope="col"
              :class="{ number: column.numeric }"
              :aria-sort="ariaSort(column.key)"
            >
              <button type="button" @click="sortBy(column.key)">
                {{ column.label() }}
                <span aria-hidden="true">{{
                  sortKey === column.key ? (ascending ? '▲' : '▼') : ''
                }}</span>
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in visible" :key="row.id" :class="{ selected: row.id === selectedId }">
            <th scope="row">
              <RouterLink :to="{ name: 'profile', params: { id: row.id } }">{{
                row.name
              }}</RouterLink>
            </th>
            <td>{{ row.district }}</td>
            <td class="number">{{ formatCount(row.children) }}</td>
            <td class="number">{{ formatValue(row.value, format) }}</td>
          </tr>
        </tbody>
      </table>
    </TableScroll>
    <button
      v-if="rows.length > INITIAL_ROWS"
      class="button secondary-button toggle"
      type="button"
      @click="showAll = !showAll"
    >
      {{ showAll ? 'Weniger anzeigen' : `Alle ${rows.length} Planungsräume anzeigen` }}
    </button>
  </div>
</template>

<style scoped>
th button {
  all: unset;
  cursor: pointer;
  font-weight: 600;
}
th button:focus-visible {
  outline: 3px solid var(--color-accent);
  outline-offset: 2px;
}
tbody th {
  font-weight: 400;
  font-size: inherit;
  color: inherit;
  border-bottom-color: var(--color-rule-soft);
}
tr.selected {
  background: var(--color-accent-soft);
}
.toggle {
  margin-top: var(--space-4);
}
</style>
