import { describe, expect, it } from 'vitest'
import { formatRounded, formatValue, NO_VALUE } from '@/domain/format'

// German formatting uses a non-breaking space before the percent sign in some engines; compare loosely.
const plain = (text: string) => text.replace(/ /g, ' ')

describe('formatValue', () => {
  it('shows shares as whole percent', () => {
    expect(plain(formatValue(0.7023, 'share'))).toBe('70 %')
  })
  it('keeps the sign for changes, also for growth', () => {
    expect(plain(formatValue(0.054, 'signedShare'))).toBe('+5 %')
    expect(plain(formatValue(-0.05, 'signedShare'))).toBe('-5 %')
  })
  it('uses a decimal comma and thousands separator', () => {
    expect(formatValue(3.76, 'squareMeters')).toBe('3,8 m²')
    expect(formatValue(1119, 'meters')).toBe('1.119 m')
  })
  it('distinguishes a missing value from zero', () => {
    expect(formatValue(null, 'share')).toBe(NO_VALUE)
    expect(plain(formatValue(0, 'share'))).toBe('0 %')
  })
})

describe('formatRounded', () => {
  it('rounds to a readable magnitude for running text', () => {
    expect(formatRounded(100921, 1000)).toBe('101.000')
    expect(formatRounded(6604)).toBe('6.600')
  })
})
