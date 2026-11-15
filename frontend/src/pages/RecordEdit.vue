<script setup>
import TransactionGuide from '../components/TransactionGuide.vue'
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LoadingIndicator } from 'frappe-ui'

import { ApiError } from '../api'
import { currencyOf } from '../company'
import FormNotes from '../components/FormNotes.vue'
import RecordForm from '../components/RecordForm.vue'
import SectionTabs from '../components/SectionTabs.vue'
import StatePanel from '../components/StatePanel.vue'
import { fieldsOf, initialValues, isDirty, loadForm, missing, saveForm } from '../forms'
import { newRequestKey } from '../registration'
import { RECORDS, detailRoute, listRoute } from '../records'

// Create or edit one record through the server's form (decision G23). Every value is checked
// again by the server when it is saved; this page only collects them.
const route = useRoute()
const router = useRouter()
const key = route.meta.list
const config = RECORDS[key]

const form = ref(null)
const values = reactive({})
let start = {}
const loading = ref(false)
const loadError = ref(null)
const saving = ref(false)
const saveError = ref(null)
const note = ref('')
let requestKey = newRequestKey()
let request = 0

// A single record (Contract settings) has no list: this page is its form, named after its DocType.
const docName = computed(() => route.params.name || (config.single ? config.doctype : null))
const isNew = computed(() => !docName.value)
const title = computed(() => {
  if (config.single) return config.title
  return isNew.value ? `New ${config.noun ? config.noun.replace(/s$/, '') : config.title}` : `Edit ${route.params.name}`
})
const currency = computed(() => values.currency || form.value?.values?.currency || currencyOf(values.company || form.value?.values?.company))
const editableCount = computed(() => fieldsOf(form.value).filter((field) => field.editable).length)
const dirty = computed(() => form.value && isDirty(form.value, values, start))
const gaps = computed(() => (form.value ? missing(form.value, values) : []))

async function load() {
  const id = ++request
  loading.value = true
  loadError.value = null
  saveError.value = null
  try {
    const result = await loadForm(config.doctype, docName.value)
    if (id !== request) return
    form.value = result
    for (const name of Object.keys(values)) delete values[name]
    Object.assign(values, initialValues(result))
    start = JSON.parse(JSON.stringify(values))
    // A new record opened from another one (e.g. "New inspection report" on a job) is filled with
    // the values in the link, for fields the form lets this user set.
    if (result.is_new) {
      for (const field of fieldsOf(result)) {
        const given = route.query[field.fieldname]
        if (field.editable && field.fieldtype !== 'Table' && typeof given === 'string') values[field.fieldname] = given
      }
    }
    requestKey = newRequestKey()
  } catch (err) {
    if (id === request) loadError.value = err instanceof ApiError ? err : new ApiError('server', err.message || 'Something went wrong.')
  } finally {
    if (id === request) loading.value = false
  }
}

async function save() {
  saving.value = true
  saveError.value = null
  note.value = ''
  try {
    const result = await saveForm(form.value, values, start, requestKey)
    if (config.single) {
      await load()
      note.value = 'Saved.'
    } else {
      await router.push({ name: detailRoute(key), params: { name: result.name }, query: { saved: '1' } })
    }
  } catch (err) {
    saveError.value = err instanceof ApiError ? err : new ApiError('server', err.message || 'Something went wrong.')
  } finally {
    saving.value = false
  }
}

watch(
  () => route.params.name,
  () => {
    note.value = ''
    load()
  },
  { immediate: true },
)
onBeforeUnmount(() => ++request)
</script>

<template>
  <TransactionGuide />
  <section class="page">
    <nav class="bj-crumb" aria-label="Breadcrumb">
      <RouterLink class="bj-link" :to="{ name: listRoute(key) }">{{ config.title }}</RouterLink>
      <span aria-hidden="true">/</span>
      <span v-if="config.single">{{ config.title }}</span>
      <template v-else-if="!isNew">
        <RouterLink class="bj-link" :to="{ name: detailRoute(key), params: { name: route.params.name } }">{{ route.params.name }}</RouterLink>
        <span aria-hidden="true">/</span>
        <span>Edit</span>
      </template>
      <span v-else>New</span>
    </nav>
    <SectionTabs v-if="config.single" :section="config.section" :current="key" />

    <div v-if="loading && !form" class="page__card bj-loading" role="status"><LoadingIndicator /><span>Loading form…</span></div>

    <div v-else-if="loadError" class="page__card">
      <StatePanel
        v-if="loadError.kind === 'denied'"
        icon="lucide-lock"
        title="You cannot do this"
        :message="loadError.message || 'Your account does not have permission for this record.'"
      />
      <StatePanel v-else icon="lucide-triangle-alert" tone="blocked" title="The form could not be loaded" :message="loadError.message">
        <button type="button" class="bj-btn bj-btn--primary" @click="load">Try again</button>
      </StatePanel>
    </div>

    <form v-else-if="form" class="re" novalidate @submit.prevent="save">
      <header class="bj-head">
        <div>
          <h1 class="page__title">{{ title }}</h1>
          <p class="bj-sub">The server checks every value when you save.</p>
        </div>
        <div class="bj-toolbar">
          <template v-if="!config.single">
            <RouterLink v-if="!isNew" class="bj-btn" :to="{ name: detailRoute(key), params: { name: route.params.name } }">Cancel</RouterLink>
            <RouterLink v-else class="bj-btn" :to="{ name: listRoute(key) }">Cancel</RouterLink>
          </template>
          <button type="submit" class="bj-btn bj-btn--primary" :disabled="saving || !editableCount || (!isNew && !dirty)">
            <span v-if="saving" class="re__spin" aria-hidden="true" />{{ isNew ? 'Create' : 'Save' }}
          </button>
        </div>
      </header>

      <FormNotes :notes="form.notes" />
      <p v-if="note" class="bj-note re__ok" role="status"><span class="lucide-circle-check-big" aria-hidden="true" />{{ note }}</p>
      <p v-if="!editableCount" class="bj-note" role="status"><span class="lucide-lock" aria-hidden="true" />Nothing on this record can be changed by your account now.</p>
      <div v-if="saveError" class="re__error" role="alert">
        <span class="lucide-triangle-alert" aria-hidden="true" />
        <div>
          <p class="bj-strong">{{ saveError.type === 'StaleRecord' ? 'Someone else changed this record' : 'Not saved' }}</p>
          <p>{{ saveError.message }}</p>
          <button v-if="saveError.type === 'StaleRecord'" type="button" class="bj-btn" @click="load">Reload (your unsaved changes are lost)</button>
        </div>
      </div>
      <p v-if="gaps.length && (dirty || isNew)" class="re__hint" role="status">Still needed: {{ gaps.join(', ') }}.</p>

      <RecordForm :form="form" :values="values" :currency="currency" />
    </form>
  </section>
</template>

<style scoped>
.re__error {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin: 12px 0;
  padding: 12px 14px;
  color: var(--bj-state-blocked);
  background: var(--bj-card);
  border: 1px solid var(--bj-state-blocked);
  border-radius: 12px;
}
.re__error p {
  margin: 0 0 6px;
  color: var(--bj-ink);
}
.re__ok {
  margin: 12px 0;
}
.re__ok > span {
  color: var(--bj-state-completed);
}
.re__hint {
  margin: 12px 0 0;
  font-size: 13px;
  color: var(--bj-muted);
}
.re__spin {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: re-spin 0.8s linear infinite;
}
@keyframes re-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
