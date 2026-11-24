<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import AsyncState from '@/components/AsyncState.vue'
import KeyFigure from '@/components/KeyFigure.vue'
import StoryChapter from '@/components/StoryChapter.vue'
import BarList, { type BarRow } from '@/components/charts/BarList.vue'
import ChartFigure from '@/components/charts/ChartFigure.vue'
import DumbbellChart from '@/components/charts/DumbbellChart.vue'
import LineChart, { type LineSeries } from '@/components/charts/LineChart.vue'
import { useAsyncData } from '@/composables/useAsyncData'
import { SERIES } from '@/domain/colors'
import { formatCount, formatRounded, formatValue } from '@/domain/format'
import { loadScenarios, loadStory } from '@/services/data'

const STATUS_ORDER = ['hoch', 'mittel', 'niedrig', 'sehr niedrig']
const NEAR_M = 400
const SHARE_TICKS = [0, 0.2, 0.4, 0.6, 0.8, 1]
const DISTANCE_TICKS = [0, 200, 400, 600, 800, 1000]
const SOURCE_WALKING =
  'Daten: Grünanlagenbestand (SenMVKU), Einwohnerdichte 2025 (AfS), ALKIS-Gebäude, OpenStreetMap-Wegenetz. Eigene Berechnung.'

const { data, error, loading, reload } = useAsyncData(async () => {
  const [story, scenarios] = await Promise.all([loadStory(), loadScenarios()])
  return { story, scenarios }
})

const findings = computed(() => data.value?.story.findings)
const share = (value: number) => formatValue(value, 'share')

const curveSeries = computed<LineSeries[]>(() => {
  const curves = data.value?.story.distanceCurves
  if (!curves) return []
  const points = (values: number[]) =>
    values.map((y, index) => ({ x: curves.distancesM[index] ?? 0, y }))
  return [
    {
      id: 'straight',
      label: 'Luftlinie',
      color: SERIES.blue,
      points: points(curves.series.straight),
    },
    { id: 'walking', label: 'Fußweg', color: SERIES.orange, points: points(curves.series.walking) },
    {
      id: 'noMainRoad',
      label: 'Fußweg ohne Querung einer Hauptstraße',
      color: SERIES.aqua,
      points: points(curves.series.noMainRoad),
    },
  ]
})
const curveTable = computed(() => {
  const curves = data.value?.story.distanceCurves
  if (!curves) return []
  return DISTANCE_TICKS.filter((distance) => distance > 0).map((distance) => {
    const index = curves.distancesM.indexOf(distance)
    return [
      `${distance} m`,
      share(curves.series.straight[index] ?? 0),
      share(curves.series.walking[index] ?? 0),
      share(curves.series.noMainRoad[index] ?? 0),
    ]
  })
})
const shareAt = (series: 'straight' | 'walking', distance: number) => {
  const curves = data.value?.story.distanceCurves
  return curves ? (curves.series[series][curves.distancesM.indexOf(distance)] ?? 0) : 0
}

const barrierRows = computed<BarRow[]>(() => {
  const shares = findings.value?.barriers.share_by_barrier_on_straight_line
  if (!shares) return []
  return [
    {
      label: 'Keine dieser Barrieren',
      detail: 'gewöhnliche Umwege im Straßennetz',
      value: shares.no_linear_barrier,
    },
    { label: 'Bahntrasse', value: shares.railway },
    { label: 'Fluss oder Kanal', value: shares.water },
    { label: 'Autobahn', value: shares.motorway },
  ].map((row) => ({ ...row, display: share(row.value) }))
})

function statusRows(
  pick:
    | 'share_playground_400_walking'
    | 'reachable_m2_per_child_1000'
    | 'share_teens_youth_facility_1000',
  format: 'share' | 'squareMeters',
): BarRow[] {
  const groups = findings.value?.by_social_status
  if (!groups) return []
  return STATUS_ORDER.flatMap((status) => {
    const group = groups[status]
    return group
      ? [{ label: status, value: group[pick], display: formatValue(group[pick], format) }]
      : []
  })
}
const statusPanels = computed(() => [
  {
    title: 'Spielplatz in 400 m Fußweg',
    max: 1,
    rows: statusRows('share_playground_400_walking', 'share'),
  },
  {
    title: 'Erreichbare Spielfläche je Kind',
    max: 5,
    rows: statusRows('reachable_m2_per_child_1000', 'squareMeters'),
  },
  {
    title: 'Jugendfreizeiteinrichtung in 1000 m (10- bis 17-Jährige)',
    max: 1,
    rows: statusRows('share_teens_youth_facility_1000', 'share'),
  },
])
const statusTable = computed(() => {
  const groups = findings.value?.by_social_status
  if (!groups) return []
  return STATUS_ORDER.flatMap((status) => {
    const group = groups[status]
    return group
      ? [
          [
            status,
            formatCount(group.children),
            share(group.share_playground_400_walking),
            formatValue(group.reachable_m2_per_child_1000, 'squareMeters'),
            share(group.share_teens_youth_facility_1000),
          ],
        ]
      : []
  })
})
const statusGroup = (status: string) => findings.value?.by_social_status[status]

