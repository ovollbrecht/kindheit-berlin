/**
 * Automatically derived remarks for a planning-area profile.
 *
 * Every remark comes from a fixed rule with a documented threshold and quotes the
 * numbers it is based on. Nothing here is generated freely; the rules are listed in
 * docs/METHODOLOGY.md and shown on the "Daten und Methodik" page.
 */
import { formatValue } from './format'
import { DEFAULT_THRESHOLD_INDEX } from './indicators'
import type { AreaValues, PlanningArea } from './types'

export interface Insight {
  id: string
  text: string
}

export interface InsightRule {
  id: string
  /** Shown on the methodology page. */
  rule: string
  evaluate: (area: PlanningArea, city: AreaValues) => string | null
}

/** Differences in shares that count as "clearly" above or below Berlin. */
export const CLEAR_SHARE_DIFFERENCE = 0.15
export const LARGE_DETOUR_GAP = 0.25
export const MAIN_ROAD_GAP = 0.15
export const REGISTER_GAP = 0.25
export const STRONG_GROWTH = 0.1
export const LOW_AREA_FACTOR = 0.5
export const HIGH_AREA_FACTOR = 1.5
export const LOW_DAYCARE_PLACES = 0.6

const share = (value: number) => formatValue(value, 'share')
const reachAt400 = (area: AreaValues, variant: 'walking' | 'straight' | 'withOsm') =>
  area.reach?.[variant][DEFAULT_THRESHOLD_INDEX] ?? null

export const INSIGHT_RULES: InsightRule[] = [
  {
    id: 'reach-vs-city',
    rule: `Anteil der Kinder mit öffentlichem Spielplatz in 400 m Fußweg weicht um mindestens ${CLEAR_SHARE_DIFFERENCE * 100} Prozentpunkte vom Berliner Wert ab.`,
    evaluate(area, city) {
      const local = reachAt400(area, 'walking')
      const reference = reachAt400(city, 'walking')
      if (
        local === null ||
        reference === null ||
        Math.abs(local - reference) < CLEAR_SHARE_DIFFERENCE
      )
        return null
      const direction = local > reference ? 'mehr' : 'weniger'
      return `Deutlich ${direction} Kinder als in Berlin insgesamt haben einen öffentlichen Spielplatz in 400 m Fußweg (${share(local)} gegenüber ${share(reference)}).`
    },
  },
  {
    id: 'detour-gap',
    rule: `Der Anteil nach Luftlinie liegt um mindestens ${LARGE_DETOUR_GAP * 100} Prozentpunkte über dem Anteil nach Fußweg (jeweils 400 m).`,
    evaluate(area) {
      const walking = reachAt400(area, 'walking')
      const straight = reachAt400(area, 'straight')
      if (walking === null || straight === null || straight - walking < LARGE_DETOUR_GAP)
        return null
      return `Auf der Karte liegt der Spielplatz für ${share(straight)} der Kinder in 400 m, zu Fuß nur für ${share(walking)}. Das Wegenetz erzwingt hier große Umwege.`
    },
  },
  {
    id: 'main-road',
    rule: `Ohne Querung einer Hauptstraße sinkt der Anteil mit Spielplatz in 400 m um mindestens ${MAIN_ROAD_GAP * 100} Prozentpunkte.`,
    evaluate(area) {
      const walking = reachAt400(area, 'walking')
      const withoutMainRoad = area.shareNoMainRoad400
      if (walking === null || withoutMainRoad === null || walking - withoutMainRoad < MAIN_ROAD_GAP)
        return null
      return `Viele Kinder erreichen ihren Spielplatz nur über eine Hauptstraße: Ohne Querung sind es ${share(withoutMainRoad)} statt ${share(walking)}.`
    },
  },
  {
    id: 'register-gap',
    rule: `Mit den zusätzlich in OpenStreetMap erfassten Spielplätzen steigt der Anteil um mindestens ${REGISTER_GAP * 100} Prozentpunkte.`,
    evaluate(area) {
      const official = reachAt400(area, 'walking')
      const withOsm = reachAt400(area, 'withOsm')
      if (official === null || withOsm === null || withOsm - official < REGISTER_GAP) return null
      return `Der amtliche Bestand zeigt hier nur einen Teil: Mit weiteren in OpenStreetMap erfassten Spielplätzen, etwa in Wohnanlagen, steigt der Anteil von ${share(official)} auf ${share(withOsm)}.`
    },
  },
  {
    id: 'play-area',
    rule: `Erreichbare Spielfläche je Kind liegt unter dem ${LOW_AREA_FACTOR}-Fachen oder über dem ${HIGH_AREA_FACTOR}-Fachen des Berliner Werts.`,
    evaluate(area, city) {
      const local = area.playM2PerChild
      const reference = city.playM2PerChild
      if (local === null || reference === null) return null
      const text = `${formatValue(local, 'squareMeters')} je Kind gegenüber ${formatValue(reference, 'squareMeters')} in Berlin`
      if (local < reference * LOW_AREA_FACTOR)
        return `Die erreichbare öffentliche Spielfläche ist klein: ${text}.`
      if (local > reference * HIGH_AREA_FACTOR)
        return `Die erreichbare öffentliche Spielfläche ist groß: ${text}.`
      return null
    },
  },
  {
    id: 'growth',
    rule: `Kinderzahl seit Ende 2022 um mindestens ${STRONG_GROWTH * 100} % gestiegen und Anteil mit Spielplatz in 400 m unter dem Berliner Wert.`,
    evaluate(area, city) {
      const local = reachAt400(area, 'walking')
      const reference = reachAt400(city, 'walking')
      if (area.childrenChange === null || local === null || reference === null) return null
      if (area.childrenChange < STRONG_GROWTH || local >= reference) return null
      return `Die Zahl der Kinder ist seit Ende 2022 um ${formatValue(area.childrenChange, 'signedShare')} gewachsen, während weniger Kinder als im Berliner Schnitt einen Spielplatz in 400 m haben.`
    },
  },
  {
    id: 'youth',
    rule: 'Weniger als die Hälfte der 10- bis 17-Jährigen hat eine Jugendfreizeiteinrichtung in 1000 m Fußweg.',
    evaluate(area) {
      if (area.youthShare1000 === null || area.youthShare1000 >= 0.5) return null
      return `Für die Mehrheit der 10- bis 17-Jährigen liegt die nächste Jugendfreizeiteinrichtung weiter als 1000 m entfernt (in 1000 m: ${share(area.youthShare1000)}).`
    },
  },
  {
    id: 'daycare',
    rule: `Weniger als ${LOW_DAYCARE_PLACES} genehmigte Kita-Plätze je Kind unter 6 Jahren in 1000 m Fußweg.`,
    evaluate(area, city) {
      const local = area.daycarePlacesPerChild
      if (local === null || city.daycarePlacesPerChild === null || local >= LOW_DAYCARE_PLACES)
        return null
      return `Auf ein Kind unter 6 Jahren kommen im Umkreis rechnerisch ${formatValue(local, 'decimal')} genehmigte Kita-Plätze (Berlin: ${formatValue(city.daycarePlacesPerChild, 'decimal')}).`
    },
  },
]

export function deriveInsights(area: PlanningArea, city: AreaValues): Insight[] {
  if (!area.enoughChildren) return []
  return INSIGHT_RULES.flatMap((rule) => {
    const text = rule.evaluate(area, city)
    return text ? [{ id: rule.id, text }] : []
  })
}
