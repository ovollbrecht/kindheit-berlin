import { computed } from 'vue'
import {
  DEFAULT_OPTIONS,
  getIndicator,
  isIndicatorKey,
  type IndicatorKey,
  type IndicatorOptions,
} from '@/domain/indicators'
import type { ReachVariant } from '@/domain/types'
import { useQueryParam } from './useQueryParam'

const DEFAULT_INDICATOR: IndicatorKey = 'playgroundReach'
const DEFAULT_DISTANCE_M = '400'
const REACH_VARIANTS: ReachVariant[] = ['walking', 'straight', 'withOsm']

/**
 * The explorer's settings, all kept in the URL so that a view can be shared as a link:
 * ?ind=<indicator>&dist=<metres>&var=<variant>&area=<planning-area id>
 */
export function useExplorerState(thresholdsM: () => number[]) {
  const indicatorParam = useQueryParam('ind', DEFAULT_INDICATOR)
  const distanceParam = useQueryParam('dist', DEFAULT_DISTANCE_M)
  const variantParam = useQueryParam('var', DEFAULT_OPTIONS.reachVariant)
  const selectedArea = useQueryParam('area', '')

  const indicatorKey = computed<IndicatorKey>({
    get: () => (isIndicatorKey(indicatorParam.value) ? indicatorParam.value : DEFAULT_INDICATOR),
    set: (key) => (indicatorParam.value = key),
  })
  const indicator = computed(() => getIndicator(indicatorKey.value))

  const options = computed<IndicatorOptions>(() => {
    const index = thresholdsM().indexOf(Number(distanceParam.value))
    const variant = REACH_VARIANTS.find((candidate) => candidate === variantParam.value)
    return {
      thresholdIndex: index === -1 ? DEFAULT_OPTIONS.thresholdIndex : index,
      reachVariant: variant ?? DEFAULT_OPTIONS.reachVariant,
    }
  })

  return { indicatorKey, indicator, options, distanceParam, variantParam, selectedArea }
}
