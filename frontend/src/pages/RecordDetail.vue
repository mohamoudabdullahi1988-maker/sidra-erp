<script setup>
import LocationPanel from '../components/LocationPanel.vue'
import RecordExtras from '../components/RecordExtras.vue'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { LoadingIndicator } from 'frappe-ui'

import { ApiError, apiGet } from '../api'
import { canRead } from '../boot'
import { currencyOf } from '../company'
import FieldValue from '../components/FieldValue.vue'
import RecordActions from '../components/RecordActions.vue'
import RelatedList from '../components/RelatedList.vue'
import StatePanel from '../components/StatePanel.vue'
import { deskLink } from '../format'
import { RECORDS, listRoute } from '../records'

// One saved record, laid out as described in records.js. For a list the form engine serves
// (G23), the server's form adds Edit, Submit, Cancel, Delete and the record's own actions.
const route = useRoute()
const key = route.meta.list
const config = RECORDS[key]
const detail = config.detail

const doc = ref(null)
const loading = ref(false)
const error = ref(null)
let request = 0

const currency = computed(() => doc.value?.currency || currencyOf(doc.value?.company))
const title = computed(() => (detail.title && doc.value?.[detail.title]) || doc.value?.name)
const desk = computed(() => (config.form ? null : deskLink(config.doctype, doc.value?.name)))
const saved = computed(() => Boolean(route.query.saved))
// Frappe's REST answer leaves out empty fields, so a missing field is not by itself
// "not permitted". For a list the form engine serves, its values list every field this user may
// read (field-level permissions applied), empty ones included.
const formValues = ref(null)
const readable = (field) => field in (doc.value ?? {}) || Boolean(formValues.value && field in formValues.value)
const related = computed(() => (detail.related ?? []).filter((item) => canRead(item.list)))
const right = (column) => ['money', 'int', 'number', 'percent'].includes(column.type)

async function load() {
  const id = ++request
  // Reloading the same record keeps it on screen (and any message an action left), so the page
  // does not flash; another record starts from blank.
  if (doc.value?.name !== route.params.name) doc.value = null
  error.value = null
  loading.value = true
  try {
    const result = await apiGet(`/api/resource/${encodeURIComponent(config.doctype)}/${encodeURIComponent(route.params.name)}`)
    if (!result.data?.name) throw new ApiError('server', 'The server sent an unexpected answer.')
    if (id === request) doc.value = result.data
  } catch (err) {
    if (id === request) error.value = err instanceof ApiError ? err : new ApiError('server', 'Something went wrong.')
  } finally {
    if (id === request) loading.value = false
  }
}

watch(() => route.params.name, load, { immediate: true })
onBeforeUnmount(() => ++request)
</script>

<template>
  <section class="page">
    <nav class="bj-crumb" aria-label="Breadcrumb">
      <RouterLink class="bj-link" :to="{ name: listRoute(key) }">{{ config.title }}</RouterLink>
      <span aria-hidden="true">/</span>
      <span>{{ route.params.name }}</span>
    </nav>

    <div v-if="loading && !doc" class="page__card bj-loading" role="status"><LoadingIndicator /><span>Loading…</span></div>

    <div v-else-if="error && !doc" class="page__card">
      <StatePanel
        v-if="error.kind === 'denied'"
        icon="lucide-lock"
        title="This record is unavailable to you"
        message="Your account does not have permission to read this record."
      />
      <StatePanel
        v-else
        icon="lucide-triangle-alert"
        tone="blocked"
        title="The record could not be loaded"
        :message="`${error.message.replace(/[.\s]+$/, '')}. Nothing is shown, because the saved record could not be read.`"
      >
        <button type="button" class="bj-btn bj-btn--primary" @click="load">Try again</button>
      </StatePanel>
    </div>

    <template v-else-if="doc">
      <header class="bj-head">
        <div>
          <h1 class="page__title">{{ title }}</h1>
          <p class="bj-sub">
            <template v-if="title !== doc.name">{{ doc.name }}</template>
            <template v-if="detail.subtitle && doc[detail.subtitle]"><template v-if="title !== doc.name"> · </template>{{ doc[detail.subtitle] }}</template>
          </p>
        </div>
        <div class="bj-toolbar">
          <span v-if="detail.status" class="bj-pill">
            <FieldValue :value="doc[detail.status]" :present="detail.status in doc" type="status" :tones="config.status" />
          </span>
          <span v-if="'docstatus' in doc && doc.docstatus !== 0" class="bj-pill"><FieldValue :value="doc.docstatus" type="docstatus" /></span>
          <a v-if="desk" class="bj-btn" :href="desk"><span class="lucide-external-link" aria-hidden="true" />Open in Desk</a>
        </div>
      </header>

      <p v-if="saved" class="bj-note rd__ok" role="status"><span class="lucide-circle-check-big" aria-hidden="true" />Saved.</p>
      <RecordActions
        v-if="config.form"
        :doctype="config.doctype"
        :name="doc.name"
        :edit-route="{ name: `${key}-edit`, params: { name: doc.name } }"
        :list-route="{ name: listRoute(key) }"
        @changed="load"
        @form="(form) => (formValues = form?.values ?? null)"
      />

      <div class="bj-grid">
        <article v-for="group in detail.groups" :key="group.title" class="bj-card">
          <h2>{{ group.title }}</h2>
          <dl class="fields">
            <div v-for="field in group.fields" :key="field.field">
              <dt>{{ field.label }}</dt>
              <dd>
                <FieldValue
                  :value="doc[field.field]"
                  :present="readable(field.field)"
                  :type="field.type"
                  :to="field.to"
                  :currency="currency"
                  :tones="config.status"
                />
              </dd>
            </div>
          </dl>
        </article>
      </div>

      <section v-for="table in detail.tables ?? []" :key="table.field" class="bj-section">
        <h2>{{ table.title }}</h2>
        <div class="page__card">
          <StatePanel v-if="!Array.isArray(doc[table.field])" icon="lucide-eye-off" :title="`${table.title} unavailable`" message="Your account may not see these rows." />
          <StatePanel v-else-if="!doc[table.field].length" icon="lucide-list" :title="`No ${table.title.toLowerCase()} recorded`" />
          <div v-else class="bj-table-wrap">
            <table class="bj-table bj-table--stack">
              <thead>
                <tr>
                  <th v-for="column in table.columns" :key="column.field" scope="col" :class="{ 'bj-right': right(column) }">{{ column.label }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in doc[table.field]" :key="row.name">
                  <td v-for="column in table.columns" :key="column.field" :data-label="column.label" :class="{ 'bj-right': right(column) }">
                    <FieldValue :value="row[column.field]" :present="column.field in row" :type="column.type" :to="column.to" :currency="currency" />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <RelatedList v-for="item in related" :key="item.list" :item="item" :value="doc.name" />
      <LocationPanel v-if="config.doctype === 'Sidra Unit'" :doctype="config.doctype" :name="doc.name" />
      <RecordExtras v-if="config.form && !config.single" :doctype="config.doctype" :name="doc.name" :reload-key="doc.modified" />
    </template>
  </section>
</template>

<style scoped>
.rd__ok {
  margin: 12px 0;
}
.rd__ok > span {
  color: var(--bj-state-completed);
}
.fields {
  display: grid;
  gap: 10px;
  margin: 0;
}
.fields > div {
  display: grid;
  grid-template-columns: minmax(110px, 40%) 1fr;
  gap: 12px;
  font-size: 14px;
}
.fields dt {
  color: var(--bj-muted);
}
.fields dd {
  margin: 0;
  overflow-wrap: anywhere;
}
</style>
