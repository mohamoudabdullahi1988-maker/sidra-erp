<script setup>
import ListInsights from '../components/ListInsights.vue'
import { computed, onMounted, ref } from 'vue'
import { Button, LoadingIndicator } from 'frappe-ui'

import { ApiError, apiGet } from '../api'
import { boot, canCreate } from '../boot'
import SectionTabs from '../components/SectionTabs.vue'
import StatePanel from '../components/StatePanel.vue'

const DOCTYPE = 'Sidra Unit'
const PAGE = 50

// Columns in display order. A column the server has not listed as readable for this user is
// still drawn, and every cell in it says "Unavailable" — never zero, never blank.
const COLUMNS = [
  { field: 'unit_code', label: 'Unit' },
  { field: 'scheme', label: 'Scheme' },
  { field: 'unit_type', label: 'Type' },
  { field: 'status', label: 'Status' },
  { field: 'area_sqm', label: 'Area', align: 'right' },
  { field: 'cash_price', label: 'Cash price', align: 'right' },
]
const readable = new Set(boot.properties?.readable_fields ?? [])
// `company` is fetched only to pick the right currency for each row.
const fields = ['name', ...[...COLUMNS.map((c) => c.field), 'company'].filter((f) => readable.has(f))]

const rows = ref([])
const hasMore = ref(false)
const loading = ref(false) // a list request is in flight
const loadedOnce = ref(false)
const error = ref(null) // ApiError from the list request

const count = ref(null) // persisted record count from the server
const countFailed = ref(false)

const state = computed(() => {
  if (error.value && !rows.value.length) return error.value.kind === 'denied' ? 'unavailable' : 'error'
  if (!loadedOnce.value) return 'loading'
  return rows.value.length ? 'ready' : 'empty'
})

async function loadCount() {
  countFailed.value = false
  try {
    const body = await apiGet(`/api/v2/doctype/${encodeURIComponent(DOCTYPE)}/count`)
    if (typeof body.data !== 'number') throw new ApiError('server', 'Unexpected count')
    count.value = body.data
  } catch {
    count.value = null
    countFailed.value = true
  }
}

async function loadPage({ reset = false } = {}) {
  if (loading.value) return
  loading.value = true
  error.value = null
  try {
    const body = await apiGet(`/api/v2/document/${encodeURIComponent(DOCTYPE)}`, {
      fields,
      order_by: 'unit_code asc',
      start: reset ? 0 : rows.value.length,
      limit: PAGE,
    })
    if (!Array.isArray(body.data)) throw new ApiError('server', 'The server sent an unexpected answer.')
    rows.value = reset ? body.data : rows.value.concat(body.data)
    hasMore.value = Boolean(body.has_next_page)
    loadedOnce.value = true
  } catch (err) {
    error.value = err instanceof ApiError ? err : new ApiError('server', 'Something went wrong.')
    // On a failed first load or reload, show nothing rather than something stale.
    if (reset) rows.value = []
  } finally {
    loading.value = false
  }
}

function reload() {
  loadCount()
  loadPage({ reset: true })
}

onMounted(reload)

const numberFormat = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 })

/** Returns { text, kind } where kind is value | none | unavailable. */
function cell(row, field) {
  if (!readable.has(field) || !(field in row)) return { text: 'Unavailable', kind: 'unavailable' }
  const value = row[field]
  if (value === null || value === undefined || value === '') return { text: '—', kind: 'none' }
  if (field === 'area_sqm') {
    return typeof value === 'number' ? { text: `${numberFormat.format(value)} m²`, kind: 'value' } : { text: '—', kind: 'none' }
  }
  if (field === 'cash_price') {
    if (typeof value !== 'number') return { text: 'Unavailable', kind: 'unavailable' }
    const currency = boot.currencies?.[row.company]
    const amount = new Intl.NumberFormat(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value)
    return { text: currency ? `${currency} ${amount}` : amount, kind: 'value' }
  }
  return { text: String(value), kind: 'value' }
}

const STATUS_TONE = {
  Available: 'completed',
  Reserved: 'current',
  'Under Contract': 'current',
  Sold: 'muted',
  Blocked: 'blocked',
}
</script>

