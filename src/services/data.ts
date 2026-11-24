/** Loads the static data files. Each file is fetched once and cached for the session. */
import type { FeatureCollection, MultiPolygon, Polygon } from 'geojson'
import type { DataSource, IndicatorData, ScenarioData, StoryData } from '@/domain/types'

export type AreaGeometries = FeatureCollection<Polygon | MultiPolygon, { id: string; name: string }>
export type DistrictGeometries = FeatureCollection<
  Polygon | MultiPolygon,
  { name: string; labelLon: number; labelLat: number }
>

const cache = new Map<string, Promise<unknown>>()

async function fetchJson(fileName: string): Promise<unknown> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/${fileName}`)
  if (!response.ok) {
    throw new Error(`Die Datei ${fileName} konnte nicht geladen werden (HTTP ${response.status}).`)
  }
  return response.json()
}

function load<T>(fileName: string, isValid: (content: unknown) => boolean): Promise<T> {
  let pending = cache.get(fileName)
  if (!pending) {
    pending = fetchJson(fileName).then((content) => {
      if (!isValid(content))
        throw new Error(`Die Datei ${fileName} hat nicht den erwarteten Aufbau.`)
      return content
    })
    // A failed request must not be cached, so that a retry can succeed.
    pending.catch(() => cache.delete(fileName))
    cache.set(fileName, pending)
  }
  return pending as Promise<T>
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null
const isFeatureCollection = (value: unknown) => isRecord(value) && Array.isArray(value.features)

export const loadIndicators = () =>
  load<IndicatorData>(
    'indicators.json',
    (content) => isRecord(content) && Array.isArray(content.areas) && isRecord(content.city),
  )
export const loadStory = () =>
  load<StoryData>('story.json', (content) => isRecord(content) && isRecord(content.findings))
export const loadScenarios = () =>
  load<ScenarioData>(
    'scenarios.json',
    (content) => isRecord(content) && isRecord(content.scenarios),
  )
export const loadSources = () => load<DataSource[]>('sources.json', Array.isArray)
export const loadAreaGeometries = () =>
  load<AreaGeometries>('planning-areas.geojson', isFeatureCollection)
export const loadDistrictGeometries = () =>
  load<DistrictGeometries>('districts.geojson', isFeatureCollection)
