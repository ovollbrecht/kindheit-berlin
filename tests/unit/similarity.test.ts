import { describe, expect, it } from 'vitest'
import { findSimilarAreas } from '@/domain/similarity'
import type { PlanningArea } from '@/domain/types'

function area(
  id: string,
  densityPerHa: number,
  childShare: number,
  childPoverty: number | null,
  children: number,
  enoughChildren = true,
): PlanningArea {
  return {
    id,
    name: id,
    densityPerHa,
    childShare,
    childPoverty,
    children,
    enoughChildren,
  } as PlanningArea
}

const target = area('target', 200, 0.16, 20, 1000)
const areas = [
  target,
  area('twin', 205, 0.16, 21, 1010),
  area('dense', 400, 0.16, 20, 1000),
  area('poor', 200, 0.16, 60, 1000),
  area('tiny', 200, 0.16, 20, 40, false),
  area('unknown', 200, 0.16, null, 1000),
]

describe('findSimilarAreas', () => {
  it('ranks the closest area first and never returns the target itself', () => {
    const result = findSimilarAreas(target, areas, 3)
    expect(result.map((entry) => entry.area.id)).toEqual(
      ['twin', 'dense', 'poor'].sort((a, b) => (a === 'twin' ? -1 : b === 'twin' ? 1 : 0)),
    )
    expect(result[0]?.area.id).toBe('twin')
    expect(result.some((entry) => entry.area.id === 'target')).toBe(false)
  })
  it('skips areas with too few children or missing features', () => {
    const ids = findSimilarAreas(target, areas, 10).map((entry) => entry.area.id)
    expect(ids).not.toContain('tiny')
    expect(ids).not.toContain('unknown')
  })
  it('reports distances in ascending order', () => {
    const distances = findSimilarAreas(target, areas, 10).map((entry) => entry.distance)
    expect(distances).toEqual([...distances].sort((a, b) => a - b))
  })
  it('returns nothing if the target itself lacks a feature', () => {
    expect(findSimilarAreas(area('x', 200, 0.16, null, 1000), areas, 3)).toEqual([])
  })
})
