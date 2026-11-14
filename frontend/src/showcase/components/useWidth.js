import { onBeforeUnmount, onMounted, ref } from 'vue'

/** The pixel width of an element, kept up to date, so charts draw at real size (readable text). */
export function useWidth(fallback = 600) {
  const el = ref(null)
  const width = ref(fallback)
  let observer
  onMounted(() => {
    if (!el.value) return
    width.value = el.value.clientWidth || fallback
    if (typeof ResizeObserver !== 'undefined') {
      observer = new ResizeObserver(([entry]) => (width.value = Math.max(240, Math.round(entry.contentRect.width))))
      observer.observe(el.value)
    }
  })
  onBeforeUnmount(() => observer?.disconnect())
  return { el, width }
}
