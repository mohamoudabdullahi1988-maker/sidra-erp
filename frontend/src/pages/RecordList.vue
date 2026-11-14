<script setup>
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
const fields = [...new Set(['name', ...config.list.map((c) => c.field), ...(config.extra ?? [])])]

const list = useList(config.doctype, {
  fields,
  filters: () => (config.company && company.value ? { company: company.value } : undefined),
  orFilters: () => (applied.value ? config.search.map((field) => [field, 'like', `%${applied.value}%`]) : undefined),
  orderBy: config.orderBy,
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
</script>

<template>
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

    <SectionTabs :section="config.section" :current="key" />

    <form class="bj-toolbar search" role="search" @submit.prevent="search">
      <label class="bj-label" :for="`search-${key}`">Search by {{ config.searchLabel.toLowerCase() }}</label>
      <input :id="`search-${key}`" v-model="query" class="bj-input" type="search" :placeholder="config.searchLabel" />
      <button type="submit" class="bj-btn" :disabled="loading">Search</button>
      <button v-if="applied" type="button" class="bj-btn" :disabled="loading" @click="clear">Clear</button>
      <button type="button" class="bj-btn" :disabled="loading" @click="reload">Refresh</button>
    </form>

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
                <th v-for="column in config.list" :key="column.field" scope="col" :class="{ 'bj-right': right(column) }">{{ column.label }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.name">
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
