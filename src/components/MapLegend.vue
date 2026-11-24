<script setup lang="ts">
import { computed } from 'vue'
import { NO_DATA_COLOR } from '@/domain/colors'
import { formatValue, type ValueFormat } from '@/domain/format'

const props = defineProps<{
  title: string
  breaks: readonly number[]
  colors: readonly string[]
  format: ValueFormat
  /** Explains why some areas have no colour. */
  noDataLabel: string
}>()

const classes = computed(() =>
  props.colors.map((color, index) => {
    const lower = props.breaks[index - 1]
    const upper = props.breaks[index]
    const text =
      lower === undefined
        ? `unter ${formatValue(upper ?? 0, props.format)}`
        : upper === undefined
          ? `${formatValue(lower, props.format)} und mehr`
          : `${formatValue(lower, props.format)} bis unter ${formatValue(upper, props.format)}`
    return { color, text }
  }),
)
</script>

<template>
  <div class="legend small">
    <p class="title">{{ title }}</p>
    <ul>
      <li v-for="entry in classes" :key="entry.text">
        <span class="swatch" :style="{ background: entry.color }" aria-hidden="true"></span
        >{{ entry.text }}
      </li>
      <li>
        <span class="swatch" :style="{ background: NO_DATA_COLOR }" aria-hidden="true"></span
        >{{ noDataLabel }}
      </li>
    </ul>
  </div>
</template>

<style scoped>
.title {
  font-weight: 600;
  margin: 0 0 var(--space-2);
}
ul {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1) var(--space-4);
  margin: 0;
  padding: 0;
  list-style: none;
}
.swatch {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  margin-right: var(--space-2);
  border: 1px solid rgb(0 0 0 / 15%);
  vertical-align: -2px;
}
</style>
