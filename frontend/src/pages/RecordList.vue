<script setup>
import BulkActions from '../components/BulkActions.vue'
import TransactionGuide from '../components/TransactionGuide.vue'
import ListInsights from '../components/ListInsights.vue'
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { canCreate } from '../boot'
import { company, currencyOf } from '../company'
import CompanyPicker from '../components/CompanyPicker.vue'
import FieldValue from '../components/FieldValue.vue'
import ListStates from '../components/ListStates.vue'
import SectionTabs from '../components/SectionTabs.vue'
import { deskNewLink } from '../format'
import { useList } from '../list'
import { RECORDS } from '../records'

// One list of saved records, described in records.js. Lists the form engine serves (G23) create
// records in Berjaya; the others still open Desk's form.
const route = useRoute()
const key = route.meta.list
const config = RECORDS[key]

const query = ref('')
const applied = ref('')
const filterField = ref(''), filterValue = ref(''), filterOperator = ref('=')
const sortField = ref('modified'), sortDirection = ref('desc')
const appliedFilter = ref(null)
const validColumns = new Set(config.list.map(c => c.field))
const filters = () => ({ ...(config.fixedFilters ?? {}), ...(config.company && company.value ? { company: company.value } : {}), ...(appliedFilter.value ? { [appliedFilter.value.field]: [appliedFilter.value.operator, appliedFilter.value.value] } : {}) })
function applyTools() {
  appliedFilter.value = validColumns.has(filterField.value) && !Object.hasOwn(config.fixedFilters ?? {}, filterField.value) && filterValue.value !== '' ? { field: filterField.value, operator: filterOperator.value, value: filterValue.value } : null
  reload()
}
function saveView() {
  try { localStorage.setItem(`berjaya-view-${key}`, JSON.stringify({ filterField: filterField.value, filterValue: filterValue.value, filterOperator: filterOperator.value, sortField: sortField.value, sortDirection: sortDirection.value })) } catch {}
}
function restoreView() {
  try {
    const v = JSON.parse(localStorage.getItem(`berjaya-view-${key}`) || '{}')
    filterField.value = validColumns.has(v.filterField) ? v.filterField : ''
    filterValue.value = typeof v.filterValue === 'string' ? v.filterValue : ''
    filterOperator.value = ['=', '!=', 'like', '>', '<', '>=', '<='].includes(v.filterOperator) ? v.filterOperator : '='
    sortField.value = validColumns.has(v.sortField) ? v.sortField : 'modified'
    sortDirection.value = v.sortDirection === 'asc' ? 'asc' : 'desc'
    applyTools()
  } catch {}
}
const fields = [...new Set(['name', ...config.list.map((c) => c.field), ...(config.extra ?? [])])]

const list = useList(config.doctype, {
  fields,
  // A list may have fixed conditions (e.g. design jobs are jobs with a design or inspection service).
  filters,
  orFilters: () => (applied.value ? config.search.map((field) => [field, 'like', `%${applied.value}%`]) : undefined),
  orderBy: () => `${validColumns.has(sortField.value) ? sortField.value : 'modified'} ${sortDirection.value === 'asc' ? 'asc' : 'desc'}`,
})
const { rows, hasMore, loading, error, count, state, reload, loadMore } = list

const currency = (row) => row.currency || currencyOf(row.company) || currencyOf(company.value)
const newLink = computed(() => (canCreate(key) ? deskNewLink(config.doctype) : null))
const right = (column) => ['money', 'int', 'number', 'percent'].includes(column.type)

function search() {
  applied.value = query.value.trim()
  reload()
}
function clear() {
  query.value = ''
  search()
}

watch(company, reload, { immediate: true })
const selected = ref([])
</script>

