<script setup lang="ts">
/** Horizontal bars as an ordinary list: readable without the bars, responsive by default. */
export interface BarRow {
  label: string
  value: number | null
  display: string
  /** Optional second line under the label. */
  detail?: string
  /** Optional reference value drawn as a tick on the bar, e.g. the Berlin value. */
  reference?: number | null
}

defineProps<{
  rows: BarRow[]
  /** Value that corresponds to a full-width bar. */
  max: number
  /** Explains the reference tick, e.g. "Berlin insgesamt". */
  referenceLabel?: string
}>()

const percent = (value: number, max: number) =>
  `${Math.min(100, Math.max(0, (value / max) * 100))}%`
</script>

<template>
  <div>
    <ul class="bar-list">
      <li v-for="row in rows" :key="row.label">
        <div class="label">
          {{ row.label }}
          <span v-if="row.detail" class="detail">{{ row.detail }}</span>
        </div>
        <div class="track" aria-hidden="true">
          <div
            v-if="row.value !== null"
            class="bar"
            :style="{ width: percent(row.value, max) }"
          ></div>
          <div
            v-if="row.reference !== null && row.reference !== undefined"
            class="reference"
            :style="{ left: percent(row.reference, max) }"
          ></div>
        </div>
        <div class="value">{{ row.display }}</div>
      </li>
    </ul>
    <p v-if="referenceLabel" class="reference-note small secondary">
      <span class="reference-key" aria-hidden="true"></span>{{ referenceLabel }}
    </p>
  </div>
</template>

<style scoped>
.bar-list {
  margin: 0;
  padding: 0;
  list-style: none;
}
li {
  display: grid;
  grid-template-columns: minmax(7rem, 14rem) 1fr minmax(4.5rem, auto);
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) 0;
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
  height: 1rem;
  background: var(--color-rule-soft);
}
.bar {
  height: 100%;
  background: var(--series-blue);
  border-radius: 0 3px 3px 0;
}
.reference {
  position: absolute;
  top: -4px;
  bottom: -4px;
  width: 2px;
  background: var(--color-ink);
}
.value {
  text-align: right;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.reference-note {
  margin: var(--space-2) 0 0;
}
.reference-key {
  display: inline-block;
  width: 2px;
  height: 0.9rem;
  margin-right: var(--space-2);
  background: var(--color-ink);
  vertical-align: text-bottom;
}
@media (max-width: 34rem) {
  li {
    grid-template-columns: 1fr auto;
  }
  .label {
    grid-column: 1 / -1;
  }
}
</style>
