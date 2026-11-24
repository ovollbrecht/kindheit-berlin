import { describe, expect, it } from 'vitest'
import {
  classIndex,
  DEFAULT_OPTIONS,
  getIndicator,
  INDICATORS,
  isIndicatorKey,
} from '@/domain/indicators'
import type { AreaValues } from '@/domain/types'

const area = {
  reach: {
    walking: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
    straight: [0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
    withOsm: [0.1, 0.2, 0.35, 0.4, 0.5, 0.6],
  },
  playM2PerChild: 2.5,
} as AreaValues

describe('indicator definitions', () => {
  it('have unique keys and strictly ascending class limits', () => {
    expect(new Set(INDICATORS.map((indicator) => indicator.key)).size).toBe(INDICATORS.length)
    for (const indicator of INDICATORS) {
      const sorted = [...indicator.breaks].sort((a, b) => a - b)
      expect(indicator.breaks, indicator.key).toEqual(sorted)
      expect(new Set(indicator.breaks).size, indicator.key).toBe(4)
    }
  })
  it('explain every indicator and name its sources', () => {
    for (const indicator of INDICATORS) {
      expect(indicator.description.length, indicator.key).toBeGreaterThan(30)
      expect(indicator.sources.length, indicator.key).toBeGreaterThan(0)
    }
  })
  it('recognise valid keys from the URL', () => {
    expect(isIndicatorKey('playgroundReach')).toBe(true)
    expect(isIndicatorKey('nonsense')).toBe(false)
  })
})

describe('playground reach', () => {
  const reach = getIndicator('playgroundReach')
  it('follows the chosen distance and variant', () => {
    expect(reach.value(area, DEFAULT_OPTIONS)).toBe(0.3)
    expect(reach.value(area, { reachVariant: 'straight', thresholdIndex: 0 })).toBe(0.2)
    expect(reach.value(area, { reachVariant: 'withOsm', thresholdIndex: 2 })).toBe(0.35)
  })
  it('is missing, not zero, when an area has too few children', () => {
    expect(reach.value({ ...area, reach: null }, DEFAULT_OPTIONS)).toBeNull()
  })
})

describe('classIndex', () => {
  const breaks = [0.2, 0.4, 0.6, 0.8]
  it('puts a value on a limit into the upper class', () => {
    expect(classIndex(0.2, breaks)).toBe(1)
    expect(classIndex(0.19, breaks)).toBe(0)
  })
  it('covers both ends', () => {
    expect(classIndex(0, breaks)).toBe(0)
    expect(classIndex(1, breaks)).toBe(4)
  })
})
