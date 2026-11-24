<script setup lang="ts">
import TableScroll from '@/components/TableScroll.vue'
import { computed, defineAsyncComponent } from 'vue'
import AsyncState from '@/components/AsyncState.vue'
import KeyFigure from '@/components/KeyFigure.vue'
import MapLegend from '@/components/MapLegend.vue'
import type { MapPoint } from '@/components/ChoroplethMap.vue'
import { useAsyncData } from '@/composables/useAsyncData'
import { useQueryParam } from '@/composables/useQueryParam'
import { classColors } from '@/domain/colors'
import { formatCount, formatValue } from '@/domain/format'
import { classIndex, DEFAULT_THRESHOLD_INDEX, getIndicator } from '@/domain/indicators'
import type { ScenarioKey, ScenarioVariant } from '@/domain/types'
import {
  loadAreaGeometries,
  loadDistrictGeometries,
  loadIndicators,
  loadScenarios,
} from '@/services/data'

const ChoroplethMap = defineAsyncComponent(() => import('@/components/ChoroplethMap.vue'))

const SCENARIO_LABELS: Record<ScenarioKey, { title: string; site: string }> = {
  greenSpace: { title: 'Neuer Spielplatz in einer bestehenden Grünanlage', site: 'Grünanlage' },
  schoolyard: { title: 'Schulhof einer öffentlichen Grundschule öffnen', site: 'Grundschule' },
}
const VARIANT_LABELS: Record<ScenarioVariant, string> = {
  official: 'Kinder ohne öffentlichen Spielplatz in 400 m',
  withOsm:
    'vorsichtig: nur Kinder ohne irgendeinen bekannten Spielplatz in 400 m (auch laut OpenStreetMap)',
}
const DEFAULT_SITES = '10'

const { data, error, loading, reload } = useAsyncData(async () => {
  const [scenarios, indicators, areas, districts] = await Promise.all([
    loadScenarios(),
    loadIndicators(),
    loadAreaGeometries(),
    loadDistrictGeometries(),
  ])
  return { scenarios, indicators, areas, districts }
})

const scenarioParam = useQueryParam('szenario', 'greenSpace')
const variantParam = useQueryParam('basis', 'official')
const sitesParam = useQueryParam('standorte', DEFAULT_SITES)

const scenarioKey = computed<ScenarioKey>(() =>
  scenarioParam.value === 'schoolyard' ? 'schoolyard' : 'greenSpace',
)
const variant = computed<ScenarioVariant>(() =>
  variantParam.value === 'withOsm' ? 'withOsm' : 'official',
)
const allSteps = computed(
  () => data.value?.scenarios.scenarios[scenarioKey.value].variants[variant.value] ?? [],
)
const siteCount = computed(() =>
  Math.min(allSteps.value.length, Math.max(1, Number(sitesParam.value) || Number(DEFAULT_SITES))),
)
const steps = computed(() => allSteps.value.slice(0, siteCount.value))

const reached = computed(() => steps.value.at(-1)?.cumulative ?? 0)
const childrenWithout = computed(
  () =>
    data.value?.scenarios.scenarios[scenarioKey.value].summary[variant.value]
      .children_without_playground_400 ?? 0,
)
const candidateGreenSpaces = computed(
  () => data.value?.scenarios.scenarios.greenSpace.summary.official.candidate_green_spaces ?? 0,
)
const candidateSchools = computed(
  () => data.value?.scenarios.scenarios.schoolyard.summary.official.public_primary_schools ?? 0,
)

const points = computed<MapPoint[]>(() =>
  steps.value.map((step) => ({
    id: step.id,
    lon: step.lon,
    lat: step.lat,
    badge: String(step.step),
    title: `${step.step}. ${step.name} (${step.district}): ${formatCount(step.childrenReached)} Kinder zusätzlich erreicht`,
  })),
)

