/** Map and chart colours. Categorical slots and the sequential ramp were checked for
 *  colour-vision-deficiency separation (see docs/ARCHITECTURE.md). */

export const SEQUENTIAL = ['#cde2fb', '#9ec5f4', '#5598e7', '#256abf', '#0d366b'] as const
/** Decrease (warm) – neutral – increase (cool). */
export const DIVERGING = ['#c2491a', '#f3b294', '#e9e7e0', '#9ec5f4', '#256abf'] as const
export const NO_DATA_COLOR = '#e4e1d8'

export const SERIES = {
  blue: '#2a78d6',
  orange: '#eb6834',
  aqua: '#1baf7a',
} as const

export function classColors(scale: 'sequential' | 'diverging'): readonly string[] {
  return scale === 'diverging' ? DIVERGING : SEQUENTIAL
}
