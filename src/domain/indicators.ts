/**
 * Central definition of every indicator the application can show:
 * label, explanation, unit, map classes and source. Views never hard-code these.
 */
import type { ValueFormat } from './format'
import type { AreaValues, ReachVariant } from './types'

export interface IndicatorOptions {
  /** Which playgrounds and which kind of distance the playground reach uses. */
  reachVariant: ReachVariant
  /** Index into IndicatorData.reachThresholdsM. */
  thresholdIndex: number
}

export const DEFAULT_THRESHOLD_INDEX = 2 // 400 m
export const DEFAULT_OPTIONS: IndicatorOptions = {
  reachVariant: 'walking',
  thresholdIndex: DEFAULT_THRESHOLD_INDEX,
}

export const REACH_VARIANT_LABELS: Record<ReachVariant, string> = {
  walking: 'Fußweg, öffentliche Spielplätze',
  straight: 'Luftlinie, öffentliche Spielplätze',
  withOsm: 'Fußweg, zusätzlich Spielplätze aus OpenStreetMap',
}

export type IndicatorKey =
  | 'playgroundReach'
  | 'playgroundMedianM'
  | 'playM2PerChild'
  | 'shareNoMainRoad400'
  | 'smallChildren200'
  | 'greenShare400'
  | 'youthShare1000'
  | 'youthPlacesPer100'
  | 'daycareMedianM'
  | 'daycarePlacesPerChild'
  | 'primarySchoolMedianM'
  | 'libraryMedianM'
  | 'children'
  | 'childShare'
  | 'childrenChange'
  | 'childPoverty'
  | 'livingSpace'
  | 'densityPerHa'

export type IndicatorGroup =
  'Spielen und Grün' | 'Jugendliche' | 'Kita, Schule, Bibliothek' | 'Kinder im Quartier' | 'Kontext'

export interface IndicatorDefinition {
  key: IndicatorKey
  group: IndicatorGroup
  label: string
  /** One sentence: what is measured and how. */
  description: string
  format: ValueFormat
  /** Four ascending limits that split the map into five classes. */
  breaks: [number, number, number, number]
  /** "diverging" for change around zero, otherwise one hue from light to dark. */
  scale: 'sequential' | 'diverging'
  /** Whether the indicator reacts to the distance and variant controls. */
  usesReachOptions: boolean
  /** Keys of public/data/sources.json */
  sources: string[]
  value: (area: AreaValues, options: IndicatorOptions) => number | null
}

const field =
  (name: Exclude<keyof AreaValues, 'reach'>) =>
  (area: AreaValues): number | null =>
    area[name]

const WALKING_SOURCES = ['blocks_population_2025', 'residential_buildings', 'berlin.osm.pbf']

