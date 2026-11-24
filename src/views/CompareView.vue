<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import AreaSearch from '@/components/AreaSearch.vue'
import AsyncState from '@/components/AsyncState.vue'
import ValueTable, { type ValueRow } from '@/components/ValueTable.vue'
import { useAsyncData } from '@/composables/useAsyncData'
import { useQueryParam } from '@/composables/useQueryParam'
import { formatValue, type ValueFormat } from '@/domain/format'
import { DEFAULT_OPTIONS, INDICATORS } from '@/domain/indicators'
import { findSimilarAreas, SIMILARITY_FEATURES } from '@/domain/similarity'
import type { AreaValues, PlanningArea } from '@/domain/types'
import { loadIndicators } from '@/services/data'

const SUGGESTIONS_SHOWN = 6
/** Pairs with similar conditions and very different play area per child (docs/FINDINGS.md). */
const EXAMPLE_PAIRS = [
  ['Am Forstacker', 'Humboldtstraße'],
  ['Wilhelmstadt Ost', 'Erieseering'],
  ['Gallwitzallee', 'Hufeisensiedlung'],
] as const
const FEATURE_FORMATS: Record<(typeof SIMILARITY_FEATURES)[number]['key'], ValueFormat> = {
  densityPerHa: 'count',
  childShare: 'share',
  childPoverty: 'percentValue',
  children: 'count',
}

const { data, error, loading, reload } = useAsyncData(loadIndicators)
const firstId = useQueryParam('a', '')
const secondId = useQueryParam('b', '')

const findArea = (id: string) => data.value?.areas.find((area) => area.id === id) ?? null
const first = computed(() => findArea(firstId.value))
const second = computed(() => findArea(secondId.value))
const places = computed<(PlanningArea | AreaValues)[]>(() =>
  first.value && second.value && data.value ? [first.value, second.value, data.value.city] : [],
)
const head = computed(() =>
  first.value && second.value ? [first.value.name, second.value.name, 'Berlin'] : [],
)

const featureRows = computed<ValueRow[]>(() =>
  SIMILARITY_FEATURES.map((feature) => ({
    label: feature.label,
    cells: places.value.map((place) =>
      formatValue(place[feature.key], FEATURE_FORMATS[feature.key]),
    ),
  })),
)
const indicatorRows = computed<ValueRow[]>(() =>
  INDICATORS.filter(
    (indicator) => !SIMILARITY_FEATURES.some((feature) => feature.key === indicator.key),
  ).map((indicator) => ({
    label: indicator.usesReachOptions ? `${indicator.label} (400 m Fußweg)` : indicator.label,
    cells: places.value.map((place) =>
      formatValue(indicator.value(place, DEFAULT_OPTIONS), indicator.format),
    ),
  })),
)

const suggestions = computed(() =>
  first.value && data.value
    ? findSimilarAreas(first.value, data.value.areas, SUGGESTIONS_SHOWN)
    : [],
)
const examples = computed(() =>
  EXAMPLE_PAIRS.flatMap(([nameA, nameB]) => {
    const a = data.value?.areas.find((area) => area.name === nameA)
    const b = data.value?.areas.find((area) => area.name === nameB)
    return a && b ? [{ a, b }] : []
  }),
)
</script>

