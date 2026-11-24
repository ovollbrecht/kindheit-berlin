<script setup lang="ts">
import { computed, ref } from 'vue'
import { useElementWidth } from '@/composables/useElementWidth'

export interface LineSeries {
  id: string
  label: string
  color: string
  points: { x: number; y: number }[]
}

const props = defineProps<{
  series: LineSeries[]
  xMax: number
  yMax: number
  xTicks: number[]
  yTicks: number[]
  xLabel: string
  formatX: (value: number) => string
  formatY: (value: number) => string
  /** Draws a vertical guide at this x and labels each series' value there. */
  markerX?: number
  /** One-sentence description for screen readers. */
  description: string
}>()

const MARGIN = { top: 12, right: 16, bottom: 44, left: 52 }
const MIN_HEIGHT = 260
const MAX_HEIGHT = 420
const ASPECT = 0.56
const MIN_LABEL_GAP = 16

const container = ref<HTMLElement | null>(null)
const width = useElementWidth(container)
const height = computed(() => Math.min(MAX_HEIGHT, Math.max(MIN_HEIGHT, width.value * ASPECT)))
const plotWidth = computed(() => width.value - MARGIN.left - MARGIN.right)
const plotHeight = computed(() => height.value - MARGIN.top - MARGIN.bottom)

const scaleX = (value: number) => MARGIN.left + (value / props.xMax) * plotWidth.value
const scaleY = (value: number) =>
  MARGIN.top + plotHeight.value - (value / props.yMax) * plotHeight.value

const paths = computed(() =>
  props.series.map((line) => ({
    ...line,
    d: line.points
      .map(
        (point, index) =>
          `${index === 0 ? 'M' : 'L'}${scaleX(point.x).toFixed(1)},${scaleY(point.y).toFixed(1)}`,
      )
      .join(' '),
  })),
)

/** Value labels at the marker, moved apart vertically so they never overlap. */
const markerLabels = computed(() => {
  if (props.markerX === undefined) return []
  const labels = props.series
    .flatMap((line) => {
      const point = line.points.find((candidate) => candidate.x === props.markerX)
      return point
        ? [
            {
              id: line.id,
              color: line.color,
              value: point.y,
              y: scaleY(point.y),
              labelY: scaleY(point.y),
            },
          ]
        : []
    })
    .sort((a, b) => a.y - b.y)
  for (let index = 1; index < labels.length; index += 1) {
    const previous = labels[index - 1]
    const current = labels[index]
    if (previous && current && current.labelY - previous.labelY < MIN_LABEL_GAP)
      current.labelY = previous.labelY + MIN_LABEL_GAP
  }
  return labels
})
</script>

<template>
  <div>
    <ul class="legend" aria-hidden="true">
      <li v-for="line in series" :key="line.id">
        <span class="swatch" :style="{ background: line.color }"></span>{{ line.label }}
      </li>
    </ul>
    <div ref="container">
      <svg :width="width" :height="height" role="img" :aria-label="description">
        <g class="grid">
          <template v-for="tick in yTicks" :key="`y${tick}`">
            <line
              :x1="MARGIN.left"
              :x2="width - MARGIN.right"
              :y1="scaleY(tick)"
              :y2="scaleY(tick)"
            />
            <text
              :x="MARGIN.left - 8"
              :y="scaleY(tick)"
              text-anchor="end"
              dominant-baseline="middle"
            >
              {{ formatY(tick) }}
            </text>
          </template>
          <template v-for="tick in xTicks" :key="`x${tick}`">
            <text :x="scaleX(tick)" :y="height - MARGIN.bottom + 18" text-anchor="middle">
              {{ formatX(tick) }}
            </text>
          </template>
          <text
            class="axis-label"
            :x="MARGIN.left + plotWidth / 2"
            :y="height - 6"
            text-anchor="middle"
          >
            {{ xLabel }}
          </text>
        </g>
        <line
          class="baseline"
          :x1="MARGIN.left"
          :x2="width - MARGIN.right"
          :y1="scaleY(0)"
          :y2="scaleY(0)"
        />
        <line
          v-if="markerX !== undefined"
          class="marker"
          :x1="scaleX(markerX)"
          :x2="scaleX(markerX)"
          :y1="MARGIN.top"
          :y2="scaleY(0)"
        />
        <path
          v-for="line in paths"
          :key="line.id"
          :d="line.d"
          :stroke="line.color"
          fill="none"
          stroke-width="2.5"
          stroke-linejoin="round"
        />
        <g v-for="label in markerLabels" :key="label.id">
          <circle
            :cx="scaleX(markerX ?? 0)"
            :cy="label.y"
            r="5"
            :fill="label.color"
            stroke="#faf8f3"
            stroke-width="2"
          />
          <text class="value-label" :x="scaleX(markerX ?? 0) + 10" :y="label.labelY + 14">
            {{ formatY(label.value) }}
          </text>
        </g>
      </svg>
    </div>
  </div>
</template>

<style scoped>
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1) var(--space-5);
  margin: 0 0 var(--space-3);
  padding: 0;
  list-style: none;
  font-size: var(--size-small);
}
.swatch {
  display: inline-block;
  width: 1.4rem;
  height: 3px;
  margin-right: var(--space-2);
  vertical-align: middle;
}
svg {
  display: block;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}
.grid line {
  stroke: var(--chart-grid);
}
.grid text {
  fill: var(--color-ink-secondary);
}
.baseline {
  stroke: var(--chart-axis);
}
.marker {
  stroke: var(--chart-axis);
  stroke-dasharray: 3 3;
}
.value-label {
  fill: var(--color-ink);
  font-weight: 600;
  paint-order: stroke;
  stroke: var(--color-paper);
  stroke-width: 3px;
}
</style>
