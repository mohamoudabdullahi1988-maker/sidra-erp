import { computed, ref } from 'vue'

import { ApiError, apiGet } from './api'

/**
 * A read-only, paged list of saved records through Frappe's permission-checked REST API.
 * `filters` and `orFilters` are functions so a page can change them and call reload(). After a
 * failed first read nothing is shown; rows are never invented and a count is only what the
 * server counted (none while a search is applied, because the count endpoint cannot match it).
 */
export function useList(doctype, { fields, filters = () => undefined, orFilters = () => undefined, orderBy, pageSize = 50 }) {
  const rows = ref([])
  const hasMore = ref(false)
  const loading = ref(false)
  const loadedOnce = ref(false)
  const error = ref(null)
  const count = ref(null)
  let request = 0

  const state = computed(() => {
    if (error.value && !rows.value.length) return error.value.kind === 'denied' ? 'unavailable' : 'error'
    if (!loadedOnce.value) return 'loading'
    return rows.value.length ? 'ready' : 'empty'
  })

  async function loadCount(id) {
    count.value = null
    if (orFilters()) return
    try {
      const body = await apiGet(`/api/v2/doctype/${encodeURIComponent(doctype)}/count`, { filters: filters() })
      if (id === request) count.value = typeof body.data === 'number' ? body.data : null
    } catch {
      if (id === request) count.value = null // unknown, shown as no count rather than zero
    }
  }

  async function loadPage(reset) {
    const id = reset ? ++request : request
    loading.value = true
    error.value = null
    if (reset) loadCount(id)
    try {
      const body = await apiGet(`/api/resource/${encodeURIComponent(doctype)}`, {
        fields,
        filters: filters(),
        or_filters: orFilters(),
        order_by: typeof orderBy === 'function' ? orderBy() : orderBy,
        limit_start: reset ? 0 : rows.value.length,
        limit_page_length: pageSize + 1, // one extra row tells whether there is a next page
      })
      if (id !== request) return
      if (!Array.isArray(body.data)) throw new ApiError('server', 'The server sent an unexpected answer.')
      const page = body.data.slice(0, pageSize)
      rows.value = reset ? page : rows.value.concat(page)
      hasMore.value = body.data.length > pageSize
      loadedOnce.value = true
    } catch (err) {
      if (id !== request) return
      error.value = err instanceof ApiError ? err : new ApiError('server', 'Something went wrong.')
      if (reset) rows.value = []
    } finally {
      if (id === request) loading.value = false
    }
  }

  return { rows, hasMore, loading, error, count, state, reload: () => loadPage(true), loadMore: () => loadPage(false) }
}