<template>
  <section class="page">
    <header class="head">
      <div>
        <h1 class="page__title">Properties</h1>
        <p class="head__count" aria-live="polite">
          <template v-if="count !== null">{{ count }} {{ count === 1 ? 'unit' : 'units' }} on record</template>
          <template v-else-if="countFailed">Unit count unavailable</template>
          <template v-else>&nbsp;</template>
        </p>
      </div>
      <div class="bj-toolbar">
        <RouterLink v-if="canCreate('units')" class="bj-btn bj-btn--primary" :to="{ name: 'units-new' }"><span class="lucide-plus" aria-hidden="true" />New unit</RouterLink>
        <Button :loading="loading" @click="reload">Refresh</Button>
      </div>
    </header>
    <ListInsights :rows="rows" :columns="COLUMNS.map(c=>({field:c.field,label:c.label}))" :busy="loading || !!error" />

    <SectionTabs section="properties" current="units" />

    <div class="page__card">
      <div v-if="state === 'loading'" class="loading" role="status">
        <LoadingIndicator class="loading__spin" />
        <span>Loading units…</span>
      </div>

      <StatePanel
        v-else-if="state === 'unavailable'"
        icon="lucide-lock"
        title="Units are unavailable to you"
        :message="error.message"
      />

      <StatePanel
        v-else-if="state === 'error'"
        icon="lucide-triangle-alert"
        tone="blocked"
        title="Units could not be loaded"
        :message="`${error.message.replace(/[.\s]+$/, '')}. Nothing is shown, because the saved records could not be read.`"
      >
        <Button variant="solid" @click="reload">Try again</Button>
      </StatePanel>

      <StatePanel
        v-else-if="state === 'empty'"
        icon="lucide-building-2"
        title="No units on record"
        message="No units have been saved yet, or none are visible to your account."
      />

      <template v-else>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th v-for="col in COLUMNS" :key="col.field" :class="{ 'is-right': col.align === 'right' }" scope="col">
                  {{ col.label }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.name">
                <td v-for="col in COLUMNS" :key="col.field" :class="{ 'is-right': col.align === 'right' }" :data-label="col.label">
                  <template v-for="c in [cell(row, col.field)]" :key="col.field">
                    <span v-if="c.kind === 'unavailable'" class="unavailable" title="Your account may not see this value">
                      <span class="lucide-eye-off" aria-hidden="true" />Unavailable
                    </span>
                    <span v-else-if="col.field === 'status' && c.kind === 'value'" class="status" :class="'status--' + (STATUS_TONE[c.text] || 'muted')">
                      <i aria-hidden="true" />{{ c.text }}
                    </span>
                    <RouterLink v-else-if="col.field === 'unit_code' && c.kind === 'value'" class="code bj-link" :to="{ name: 'units-detail', params: { name: row.name } }">{{ c.text }}</RouterLink>
                    <span v-else :class="{ none: c.kind === 'none', code: col.field === 'unit_code' }">{{ c.text }}</span>
                  </template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <footer class="foot">
          <span>
            Showing {{ rows.length }}<template v-if="count !== null"> of {{ count }}</template>
          </span>
          <span v-if="error" class="foot__error" role="alert">
            <span class="lucide-triangle-alert" aria-hidden="true" />More units could not be loaded: {{ error.message }}
          </span>
          <Button v-if="hasMore" :loading="loading" @click="loadPage()">Load more</Button>
        </footer>
      </template>
    </div>
  </section>
</template>

<style scoped>
.head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}
.head__count {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--bj-muted);
}
.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 56px 24px;
  font-size: 14px;
  color: var(--bj-muted);
}
.loading__spin {
  width: 18px;
  height: 18px;
}
.table-wrap {
  overflow-x: auto;
}
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.table th {
  text-align: left;
  font-weight: 500;
  font-size: 12px;
  color: var(--bj-muted);
  background: var(--bj-ground);
  padding: 10px 16px;
  border-bottom: 1px solid var(--bj-line);
  white-space: nowrap;
}
.table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--bj-line);
  white-space: nowrap;
}
.table tbody tr:last-child td {
  border-bottom: 0;
}
.table tbody tr:hover {
  background: var(--bj-terracotta-tint);
}
.is-right {
  text-align: right !important;
  font-variant-numeric: tabular-nums;
}
.code {
  font-weight: 500;
}
.none {
  color: var(--bj-state-pending);
}
.unavailable {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-style: italic;
  color: var(--bj-muted);
}
.unavailable > span {
  width: 14px;
  height: 14px;
}
.status {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}
.status i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--bj-state-pending);
}
.status--completed i {
  background: var(--bj-state-completed);
}
.status--current i {
  background: var(--bj-state-current);
}
.status--blocked i {
  background: var(--bj-state-blocked);
}
.status--muted i {
  background: var(--bj-muted);
}
.foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 16px;
  border-top: 1px solid var(--bj-line);
  font-size: 13px;
  color: var(--bj-muted);
}
.foot__error {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--bj-state-blocked);
}
.foot__error > span {
  width: 14px;
  height: 14px;
}

/* Phone: each unit becomes a labelled card instead of a wide table. */
@media (max-width: 640px) {
  .table thead {
    display: none;
  }
  .table,
  .table tbody,
  .table tr,
  .table td {
    display: block;
  }
  .table tr {
    padding: 10px 16px;
    border-bottom: 1px solid var(--bj-line);
  }
  .table tbody tr:last-child {
    border-bottom: 0;
  }
  .table td {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    padding: 3px 0;
    border: 0;
    white-space: normal;
    text-align: right !important;
  }
  .table td::before {
    content: attr(data-label);
    color: var(--bj-muted);
    font-size: 12px;
    text-align: left;
  }
}
</style>
