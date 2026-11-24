import { onBeforeUnmount, onMounted, ref, type Ref } from 'vue'

/** Current pixel width of an element, so charts can draw at real size instead of scaling text. */
export function useElementWidth(element: Ref<HTMLElement | null>, initialWidth = 640): Ref<number> {
  const width = ref(initialWidth)
  let observer: ResizeObserver | null = null

  onMounted(() => {
    if (!element.value) return
    width.value = element.value.clientWidth || initialWidth
    observer = new ResizeObserver((entries) => {
      const measured = entries[0]?.contentRect.width
      if (measured) width.value = measured
    })
    observer.observe(element.value)
  })
  onBeforeUnmount(() => observer?.disconnect())

  return width
}
