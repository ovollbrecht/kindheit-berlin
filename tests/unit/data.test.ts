/**
 * Consistency of the published data files: what the map, the tables and the story show
 * must agree with each other and with the findings the documentation quotes.
 */
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { DEFAULT_OPTIONS, INDICATORS } from '@/domain/indicators'
import type { DataSource, IndicatorData, ScenarioData, StoryData } from '@/domain/types'

const read = <T>(name: string) => JSON.parse(readFileSync(`public/data/${name}`, 'utf8')) as T
const indicators = read<IndicatorData>('indicators.json')
const story = read<StoryData>('story.json')
const scenarios = read<ScenarioData>('scenarios.json')
const sources = read<DataSource[]>('sources.json')
const geometry = read<{ features: { properties: { id: string } }[] }>('planning-areas.geojson')

describe('planning areas', () => {
  it('are the 542 areas of the LOR system, with matching geometry', () => {
    expect(indicators.areas).toHaveLength(542)
    expect(new Set(geometry.features.map((feature) => feature.properties.id))).toEqual(
      new Set(indicators.areas.map((area) => area.id)),
    )
  })
  it('add up to the Berlin totals', () => {
    const sum = (key: 'children' | 'residents' | 'age0to5' | 'age6to9' | 'age10to17') =>
      indicators.areas.reduce((total, area) => total + area[key], 0)
    expect(sum('children')).toBe(indicators.city.children)
    // Residents are rounded per area after distributing blocks to buildings.
    expect(Math.abs(sum('residents') - indicators.city.residents)).toBeLessThan(100)
    expect(
      Math.abs(sum('age0to5') + sum('age6to9') + sum('age10to17') - indicators.city.children),
    ).toBeLessThan(600)
  })
  it('publish no child-weighted values where too few children live', () => {
    for (const area of indicators.areas.filter((candidate) => !candidate.enoughChildren)) {
      expect(area.children, area.id).toBeLessThan(indicators.minChildrenForShares)
      expect(area.reach, area.id).toBeNull()
      expect(area.playM2PerChild, area.id).toBeNull()
    }
  })
  it('never reach more children on foot than as the crow flies', () => {
    for (const area of indicators.areas) {
      if (!area.reach) continue
      area.reach.walking.forEach((share, index) =>
        expect(share, area.id).toBeLessThanOrEqual((area.reach?.straight[index] ?? 0) + 1e-9),
      )
      area.reach.walking.forEach((share, index) =>
        expect(share, area.id).toBeLessThanOrEqual((area.reach?.withOsm[index] ?? 0) + 1e-9),
      )
    }
  })
  it('have a value or an explicit null for every indicator', () => {
    for (const indicator of INDICATORS) {
      const values = indicators.areas.map((area) => indicator.value(area, DEFAULT_OPTIONS))
      expect(
        values.some((value) => value !== null),
        indicator.key,
      ).toBe(true)
      expect(
        values.every((value) => value === null || Number.isFinite(value)),
        indicator.key,
      ).toBe(true)
      expect(indicator.value(indicators.city, DEFAULT_OPTIONS), indicator.key).not.toBeNull()
    }
  })
})

describe('story figures', () => {
  const at400 = (series: keyof StoryData['distanceCurves']['series']) =>
    story.distanceCurves.series[series][story.distanceCurves.distancesM.indexOf(400)] ?? NaN
  it('match the explorer: Berlin value of the reach indicator equals the curve at 400 m', () => {
    expect(at400('walking')).toBeCloseTo(indicators.city.reach?.walking[2] ?? NaN, 3)
    expect(at400('straight')).toBeCloseTo(indicators.city.reach?.straight[2] ?? NaN, 3)
    expect(at400('withOsm')).toBeCloseTo(indicators.city.reach?.withOsm[2] ?? NaN, 3)
  })
  it('reproduce the published findings', () => {
    // docs/FINDINGS.md quotes these; a change in the data must be noticed here.
    expect(at400('straight')).toBeCloseTo(0.863, 2)
    expect(at400('walking')).toBeCloseTo(0.702, 2)
    expect(story.findings.reference.children_under_18).toBe(627759)
    expect(story.findings.supply_per_child.city_m2_per_resident).toBeCloseTo(0.603, 2)
  })
  it('order the three ways of measuring consistently at every distance', () => {
    const { straight, walking, securedCrossings, noMainRoad } = story.distanceCurves.series
    walking.forEach((share, index) => {
      expect(share).toBeLessThanOrEqual((straight[index] ?? 0) + 1e-9)
      expect(securedCrossings[index] ?? 0).toBeLessThanOrEqual(share + 1e-9)
      expect(noMainRoad[index] ?? 0).toBeLessThanOrEqual((securedCrossings[index] ?? 0) + 1e-9)
    })
  })
})

describe('scenarios', () => {
  it('number their steps, sum up correctly and gain less with every step', () => {
    for (const scenario of Object.values(scenarios.scenarios)) {
      for (const steps of Object.values(scenario.variants)) {
        let cumulative = 0
        steps.forEach((step, index) => {
          cumulative += step.childrenReached
          expect(step.step).toBe(index + 1)
          expect(step.cumulative).toBe(cumulative)
          if (index > 0)
            expect(step.childrenReached).toBeLessThanOrEqual(steps[index - 1]?.childrenReached ?? 0)
        })
      }
    }
  })
  it('cannot reach more children than are counted as not yet served', () => {
    for (const scenario of Object.values(scenarios.scenarios)) {
      for (const variant of ['official', 'withOsm'] as const) {
        expect(scenario.variants[variant].at(-1)?.cumulative ?? 0).toBeLessThanOrEqual(
          scenario.summary[variant].children_without_playground_400,
        )
      }
    }
  })
  it('are more cautious when OpenStreetMap playgrounds count as existing supply', () => {
    for (const scenario of Object.values(scenarios.scenarios)) {
      expect(scenario.variants.withOsm.at(-1)?.cumulative ?? 0).toBeLessThan(
        scenario.variants.official.at(-1)?.cumulative ?? 0,
      )
    }
  })
})

describe('sources', () => {
  it('cover every source an indicator refers to', () => {
    const keys = new Set(sources.map((source) => source.key))
    for (const indicator of INDICATORS)
      for (const key of indicator.sources) expect(keys, `${indicator.key} -> ${key}`).toContain(key)
  })
  it('state licence, provider and a landing page', () => {
    for (const source of sources) {
      expect(source.license, source.key).toBeTruthy()
      expect(source.provider, source.key).toBeTruthy()
      expect(source.dataset_page, source.key).toMatch(/^https:\/\//)
    }
  })
})