<template>
  <TransactionGuide />
  <section class="page">
    <header class="bj-head">
      <div>
        <h1 class="page__title">{{ config.title }}</h1>
        <p class="bj-sub" aria-live="polite">
          <template v-if="count !== null">{{ count }} on record</template>
          <template v-else-if="applied">Matching “{{ applied }}”</template>
          <template v-else>&nbsp;</template>
        </p>
      </div>
      <div class="bj-toolbar">
        <CompanyPicker v-if="config.company" />
        <RouterLink v-if="newLink && config.form" class="bj-btn bj-btn--primary" :to="{ name: `${key}-new` }">
          <span class="lucide-plus" aria-hidden="true" />New
        </RouterLink>
        <a v-else-if="newLink" class="bj-btn bj-btn--primary" :href="newLink">
          <span class="lucide-plus" aria-hidden="true" />New in Desk
        </a>
      </div>
    </header>
    <ListInsights :rows="rows" :columns="config.list" :group="config.list.find(c => c.field === 'status' || c.field === 'docstatus')?.field || config.list.find(c => c.type === 'select')?.field || config.list[1]?.field || 'name'" :busy="loading || !!error" />
    <BulkActions v-model="selected" :doctype="config.doctype" :rows="rows" :loading="loading" @changed="reload" />

    <SectionTabs :section="config.section" :current="key" />

    <form class="bj-toolbar search" role="search" @submit.prevent="search">
      <label class="bj-label" :for="`search-${key}`">Search by {{ config.searchLabel.toLowerCase() }}</label>
      <input :id="`search-${key}`" v-model="query" class="bj-input" type="search" :placeholder="config.searchLabel" />
      <button type="submit" class="bj-btn" :disabled="loading">Search</button>
      <button v-if="applied" type="button" class="bj-btn" :disabled="loading" @click="clear">Clear</button>
      <button type="button" class="bj-btn" :disabled="loading" @click="reload">Refresh</button>
    </form>

    <details class="page__card bj-card" style="margin-bottom:16px"><summary>Filter, sort and saved view</summary>
      <form class="bj-toolbar" style="margin-top:12px" @submit.prevent="applyTools">
        <label>Field<select v-model="filterField" class="bj-select"><option value="">No extra filter</option><option v-for="c in config.list" :key="c.field" :value="c.field">{{ c.label }}</option></select></label>
        <label>Operator<select v-model="filterOperator" class="bj-select"><option v-for="op in ['=', '!=', 'like', '>', '<', '>=', '<=']" :key="op">{{ op }}</option></select></label>
        <label>Value<input v-model="filterValue" class="bj-input" placeholder="Use % as wildcard for like" /></label>
        <label>Sort<select v-model="sortField" class="bj-select"><option value="modified">Updated</option><option v-for="c in config.list" :key="c.field" :value="c.field">{{ c.label }}</option></select></label>
        <label>Order<select v-model="sortDirection" class="bj-select"><option value="desc">Descending</option><option value="asc">Ascending</option></select></label>
        <button class="bj-btn">Apply to full list</button><button type="button" class="bj-btn" @click="saveView">Save view on this browser</button><button type="button" class="bj-btn" @click="restoreView">Restore saved view</button>
      </form>
    </details>
    <div class="page__card">
      <ListStates
        :state="state"
        :error="error"
        :noun="config.noun"
        :icon="config.icon"
        :empty-message="applied ? `Nothing saved matches “${applied}”.` : ''"
        @retry="reload"
      >
        <div class="bj-table-wrap" :aria-busy="loading">
          <table class="bj-table bj-table--stack">
            <thead>
              <tr>
                <th scope="col">Select</th>
                <th v-for="column in config.list" :key="column.field" scope="col" :class="{ 'bj-right': right(column) }">{{ column.label }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.name">
                <td data-label="Select"><input v-model="selected" type="checkbox" :value="row.name" :aria-label="`Select ${row.name}`" :disabled="loading" /></td>
                <td v-for="column in config.list" :key="column.field" :data-label="column.label" :class="{ 'bj-right': right(column) }">
                  <FieldValue
                    :value="row[column.field]"
                    :present="column.field in row"
                    :type="column.type"
                    :to="column.type === 'id' ? key : column.to"
                    :name="row.name"
                    :currency="currency(row)"
                    :tones="config.status"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <footer class="bj-foot">
          <span>Showing {{ rows.length }}<template v-if="count !== null"> of {{ count }}</template></span>
          <span v-if="error" role="alert">More could not be loaded: {{ error.message }}</span>
          <button v-if="hasMore" type="button" class="bj-btn" :disabled="loading" @click="loadMore">Load more</button>
        </footer>
      </ListStates>
    </div>
  </section>
</template>

<style scoped>
.search {
  margin-bottom: 12px;
}
</style>
