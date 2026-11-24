import { shallowRef, type ShallowRef } from 'vue'

export interface AsyncData<T> {
  data: ShallowRef<T | null>
  error: ShallowRef<string | null>
  loading: ShallowRef<boolean>
  reload: () => void
}

/** Runs a loader once and exposes its state for templates (loading, error, data). */
export function useAsyncData<T>(loader: () => Promise<T>): AsyncData<T> {
  const data = shallowRef<T | null>(null)
  const error = shallowRef<string | null>(null)
  const loading = shallowRef(true)

  function reload(): void {
    loading.value = true
    error.value = null
    loader()
      .then((result) => (data.value = result))
      .catch((reason: unknown) => {
        error.value =
          reason instanceof Error ? reason.message : 'Unbekannter Fehler beim Laden der Daten.'
      })
      .finally(() => (loading.value = false))
  }

  reload()
  return { data, error, loading, reload }
}
