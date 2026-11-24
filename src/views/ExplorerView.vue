<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'
import { RouterLink } from 'vue-router'
import AreaSearch from '@/components/AreaSearch.vue'
import AreaTable, { type AreaRow } from '@/components/AreaTable.vue'
import AsyncState from '@/components/AsyncState.vue'
import MapLegend from '@/components/MapLegend.vue'
import { useAsyncData } from '@/composables/useAsyncData'
import { useExplorerState } from '@/composables/useExplorerState'
import { classColors } from '@/domain/colors'
import { formatCount, formatValue } from '@/domain/format'
import {
  classIndex,
  INDICATORS,
  REACH_VARIANT_LABELS,
  type IndicatorGroup,
} from '@/domain/indicators'
import type { AreaValues } from '@/domain/types'
import {
  loadAreaGeometries,
  loadDistrictGeometries,
  loadIndicators,
  loadSources,
} from '@/services/data'

// The map library is large; it is only fetched when a map is actually shown.
const ChoroplethMap = defineAsyncComponent(() => import('@/components/ChoroplethMap.vue'))

const { data, error, loading, reload } = useAsyncData(async () => {
  const [indicators, areas, districts, sources] = await Promise.all([
    loadIndicators(),
    loadAreaGeometries(),
    loadDistrictGeometries(),
    loadSources(),
  ])
  return { indicators, areas, districts, sources }
})

const { indicatorKey, indicator, options, distanceParam, variantParam, selectedArea } =
  useExplorerState(() => data.value?.indicators.reachThresholdsM ?? [])

const groups = computed(() => {
  const names = [...new Set(INDICATORS.map((entry) => entry.group))] as IndicatorGroup[]
  return names.map((name) => ({
    name,
    indicators: INDICATORS.filter((entry) => entry.group === name),
  }))
})

const colors = computed(() => classColors(indicator.value.scale))
const valueOf = (area: AreaValues) => indicator.value.value(area, options.value)
const display = (value: number | null) => formatValue(value, indicator.value.format)

/** Indicator label including the chosen distance, e.g. "… (400 m, Fußweg)". */
const valueLabel = computed(() => {
  if (!indicator.value.usesReachOptions) return indicator.value.label
  const distance = data.value?.indicators.reachThresholdsM[options.value.thresholdIndex]
  return `${indicator.value.label} (${distance} m, ${REACH_VARIANT_LABELS[options.value.reachVariant]})`
})

const rows = computed<AreaRow[]>(() =>
  (data.value?.indicators.areas ?? []).map((area) => ({
    id: area.id,
    name: area.name,
    district: area.district,
    children: area.children,
    value: valueOf(area),
  })),
)
const areaColors = computed(() => {
  const result = new Map<string, string>()
  for (const row of rows.value) {
    if (row.value !== null)
      result.set(row.id, colors.value[classIndex(row.value, indicator.value.breaks)] ?? '')
  }
  return result
})
const tooltips = computed(
  () =>
    new Map(
      rows.value.map((row) => [row.id, `${row.name} (${row.district})\n${display(row.value)}`]),
    ),
)

const selected = computed(
  () => data.value?.indicators.areas.find((area) => area.id === selectedArea.value) ?? null,
)
const cityValue = computed(() => (data.value ? valueOf(data.value.indicators.city) : null))
const sourceTitles = computed(() =>
  indicator.value.sources.flatMap((key) => {
    const source = data.value?.sources.find((candidate) => candidate.key === key)
    return source ? [source] : []
  }),
)
</script>

