<script setup>
import TransactionGuide from '../components/TransactionGuide.vue'
import ListInsights from '../components/ListInsights.vue'
import { computed, ref, watch } from 'vue'
import { LoadingIndicator } from 'frappe-ui'

import { ApiError, apiGet } from '../api'
import CompanyPicker from '../components/CompanyPicker.vue'
import ListStates from '../components/ListStates.vue'
import StatePanel from '../components/StatePanel.vue'
import { company } from '../company'
import { dateText, dateTimeText, deskLink, money, percentText, sitePath, textValue } from '../format'
import { useList } from '../list'

// Figures come from the server's own summary of the ledger (get_dashboard -> payments); the
// two lists are the submitted native invoices and receipts this user may read. The page adds
// nothing up: a figure the server does not give is "Unavailable".
const METHOD = '/api/method/sidra_realestate.api.staff_dashboard.get_dashboard'
const PERIODS = [
  { value: 'this_month', label: 'This month' },
  { value: 'last_30_days', label: 'Last 30 days' },
  { value: 'last_90_days', label: 'Last 90 days' },
]

const period = ref('this_month')
const summary = ref(null) // { payments, currency, as_of }
const summaryLoading = ref(false)
const summaryError = ref(null)
const tab = ref('invoices')
let request = 0

const scope = () => (company.value ? { company: company.value, docstatus: 1 } : { docstatus: 1 })
const invoices = useList('Sales Invoice', {
  fields: ['name', 'customer', 'posting_date', 'due_date', 'grand_total', 'outstanding_amount', 'currency', 'status'],
  filters: scope,
  orderBy: 'posting_date desc',
})
const receipts = useList('Payment Entry', {
  fields: ['name', 'party', 'posting_date', 'paid_amount', 'paid_from_account_currency', 'mode_of_payment', 'reference_no'],
  filters: () => ({ ...scope(), payment_type: 'Receive' }),
  orderBy: 'posting_date desc',
})
const loaded = { invoices: false, receipts: false }

const payments = computed(() => summary.value?.payments ?? null)
const figures = computed(() => (payments.value?.available ? payments.value : null))
const periodLabel = computed(() => PERIODS.find((item) => item.value === period.value)?.label.toLowerCase())
const INVOICE_TONE = { Paid: 'completed', Overdue: 'blocked', Unpaid: 'current', 'Partly Paid': 'current' }

async function loadSummary() {
  const id = ++request
  summary.value = null
  summaryError.value = null
  if (!company.value) return
  summaryLoading.value = true
  try {
    const body = await apiGet(METHOD, { company: company.value, period: period.value })
    if (id !== request) return
    if (!body.message || typeof body.message.payments !== 'object') throw new ApiError('server', 'The server sent an unexpected answer.')
    summary.value = body.message
  } catch (err) {
    if (id === request) summaryError.value = err instanceof ApiError ? err : new ApiError('server', 'Something went wrong.')
  } finally {
    if (id === request) summaryLoading.value = false
  }
}

function openTab(name) {
  tab.value = name
  if (!loaded[name]) {
    loaded[name] = true
    ;(name === 'invoices' ? invoices : receipts).reload()
  }
}

function reloadAll() {
  loadSummary()
  loaded.invoices = loaded.receipts = false
  openTab(tab.value)
}

watch([company, period], loadSummary)
watch(company, reloadAll, { immediate: true })
</script>

