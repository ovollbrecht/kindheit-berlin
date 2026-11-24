/**
 * Finds planning areas with similar framework conditions, so that differences in
 * supply can be compared fairly. Similarity never uses the supply indicators themselves.
 */
import type { PlanningArea } from './types'

export interface SimilarityFeature {
  key: 'densityPerHa' | 'childShare' | 'childPoverty' | 'children'
  label: string
}

export const SIMILARITY_FEATURES: SimilarityFeature[] = [
  { key: 'densityPerHa', label: 'Bebauungsdichte (Einwohner je Hektar)' },
  { key: 'childShare', label: 'Anteil der unter 18-Jährigen' },
  { key: 'childPoverty', label: 'Kinderarmut' },
  { key: 'children', label: 'Zahl der Kinder' },
]

export interface SimilarArea {
  area: PlanningArea
  /** Euclidean distance in standard deviations; 0 = identical on all features. */
  distance: number
}

type FeatureVector = number[]

function featureVector(area: PlanningArea): FeatureVector | null {
  const values = SIMILARITY_FEATURES.map((feature) => area[feature.key])
  return values.every((value): value is number => value !== null) ? values : null
}

function meanAndDeviation(values: number[]): { mean: number; deviation: number } {
  const mean = values.reduce((sum, value) => sum + value, 0) / values.length
  const variance = values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length
  return { mean, deviation: Math.sqrt(variance) || 1 }
}

/** The `count` most similar areas to `target`, nearest first. Areas with too few children
 *  or missing features are not considered. */
export function findSimilarAreas(
  target: PlanningArea,
  areas: PlanningArea[],
  count: number,
): SimilarArea[] {
  const candidates = areas
    .filter((area) => area.enoughChildren)
    .map((area) => ({ area, vector: featureVector(area) }))
    .filter(
      (entry): entry is { area: PlanningArea; vector: FeatureVector } => entry.vector !== null,
    )
  const targetVector = featureVector(target)
  if (!targetVector || candidates.length === 0) return []

  const statistics = SIMILARITY_FEATURES.map((_, index) =>
    meanAndDeviation(candidates.map((entry) => entry.vector[index] as number)),
  )
  const standardise = (vector: FeatureVector) =>
    vector.map((value, index) => {
      const { mean, deviation } = statistics[index] as { mean: number; deviation: number }
      return (value - mean) / deviation
    })
  const standardTarget = standardise(targetVector)

  return candidates
    .filter((entry) => entry.area.id !== target.id)
    .map((entry) => {
      const standard = standardise(entry.vector)
      const squared = standard.reduce(
        (sum, value, index) => sum + (value - (standardTarget[index] as number)) ** 2,
        0,
      )
      return { area: entry.area, distance: Math.sqrt(squared) }
    })
    .sort((a, b) => a.distance - b.distance)
    .slice(0, count)
}
