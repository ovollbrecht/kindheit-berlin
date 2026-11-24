<script setup lang="ts">
import TableScroll from '@/components/TableScroll.vue'
import { computed } from 'vue'
import AsyncState from '@/components/AsyncState.vue'
import { useAsyncData } from '@/composables/useAsyncData'
import { REPOSITORY_URL } from '@/config'
import { INDICATORS } from '@/domain/indicators'
import { INSIGHT_RULES } from '@/domain/insights'
import { SIMILARITY_FEATURES } from '@/domain/similarity'
import { loadIndicators, loadSources } from '@/services/data'

const { data, error, loading, reload } = useAsyncData(async () => {
  const [sources, indicators] = await Promise.all([loadSources(), loadIndicators()])
  return { sources, indicators }
})

const dataUrl = (fileName: string) => `${import.meta.env.BASE_URL}data/${fileName}`
const DOWNLOADS = [
  { file: 'planning-area-indicators.csv', label: 'Alle Kennzahlen je Planungsraum (CSV)' },
  { file: 'indicators.json', label: 'Kennzahlen mit Berliner Vergleichswerten (JSON)' },
  { file: 'scenarios.json', label: 'Szenarien: Standorte und erreichte Kinder (JSON)' },
  { file: 'planning-areas.geojson', label: 'Vereinfachte Geometrie der Planungsräume (GeoJSON)' },
]
const formatDate = (iso: string | null) =>
  iso ? new Date(iso).toLocaleDateString('de-DE') : 'unbekannt'
const sourceTitle = (key: string) =>
  data.value?.sources.find((source) => source.key === key)?.title ?? key
const indicatorSources = computed(
  () =>
    new Map(
      INDICATORS.map((indicator) => [indicator.key, indicator.sources.map(sourceTitle).join('; ')]),
    ),
)
</script>