<template>
  <div class="page explorer">
    <header class="text-column">
      <p class="eyebrow">Berlin-Explorer</p>
      <h1>Wie sieht es im eigenen Quartier aus?</h1>
      <p class="lead">
        Eine Kennzahl zur Zeit, für alle 542 Planungsräume. Die Karte zeigt das Muster, die Tabelle
        die genauen Werte.
      </p>
    </header>

    <AsyncState :loading="loading" :error="error" @retry="reload">
      <template v-if="data">
        <form class="controls" @submit.prevent>
          <div class="field wide">
            <label for="indicator">Kennzahl</label>
            <select id="indicator" v-model="indicatorKey">
              <optgroup v-for="group in groups" :key="group.name" :label="group.name">
                <option v-for="entry in group.indicators" :key="entry.key" :value="entry.key">
                  {{ entry.label }}
                </option>
              </optgroup>
            </select>
          </div>
          <template v-if="indicator.usesReachOptions">
            <div class="field">
              <label for="distance">Entfernung</label>
              <select id="distance" v-model="distanceParam">
                <option
                  v-for="threshold in data.indicators.reachThresholdsM"
                  :key="threshold"
                  :value="String(threshold)"
                >
                  {{ threshold }} m
                </option>
              </select>
            </div>
            <div class="field">
              <label for="variant">Gemessen als</label>
              <select id="variant" v-model="variantParam">
                <option v-for="(label, key) in REACH_VARIANT_LABELS" :key="key" :value="key">
                  {{ label }}
                </option>
              </select>
            </div>
          </template>
          <AreaSearch
            class="wide"
            :areas="data.indicators.areas"
            label="Planungsraum suchen"
            :selected-id="selectedArea"
            @select="selectedArea = $event"
          />
        </form>

        <div class="explanation text-column">
          <h2 class="indicator-title">{{ valueLabel }}</h2>
          <p>{{ indicator.description }}</p>
          <p class="small secondary">
            Berlin insgesamt: <strong>{{ display(cityValue) }}</strong> · Daten:
            <template v-for="(source, index) in sourceTitles" :key="source.key">
              <a :href="source.dataset_page">{{ source.title }}</a><span
                v-if="index < sourceTitles.length - 1"
                >,
              </span>
            </template>
          </p>
        </div>

        <div class="map-layout">
          <div>
            <ChoroplethMap
              :areas="data.areas"
              :districts="data.districts"
              :colors="areaColors"
              :tooltips="tooltips"
              :selected-id="selectedArea"
              :label="`Karte der Berliner Planungsräume: ${valueLabel}. Die Werte stehen in der Tabelle unter der Karte.`"
              @select="selectedArea = $event"
            />
            <MapLegend
              class="legend"
              :title="valueLabel"
              :breaks="indicator.breaks"
              :colors="colors"
              :format="indicator.format"
              :no-data-label="`keine Angabe (unter ${data.indicators.minChildrenForShares} Kinder oder Wert fehlt)`"
            />
          </div>

          <aside class="selection" aria-live="polite">
            <template v-if="selected">
              <p class="small secondary">{{ selected.district }} · {{ selected.region }}</p>
              <h2>{{ selected.name }}</h2>
              <p class="selected-value">{{ display(valueOf(selected)) }}</p>
              <p class="small secondary">Berlin insgesamt: {{ display(cityValue) }}</p>
              <p class="small">
                {{ formatCount(selected.children) }} Kinder und Jugendliche unter 18
              </p>
              <p v-if="!selected.enoughChildren" class="note">
                Hier wohnen weniger als {{ data.indicators.minChildrenForShares }} Kinder. Anteile
                wären zufallsanfällig und werden nicht ausgewiesen.
              </p>
              <p>
                <RouterLink class="button" :to="{ name: 'profile', params: { id: selected.id } }"
                  >Quartiersprofil öffnen</RouterLink
                >
              </p>
              <p>
                <RouterLink :to="{ name: 'compare', query: { a: selected.id } }"
                  >Mit einem anderen Quartier vergleichen</RouterLink
                >
              </p>
            </template>
            <template v-else>
              <h2>Kein Quartier ausgewählt</h2>
              <p class="secondary">
                Ein Quartier in der Karte anklicken oder oben nach dem Namen suchen.
              </p>
            </template>
          </aside>
        </div>

        <section class="table-section" aria-labelledby="tabelle">
          <h2 id="tabelle">Alle Planungsräume</h2>
          <AreaTable
            :rows="rows"
            :value-label="valueLabel"
            :format="indicator.format"
            :selected-id="selectedArea"
          />
        </section>
      </template>
    </AsyncState>
  </div>
</template>

<style scoped>
.explorer {
  padding-top: var(--space-7);
}
header h1 {
  font-size: var(--size-h2);
  margin-bottom: var(--space-4);
}
.controls {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr));
  gap: var(--space-4);
  align-items: end;
  margin: var(--space-6) 0;
  padding: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-rule);
}
.controls .wide {
  grid-column: span 2;
}
.controls select {
  width: 100%;
}
@media (max-width: 40rem) {
  .controls .wide {
    grid-column: auto;
  }
}
.indicator-title {
  font-size: var(--size-h3);
  margin-bottom: var(--space-2);
}
.map-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 19rem;
  gap: var(--space-6);
  margin-top: var(--space-5);
}
@media (max-width: 60rem) {
  .map-layout {
    grid-template-columns: 1fr;
  }
}
.legend {
  margin-top: var(--space-3);
}
.selection {
  border-top: 2px solid var(--color-ink);
  padding-top: var(--space-3);
}
.selection h2 {
  font-size: 1.6rem;
  margin-bottom: var(--space-3);
}
.selected-value {
  font-family: var(--font-display);
  font-size: var(--size-figure);
  font-weight: 600;
  line-height: 1;
  margin-bottom: var(--space-2);
}
.table-section {
  margin-top: var(--space-8);
}
.table-section h2 {
  font-size: var(--size-h3);
  margin-bottom: var(--space-4);
}
</style>
