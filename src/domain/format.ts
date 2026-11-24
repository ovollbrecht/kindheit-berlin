/** Number formatting for German readers. All user-visible numbers go through here. */

export type ValueFormat =
  | 'share' // 0..1 shown as percent
  | 'signedShare' // -1..1 shown as signed percent
  | 'percentValue' // already in percent
  | 'meters'
  | 'squareMeters'
  | 'count'
  | 'decimal'

const LOCALE = 'de-DE'
export const NO_VALUE = 'keine Angabe'

const number = (digits: number) =>
  new Intl.NumberFormat(LOCALE, { minimumFractionDigits: digits, maximumFractionDigits: digits })
const INTEGER = number(0)
const ONE_DECIMAL = number(1)
const SIGNED_INTEGER = new Intl.NumberFormat(LOCALE, {
  maximumFractionDigits: 0,
  signDisplay: 'exceptZero',
})

export function formatCount(value: number): string {
  return INTEGER.format(value)
}

/** Rounds to a readable magnitude for running text, e.g. 100921 -> "101.000". */
export function formatRounded(value: number, step = 100): string {
  return INTEGER.format(Math.round(value / step) * step)
}

export function formatValue(value: number | null | undefined, format: ValueFormat): string {
  if (value === null || value === undefined || Number.isNaN(value)) return NO_VALUE
  switch (format) {
    case 'share':
      return `${INTEGER.format(value * 100)} %`
    case 'signedShare':
      return `${SIGNED_INTEGER.format(value * 100)} %`
    case 'percentValue':
      return `${ONE_DECIMAL.format(value)} %`
    case 'meters':
      return `${INTEGER.format(value)} m`
    case 'squareMeters':
      return `${ONE_DECIMAL.format(value)} m²`
    case 'count':
      return INTEGER.format(value)
    case 'decimal':
      return ONE_DECIMAL.format(value)
  }
}
