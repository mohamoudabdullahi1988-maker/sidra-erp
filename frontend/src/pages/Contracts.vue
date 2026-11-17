<script setup>
import BulkActions from '../components/BulkActions.vue'
import TransactionGuide from '../components/TransactionGuide.vue'
import ListInsights from '../components/ListInsights.vue'
import { computed, onMounted, ref } from 'vue'
import { LoadingIndicator } from 'frappe-ui'

import { ApiError, apiGet } from '../api'
import SectionTabs from '../components/SectionTabs.vue'
import { textValue } from '../format'
import StatePanel from '../components/StatePanel.vue'
import { canCreate } from '../boot'
import { CONTRACT, sourceText, statusText, statusTone } from '../contracts'

const PAGE = 25
const newLink = canCreate('contracts')
const LIST_FIELDS = ['name', 'customer', 'docstatus', 'source', 'contract_type', 'external_reference']

const rows = ref([])
const query = ref('')
const applied = ref('') // the search the rows on screen belong to
const page = ref(0)
const more = ref(false)
const loading = ref(false)
const loadedOnce = ref(false)
const error = ref(null)
let request = 0

const state = computed(() => {
  if (error.value) return error.value.kind === 'denied' ? 'unavailable' : 'error'
  if (!loadedOnce.value) return 'loading'
  return rows.value.length ? 'ready' : 'empty'
})

async function load(next = 0) {
  const id = ++request
  const term = query.value.trim()
  loading.value = true
  error.value = null
  try {
    const like = `%${term}%`
    const list = await apiGet(CONTRACT, {
      fields: LIST_FIELDS,
      or_filters: term
        ? [
            ['name', 'like', like],
            ['external_reference', 'like', like],
            ['customer', 'like', like],
          ]
        : undefined,
      limit_start: next * PAGE,
      limit_page_length: PAGE + 1,
      order_by: 'modified desc',
    })
    if (!Array.isArray(list.data)) throw new ApiError('server', 'The server sent an unexpected answer.')
    const shown = list.data.slice(0, PAGE)
    // Units are rows of the contract, so each permitted contract is read for its own units.
    // A contract that cannot be read shows "Unavailable" for its property, not a blank.
    const documents = await Promise.allSettled(shown.map((row) => apiGet(`${CONTRACT}/${encodeURIComponent(row.name)}`)))
    if (id !== request) return
    rows.value = shown.map((row, index) => {
      const units = documents[index].status === 'fulfilled' ? documents[index].value?.data?.units : null
      return { ...row, units: Array.isArray(units) ? units.map((unit) => unit.unit).filter(Boolean) : null }
    })
    page.value = next
    more.value = list.data.length > PAGE
    applied.value = term
    loadedOnce.value = true
  } catch (err) {
    if (id !== request) return
    error.value = err instanceof ApiError ? err : new ApiError('server', 'Something went wrong.')
    rows.value = [] // nothing stale is left on screen after a failed read
  } finally {
    if (id === request) loading.value = false
  }
}

function clear() {
  query.value = ''
  load()
}

onMounted(() => load())
const selected = ref([])
</script>

<template>
  <TransactionGuide />
  <section class="page">
    <header class="bj-head">
      <div>
        <h1 class="page__title">Contracts</h1>
        <p class="bj-sub">Saved sale contracts, newest change first</p>
      </div>
      <form class="bj-toolbar" role="search" @submit.prevent="load()">
        <label class="bj-label" for="contract-search">Search by reference or customer</label>
        <input id="contract-search" v-model="query" class="bj-input" type="search" placeholder="Reference or customer" />
        <button type="submit" class="bj-btn" :disabled="loading">Search</button>
        <button v-if="applied" type="button" class="bj-btn" :disabled="loading" @click="clear">Clear</button>
        <RouterLink v-if="newLink" class="bj-btn bj-btn--primary" :to="{ name: 'contract-new' }"><span class="lucide-plus" aria-hidden="true" />Register external contract</RouterLink>
        <RouterLink v-if="newLink" class="bj-btn" :to="{ name: 'contracts-new' }"><span class="lucide-plus" aria-hidden="true" />New contract</RouterLink>
      </form>
    </header>
    <ListInsights :rows="rows" group="source" :columns="[{field:'name',label:'Contract'},{field:'customer',label:'Customer'},{field:'source',label:'Source'},{field:'contract_type',label:'Type'}]" :busy="loading || !!error" />
    <BulkActions v-model="selected" :doctype="'Sidra Sale Contract'" :rows="rows" :loading="loading" @changed="load(0)" />

    <SectionTabs section="contracts" current="contracts" />

    <div class="page__card">
      <div v-if="state === 'loading'" class="bj-loading" role="status"><LoadingIndicator /><span>Loading contracts…</span></div>

      <StatePanel v-else-if="state === 'unavailable'" icon="lucide-lock" title="Contracts are unavailable to you" :message="error.message" />

      <StatePanel
        v-else-if="state === 'error'"
        icon="lucide-triangle-alert"
        tone="blocked"
        title="Contracts could not be loaded"
        :message="`${error.message.replace(/[.\s]+$/, '')}. Nothing is shown, because the saved records could not be read.`"
      >
        <button type="button" class="bj-btn bj-btn--primary" @click="load(page)">Try again</button>
      </StatePanel>

      <StatePanel
        v-else-if="state === 'empty'"
        icon="lucide-file-text"
        :title="applied ? 'No contract matches' : 'No contracts on record'"
        :message="applied ? `Nothing saved matches “${applied}”.` : 'No contracts have been saved yet, or none are visible to your account.'"
      />

      <template v-else>
        <div class="bj-table-wrap" :aria-busy="loading">
          <table class="bj-table bj-table--stack">
            <thead>
              <tr>
                <th scope="col">Select</th>
                <th scope="col">Reference</th>
                <th scope="col">Customer</th>
                <th scope="col">Property</th>
                <th scope="col">Source</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.name">
                <td data-label="Select"><input v-model="selected" type="checkbox" :value="row.name" :aria-label="`Select ${row.name}`" :disabled="loading" /></td>
                <td data-label="Reference">
                  <span>
                    <RouterLink class="bj-link" :to="{ name: 'contract-detail', params: { name: row.name } }">{{ row.name }}</RouterLink>
                    <span v-if="row.external_reference" class="bj-small">{{ row.external_reference }}</span>
                  </span>
                </td>
                <td data-label="Customer">{{ textValue(row.customer) }}</td>
                <td data-label="Property">
                  <span v-if="row.units === null" class="bj-unavailable">Unavailable</span>
                  <span v-else-if="!row.units.length" class="bj-muted">None recorded</span>
                  <span v-else>{{ row.units.join(', ') }}</span>
                </td>
                <td data-label="Source">{{ sourceText(row) }}</td>
                <td data-label="Status">
                  <span class="bj-chip" :class="'bj-chip--' + statusTone(row.docstatus)">{{ statusText(row.docstatus) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <footer class="bj-foot">
          <span>Page {{ page + 1 }} · {{ rows.length }} {{ rows.length === 1 ? 'contract' : 'contracts' }} shown</span>
          <span class="bj-toolbar">
            <button type="button" class="bj-btn" :disabled="loading || !page" @click="load(page - 1)">Previous</button>
            <button type="button" class="bj-btn" :disabled="loading || !more" @click="load(page + 1)">Next</button>
          </span>
        </footer>
      </template>
    </div>
  </section>
</template>