const growthRows = computed<BarRow[]>(() => {
  const growth = findings.value?.growth_2022_2025
  if (!growth) return []
  return [
    {
      label: 'Quartiere mit wachsender Kinderzahl',
      detail: 'mindestens +10 % seit Ende 2022',
      value: growth.share_400_walking_growing,
      display: share(growth.share_400_walking_growing),
    },
    {
      label: 'Quartiere mit sinkender Kinderzahl',
      detail: 'mindestens −5 % seit Ende 2022',
      value: growth.share_400_walking_shrinking,
      display: share(growth.share_400_walking_shrinking),
    },
  ]
})

/** Change of the child population in a city zone as an unsigned percentage, e.g. "5,0 %". */
const zoneChange = (zone: string) =>
  formatValue(
    Math.abs(findings.value?.growth_2022_2025.by_city_zone[zone] ?? 0) * 100,
    'percentValue',
  )

const housingRows = computed(() =>
  (data.value?.story.housingTypes ?? []).map((type) => ({
    label: type.name,
    detail: `${formatCount(type.children)} Kinder`,
    from: type.shareOfficial,
    to: type.shareWithOsm,
    fromDisplay: share(type.shareOfficial),
    toDisplay: share(type.shareWithOsm),
  })),
)

const scenarioSeries = computed<LineSeries[]>(() => {
  const scenarios = data.value?.scenarios.scenarios
  if (!scenarios) return []
  const points = (key: 'greenSpace' | 'schoolyard') => [
    { x: 0, y: 0 },
    ...scenarios[key].variants.official.map((step) => ({ x: step.step, y: step.cumulative })),
  ]
  return [
    {
      id: 'greenSpace',
      label: 'Neuer Spielplatz in einer bestehenden Grünanlage',
      color: SERIES.blue,
      points: points('greenSpace'),
    },
    {
      id: 'schoolyard',
      label: 'Geöffneter Schulhof einer öffentlichen Grundschule',
      color: SERIES.orange,
      points: points('schoolyard'),
    },
  ]
})
const scenarioTotal = (key: 'greenSpace' | 'schoolyard', variant: 'official' | 'withOsm') =>
  data.value?.scenarios.scenarios[key].variants[variant].at(-1)?.cumulative ?? 0
const scenarioTable = computed(() =>
  [1, 5, 10, 15, 20, 25].map((count) => {
    const at = (key: 'greenSpace' | 'schoolyard') =>
      formatCount(
        data.value?.scenarios.scenarios[key].variants.official[count - 1]?.cumulative ?? 0,
      )
    return [`${count}`, at('greenSpace'), at('schoolyard')]
  }),
)
</script>