// Background of the map: the share of children who already have a playground nearby.
const reachIndicator = getIndicator('playgroundReach')
const reachVariant = computed(() => (variant.value === 'withOsm' ? 'withOsm' : 'walking'))
const backgroundColors = computed(() => {
  const result = new Map<string, string>()
  for (const area of data.value?.indicators.areas ?? []) {
    const value = area.reach?.[reachVariant.value][DEFAULT_THRESHOLD_INDEX]
    if (value !== undefined)
      result.set(area.id, classColors('sequential')[classIndex(value, reachIndicator.breaks)] ?? '')
  }
  return result
})
const tooltips = computed(
  () =>
    new Map(
      (data.value?.indicators.areas ?? []).map((area) => [
        area.id,
        `${area.name} (${area.district})\nSpielplatz in 400 m: ${formatValue(area.reach?.[reachVariant.value][DEFAULT_THRESHOLD_INDEX], 'share')}`,
      ]),
    ),
)
</script>

<template>
  <div class="page potential">
    <header class="text-column">
      <p class="eyebrow">Potenziale</p>
      <h1>Wo würde ein zusätzliches Angebot die meisten Kinder erreichen?</h1>
      <p class="lead">
        Eine Modellrechnung: Welche Standorte brächten die meisten Kinder, die bisher keinen
        Spielplatz in 400 Metern Fußweg haben, in dessen Nähe?
      </p>
    </header>

    <div class="note text-column">
      <p>
        <strong>Das ist keine Planungsempfehlung.</strong> Die Rechnung kennt weder
        Eigentumsverhältnisse noch Naturschutz, Kosten, Aufsicht oder die Größe der Fläche. Sie
        zeigt, wo sich eine genauere Prüfung lohnen könnte.
      </p>
    </div>

    <AsyncState :loading="loading" :error="error" @retry="reload">
      <template v-if="data">
        <form class="controls" @submit.prevent>
          <fieldset>
            <legend>Maßnahme</legend>
            <label v-for="(label, key) in SCENARIO_LABELS" :key="key"
              ><input v-model="scenarioParam" type="radio" name="scenario" :value="key" />
              {{ label.title }}</label
            >
          </fieldset>
          <fieldset>
            <legend>Wer gilt als noch nicht erreicht?</legend>
            <label v-for="(label, key) in VARIANT_LABELS" :key="key"
              ><input v-model="variantParam" type="radio" name="variant" :value="key" />
              {{ label }}</label
            >
          </fieldset>
          <div class="field">
            <label for="sites">Anzahl der Standorte: {{ siteCount }}</label>
            <input
              id="sites"
              v-model="sitesParam"
              type="range"
              min="1"
              :max="allSteps.length"
              step="1"
            />
          </div>
        </form>

        <div class="figures" aria-live="polite">
          <KeyFigure
            :value="formatCount(reached)"
            :caption="`Kinder und Jugendliche würden durch ${siteCount} Standorte zusätzlich erreicht`"
          />
          <KeyFigure
            :value="formatValue(reached / childrenWithout, 'share')"
            :caption="`der ${formatCount(childrenWithout)} Kinder, die nach dieser Zählung bisher keinen Spielplatz in 400 m haben`"
          />
        </div>

        <div class="layout">
          <div>
            <ChoroplethMap
              :areas="data.areas"
              :districts="data.districts"
              :colors="backgroundColors"
              :tooltips="tooltips"
              :points="points"
              label="Karte der vorgeschlagenen Standorte auf dem Anteil der Kinder mit Spielplatz in 400 Metern. Die Standorte stehen in der Liste neben der Karte."
            />
            <MapLegend
              class="legend"
              title="Hintergrund: Kinder mit Spielplatz in 400 m Fußweg"
              :breaks="reachIndicator.breaks"
              :colors="classColors('sequential')"
              format="share"
              :no-data-label="`unter ${data.indicators.minChildrenForShares} Kinder`"
            />
          </div>
          <section aria-labelledby="standorte">
            <h2 id="standorte">Die {{ siteCount }} wirksamsten Standorte</h2>
            <p class="small secondary">
              Jeder Standort zählt nur Kinder, die kein vorheriger Standort schon erreicht.
            </p>
            <TableScroll label="Tabelle der Standorte">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Nr.</th>
                    <th scope="col">{{ SCENARIO_LABELS[scenarioKey].site }}</th>
                    <th scope="col" class="number">Kinder zusätzlich</th>
                    <th scope="col" class="number">Summe</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="step in steps" :key="step.id">
                    <td>{{ step.step }}</td>
                    <th scope="row">
                      {{ step.name }}<span class="district">{{ step.district }}</span>
                    </th>
                    <td class="number">{{ formatCount(step.childrenReached) }}</td>
                    <td class="number">{{ formatCount(step.cumulative) }}</td>
                  </tr>
                </tbody>
              </table>
            </TableScroll>
          </section>
        </div>

        <section class="assumptions text-column" aria-labelledby="annahmen">
          <h2 id="annahmen">Annahmen der Rechnung</h2>
          <ul>
            <li>
              Ein Kind gilt als erreicht, wenn der Fußweg vom Wohngebäude zum Standort höchstens 400
              Meter beträgt.
            </li>
            <li>
              Ausgewählt wird Schritt für Schritt der Standort, der die meisten noch nicht
              erreichten Kinder hinzugewinnt. Überschneidungen werden nicht doppelt gezählt.
            </li>
            <li>
              Grünanlagen: öffentliche Grünanlagen ab 2.000 m² ohne Spielplatz im Umkreis von 50
              Metern ({{ formatCount(candidateGreenSpaces) }} Flächen).
            </li>
            <li>
              Schulhöfe: alle öffentlichen Grundschulen ({{ formatCount(candidateSchools) }}). Ob
              ein Hof geeignet und eine Öffnung möglich ist, wurde nicht geprüft.
            </li>
            <li>
              Nicht berücksichtigt: Größe und Ausstattung des neuen Angebots, Kosten, Betreuung,
              Lärmschutz, bestehende Planungen der Bezirke.
            </li>
          </ul>
        </section>
      </template>
    </AsyncState>
  </div>
