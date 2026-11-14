<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { LoadingIndicator } from 'frappe-ui'

import { ApiError, apiGet } from '../api'
import RecordActions from '../components/RecordActions.vue'
import StatePanel from '../components/StatePanel.vue'
import { canRead } from '../boot'
import { JOB_DOCTYPE, jobTone, stageTone } from '../construction'
import { dateText, dateTimeText, isAmount, money, percentText, textValue } from '../format'

const route = useRoute()
const doc = ref(null)
const loading = ref(false)
const error = ref(null)
let request = 0

const cash = (field) => (doc.value && field in doc.value ? money(doc.value[field], doc.value.currency) : 'Unavailable')
const stages = computed(() => (Array.isArray(doc.value?.stages) ? doc.value.stages : null))
const boqLines = computed(() => (Array.isArray(doc.value?.boq) ? doc.value.boq.length : null))
// Counted from the saved stage rows; no percentage is estimated.
const done = computed(() => stages.value?.filter((stage) => stage.status === 'Completed').length ?? 0)

async function load() {
  const id = ++request
  if (doc.value?.name !== route.params.name) doc.value = null // the same job reloads in place
  error.value = null
  loading.value = true
  try {
    const result = await apiGet(`/api/resource/${encodeURIComponent(JOB_DOCTYPE)}/${encodeURIComponent(route.params.name)}`)
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
      <RouterLink class="bj-link" :to="{ name: 'construction' }">Construction</RouterLink>
      <span aria-hidden="true">/</span>
      <span>{{ route.params.name }}</span>
    </nav>

    <div v-if="loading && !doc" class="page__card bj-loading" role="status"><LoadingIndicator /><span>Loading job…</span></div>

    <div v-else-if="error && !doc" class="page__card">
      <StatePanel v-if="error.kind === 'denied'" icon="lucide-lock" title="This job is unavailable to you" message="Your account does not have permission to read this construction job." />
      <StatePanel
        v-else
        icon="lucide-triangle-alert"
        tone="blocked"
        title="The job could not be loaded"
        :message="`${error.message.replace(/[.\s]+$/, '')}. Nothing is shown, because the saved record could not be read.`"
      >
        <button type="button" class="bj-btn bj-btn--primary" @click="load">Try again</button>
      </StatePanel>
    </div>

    <template v-else-if="doc">
      <header class="bj-head">
        <div>
          <h1 class="page__title">{{ doc.name }}</h1>
          <p class="bj-sub">{{ textValue(doc.customer) }}</p>
        </div>
        <div class="bj-toolbar">
          <span v-if="doc.service_type" class="bj-pill">{{ doc.service_type }}</span>
          <span class="bj-pill bj-chip" :class="'bj-chip--' + jobTone(doc.status)">{{ doc.status || 'Status not recorded' }}</span>
        </div>
      </header>

      <p v-if="route.query.saved" class="bj-note saved-note" role="status"><span class="lucide-circle-check-big" aria-hidden="true" />Saved.</p>
      <RecordActions
        :doctype="JOB_DOCTYPE"
        :name="doc.name"
        :edit-route="{ name: 'jobs-edit', params: { name: doc.name } }"
        :list-route="{ name: 'construction' }"
        :reload-key="doc.modified"
        @changed="load"
      />

      <div class="bj-grid">
        <article class="bj-card">
          <h2>Client</h2>
          <p class="bj-strong">
            <RouterLink v-if="canRead('customers') && doc.customer" class="bj-link" :to="{ name: 'customers-detail', params: { name: doc.customer } }">{{ doc.customer }}</RouterLink>
            <template v-else>{{ textValue(doc.customer) }}</template>
          </p>
          <p class="bj-muted">{{ doc.company || 'Company not recorded' }}</p>
        </article>
        <article class="bj-card">
          <h2>Site</h2>
          <p class="bj-strong">{{ doc.site_location || 'Location not recorded' }}</p>
          <p v-if="doc.plot_number" class="bj-muted">Plot {{ doc.plot_number }}</p>
          <p v-if="doc.title_reference" class="bj-muted">Title {{ doc.title_reference }}</p>
        </article>
        <article class="bj-card">
          <h2>Engineer</h2>
          <p class="bj-strong">{{ doc.engineer || 'Not assigned' }}</p>
          <p v-if="doc.contract_quotation" class="bj-muted">Quotation {{ doc.contract_quotation }}</p>
        </article>
      </div>

      <section class="bj-section">
        <h2>Contract</h2>
        <div class="page__card bj-card">
          <p v-if="!doc.contract_quotation && !isAmount(doc.contract_value)" class="bj-muted">This job has no contract recorded yet.</p>
          <dl v-else class="bj-kv">
            <div><dt>Contract value</dt><dd>{{ cash('contract_value') }}</dd></div>
            <div><dt>Approved variations</dt><dd>{{ cash('approved_variations') }}</dd></div>
            <div><dt>Current contract value</dt><dd>{{ cash('current_contract_value') }}</dd></div>
            <div>
              <dt>Bill of quantities</dt>
              <dd>
                {{ cash('boq_total') }}
                <span v-if="boqLines !== null" class="bj-small">{{ boqLines }} {{ boqLines === 1 ? 'line' : 'lines' }}<template v-if="doc.boq_revision_no"> · revision {{ doc.boq_revision_no }}</template></span>
              </dd>
            </div>
            <div><dt>Start</dt><dd>{{ dateText(doc.contract_start_date) }}</dd></div>
            <div><dt>End</dt><dd>{{ dateText(doc.contract_end_date) }}</dd></div>
            <div><dt>Retention</dt><dd>{{ percentText(doc.retention_pct) }}</dd></div>
            <div>
              <dt>Approved</dt>
              <dd>
                {{ doc.contract_approved_by || 'Not recorded' }}
                <span v-if="doc.contract_approved_on" class="bj-small">{{ dateTimeText(doc.contract_approved_on) }}</span>
              </dd>
            </div>
          </dl>
        </div>
      </section>

      <section class="bj-section">
        <h2>Stages</h2>
        <div class="page__card">
          <StatePanel v-if="!stages" icon="lucide-eye-off" title="Stages unavailable" message="Your account may not see this job's stages." />
          <StatePanel v-else-if="!stages.length" icon="lucide-list-checks" title="No stages recorded" />
          <template v-else>
            <div class="bj-table-wrap">
              <table class="bj-table bj-table--stack">
                <thead>
                  <tr>
                    <th scope="col">Stage</th>
                    <th scope="col">Status</th>
                    <th scope="col">Planned</th>
                    <th scope="col">Finished</th>
                    <th scope="col" class="bj-right">Complete</th>
                    <th scope="col">Certified</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="stage in stages" :key="stage.name">
                    <td data-label="Stage" class="bj-strong">{{ stage.stage_name || '—' }}</td>
                    <td data-label="Status"><span class="bj-chip" :class="'bj-chip--' + stageTone(stage.status)">{{ stage.status || '—' }}</span></td>
                    <td data-label="Planned">{{ dateText(stage.planned_start) }} – {{ dateText(stage.planned_end) }}</td>
                    <td data-label="Finished">{{ dateText(stage.actual_end) }}</td>
                    <td data-label="Complete" class="bj-right">{{ percentText(stage.completion_pct) }}</td>
                    <td data-label="Certified">
                      <span v-if="stage.certified">
                        Yes<span v-if="stage.certified_by" class="bj-small">{{ stage.certified_by }}<template v-if="stage.certified_on"> · {{ dateText(stage.certified_on) }}</template></span>
                      </span>
                      <span v-else class="bj-muted">No</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="bj-foot">{{ done }} of {{ stages.length }} stages recorded as completed.</p>
          </template>
        </div>
      </section>
    </template>
  </section>
</template>

<style scoped>
.saved-note {
  margin: 12px 0;
}
.saved-note > span {
  color: var(--bj-state-completed);
}
</style>