<template>
  <article>
    <header class="hero page">
      <p class="eyebrow">Offene Daten · Berlin · Stand 31.12.2025</p>
      <h1>Wege statt Kreise</h1>
      <p class="lead text-column">
        Auf dem Stadtplan liegt der nächste Spielplatz für fast alle Berliner Kinder um die Ecke. Zu
        Fuß ist er für viele ein gutes Stück weiter. Wir haben für jedes Wohngebäude der Stadt den
        tatsächlichen Weg berechnet: zum Spielplatz, zur Kita, zur Schule, zum Jugendclub.
      </p>
    </header>

    <div class="page">
      <AsyncState :loading="loading" :error="error" @retry="reload" />
    </div>

    <template v-if="data && findings">
      <section class="page figures" aria-label="Die wichtigsten Zahlen">
        <KeyFigure
          :value="share(shareAt('straight', NEAR_M))"
          caption="der unter 18-Jährigen wohnen höchstens 400 m Luftlinie von einem öffentlichen Spielplatz"
        />
        <KeyFigure
          :value="share(shareAt('walking', NEAR_M))"
          caption="haben ihn auch in höchstens 400 m Fußweg"
        />
        <KeyFigure
          :value="
            formatRounded(
              findings.straight_line_versus_walking.children_within_400_straight_but_not_walking,
              1000,
            )
          "
          caption="Kinder und Jugendliche liegen dazwischen: nah auf der Karte, weiter zu Fuß"
        />
      </section>

      <StoryChapter :number="1" title="Der Kreis auf der Karte täuscht">
        <p>
          Wer Nähe misst, zieht meist einen Kreis: 400 Meter um jeden Spielplatz, und alle Kinder
          darin gelten als versorgt. Kinder laufen aber nicht durch Häuserblocks, über Bahndämme
          oder quer über Grundstücke. Sie folgen Gehwegen und Pfaden.
        </p>
        <p>
          Rechnet man mit diesen Wegen, schrumpft der Anteil der Kinder mit einem Spielplatz in 400
          Metern von {{ share(shareAt('straight', NEAR_M)) }} auf
          {{ share(shareAt('walking', NEAR_M)) }}. Der mittlere Fußweg beträgt
          {{
            formatValue(
              findings.straight_line_versus_walking.walking_distance_quantiles_m.p50,
              'meters',
            )
          }}, die mittlere Luftlinie
          {{
            formatValue(
              findings.straight_line_versus_walking.straight_distance_quantiles_m.p50,
              'meters',
            )
          }}.
        </p>
        <template #figure>
          <ChartFigure
            title="Je genauer der Weg, desto weniger Kinder wohnen nah am Spielplatz"
            subtitle="Anteil der unter 18-Jährigen, die höchstens so weit vom nächsten öffentlichen Spielplatz wohnen"
            :source="SOURCE_WALKING"
            :table-head="['Entfernung', 'Luftlinie', 'Fußweg', 'Fußweg ohne Hauptstraße']"
            :table-rows="curveTable"
          >
            <LineChart
              :series="curveSeries"
              :x-max="1000"
              :y-max="1"
              :x-ticks="DISTANCE_TICKS"
              :y-ticks="SHARE_TICKS"
              :marker-x="NEAR_M"
              x-label="Entfernung zum nächsten öffentlichen Spielplatz in Metern"
              :format-x="(value) => String(value)"
              :format-y="share"
              description="Liniendiagramm: Bei jeder Entfernung liegt der Anteil nach Luftlinie über dem Anteil nach Fußweg. Die Werte stehen in der Tabelle darunter."
            />
          </ChartFigure>
        </template>
        <template #after>
          <p>
            <RouterLink :to="{ name: 'explorer', query: { ind: 'playgroundReach' } }"
              >Im Explorer nachsehen, wie groß die Lücke im eigenen Quartier ist</RouterLink
            >
          </p>
        </template>
      </StoryChapter>

      <StoryChapter :number="2" title="Es sind nicht die großen Barrieren">
        <p>
          Naheliegend wäre, die Schuld bei Bahntrassen, Kanälen und Autobahnen zu suchen. Die Daten
          widersprechen: Nur bei jedem zehnten der betroffenen Kinder liegt eine solche Barriere auf
          der direkten Linie zum Spielplatz. In den übrigen Fällen ist es das gewöhnliche
          Straßennetz, das den Weg verlängert: lange Blöcke, fehlende Durchgänge, Sackgassen.
        </p>
        <template #figure>
          <ChartFigure
            title="Was zwischen Kind und Spielplatz liegt"
            subtitle="Kinder mit Spielplatz in 400 m Luftlinie, aber nicht in 400 m Fußweg: Was liegt auf der direkten Linie?"
            source="Daten: wie oben; Bahn, Gewässer und Autobahnen aus OpenStreetMap. Ein Weg kann mehrere Barrieren kreuzen. Eigene Berechnung."
            :table-head="['Auf der direkten Linie', 'Anteil der betroffenen Kinder']"
            :table-rows="barrierRows.map((row) => [row.label, row.display])"
          >
            <BarList :rows="barrierRows" :max="1" />
          </ChartFigure>
          <div class="figures inline">
            <KeyFigure
              :value="
                formatRounded(
                  findings.straight_line_versus_walking.children_needing_main_road_crossing_for_400,
                )
              "
              caption="Kinder erreichen ihren Spielplatz in 400 m nur, wenn sie eine Hauptverkehrsstraße queren"
            />
            <KeyFigure
              :value="
                formatRounded(
                  findings.straight_line_versus_walking
                    .children_needing_unsecured_main_road_crossing_for_400,
                )
              "
              caption="davon nur über eine Querung, für die weder Ampel noch Zebrastreifen erfasst ist"
            />
          </div>
        </template>
        <template #after>
          <p>
            <RouterLink :to="{ name: 'explorer', query: { ind: 'shareNoMainRoad400' } }"
              >Karte: Spielplatz in 400 m ohne Hauptstraße</RouterLink
            >
          </p>
        </template>
      </StoryChapter>

      <StoryChapter :number="3" title="Nah, aber voll">
        <p>
          Man könnte erwarten, dass Kinder in ärmeren Quartieren weitere Wege haben. Es ist
          umgekehrt. In Planungsräumen mit hohem sozialen Status hat nicht einmal jedes zweite Kind
          einen öffentlichen Spielplatz in 400 Metern, in Räumen mit niedrigem Status sind es drei
          von vier. Der Grund ist die Bebauung: Wo dicht gebaut ist, liegt vieles nah. In
          Einfamilienhausgebieten ersetzt oft der eigene Garten den Spielplatz.
        </p>
        <p>
          Die Kehrseite zeigt die mittlere Grafik. In Quartieren mit sehr niedrigem Status teilen
          sich mehr Kinder dieselbe Fläche:
          {{
            formatValue(statusGroup('sehr niedrig')?.reachable_m2_per_child_1000, 'squareMeters')
          }}
          je Kind gegenüber
          {{ formatValue(statusGroup('niedrig')?.reachable_m2_per_child_1000, 'squareMeters') }}
          bei niedrigem Status. Nähe allein sagt wenig darüber, wie viel Platz zum Spielen bleibt.
        </p>
        <template #figure>
          <ChartFigure
            title="Kurze Wege bei niedrigem Status, wenig Fläche bei sehr niedrigem"
            subtitle="Planungsräume nach Status-Index des Monitorings Soziale Stadtentwicklung 2025, gewichtet mit der Zahl der Kinder"
            source="Daten: MSS 2025 (SenStadt), Grünanlagenbestand (SenMVKU), Jugendfreizeiteinrichtungen (SenBJF), Einwohnerdichte 2025 (AfS). Eigene Berechnung."
            :table-head="[
              'Status-Index',
              'Kinder',
              'Spielplatz in 400 m',
              'Spielfläche je Kind',
              'Jugendeinrichtung in 1000 m',
            ]"
            :table-rows="statusTable"
          >
            <div class="panels">
              <div v-for="panel in statusPanels" :key="panel.title">
                <h4>{{ panel.title }}</h4>
                <BarList :rows="panel.rows" :max="panel.max" />
              </div>
            </div>
          </ChartFigure>
        </template>
        <template #after>
          <p>
            Für Jugendliche ist das Gefälle am stärksten:
            {{ formatRounded(findings.age_groups.teens_without_youth_facility_within_1000) }}
            der 10- bis 17-Jährigen haben keine Jugendfreizeiteinrichtung in 1000 Metern.
            <RouterLink :to="{ name: 'explorer', query: { ind: 'youthShare1000' } }"
              >Zur Karte der Jugendeinrichtungen</RouterLink
            >
          </p>
        </template>
      </StoryChapter>

      <StoryChapter :number="4" title="Die Kinderzahl wächst dort, wo die Wege länger sind">
        <p>
          Zwischen Ende 2022 und Ende 2025 ist die Zahl der unter 18-Jährigen in der inneren Stadt
          um
          {{ zoneChange('Innere Stadt') }} gesunken und in der äußeren Stadt um
          {{ zoneChange('Äußere Stadt') }}
          gestiegen. Berlins Kinder leben zunehmend am Rand.
        </p>
        <p>
          In {{ findings.growth_2022_2025.planning_areas_growing_10pct }} Planungsräumen wuchs die
          Kinderzahl um mindestens zehn Prozent, zusammen um
          {{ formatRounded(findings.growth_2022_2025.children_added_in_growing_areas) }}
          Kinder. Gerade dort sind Spielplätze seltener fußläufig erreichbar.
        </p>
        <template #figure>
          <div class="figures inline">
            <KeyFigure
              :value="
                formatValue(
                  findings.growth_2022_2025.by_city_zone['Innere Stadt'] ?? 0,
                  'signedShare',
                )
              "
              caption="unter 18-Jährige in der inneren Stadt, Ende 2022 bis Ende 2025"
            />
            <KeyFigure
              :value="
                formatValue(
                  findings.growth_2022_2025.by_city_zone['Äußere Stadt'] ?? 0,
                  'signedShare',
                )
              "
              caption="unter 18-Jährige in der äußeren Stadt"
            />
          </div>
          <ChartFigure
            title="Kinder mit Spielplatz in 400 m Fußweg"
            subtitle="Planungsräume nach Entwicklung der Kinderzahl seit Ende 2022"
            source="Daten: Einwohnerdichte 2022 und 2025 (AfS), Grünanlagenbestand (SenMVKU). Eigene Berechnung."
            :table-head="['Planungsräume', 'Kinder mit Spielplatz in 400 m']"
            :table-rows="growthRows.map((row) => [row.label, row.display])"
          >
            <BarList :rows="growthRows" :max="1" />
          </ChartFigure>
        </template>
        <template #after>
          <p>
            <RouterLink :to="{ name: 'explorer', query: { ind: 'childrenChange' } }"
              >Karte: Wo die Kinderzahl wächst und wo sie sinkt</RouterLink
            >
          </p>
        </template>
      </StoryChapter>

      <StoryChapter :number="5" title="Was die amtliche Liste nicht zeigt">
        <p>
          Der amtliche Bestand kennt
          {{ formatCount(findings.osm_robustness.official_public_playgrounds) }} öffentliche
          Spielplätze. In OpenStreetMap sind in Berlin
          {{ formatCount(findings.osm_robustness.osm_playgrounds_in_berlin) }} eingetragen, darunter
          viele in Wohnanlagen. Für Großsiedlungen macht das den Unterschied: Nach amtlichem Bestand
          haben dort
          {{ share(findings.osm_robustness.share_children_large_estates_400_official_only) }}
          der Kinder einen Spielplatz in 400 Metern, mit den weiteren Plätzen sind es
          {{ share(findings.osm_robustness.share_children_large_estates_400_official_plus_osm) }}.
        </p>
        <p>
          Wer über Unterversorgung spricht, sollte diese Lücke kennen. Deshalb lässt sich im
          Explorer zwischen beiden Sichten umschalten. Flächenangaben gibt es nur für die
          öffentlichen Plätze.
        </p>
        <template #figure>
          <ChartFigure
            title="Großsiedlungen: Der amtliche Bestand zeigt nur einen Teil"
            subtitle="Anteil der Kinder mit einem Spielplatz in 400 m Fußweg, nach Bebauungstyp des Wohnblocks"
            source="Daten: Stadtstrukturtypen und Einwohnerdichte 2025 (Umweltatlas/AfS), Grünanlagenbestand (SenMVKU), OpenStreetMap. Eigene Berechnung."
            :table-head="['Bebauungstyp', 'nur öffentliche Spielplätze', 'mit OpenStreetMap']"
            :table-rows="
              housingRows.map((row) => [
                `${row.label} (${row.detail})`,
                row.fromDisplay,
                row.toDisplay,
              ])
            "
          >
            <DumbbellChart
              :rows="housingRows"
              from-label="nur öffentliche Spielplätze (amtlicher Bestand)"
              to-label="zusätzlich weitere in OpenStreetMap erfasste Spielplätze"
            />
          </ChartFigure>
        </template>
        <template #after>
          <p class="note">
            Auch zur Barrierefreiheit schweigt der amtliche Bestand: Kein Spielplatz hat eine Angabe
            zu Ausstattung oder Zugänglichkeit. In OpenStreetMap tragen
            {{ formatCount(findings.osm_robustness.osm_playgrounds_with_wheelchair_tag) }} von
            {{ formatCount(findings.osm_robustness.osm_playgrounds_in_berlin) }} Spielplätzen
            überhaupt eine Rollstuhl-Angabe. Eine fehlende Angabe bedeutet nicht, dass ein Platz
            nicht barrierefrei ist.
          </p>
        </template>
      </StoryChapter>

      <StoryChapter :number="6" title="Was wäre, wenn?">
        <p>
          Wo würde ein zusätzlicher Spielplatz die meisten Kinder erreichen, die bisher keinen in
          der Nähe haben? Wir haben zwei Möglichkeiten durchgerechnet: einen neuen Spielplatz in
          einer bestehenden öffentlichen Grünanlage und die Öffnung von Grundschulhöfen außerhalb
          der Unterrichtszeit. Kein Kind wird doppelt gezählt.
        </p>
        <p>
          25 Standorte in Grünanlagen würden
          {{ formatRounded(scenarioTotal('greenSpace', 'official')) }} Kinder zusätzlich erreichen,
          25 Schulhöfe {{ formatRounded(scenarioTotal('schoolyard', 'official')) }}. Rechnet man
          vorsichtig und zählt nur Kinder, die auch laut OpenStreetMap keinen Spielplatz in der Nähe
          haben, sind es {{ formatRounded(scenarioTotal('greenSpace', 'withOsm')) }} und
          {{ formatRounded(scenarioTotal('schoolyard', 'withOsm')) }}.
        </p>
        <template #figure>
          <ChartFigure
            title="Modellrechnung: Wenige Standorte, viele Kinder"
            subtitle="Zusätzlich erreichte Kinder ohne öffentlichen Spielplatz in 400 m Fußweg, bei Auswahl des jeweils wirksamsten nächsten Standorts"
            source="Hypothetisches Szenario. Eigentum, Naturschutz, Kosten und Aufsicht sind nicht geprüft. Eigene Berechnung."
            :table-head="['Standorte', 'Grünanlagen', 'Schulhöfe']"
            :table-rows="scenarioTable"
          >
            <LineChart
              :series="scenarioSeries"
              :x-max="25"
              :y-max="22000"
              :x-ticks="[0, 5, 10, 15, 20, 25]"
              :y-ticks="[0, 5000, 10000, 15000, 20000]"
              :marker-x="25"
              x-label="Anzahl der Standorte"
              :format-x="(value) => String(value)"
              :format-y="formatCount"
              description="Liniendiagramm: Die zusätzlich erreichten Kinder steigen mit der Zahl der Standorte, bei Grünanlagen etwa doppelt so stark wie bei Schulhöfen. Die Werte stehen in der Tabelle darunter."
            />
          </ChartFigure>
        </template>
        <template #after>
          <p>
            <RouterLink class="button" :to="{ name: 'potential' }"
              >Standorte auf der Karte ansehen</RouterLink
            >
          </p>
        </template>
      </StoryChapter>

      <section class="page closing">
        <div class="text-column">
          <h2>Selbst nachsehen</h2>
          <p>
            Alle Zahlen stammen aus offenen Daten des Landes Berlin, des Amts für Statistik und aus
            OpenStreetMap. Sie beschreiben Wege und Flächen, nicht die Qualität eines Spielplatzes
            und schon gar nicht die einer Kindheit.
          </p>
        </div>
        <ul class="next">
          <li>
            <RouterLink :to="{ name: 'explorer' }">Berlin-Explorer</RouterLink>
            <span>18 Kennzahlen für 542 Planungsräume, als Karte und Tabelle</span>
          </li>
          <li>
            <RouterLink :to="{ name: 'compare' }">Quartiersvergleich</RouterLink>
            <span>Zwei Quartiere nebeneinander, mit Vorschlägen für ähnliche Quartiere</span>
          </li>
          <li>
            <RouterLink :to="{ name: 'methods' }">Daten und Methodik</RouterLink>
            <span>Quellen, Rechenwege, Einschränkungen, Download</span>
          </li>
        </ul>
      </section>
    </template>
  </article>
