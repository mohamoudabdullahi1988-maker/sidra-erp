<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { LoadingIndicator } from 'frappe-ui'

import { ApiError, apiGet, apiPost } from '../api'
import RecordActions from '../components/RecordActions.vue'
import StatePanel from '../components/StatePanel.vue'
import WorkflowPanel from '../components/WorkflowPanel.vue'
import { CONTRACT, CONTRACT_DOCTYPE, permissions, sourceText, statusText, statusTone, timeline } from '../contracts'
import { dateText, fileLink, isAmount, money, textValue } from '../format'
import { claimPanel, releasePanel } from '../panel'
import { canRead } from '../boot'
import { CONFIRM_METHOD, canConfirm, canEdit, isRegisteredDraft, printLink, savedDifference } from '../registration'

const route = useRoute()
const doc = ref(null)
const loading = ref(false)
const error = ref(null)
const flow = ref(null)
const flowLoading = ref(false)
const flowError = ref('')
let request = 0
let flowRequest = 0

// Confirmation (decision D7). Offered only when the server's timeline lists it; the server
// checks permission, every confirmation rule and the record's version again when it is sent.
const confirming = ref(false)
const confirmOpen = ref(false)
const acknowledged = ref(false)
const confirmError = ref(null)
const confirmedNote = ref('')
// Edit is offered when the server says this user may write the draft, or lists an edit action.
const mayWrite = ref(false)
const showEdit = computed(() => isRegisteredDraft(doc.value) && (mayWrite.value || canEdit(flow.value)))
const showConfirm = computed(() => doc.value?.docstatus === 0 && canConfirm(flow.value))
const savedGap = computed(() => savedDifference(doc.value))

function openConfirm() {
  confirmOpen.value = true
  acknowledged.value = false
  confirmError.value = null
}

async function confirmRegistration() {
  confirming.value = true
  confirmError.value = null
  try {
    const result = await apiPost(CONFIRM_METHOD, {
      contract: doc.value.name,
      expected_modified: doc.value.modified,
      acknowledge_difference: acknowledged.value ? 1 : 0,
    })
    confirmOpen.value = false
    await load()
    confirmedNote.value = result?.repeated ? 'This contract was already confirmed by you.' : 'Contract confirmed.'
  } catch (err) {
    confirmError.value = err instanceof ApiError ? err : new ApiError('server', 'Something went wrong.')
  } finally {
    confirming.value = false
  }
}

// A field the server left out of the record (not permitted for this user) is "Unavailable".
const cash = (field, row = doc.value) => (row && field in row ? money(row[field], doc.value?.currency) : 'Unavailable')
const units = computed(() => (Array.isArray(doc.value?.units) ? doc.value.units : null))
const schedule = computed(() => (Array.isArray(doc.value?.schedule) ? doc.value.schedule : null))
const external = computed(() => String(doc.value?.source || '').startsWith('External'))

// Shown for information only: whether a difference blocks registration is the server's call
// and appears in the workflow panel.
const difference = computed(() => {
  const { amount_due: due, schedule_total: total } = doc.value || {}
  if (!isAmount(due) || !isAmount(total)) return null
  const gap = Math.round((Number(due) - Number(total)) * 100) / 100
  return gap === 0 ? null : gap
})

async function refreshWorkflow() {
  if (!doc.value) return
  const id = ++flowRequest
  flowLoading.value = true
  flowError.value = ''
  try {
    const result = await timeline(doc.value.name)
    if (id === flowRequest) flow.value = result
  } catch (err) {
    if (id !== flowRequest) return
    flow.value = null // a failed read leaves no earlier answer on screen
    flowError.value =
      err.kind === 'denied' ? 'You do not have permission to see this workflow.' : err.message || 'The workflow could not be loaded.'
  } finally {
    if (id === flowRequest) flowLoading.value = false
  }
}

async function load() {
  const id = ++request
  ++flowRequest
  confirmOpen.value = false
  // Reloading the same contract keeps it on screen, with any message an action left.
  const same = doc.value?.name === route.params.name
  if (!same) {
    confirmedNote.value = ''
    doc.value = null
    flow.value = null
  }
  flowError.value = ''
  flowLoading.value = false
  error.value = null
  loading.value = true
  try {
    const result = await apiGet(`${CONTRACT}/${encodeURIComponent(route.params.name)}`)
    if (!result.data?.name) throw new ApiError('server', 'The server sent an unexpected answer.')
    if (id !== request) return
    doc.value = result.data
    mayWrite.value = false
    refreshWorkflow()
    if (isRegisteredDraft(result.data)) {
      permissions(result.data.name)
        .then((allowed) => {
          if (id === request) mayWrite.value = Boolean(allowed.write)
        })
        .catch(() => {}) // unknown: no Edit button unless the timeline lists an edit action
    }
  } catch (err) {
    if (id === request) error.value = err instanceof ApiError ? err : new ApiError('server', 'Something went wrong.')
  } finally {
    if (id === request) loading.value = false
  }
}

function onFocus() {
  if (!flowLoading.value) refreshWorkflow()
}

