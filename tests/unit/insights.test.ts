import { describe, expect, it } from 'vitest'
import { deriveInsights, INSIGHT_RULES } from '@/domain/insights'
import type { AreaValues, PlanningArea } from '@/domain/types'

const reach = (walking: number, straight: number, withOsm: number) => ({
  walking: [0, 0, walking, 0, 0, 0],
  straight: [0, 0, straight, 0, 0, 0],
  withOsm: [0, 0, withOsm, 0, 0, 0],
})

const city = {
  reach: reach(0.7, 0.86, 0.84),
  playM2PerChild: 3.8,
  daycarePlacesPerChild: 0.93,
} as AreaValues

/** An area that matches Berlin on everything: no rule may fire. */
const average = {
  enoughChildren: true,
  reach: reach(0.7, 0.86, 0.84),
  shareNoMainRoad400: 0.65,
  playM2PerChild: 3.8,
  childrenChange: 0,
  youthShare1000: 0.76,
  daycarePlacesPerChild: 0.93,
} as PlanningArea

const ids = (area: PlanningArea) => deriveInsights(area, city).map((insight) => insight.id)

describe('deriveInsights', () => {
  it('stays silent for an average area', () => {
    expect(ids(average)).toEqual([])
  })
  it('never comments on areas with too few children', () => {
    expect(ids({ ...average, enoughChildren: false, youthShare1000: 0 })).toEqual([])
  })
  it('flags a clear difference to Berlin and quotes both numbers', () => {
    const [insight] = deriveInsights({ ...average, reach: reach(0.5, 0.6, 0.55) }, city)
    expect(insight?.id).toBe('reach-vs-city')
    expect(insight?.text).toMatch(/weniger/)
    expect(insight?.text.replace(/ /g, ' ')).toContain('50 %')
    expect(insight?.text.replace(/ /g, ' ')).toContain('70 %')
  })
  it('does not flag a difference just below the threshold', () => {
    expect(ids({ ...average, reach: reach(0.56, 0.7, 0.6) })).toEqual([])
  })
  it('flags detours, main roads and the gap in the official register independently', () => {
    expect(ids({ ...average, reach: reach(0.6, 0.9, 0.7) })).toEqual(['detour-gap'])
    expect(ids({ ...average, shareNoMainRoad400: 0.5 })).toEqual(['main-road'])
    expect(ids({ ...average, reach: reach(0.7, 0.86, 0.97) })).toEqual(['register-gap'])
  })
  it('flags growth only when access is below Berlin', () => {
    expect(ids({ ...average, childrenChange: 0.2 })).toEqual([])
    expect(ids({ ...average, childrenChange: 0.2, reach: reach(0.6, 0.75, 0.7) })).toEqual([
      'growth',
    ])
  })
  it('treats missing values as unknown, not as a finding', () => {
    expect(
      ids({ ...average, youthShare1000: null, daycarePlacesPerChild: null, playM2PerChild: null }),
    ).toEqual([])
  })
  it('documents every rule', () => {
    for (const rule of INSIGHT_RULES) expect(rule.rule.length, rule.id).toBeGreaterThan(30)
  })
})
