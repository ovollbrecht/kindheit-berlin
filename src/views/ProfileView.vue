<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import AsyncState from '@/components/AsyncState.vue'
import KeyFigure from '@/components/KeyFigure.vue'
import ValueTable, { type ValueRow } from '@/components/ValueTable.vue'
import BarList, { type BarRow } from '@/components/charts/BarList.vue'
import { useAsyncData } from '@/composables/useAsyncData'
import { formatCount, formatValue, type ValueFormat } from '@/domain/format'
import { DEFAULT_THRESHOLD_INDEX } from '@/domain/indicators'
import { deriveInsights } from '@/domain/insights'
import { findSimilarAreas } from '@/domain/similarity'
import type { AreaValues } from '@/domain/types'
import { loadIndicators } from '@/services/data'

const props = defineProps<{ id: string }>()
const SIMILAR_AREAS_SHOWN = 5

const { data, error, loading, reload } = useAsyncData(loadIndicators)
const area = computed(
  () => data.value?.areas.find((candidate) => candidate.id === props.id) ?? null,
)
const city = computed(() => data.value?.city ?? null)

const reach400 = (values: AreaValues, variant: 'walking' | 'straight' | 'withOsm') =>
  values.reach?.[variant][DEFAULT_THRESHOLD_INDEX] ?? null

const ageRows = computed<BarRow[]>(() => {
  if (!area.value) return []
  const current = area.value
  return [
    { label: 'unter 6 Jahre', value: current.age0to5 },
    { label: '6 bis 9 Jahre', value: current.age6to9 },
    { label: '10 bis 17 Jahre', value: current.age10to17 },
  ].map((row) => ({ ...row, display: formatCount(row.value) }))
})
const maxAgeGroup = computed(() => Math.max(1, ...ageRows.value.map((row) => row.value ?? 0)))

const shareRows = computed<BarRow[]>(() => {
  if (!area.value || !city.value) return []
  const current = area.value
  const berlin = city.value
  const row = (
    label: string,
    value: number | null,
    reference: number | null,
    detail?: string,
  ): BarRow => ({ label, detail, value, reference, display: formatValue(value, 'share') })
  return [
    row(
      'Spielplatz in 400 m Fußweg',
      reach400(current, 'walking'),
      reach400(berlin, 'walking'),
      'öffentliche Spielplätze',
    ),
    row(
      'Spielplatz in 400 m Luftlinie',
      reach400(current, 'straight'),
      reach400(berlin, 'straight'),
      'zum Vergleich',
    ),
    row(
      'Spielplatz in 400 m ohne Hauptstraße',
      current.shareNoMainRoad400,
      berlin.shareNoMainRoad400,
      'ohne Querung einer Hauptverkehrsstraße',
    ),
    row(
      'Spielplatz in 400 m, mit OpenStreetMap',
      reach400(current, 'withOsm'),
      reach400(berlin, 'withOsm'),
      'zusätzlich nicht als privat markierte Plätze',
    ),
    row('Unter 6-Jährige: Spielplatz in 200 m', current.smallChildren200, berlin.smallChildren200),
    row('Grünanlage in 400 m', current.greenShare400, berlin.greenShare400, 'ab 0,5 Hektar'),
    row(
      '10- bis 17-Jährige: Jugendfreizeiteinrichtung in 1000 m',
      current.youthShare1000,
      berlin.youthShare1000,
    ),
  ]
})

function tableRows(
  entries: [
    label: string,
    key: Exclude<keyof AreaValues, 'reach'>,
    format: ValueFormat,
    hint?: string,
  ][],
): ValueRow[] {
  if (!area.value || !city.value) return []
  const current = area.value
  const berlin = city.value
  return entries.map(([label, key, format, hint]) => ({
    label,
    hint,
    cells: [formatValue(current[key], format), formatValue(berlin[key], format)],
  }))
}
const distanceRows = computed(() =>
  tableRows([
    ['Spielplatz', 'playgroundMedianM', 'meters', 'alle unter 18-Jährigen'],
    ['Kita', 'daycareMedianM', 'meters', 'unter 6-Jährige'],
    ['Öffentliche Grundschule', 'primarySchoolMedianM', 'meters', '6- bis 9-Jährige'],
    ['Jugendfreizeiteinrichtung', 'youthMedianM', 'meters', '10- bis 17-Jährige'],
    ['Öffentliche Sportanlage', 'sportsMedianM', 'meters', 'alle unter 18-Jährigen'],
    ['Bibliothek', 'libraryMedianM', 'meters', 'alle unter 18-Jährigen'],
  ]),
)
const capacityRows = computed(() =>
  tableRows([
    [
      'Erreichbare Spielfläche je Kind',
      'playM2PerChild',
      'squareMeters',
      'öffentliche Plätze in 1000 m Fußweg, geteilt mit allen Kindern im Einzugsbereich',
    ],
    [
      'Spielfläche je Einwohner im Planungsraum',
      'playM2PerResidentInside',
      'squareMeters',
      'Sicht des amtlichen Richtwerts von 1 m² je Einwohner',
    ],
    [
      'Genehmigte Kita-Plätze je Kind unter 6',
      'daycarePlacesPerChild',
      'decimal',
      'in 1000 m Fußweg',
    ],
    [
      'Plätze in Jugendfreizeiteinrichtungen je 100 Jugendliche',
      'youthPlacesPer100',
      'decimal',
      'in 1000 m Fußweg',
    ],
  ]),
)
const contextRows = computed(() =>
  tableRows([
    [
      'Kinderarmut',
      'childPoverty',
      'percentValue',
      'unter 15-Jährige in Bedarfsgemeinschaften nach SGB II, 31.12.2024',
    ],
    [
      'Kinder in alleinerziehenden Haushalten',
      'singleParent',
      'percentValue',
      'Anteil an allen unter 18-Jährigen, 31.12.2024',
    ],
    ['Wohnfläche je Einwohner', 'livingSpace', 'squareMeters', '31.12.2024'],
    ['Einwohner je Hektar bewohnter Blockfläche', 'densityPerHa', 'count'],
  ]),
)