watch(() => route.params.name, load, { immediate: true })
// The panel belongs to a contract that could be read: no record, no Workflow button.
watch(doc, (now, before) => {
  if (now && !before) claimPanel()
  else if (!now && before) releasePanel()
})
onMounted(() => window.addEventListener('focus', onFocus))
onBeforeUnmount(() => {
  ++request
  ++flowRequest
  window.removeEventListener('focus', onFocus)
  releasePanel()
})
</script>

<template>
  <section class="page">
    <nav class="bj-crumb" aria-label="Breadcrumb">
      <RouterLink class="bj-link" :to="{ name: 'contracts' }">Contracts</RouterLink>
      <span aria-hidden="true">/</span>
      <span>{{ route.params.name }}</span>
    </nav>

    <div v-if="loading && !doc" class="page__card bj-loading" role="status"><LoadingIndicator /><span>Loading contract…</span></div>

    <div v-else-if="error && !doc" class="page__card">
      <StatePanel
        v-if="error.kind === 'denied'"
        icon="lucide-lock"
        title="This contract is unavailable to you"
        message="Your account does not have permission to read this contract."
      />
      <StatePanel
        v-else
        icon="lucide-triangle-alert"
        tone="blocked"
        title="The contract could not be loaded"
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
          <span v-if="doc.external_reference" class="bj-pill">{{ doc.external_reference }}</span>
          <span class="bj-pill">{{ sourceText(doc) }}</span>
          <span class="bj-pill bj-chip" :class="'bj-chip--' + statusTone(doc.docstatus)">{{ statusText(doc.docstatus) }}</span>
          <a class="bj-btn" :href="printLink(doc.name)" target="_blank" rel="noopener"><span class="lucide-printer" aria-hidden="true" />Print</a>
          <RouterLink v-if="showEdit" class="bj-btn" :to="{ name: 'contract-edit', params: { name: doc.name } }"><span class="lucide-pencil" aria-hidden="true" />Edit draft</RouterLink>
          <button v-if="showConfirm && !confirmOpen" type="button" class="bj-btn bj-btn--primary" @click="openConfirm">
            <span class="lucide-check" aria-hidden="true" />Confirm contract
          </button>
        </div>
      </header>

      <p v-if="route.query.saved" class="bj-note saved-note" role="status"><span class="lucide-circle-check-big" aria-hidden="true" />Saved.</p>
      <!-- Generated and cash contracts: Edit, Submit (sign), Revise draft, Cancel, Delete through the form
           engine (G23). A registered contract is edited and confirmed by the buttons above. -->
      <RecordActions
        :doctype="CONTRACT_DOCTYPE"
        :name="doc.name"
        :edit-route="external ? null : { name: 'contracts-edit', params: { name: doc.name } }"
        :list-route="{ name: 'contracts' }"
        :reload-key="doc.modified"
        @changed="load"
      />

      <p v-if="confirmedNote" class="bj-note confirm__ok" role="status"><span class="lucide-circle-check-big" aria-hidden="true" />{{ confirmedNote }}</p>

      <section v-if="confirmOpen" class="page__card bj-card confirm" aria-labelledby="confirm-title">
        <h2 id="confirm-title">Confirm {{ doc.name }}?</h2>
        <p>
          Confirming registers this contract as signed. Its units become Under Contract, its terms are frozen and it can no longer be edited.
          Nothing is posted to the ledger.
        </p>
        <label v-if="savedGap !== null" class="confirm__ack">
          <input v-model="acknowledged" type="checkbox" />
          <span>
            I acknowledge that the saved schedule differs from the amount due by {{ money(savedGap, doc.currency) }}. My name is recorded on the contract
            with this acknowledgement.
          </span>
        </label>
        <div v-if="confirmError" class="confirm__error" role="alert">
          <span class="lucide-triangle-alert" aria-hidden="true" />
          <div>
            <p class="bj-strong">{{ confirmError.type === 'StaleRecord' ? 'Someone else changed this contract' : 'Not confirmed' }}</p>
            <p>{{ confirmError.message }}</p>
            <button v-if="confirmError.type === 'StaleRecord'" type="button" class="bj-btn" @click="load">Reload</button>
          </div>
        </div>
        <div class="bj-toolbar">
          <button type="button" class="bj-btn bj-btn--primary" :disabled="confirming || (savedGap !== null && !acknowledged)" @click="confirmRegistration">
            <span v-if="confirming" class="confirm__spin" aria-hidden="true" />Confirm contract
          </button>
          <button type="button" class="bj-btn" :disabled="confirming" @click="confirmOpen = false">Cancel</button>
        </div>
      </section>

      <div class="bj-grid">
        <article class="bj-card">
          <h2>Buyer</h2>
          <p class="bj-strong">
            <RouterLink v-if="canRead('customers') && doc.customer" class="bj-link" :to="{ name: 'customers-detail', params: { name: doc.customer } }">{{ doc.customer }}</RouterLink>
            <template v-else>{{ textValue(doc.customer) }}</template>
          </p>
          <p class="bj-muted">{{ doc.company || 'Company not recorded' }}</p>
        </article>
        <article class="bj-card">
          <h2>Property</h2>
          <p v-if="!units" class="bj-unavailable">Unavailable</p>
          <p v-else-if="!units.length" class="bj-muted">None recorded</p>
          <template v-else>
            <p v-for="unit in units" :key="unit.name">
              <span class="bj-strong">{{ textValue(unit.unit) }}</span>
              <span v-if="unit.scheme" class="bj-muted"> · {{ unit.scheme }}</span>
            </p>
          </template>
        </article>
        <article class="bj-card">
          <h2>{{ external ? 'External agreement' : 'Signed agreement' }}</h2>
          <p v-if="fileLink(doc.signed_copy)">
            <a class="bj-link" :href="fileLink(doc.signed_copy)" target="_blank" rel="noopener">{{ doc.signed_copy.split('/').pop() }}</a>
          </p>
          <p v-else class="bj-muted">No file attached</p>
          <p class="bj-muted">Signed {{ doc.signed_on ? dateText(doc.signed_on) : 'date not recorded' }}</p>
        </article>
      </div>

      <section class="bj-section">
        <h2>Amounts</h2>
        <div class="page__card bj-card">
          <dl class="bj-kv">
            <div><dt>Sale price</dt><dd>{{ cash('agreed_price') }}</dd></div>
            <div><dt>Down payment</dt><dd>{{ cash('down_payment') }}</dd></div>
            <div><dt>Agreed balance</dt><dd>{{ cash('amount_due') }}</dd></div>
            <div><dt>Schedule total</dt><dd>{{ cash('schedule_total') }}</dd></div>
          </dl>
          <p v-if="difference !== null" class="bj-note" role="status">
            <span class="lucide-info" aria-hidden="true" />
            <span>
              The schedule total is {{ cash('schedule_total') }} and the agreed balance is {{ cash('amount_due') }}: a difference of
              {{ money(difference, doc.currency) }}. Whether this holds up registration is decided by the server and shown in the workflow.
            </span>
          </p>
        </div>
      </section>

      <section class="bj-section">
        <h2>Installment schedule</h2>
        <div class="page__card">
          <StatePanel v-if="!schedule" icon="lucide-eye-off" title="Schedule unavailable" message="Your account may not see this contract's schedule." />
          <StatePanel v-else-if="!schedule.length" icon="lucide-calendar" title="No schedule rows recorded" />
          <template v-else>
            <div class="bj-table-wrap">
              <table class="bj-table bj-table--stack">
                <thead>
                  <tr>
                    <th scope="col">No.</th>
                    <th scope="col">Due date</th>
                    <th scope="col">Type</th>
                    <th scope="col" class="bj-right">Amount</th>
                    <th scope="col">Payment status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in schedule" :key="row.name">
                    <td data-label="No.">{{ row.seq ?? row.idx ?? '—' }}</td>
                    <td data-label="Due date">{{ dateText(row.due_date) }}</td>
                    <td data-label="Type">{{ row.row_type || 'Installment' }}</td>
                    <td data-label="Amount" class="bj-right">{{ cash('amount', row) }}</td>
                    <td data-label="Payment status"><span class="bj-unavailable">Not recorded</span></td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <th scope="row" colspan="3">Total ({{ schedule.length }} {{ schedule.length === 1 ? 'row' : 'rows' }})</th>
                    <td data-label="Total" class="bj-right">{{ cash('schedule_total') }}</td>
                    <td />
                  </tr>
                </tfoot>
              </table>
            </div>
            <p class="bj-foot">Payments against installments are not recorded in the system yet, so no row is shown as paid or unpaid.</p>
          </template>
        </div>
      </section>
    </template>

    <Teleport defer to="#berjaya-panel">
      <WorkflowPanel v-if="doc" :timeline="flow" :loading="flowLoading" :error="flowError" @refresh="refreshWorkflow" />
    </Teleport>
  </section>
</template>

<style scoped>
.saved-note {
  margin: 12px 0;
}
.saved-note > span {
  color: var(--bj-state-completed);
}
.confirm {
  margin: 16px 0;
  border-color: var(--bj-terracotta);
}
.confirm h2 {
  margin: 0 0 8px;
}
.confirm > p {
  margin: 0 0 12px;
}
.confirm__ack {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin: 0 0 12px;
  padding: 12px;
  background: var(--bj-terracotta-tint);
  border-radius: 8px;
  cursor: pointer;
}
.confirm__ack input {
  width: 20px;
  height: 20px;
  margin-top: 2px;
  flex: none;
}
.confirm__error {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin: 0 0 12px;
  padding: 12px 14px;
  color: var(--bj-state-blocked);
  border: 1px solid var(--bj-state-blocked);
  border-radius: 12px;
}
.confirm__error p {
  margin: 0 0 6px;
  color: var(--bj-ink);
}
.confirm__ok {
  margin: 12px 0;
}
.confirm__ok > span {
  color: var(--bj-state-completed);
}
.confirm__spin {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: confirm-spin 0.8s linear infinite;
}
@keyframes confirm-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
