<script setup lang="ts">
/** Two values per row on a common 0–100 % scale, connected by a line. */
export interface DumbbellRow {
  label: string
  detail: string
  from: number
  to: number
  fromDisplay: string
  toDisplay: string
}

defineProps<{ rows: DumbbellRow[]; fromLabel: string; toLabel: string }>()

const position = (value: number) => `${value * 100}%`
</script>

<template>
  <div>
    <ul class="legend small">
      <li><span class="dot from" aria-hidden="true"></span>{{ fromLabel }}</li>
      <li><span class="dot to" aria-hidden="true"></span>{{ toLabel }}</li>
    </ul>
    <ul class="rows">
      <li v-for="row in rows" :key="row.label">
        <div class="label">
          {{ row.label }}
          <span class="detail">{{ row.detail }}</span>
        </div>
        <div class="track" aria-hidden="true">
          <div
            class="link"
            :style="{ left: position(row.from), width: position(row.to - row.from) }"
          ></div>
          <div class="dot from" :style="{ left: position(row.from) }"></div>
          <div class="dot to" :style="{ left: position(row.to) }"></div>
        </div>
        <div class="values">
          <span>{{ row.fromDisplay }}</span>
          <span class="visually-hidden">, mit OpenStreetMap </span>
          <span aria-hidden="true"> → </span>
          <span>{{ row.toDisplay }}</span>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.legend,
.rows {
  margin: 0;
  padding: 0;
  list-style: none;
}
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1) var(--space-5);
  margin-bottom: var(--space-3);
}
.rows li {
  display: grid;
  grid-template-columns: minmax(8rem, 16rem) 1fr 7.5rem;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--color-rule-soft);
}
.label {
  font-size: var(--size-small);
  line-height: 1.3;
}
.detail {
  display: block;
  color: var(--color-ink-secondary);
}
.track {
  position: relative;
  height: 2px;
  margin: 0 8px;
  background: var(--color-rule-soft);
}
.link {
  position: absolute;
  top: -1px;
  height: 4px;
  background: var(--chart-axis);
}
.dot {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid var(--color-paper);
}
.track .dot {
  position: absolute;
  top: -6px;
  margin-left: -7px;
}
.legend .dot {
  margin-right: var(--space-2);
  vertical-align: -2px;
}
.dot.from {
  background: var(--series-blue);
}
.dot.to {
  background: var(--series-orange);
}
.values {
  text-align: right;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
@media (max-width: 38rem) {
  .rows li {
    grid-template-columns: 1fr auto;
  }
  .label {
    grid-column: 1 / -1;
  }
}
</style>