export const INDICATORS: IndicatorDefinition[] = [
  {
    key: 'playgroundReach',
    group: 'Spielen und Grün',
    label: 'Kinder mit Spielplatz in der Nähe',
    description:
      'Anteil der unter 18-Jährigen, deren Wohngebäude höchstens die gewählte Entfernung vom nächsten Spielplatz liegt.',
    format: 'share',
    breaks: [0.2, 0.4, 0.6, 0.8],
    scale: 'sequential',
    usesReachOptions: true,
    sources: ['playgrounds', ...WALKING_SOURCES],
    value: (area, options) => area.reach?.[options.reachVariant][options.thresholdIndex] ?? null,
  },
  {
    key: 'playM2PerChild',
    group: 'Spielen und Grün',
    label: 'Erreichbare Spielfläche je Kind',
    description:
      'Netto-Spielfläche öffentlicher Spielplätze in 1000 m Fußweg, geteilt durch alle Kinder, die denselben Platz erreichen (zweistufiges Einzugsbereichsverfahren).',
    format: 'squareMeters',
    breaks: [1.5, 3, 4.5, 6],
    scale: 'sequential',
    usesReachOptions: false,
    sources: ['playgrounds', ...WALKING_SOURCES],
    value: field('playM2PerChild'),
  },
  {
    key: 'playgroundMedianM',
    group: 'Spielen und Grün',
    label: 'Mittlerer Fußweg zum Spielplatz',
    description:
      'Median des Fußwegs zum nächsten öffentlichen Spielplatz über alle Kinder des Quartiers.',
    format: 'meters',
    breaks: [200, 300, 450, 700],
    scale: 'sequential',
    usesReachOptions: false,
    sources: ['playgrounds', ...WALKING_SOURCES],
    value: field('playgroundMedianM'),
  },
  {
    key: 'shareNoMainRoad400',
    group: 'Spielen und Grün',
    label: 'Spielplatz in 400 m ohne Hauptstraße',
    description:
      'Anteil der Kinder, die einen öffentlichen Spielplatz in 400 m Fußweg erreichen, ohne eine Hauptverkehrsstraße zu queren.',
    format: 'share',
    breaks: [0.2, 0.4, 0.6, 0.8],
    scale: 'sequential',
    usesReachOptions: false,
    sources: ['playgrounds', ...WALKING_SOURCES],
    value: field('shareNoMainRoad400'),
  },
  {
    key: 'smallChildren200',
    group: 'Spielen und Grün',
    label: 'Unter 6-Jährige mit Spielplatz in 200 m',
    description:
      'Anteil der unter 6-Jährigen mit einem öffentlichen Spielplatz in höchstens 200 m Fußweg.',
    format: 'share',
    breaks: [0.15, 0.3, 0.45, 0.6],
    scale: 'sequential',
    usesReachOptions: false,
    sources: ['playgrounds', ...WALKING_SOURCES],
    value: field('smallChildren200'),
  },
  {
    key: 'greenShare400',
    group: 'Spielen und Grün',
    label: 'Kinder mit Grünanlage in 400 m',
    description:
      'Anteil der Kinder mit einer öffentlichen Grünanlage ab 0,5 Hektar in höchstens 400 m Fußweg.',
    format: 'share',
    breaks: [0.2, 0.4, 0.6, 0.8],
    scale: 'sequential',
    usesReachOptions: false,
    sources: ['green_spaces', ...WALKING_SOURCES],
    value: field('greenShare400'),
  },
  {
    key: 'youthShare1000',
    group: 'Jugendliche',
    label: '10- bis 17-Jährige mit Jugendfreizeiteinrichtung in 1000 m',
    description:
      'Anteil der 10- bis 17-Jährigen mit einer Jugendfreizeiteinrichtung in höchstens 1000 m Fußweg.',
    format: 'share',
    breaks: [0.2, 0.4, 0.6, 0.8],
    scale: 'sequential',
    usesReachOptions: false,
    sources: ['youth_facilities', ...WALKING_SOURCES],
    value: field('youthShare1000'),
  },
  {
    key: 'youthPlacesPer100',
    group: 'Jugendliche',
    label: 'Plätze in Jugendfreizeiteinrichtungen je 100 Jugendliche',
    description:
      'Plätze der Einrichtungen in 1000 m Fußweg, geteilt durch alle 10- bis 17-Jährigen, die dieselbe Einrichtung erreichen.',
    format: 'decimal',
    breaks: [5, 12, 20, 30],
    scale: 'sequential',
    usesReachOptions: false,
    sources: ['youth_facilities', ...WALKING_SOURCES],
    value: field('youthPlacesPer100'),
  },
  {
    key: 'daycarePlacesPerChild',
    group: 'Kita, Schule, Bibliothek',
    label: 'Genehmigte Kita-Plätze je Kind unter 6',
    description:
      'Genehmigte Plätze der Kitas in 1000 m Fußweg, geteilt durch alle unter 6-Jährigen, die dieselbe Kita erreichen. Über freie Plätze sagt der Wert nichts.',
    format: 'decimal',
    breaks: [0.5, 0.75, 1, 1.25],
    scale: 'sequential',
    usesReachOptions: false,
    sources: ['daycare', ...WALKING_SOURCES],
    value: field('daycarePlacesPerChild'),
  },
  {
    key: 'daycareMedianM',
    group: 'Kita, Schule, Bibliothek',
    label: 'Mittlerer Fußweg zur nächsten Kita',
    description: 'Median des Fußwegs zur nächsten Kita über alle unter 6-Jährigen des Quartiers.',
    format: 'meters',
    breaks: [200, 300, 450, 700],
    scale: 'sequential',
    usesReachOptions: false,
    sources: ['daycare', ...WALKING_SOURCES],
    value: field('daycareMedianM'),
  },
  {
    key: 'primarySchoolMedianM',
    group: 'Kita, Schule, Bibliothek',
    label: 'Mittlerer Fußweg zur nächsten Grundschule',
    description:
      'Median des Fußwegs zur nächsten öffentlichen Grundschule über alle 6- bis 9-Jährigen. Die zuständige Schule laut Einschulbereich kann eine andere sein.',
    format: 'meters',
    breaks: [400, 600, 800, 1200],
    scale: 'sequential',
    usesReachOptions: false,
    sources: ['schools', ...WALKING_SOURCES],
    value: field('primarySchoolMedianM'),
  },
  {
    key: 'libraryMedianM',
    group: 'Kita, Schule, Bibliothek',
    label: 'Mittlerer Fußweg zur nächsten Bibliothek',
    description:
      'Median des Fußwegs zur nächsten in OpenStreetMap erfassten Bibliothek über alle Kinder.',
    format: 'meters',
    breaks: [600, 1000, 1500, 2500],
    scale: 'sequential',
    usesReachOptions: false,
    sources: WALKING_SOURCES,
    value: field('libraryMedianM'),
  },
  {
    key: 'children',
    group: 'Kinder im Quartier',
    label: 'Zahl der unter 18-Jährigen',
    description: 'Einwohnerinnen und Einwohner unter 18 Jahren am 31.12.2025.',
    format: 'count',
    breaks: [500, 1000, 1500, 2500],
    scale: 'sequential',
    usesReachOptions: false,
    sources: ['blocks_population_2025'],
    value: field('children'),
  },
  {
    key: 'childShare',
    group: 'Kinder im Quartier',
    label: 'Anteil der unter 18-Jährigen',
    description: 'Unter 18-Jährige je Einwohner am 31.12.2025.',
    format: 'share',
    breaks: [0.12, 0.15, 0.18, 0.21],
    scale: 'sequential',
    usesReachOptions: false,
    sources: ['blocks_population_2025'],
    value: field('childShare'),
  },
  {
    key: 'childrenChange',
    group: 'Kinder im Quartier',
    label: 'Veränderung der Kinderzahl 2022 bis 2025',
    description: 'Veränderung der Zahl der unter 18-Jährigen vom 31.12.2022 bis zum 31.12.2025.',
    format: 'signedShare',
    breaks: [-0.1, -0.03, 0.03, 0.1],
    scale: 'diverging',
    usesReachOptions: false,
    sources: ['blocks_population_2025', 'blocks_population_2022'],
    value: field('childrenChange'),
  },
  {
    key: 'childPoverty',
    group: 'Kontext',
    label: 'Kinderarmut',
    description:
      'Anteil der unter 15-Jährigen in Bedarfsgemeinschaften nach SGB II am 31.12.2024 (Monitoring Soziale Stadtentwicklung 2025, Indikator S4).',
    format: 'percentValue',
    breaks: [8, 16, 28, 40],
    scale: 'sequential',
    usesReachOptions: false,
    sources: ['mss2025_index_indicators'],
    value: field('childPoverty'),
  },
  {
    key: 'livingSpace',
    group: 'Kontext',
    label: 'Wohnfläche je Einwohner',
    description:
      'Durchschnittliche Wohnfläche je Einwohnerin und Einwohner in m² am 31.12.2024 (Monitoring Soziale Stadtentwicklung 2025, Indikator K15).',
    format: 'squareMeters',
    breaks: [32, 36, 40, 46],
    scale: 'sequential',
    usesReachOptions: false,
    sources: ['mss2025_context_indicators'],
    value: field('livingSpace'),
  },
  {
    key: 'densityPerHa',
    group: 'Kontext',
    label: 'Einwohner je Hektar bewohnter Blockfläche',
    description: 'Einwohner am 31.12.2025 geteilt durch die Fläche der bewohnten Blöcke.',
    format: 'count',
    breaks: [50, 120, 220, 320],
    scale: 'sequential',
    usesReachOptions: false,
    sources: ['blocks_population_2025'],
    value: field('densityPerHa'),
  },
]

const BY_KEY = new Map(INDICATORS.map((indicator) => [indicator.key, indicator]))

export function isIndicatorKey(key: string): key is IndicatorKey {
  return BY_KEY.has(key as IndicatorKey)
}

export function getIndicator(key: IndicatorKey): IndicatorDefinition {
  // Every IndicatorKey is defined above; the test suite checks this.
  return BY_KEY.get(key) as IndicatorDefinition
}

/** Class index 0..4 for a value, given the four limits of an indicator. */
export function classIndex(value: number, breaks: readonly number[]): number {
  const index = breaks.findIndex((limit) => value < limit)
  return index === -1 ? breaks.length : index
}