<template>
  <TransactionGuide />
  <section class="page">
    <header class="bj-head">
      <div>
        <h1 class="page__title">Finance</h1>
        <p class="bj-sub">
          <template v-if="summary?.as_of">Ledger position as at {{ dateTimeText(summary.as_of) }}</template>
          <template v-else>Invoices and receipts from the ledger</template>
        </p>
      </div>
      <div class="bj-toolbar">
        <CompanyPicker />
        <label class="bj-label" for="finance-period">Period</label>
        <select id="finance-period" v-model="period" class="bj-select">
          <option v-for="item in PERIODS" :key="item.value" :value="item.value">{{ item.label }}</option>
        </select>
        <button type="button" class="bj-btn" :disabled="summaryLoading" @click="reloadAll">Refresh</button>
      </div>
    </header>
    <ListInsights v-if="tab === 'invoices'" :rows="invoices.rows.value" :busy="invoices.loading.value || !!invoices.error.value" :columns="[{field:'name',label:'Invoice'},{field:'customer',label:'Customer'},{field:'status',label:'Status'},{field:'due_date',label:'Due date'}]" />
    <ListInsights v-else :rows="receipts.rows.value" :busy="receipts.loading.value || !!receipts.error.value" group="mode_of_payment" :columns="[{field:'name',label:'Receipt'},{field:'party',label:'Party'},{field:'posting_date',label:'Date'},{field:'mode_of_payment',label:'Payment method'}]" />

    <div v-if="!company" class="page__card">
      <StatePanel icon="lucide-building" title="No Company is available to you" message="Finance is shown for one Company at a time, and your account can read none." />
    </div>

    <template v-else>
      <div v-if="summaryLoading" class="page__card bj-loading" role="status"><LoadingIndicator /><span>Loading the ledger position…</span></div>

      <div v-else-if="summaryError" class="page__card">
        <StatePanel
          :icon="summaryError.kind === 'denied' ? 'lucide-lock' : 'lucide-triangle-alert'"
          :tone="summaryError.kind === 'denied' ? 'muted' : 'blocked'"
          :title="summaryError.kind === 'denied' ? 'The ledger position is unavailable to you' : 'The ledger position could not be loaded'"
          :message="`${summaryError.message.replace(/[.\s]+$/, '')}. No figure is shown.`"
        >
          <button type="button" class="bj-btn bj-btn--primary" @click="loadSummary">Try again</button>
        </StatePanel>
      </div>

      <template v-else-if="summary">
        <div class="bj-grid">
          <article class="bj-card">
            <h2>Received, {{ periodLabel }}</h2>
            <p class="bj-figure" :class="{ 'bj-unavailable': !figures }">{{ figures ? money(figures.received, summary.currency) : 'Unavailable' }}</p>
            <p v-if="figures && sitePath(figures.cash_drilldown?.path)"><a class="bj-link" :href="sitePath(figures.cash_drilldown.path)">Open receipts</a></p>
          </article>
          <article class="bj-card">
            <h2>Overdue</h2>
            <p class="bj-figure" :class="{ 'bj-unavailable': !figures }">{{ figures ? money(figures.overdue, summary.currency) : 'Unavailable' }}</p>
            <p v-if="figures" class="bj-muted">
              {{ figures.overdue_invoices ?? '—' }} {{ figures.overdue_invoices === 1 ? 'invoice' : 'invoices' }}
              <template v-if="sitePath(figures.overdue_drilldown?.path)"> · <a class="bj-link" :href="sitePath(figures.overdue_drilldown.path)">Receivables report</a></template>
            </p>
          </article>
          <article class="bj-card">
            <h2>Collected of amounts due</h2>
            <p class="bj-figure" :class="{ 'bj-unavailable': !figures || figures.collection_rate == null }">{{ figures ? percentText(figures.collection_rate) : 'Unavailable' }}</p>
          </article>
        </div>

        <p v-if="payments?.notice || payments?.reason" class="bj-note">
          <span class="lucide-info" aria-hidden="true" /><span>{{ payments.notice || payments.reason }}</span>
        </p>

        <section v-if="figures && Array.isArray(figures.aging)" class="bj-section">
          <h2>Overdue by age</h2>
          <div class="page__card bj-card">
            <dl class="bj-kv">
              <div v-for="bucket in figures.aging" :key="bucket.label"><dt>{{ bucket.label }}</dt><dd>{{ money(bucket.amount, summary.currency) }}</dd></div>
            </dl>
          </div>
        </section>
      </template>

      <section class="bj-section">
        <h2>Ledger documents</h2>
        <div class="page__card">
          <div class="bj-tabs" role="tablist" aria-label="Ledger documents">
            <button type="button" class="bj-tab" role="tab" :aria-selected="tab === 'invoices'" @click="openTab('invoices')">Invoices</button>
            <button type="button" class="bj-tab" role="tab" :aria-selected="tab === 'receipts'" @click="openTab('receipts')">Receipts</button>
          </div>

          <ListStates
            v-if="tab === 'invoices'"
            :state="invoices.state.value"
            :error="invoices.error.value"
            noun="invoices"
            icon="lucide-receipt"
            empty-message="No submitted sales invoice is on the ledger for this Company, or none is visible to your account."
            @retry="invoices.reload"
          >
            <div class="bj-table-wrap">
              <table class="bj-table bj-table--stack">
                <thead>
                  <tr>
                    <th scope="col">Invoice</th>
                    <th scope="col">Customer</th>
                    <th scope="col">Posted</th>
                    <th scope="col">Due</th>
                    <th scope="col" class="bj-right">Total</th>
                    <th scope="col" class="bj-right">Outstanding</th>
                    <th scope="col">Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in invoices.rows.value" :key="row.name">
                    <td data-label="Invoice"><a class="bj-link" :href="deskLink('Sales Invoice', row.name)">{{ row.name }}</a></td>
                    <td data-label="Customer">{{ textValue(row.customer) }}</td>
                    <td data-label="Posted">{{ dateText(row.posting_date) }}</td>
                    <td data-label="Due">{{ dateText(row.due_date) }}</td>
                    <td data-label="Total" class="bj-right">{{ 'grand_total' in row ? money(row.grand_total, row.currency) : 'Unavailable' }}</td>
                    <td data-label="Outstanding" class="bj-right">{{ 'outstanding_amount' in row ? money(row.outstanding_amount, row.currency) : 'Unavailable' }}</td>
                    <td data-label="Status"><span class="bj-chip" :class="'bj-chip--' + (INVOICE_TONE[row.status] || 'muted')">{{ row.status || '—' }}</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
            <footer class="bj-foot">
              <span>Showing {{ invoices.rows.value.length }}<template v-if="invoices.count.value !== null"> of {{ invoices.count.value }}</template></span>
              <button v-if="invoices.hasMore.value" type="button" class="bj-btn" :disabled="invoices.loading.value" @click="invoices.loadMore">Load more</button>
            </footer>
          </ListStates>

          <ListStates
            v-else
            :state="receipts.state.value"
            :error="receipts.error.value"
            noun="receipts"
            icon="lucide-banknote"
            empty-message="No submitted receipt is on the ledger for this Company, or none is visible to your account."
            @retry="receipts.reload"
          >
            <div class="bj-table-wrap">
              <table class="bj-table bj-table--stack">
                <thead>
                  <tr>
                    <th scope="col">Receipt</th>
                    <th scope="col">From</th>
                    <th scope="col">Posted</th>
                    <th scope="col">Method</th>
                    <th scope="col">Reference</th>
                    <th scope="col" class="bj-right">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in receipts.rows.value" :key="row.name">
                    <td data-label="Receipt"><a class="bj-link" :href="deskLink('Payment Entry', row.name)">{{ row.name }}</a></td>
                    <td data-label="From">{{ textValue(row.party) }}</td>
                    <td data-label="Posted">{{ dateText(row.posting_date) }}</td>
                    <td data-label="Method">{{ row.mode_of_payment || '—' }}</td>
                    <td data-label="Reference">{{ row.reference_no || '—' }}</td>
                    <td data-label="Amount" class="bj-right">{{ 'paid_amount' in row ? money(row.paid_amount, row.paid_from_account_currency) : 'Unavailable' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <footer class="bj-foot">
              <span>Showing {{ receipts.rows.value.length }}<template v-if="receipts.count.value !== null"> of {{ receipts.count.value }}</template></span>
              <button v-if="receipts.hasMore.value" type="button" class="bj-btn" :disabled="receipts.loading.value" @click="receipts.loadMore">Load more</button>
            </footer>
          </ListStates>
        </div>
      </section>
    </template>
  </section>
</template>