<template>
  <div class="page compare">
    <header class="text-column">
      <p class="eyebrow">Quartiersvergleich</p>
      <h1>Gleiche Voraussetzungen, andere Versorgung?</h1>
      <p class="lead">
        Zwei Planungsräume nebeneinander. Für jedes Quartier schlagen wir andere vor, die bei
        Dichte, Kinderanteil, Kinderarmut und Kinderzahl ähnlich sind.
      </p>
    </header>

    <AsyncState :loading="loading" :error="error" @retry="reload">
      <template v-if="data">
        <form class="pickers" @submit.prevent>
          <AreaSearch
            :areas="data.areas"
            label="Erstes Quartier"
            :selected-id="firstId"
            @select="firstId = $event"
          />
          <AreaSearch
            :areas="data.areas"
            label="Zweites Quartier"
            :selected-id="secondId"
            @select="secondId = $event"
          />
        </form>

        <section v-if="!first" class="text-column">
          <h2>Zum Einstieg</h2>
          <p>
            Drei Paare mit ähnlichen Rahmenbedingungen und sehr unterschiedlicher Spielfläche je
            Kind:
          </p>
          <ul>
            <li v-for="pair in examples" :key="pair.a.id">
              <RouterLink :to="{ name: 'compare', query: { a: pair.a.id, b: pair.b.id } }">
                {{ pair.a.name }} ({{ pair.a.district }}) und {{ pair.b.name }} ({{
                  pair.b.district
                }})
              </RouterLink>
            </li>
          </ul>
        </section>

        <section v-if="first && suggestions.length" aria-labelledby="vorschlaege">
          <h2 id="vorschlaege">Ähnliche Quartiere zu {{ first.name }}</h2>
          <p class="text-column secondary">
            Ausgewählt nach dem geringsten Abstand bei vier Merkmalen: Einwohner je Hektar, Anteil
            der unter 18-Jährigen, Kinderarmut und Zahl der Kinder (jeweils standardisiert).
            Versorgungskennzahlen fließen nicht ein.
          </p>
          <ul class="suggestions">
            <li v-for="entry in suggestions" :key="entry.area.id">
              <button
                type="button"
                class="suggestion"
                :aria-pressed="entry.area.id === secondId"
                @click="secondId = entry.area.id"
              >
                <strong>{{ entry.area.name }}</strong>
                <span class="small secondary">{{ entry.area.district }}</span>
                <span class="small"
                  >Spielfläche je Kind:
                  {{ formatValue(entry.area.playM2PerChild, 'squareMeters') }}</span
                >
              </button>
            </li>
          </ul>
        </section>

        <template v-if="first && second">
          <section aria-labelledby="vergleichbar">
            <h2 id="vergleichbar">Wie ähnlich sind die beiden?</h2>
            <ValueTable
              caption="Merkmale, nach denen Ähnlichkeit bestimmt wird"
              :head="head"
              :rows="featureRows"
            />
          </section>
          <section aria-labelledby="kennzahlen">
            <h2 id="kennzahlen">Wege und Angebote im Vergleich</h2>
            <ValueTable
              caption="Kennzahlen der beiden Quartiere und Berlins"
              :head="head"
              :rows="indicatorRows"
            />
            <p class="links">
              <RouterLink :to="{ name: 'profile', params: { id: first.id } }"
                >Profil {{ first.name }}</RouterLink
              >
              <RouterLink :to="{ name: 'profile', params: { id: second.id } }"
                >Profil {{ second.name }}</RouterLink
              >
            </p>
          </section>
        </template>
      </template>
    </AsyncState>
  </div>
</template>

<style scoped>
.compare {
  padding-top: var(--space-7);
}
header h1 {
  font-size: var(--size-h2);
  margin-bottom: var(--space-4);
}
.pickers {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  gap: var(--space-5);
  max-width: 50rem;
  margin: var(--space-6) 0;
}
section {
  margin-top: var(--space-7);
}
section h2 {
  font-size: var(--size-h3);
  margin-bottom: var(--space-3);
}
.suggestions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
  gap: var(--space-3);
  margin: var(--space-4) 0 0;
  padding: 0;
  list-style: none;
}
.suggestion {
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 100%;
  min-height: 2.75rem;
  padding: var(--space-3) var(--space-4);
  text-align: left;
  background: var(--color-surface);
  border: 1px solid var(--color-rule);
  border-radius: var(--radius);
  cursor: pointer;
}
.suggestion:hover {
  border-color: var(--color-accent);
}
.suggestion[aria-pressed='true'] {
  border-color: var(--color-accent);
  background: var(--color-accent-soft);
}
.links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-5);
  margin-top: var(--space-5);
}
</style>
