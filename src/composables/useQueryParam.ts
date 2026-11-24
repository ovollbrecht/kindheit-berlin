import { computed, type WritableComputedRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'

/**
 * Two-way binding between a value and a URL query parameter, so that every view state
 * can be shared as a link. The parameter is omitted while the value equals the default.
 */
export function useQueryParam(name: string, defaultValue: string): WritableComputedRef<string> {
  const route = useRoute()
  const router = useRouter()
  return computed({
    get: () => {
      const value = route.query[name]
      return typeof value === 'string' && value !== '' ? value : defaultValue
    },
    set: (value) => {
      const query = { ...route.query }
      if (value === defaultValue) delete query[name]
      else query[name] = value
      void router.replace({ query })
    },
  })
}