</template>

<style scoped>
.potential {
  padding-top: var(--space-7);
}
header h1 {
  font-size: var(--size-h2);
  margin-bottom: var(--space-4);
}
.controls {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(17rem, 1fr));
  gap: var(--space-5) var(--space-7);
  margin: var(--space-6) 0;
  padding: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-rule);
}
fieldset {
  margin: 0;
  padding: 0;
  border: 0;
}
legend {
  padding: 0;
  margin-bottom: var(--space-2);
  font-size: var(--size-small);
  font-weight: 600;
  color: var(--color-ink-secondary);
}
fieldset label {
  display: block;
  padding: var(--space-2) 0;
  cursor: pointer;
}
input[type='range'] {
  width: 100%;
  min-height: 2.75rem;
  accent-color: var(--color-accent);
}
.figures {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
  gap: var(--space-6);
  max-width: 44rem;
  margin-bottom: var(--space-6);
}
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr);
  gap: var(--space-6);
}
@media (max-width: 62rem) {
  .layout {
    grid-template-columns: 1fr;
  }
}
.layout h2 {
  font-size: var(--size-h3);
  margin-bottom: var(--space-2);
}
.legend {
  margin-top: var(--space-3);
}
tbody th {
  font-weight: 400;
  font-size: inherit;
  color: inherit;
  border-bottom-color: var(--color-rule-soft);
}
.district {
  display: block;
  font-size: var(--size-small);
  color: var(--color-ink-secondary);
}
.assumptions {
  margin-top: var(--space-8);
}
.assumptions h2 {
  font-size: var(--size-h3);
  margin-bottom: var(--space-3);
}
.assumptions li {
  margin-bottom: var(--space-2);
}
</style>