<template>
  <div class="page methods">
    <header class="text-column">
      <p class="eyebrow">Daten und Methodik</p>
      <h1>Woher die Zahlen kommen</h1>
      <p class="lead">
        Jede Kennzahl dieser Anwendung lässt sich auf offene Daten und einen dokumentierten
        Rechenweg zurückführen. Die Skripte sind öffentlich.
      </p>
    </header>

    <nav class="toc" aria-label="Inhalt dieser Seite">
      <a href="#rechenweg">Rechenweg</a>
      <a href="#kennzahlen">Kennzahlen</a>
      <a href="#regeln">Regeln für Auffälligkeiten</a>
      <a href="#grenzen">Grenzen</a>
      <a href="#quellen">Quellen</a>
      <a href="#download">Download</a>
    </nav>

    <section id="rechenweg" class="text-column">
      <h2>Der Rechenweg in sieben Schritten</h2>
      <ol>
        <li>
          <strong>Wo Kinder wohnen.</strong> Das Amt für Statistik veröffentlicht die Einwohner nach
          Altersgruppen je Block (31.12.2025). Wir verteilen sie auf die Wohngebäude des Blocks, im
          Verhältnis zur Geschossfläche (Grundfläche mal Geschosszahl aus ALKIS). So entstehen rund
          167.000 Wohnstandorte.
        </li>
        <li>
          <strong>Das Wegenetz.</strong> Alle für Fußgänger nutzbaren Wege aus OpenStreetMap:
          Gehwege, Wohnstraßen, Parkwege, Treppen. Autobahnen und gesperrte Wege gehören nicht dazu.
        </li>
        <li>
          <strong>Der Weg zum Angebot.</strong> Für jeden Wohnstandort berechnen wir die kürzeste
          Strecke im Wegenetz zum nächsten Spielplatz, zur nächsten Kita, Grundschule,
          Jugendfreizeiteinrichtung, Grünanlage, Sportanlage und Bibliothek. Flächen wie Spielplätze
          gelten an jedem Wegpunkt im Umkreis von 15 Metern als erreicht.
        </li>
        <li>
          <strong>Hauptstraßen.</strong> In einer zweiten Rechnung dürfen Hauptverkehrsstraßen
          (OpenStreetMap-Klassen primary, secondary, trunk) gar nicht gequert werden, in einer
          dritten nur an Ampeln und markierten Überwegen.
        </li>
        <li>
          <strong>Fläche je Kind.</strong> Die Netto-Spielfläche jedes Platzes wird durch alle
          Kinder geteilt, die ihn in 1000 Metern erreichen. Jedes Kind erhält die Summe der Anteile
          seiner erreichbaren Plätze (zweistufiges Einzugsbereichsverfahren). Verwaltungsgrenzen
          spielen dabei keine Rolle.
        </li>
        <li>
          <strong>Zusammenfassung.</strong> Für jeden der 542 Planungsräume werden die Werte mit der
          Zahl der Kinder gewichtet. Bei weniger als
          {{ data?.indicators.minChildrenForShares ?? 100 }} Kindern weisen wir keine Anteile aus.
        </li>
        <li>
          <strong>Szenarien.</strong> Schrittweise wird der Standort gewählt, der die meisten noch
          nicht erreichten Kinder hinzugewinnt (Greedy-Verfahren für das Maximum-Coverage-Problem).
          Kein Kind wird doppelt gezählt.
        </li>
      </ol>
      <p>
        Entfernungen: 200 Meter für unter 6-Jährige, 400 Meter als allgemeine Schwelle, 1000 Meter
        für ältere Kinder und Jugendliche, angelehnt an DIN 18034. Im Explorer lässt sich die
        Schwelle ändern.
      </p>
      <p>
        <strong>Ähnliche Quartiere</strong> werden über vier standardisierte Merkmale bestimmt:
        {{ SIMILARITY_FEATURES.map((feature) => feature.label).join(', ') }}. Versorgungskennzahlen
        fließen nicht ein.
      </p>
    </section>

    <section id="kennzahlen">
      <h2>Kennzahlen</h2>
      <TableScroll label="Tabelle der Kennzahlen">
        <table>
          <thead>
            <tr>
              <th scope="col">Kennzahl</th>
              <th scope="col">Berechnung</th>
              <th scope="col">Quellen</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="indicator in INDICATORS" :key="indicator.key">
              <th scope="row">{{ indicator.label }}</th>
              <td>{{ indicator.description }}</td>
              <td class="small">{{ indicatorSources.get(indicator.key) }}</td>
            </tr>
          </tbody>
        </table>
      </TableScroll>
    </section>

    <section id="regeln" class="text-column">
      <h2>Regeln für Auffälligkeiten</h2>
      <p>
        Die Hinweise im Quartiersprofil entstehen aus diesen festen Regeln. Ein Hinweis erscheint
        nur, wenn seine Bedingung erfüllt ist, und nennt immer die Zahlen, auf denen er beruht.
      </p>
      <ol>
        <li v-for="rule in INSIGHT_RULES" :key="rule.id">{{ rule.rule }}</li>
      </ol>
    </section>

    <section id="grenzen" class="text-column">
      <h2>Was die Zahlen nicht können</h2>
      <ul>
        <li>
          <strong>Spielplätze in Wohnanlagen fehlen im amtlichen Bestand.</strong> Er enthält nur
          öffentliche Spielplätze der Bezirke. OpenStreetMap schließt die Lücke teilweise, aber ohne
          Flächen. Die Spielfläche je Kind gilt deshalb nur für öffentliche Plätze.
        </li>
        <li>
          <strong>Wohnorte sind ein Modell.</strong> Innerhalb eines Blocks kennen wir nur die
          Gebäude, nicht die Familien. Die Unsicherheit der Berliner Gesamtwerte liegt bei wenigen
          Prozentpunkten.
        </li>
        <li>
          <strong>Das Wegenetz ist nicht vollständig.</strong> Wege durch Wohnanlagen, Zäune und
          tatsächliche Eingänge sind nicht überall erfasst, Querungen ebenso wenig.
        </li>
        <li>
          <strong>Hauptstraßen sind über die Straßenklasse bestimmt,</strong> nicht über gemessene
          Verkehrsmengen oder Geschwindigkeiten.
        </li>
        <li>
          <strong>Nähe ist nicht Qualität.</strong> Zustand, Ausstattung, Aufsicht und
          Barrierefreiheit der Angebote sind in den Daten nicht enthalten. Fehlende Angaben zur
          Barrierefreiheit bedeuten nicht, dass ein Angebot nicht barrierefrei ist.
        </li>
        <li>
          <strong>Kita-Plätze sind genehmigte Plätze.</strong> Ob Plätze frei sind, ist nicht
          veröffentlicht.
        </li>
        <li>
          <strong>Unfälle haben kein Alter.</strong> Der Unfallatlas nennt Ort und Zeit, aber nicht,
          ob Kinder beteiligt waren.
        </li>
        <li>
          <strong>Zusammenhänge sind keine Ursachen.</strong> Alle Vergleiche beziehen sich auf
          Gebiete. Rückschlüsse auf einzelne Kinder oder Familien sind nicht zulässig.
        </li>
        <li>
          <strong>Die Datenstände unterscheiden sich:</strong> Bevölkerung Ende 2025, Sozialdaten
          Ende 2024, Umwelt 2023/2024, Unfälle 2018 bis 2024.
        </li>
      </ul>
    </section>

    <section id="quellen">
      <h2>Quellen und Lizenzen</h2>
      <AsyncState :loading="loading" :error="error" @retry="reload">
        <TableScroll v-if="data" label="Tabelle der Datenquellen">
          <table>
            <thead>
              <tr>
                <th scope="col">Datensatz</th>
                <th scope="col">Anbieter</th>
                <th scope="col">Stand</th>
                <th scope="col">Verwendet für</th>
                <th scope="col">Lizenz</th>
                <th scope="col">Abruf</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="source in data.sources" :key="source.key">
                <th scope="row">
                  <a :href="source.dataset_page">{{ source.title }}</a>
                </th>
                <td>{{ source.provider }}</td>
                <td>{{ source.reference_date }}</td>
                <td>{{ source.used_for }}</td>
                <td>{{ source.license }}</td>
                <td>{{ formatDate(source.retrieved) }}</td>
              </tr>
            </tbody>
          </table>
        </TableScroll>
      </AsyncState>
      <p class="small secondary text-column">
        Geodaten des Landes Berlin: Datenlizenz Deutschland – Zero – Version 2.0. Amt für Statistik
        Berlin-Brandenburg: CC BY 3.0 DE. OpenStreetMap: © OpenStreetMap-Mitwirkende, Open Database
        License. Die abgeleiteten Kennzahlen aus OpenStreetMap-Daten stehen ebenfalls unter der
        ODbL.
      </p>
    </section>

    <section id="download" class="text-column">
      <h2>Download und Nachnutzung</h2>
      <ul>
        <li v-for="download in DOWNLOADS" :key="download.file">
          <a :href="dataUrl(download.file)" download>{{ download.label }}</a>
        </li>
      </ul>
      <p>
        Eigene Texte und Grafiken stehen unter
        <a href="https://creativecommons.org/licenses/by/4.0/deed.de">CC BY 4.0</a>, der Quellcode
        unter der MIT-Lizenz. Datenaufbereitung und Auswertung lassen sich mit den Skripten im
        <a :href="REPOSITORY_URL">Repository</a> vollständig nachrechnen.
      </p>
      <p>
        <strong>Einsatz von KI:</strong> Recherche, Datenaufbereitung, Auswertung, Programmcode und
        Texte wurden mit Claude Code (Anthropic) erstellt und vom Einreichenden geprüft. Die Zahlen
        in der Anwendung werden nicht von einem Sprachmodell erzeugt, sondern von den
        veröffentlichten Skripten berechnet.
      </p>
    </section>
  </div>
</template>

<style scoped>
.methods {
  padding-top: var(--space-7);
}
header h1 {
  font-size: var(--size-h2);
  margin-bottom: var(--space-4);
}
.toc {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-5);
  margin: var(--space-6) 0;
  padding: var(--space-3) 0;
  border-top: 1px solid var(--color-rule);
  border-bottom: 1px solid var(--color-rule);
}
section {
  margin-top: var(--space-8);
  scroll-margin-top: var(--space-5);
}
section h2 {
  font-size: 1.6rem;
  margin-bottom: var(--space-4);
}
li {
  margin-bottom: var(--space-3);
}
tbody th {
  font-weight: 600;
  font-size: inherit;
  color: inherit;
  border-bottom-color: var(--color-rule-soft);
  min-width: 13rem;
}
td {
  font-size: var(--size-small);
}
</style>