const insights = computed(() =>
  area.value && city.value ? deriveInsights(area.value, city.value) : [],
)
const similar = computed(() =>
  area.value && data.value
    ? findSimilarAreas(area.value, data.value.areas, SIMILAR_AREAS_SHOWN)
    : [],
)
</script>

<template>
  <div class="page profile">
    <AsyncState :loading="loading" :error="error" @retry="reload">
      <div v-if="!area" class="text-column">
        <h1>Quartier nicht gefunden</h1>
        <p>
          Zu dieser Adresse gibt es keinen Planungsraum.
          <RouterLink :to="{ name: 'explorer' }">Zum Explorer</RouterLink>
        </p>
      </div>

      <article v-else-if="city">
        <header>
          <p class="eyebrow">Quartiersprofil · {{ area.district }} · {{ area.region }}</p>
          <h1>{{ area.name }}</h1>
          <p class="secondary">
            Planungsraum {{ area.id }} · {{ area.zone }} · Bevölkerungsstand 31.12.2025
          </p>
          <p class="actions">
            <RouterLink :to="{ name: 'explorer', query: { area: area.id } }"
              >In der Karte zeigen</RouterLink
            >
            <RouterLink :to="{ name: 'compare', query: { a: area.id } }">Vergleichen</RouterLink>
          </p>
        </header>

        <p v-if="!area.enoughChildren" class="note text-column">
          In diesem Planungsraum wohnen weniger als {{ data?.minChildrenForShares }} Kinder und
          Jugendliche. Anteile und Mittelwerte wären zufallsanfällig und werden deshalb nicht
          ausgewiesen.
        </p>

        <section aria-labelledby="kinder">
          <h2 id="kinder">Kinder im Quartier</h2>
          <div class="figures">
            <KeyFigure
              :value="formatCount(area.children)"
              caption="Kinder und Jugendliche unter 18 Jahren"
            />
            <KeyFigure
              :value="formatValue(area.childShare, 'share')"
              :caption="`der Einwohner sind unter 18 (Berlin: ${formatValue(city.childShare, 'share')})`"
            />
            <KeyFigure
              :value="formatValue(area.childrenChange, 'signedShare')"
              :caption="`Veränderung der Kinderzahl seit Ende 2022 (Berlin: ${formatValue(city.childrenChange, 'signedShare')})`"
            />
          </div>
          <div class="narrow"><BarList :rows="ageRows" :max="maxAgeGroup" /></div>
        </section>

        <section v-if="area.enoughChildren" aria-labelledby="auffaellig">
          <h2 id="auffaellig">Auffälligkeiten</h2>
          <ul v-if="insights.length" class="insights text-column">
            <li v-for="insight in insights" :key="insight.id">{{ insight.text }}</li>
          </ul>
          <p v-else class="text-column">
            Nach den festgelegten Regeln weicht dieses Quartier in keinem Punkt deutlich vom
            Berliner Bild ab.
          </p>
          <p class="small secondary text-column">
            Diese Sätze entstehen aus festen Regeln mit dokumentierten Schwellen, nicht aus freier
            Textgenerierung.
            <RouterLink :to="{ name: 'methods', hash: '#regeln' }">Regeln ansehen</RouterLink>
          </p>
        </section>

        <section v-if="area.enoughChildren" aria-labelledby="wege">
          <h2 id="wege">Was ist in der Nähe?</h2>
          <div class="wide">
            <BarList :rows="shareRows" :max="1" reference-label="Berlin insgesamt" />
          </div>

          <div class="two-columns">
            <div>
              <h3>Mittlerer Fußweg zum nächsten Angebot</h3>
              <ValueTable
                caption="Mittlerer Fußweg zum nächsten Angebot, Quartier und Berlin"
                :head="[area.name, 'Berlin']"
                :rows="distanceRows"
              />
            </div>
            <div>
              <h3>Wie viel Angebot kommt auf ein Kind?</h3>
              <ValueTable
                caption="Angebot je Kind, Quartier und Berlin"
                :head="[area.name, 'Berlin']"
                :rows="capacityRows"
              />
            </div>
          </div>
        </section>

        <section aria-labelledby="umfeld">
          <h2 id="umfeld">Umfeld</h2>
          <div class="two-columns">
            <div>
              <h3>Soziale Rahmenbedingungen</h3>
              <ValueTable
                caption="Soziale Rahmenbedingungen, Quartier und Berlin"
                :head="[area.name, 'Berlin']"
                :rows="contextRows"
              />
              <p class="small secondary">
                Status-Index: {{ area.statusIndex ?? 'keine Angabe' }} (Monitoring Soziale
                Stadtentwicklung 2025). Die Werte beschreiben Rahmenbedingungen eines Gebiets, nicht
                einzelne Familien.
              </p>
            </div>
            <div>
              <h3>Umwelt und Verkehr</h3>
              <dl>
                <dt>Lärmbelastung</dt>
                <dd>{{ area.envNoise ?? 'keine Angabe' }}</dd>
                <dt>Luftbelastung</dt>
                <dd>{{ area.envAir ?? 'keine Angabe' }}</dd>
                <dt>Thermische Belastung</dt>
                <dd>{{ area.envHeat ?? 'keine Angabe' }}</dd>
                <dt>Grünversorgung</dt>
                <dd>{{ area.envGreen ?? 'keine Angabe' }}</dd>
                <dt>Mehrfachbelastung</dt>
                <dd>{{ area.envBurdens ?? 'keine Angabe' }}</dd>
                <dt>Unfälle mit verletzten Fußgängern oder Radfahrenden zu Schulwegzeiten</dt>
                <dd>{{ formatValue(area.accidentsSchoolRun, 'count') }} (2018 bis 2024)</dd>
              </dl>
              <p class="small secondary">
                Umwelt: Umweltgerechtigkeitsatlas 2023/2024, nur Klassen. Unfälle: Unfallatlas,
                montags bis freitags 7–8 und 13–16 Uhr; das Alter der Beteiligten ist nicht bekannt.
              </p>
            </div>
          </div>
        </section>

        <section v-if="similar.length" aria-labelledby="aehnlich">
          <h2 id="aehnlich">Ähnliche Quartiere</h2>
          <p class="text-column">
            Diese Planungsräume ähneln {{ area.name }} bei Bebauungsdichte, Kinderanteil,
            Kinderarmut und Kinderzahl am stärksten. Wie gut sie versorgt sind, spielt für die
            Auswahl keine Rolle.
          </p>
          <ul class="similar">
            <li v-for="entry in similar" :key="entry.area.id">
              <RouterLink :to="{ name: 'compare', query: { a: area.id, b: entry.area.id } }">{{
                entry.area.name
              }}</RouterLink>
              <span class="small secondary"
                >{{ entry.area.district }} · erreichbare Spielfläche
                {{ formatValue(entry.area.playM2PerChild, 'squareMeters') }} je Kind</span
              >
            </li>
          </ul>
        </section>
      </article>
    </AsyncState>
  </div>