</template>

<style scoped>
.hero {
  padding-top: var(--space-8);
  padding-bottom: var(--space-6);
}
.hero h1 {
  margin-bottom: var(--space-5);
}
.figures {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
  gap: var(--space-6);
  padding-bottom: var(--space-8);
}
.figures.inline {
  padding: var(--space-5) 0;
  max-width: 44rem;
}
.panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr));
  gap: var(--space-6);
}
h4 {
  font-family: var(--font-text);
  font-size: var(--size-small);
  font-weight: 600;
  margin: 0 0 var(--space-2);
  min-height: 2.6em;
}
.panels :deep(li) {
  grid-template-columns: 6rem 1fr auto;
}
.closing {
  padding-top: var(--space-8);
  border-top: 1px solid var(--color-rule);
}
.closing h2 {
  margin-bottom: var(--space-4);
}
.next {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr));
  gap: var(--space-5);
  margin: var(--space-6) 0 0;
  padding: 0;
  list-style: none;
}
.next li {
  border-top: 2px solid var(--color-ink);
  padding-top: var(--space-3);
}
.next a {
  display: block;
  font-family: var(--font-display);
  font-size: var(--size-h3);
  font-weight: 600;
}
.next span {
  color: var(--color-ink-secondary);
  font-size: var(--size-small);
}
</style>