</template>

<style scoped>
.profile {
  padding-top: var(--space-7);
}
header h1 {
  margin-bottom: var(--space-3);
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-5);
  margin-top: var(--space-4);
}
section {
  margin-top: var(--space-8);
  padding-top: var(--space-5);
  border-top: 1px solid var(--color-rule);
}
section h2 {
  margin-bottom: var(--space-5);
}
h3 {
  margin-bottom: var(--space-3);
}
.figures {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-6);
}
.narrow {
  max-width: 34rem;
}
.wide {
  max-width: 52rem;
}
.wide :deep(li) {
  grid-template-columns: minmax(9rem, 20rem) 1fr minmax(4.5rem, auto);
}
.two-columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(19rem, 1fr));
  gap: var(--space-7);
  margin-top: var(--space-7);
}
.insights {
  padding-left: 1.2rem;
}
.insights li {
  margin-bottom: var(--space-3);
}
dl {
  display: grid;
  grid-template-columns: 1fr auto;
  margin: 0 0 var(--space-4);
}
dt,
dd {
  margin: 0;
  padding: var(--space-2) 0;
  border-bottom: 1px solid var(--color-rule-soft);
}
dd {
  text-align: right;
  font-weight: 600;
  padding-left: var(--space-4);
}
.similar {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr));
  gap: var(--space-4) var(--space-6);
  margin: var(--space-5) 0 0;
  padding: 0;
  list-style: none;
}
.similar a {
  display: block;
  font-weight: 600;
}
</style>
