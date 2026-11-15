<script setup>
import TransactionGuide from '../components/TransactionGuide.vue'
import ListInsights from '../components/ListInsights.vue'
import { computed, ref, watch } from 'vue'

import { ApiError, apiGet } from '../api'
import CompanyPicker from '../components/CompanyPicker.vue'
import ListStates from '../components/ListStates.vue'
import StatePanel from '../components/StatePanel.vue'
import { company } from '../company'
import { dateText, money, monthText, shiftMonth, textValue } from '../format'

// One calendar month of the agreed installment schedule, as the server reports it. Every
// total on this page is the server's; the page adds nothing up.
const METHOD = '/api/method/sidra_realestate.api.staff_dashboard.get_installment_calendar'

const now = new Date()
const month = ref(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`)
const data = ref(null)
const loading = ref(false)
const error = ref(null)
const show = ref('all')
let request = 0

const TILES = [
  { key: 'month', label: 'Scheduled this month' },
  { key: 'past_due', label: 'Due date passed' },
  { key: 'today', label: 'Due today' },
  { key: 'upcoming', label: 'Still to come' },
]
// A passed date is not proof of an unpaid amount, so it is never called "overdue" here.
const STATE = {
  past_due: { text: 'Date passed', tone: 'muted' },
  today: { text: 'Due today', tone: 'current' },
  upcoming: { text: 'Upcoming', tone: 'pending' },
}

const state = computed(() => {
  if (error.value) return error.value.kind === 'denied' ? 'unavailable' : 'error'
  if (!data.value) return 'loading'
  if (data.value.available === false) return 'closed'
  return data.value.events.length ? 'ready' : 'empty'
})
const events = computed(() => {
  const all = data.value?.events ?? []
  return show.value === 'all' ? all : all.filter((event) => event.date_state === show.value)
})
const tile = (key) => data.value?.summary?.[key] ?? null

async function load() {
  const id = ++request
  data.value = null
  error.value = null
  if (!company.value) return
  loading.value = true
  try {
    const body = await apiGet(METHOD, { company: company.value, month: month.value })
    if (id !== request) return
    const answer = body.message
    if (!answer || !Array.isArray(answer.events)) throw new ApiError('server', 'The server sent an unexpected answer.')
    data.value = answer
  } catch (err) {
    if (id === request) error.value = err instanceof ApiError ? err : new ApiError('server', 'Something went wrong.')
  } finally {
    if (id === request) loading.value = false
  }
}

watch([company, month], load, { immediate: true })
</script>

<template>
  <TransactionGuide />
  <section class="page">
    <header class="bj-head">
      <div>
        <h1 class="page__title">Collections</h1>
        <p class="bj-sub">Installments falling due, from confirmed contracts</p>
      </div>
      <div class="bj-toolbar">
        <CompanyPicker />
        <button type="button" class="bj-btn bj-btn--icon" aria-label="Previous month" :disabled="loading" @click="month = shiftMonth(month, -1)">
          <span class="lucide-chevron-left" aria-hidden="true" />
        </button>
        <strong class="month" aria-live="polite">{{ monthText(month) }}</strong>
        <button type="button" class="bj-btn bj-btn--icon" aria-label="Next month" :disabled="loading" @click="month = shiftMonth(month, 1)">
          <span class="lucide-chevron-right" aria-hidden="true" />
        </button>
        <button type="button" class="bj-btn" :disabled="loading" @click="load">Refresh</button>
      </div>
    </header>
    <ListInsights :rows="events" group="date_state" :columns="[{field:'contract_id',label:'Contract'},{field:'due_date',label:'Due date'},{field:'date_state',label:'Date state'},{field:'amount',label:'Amount'},{field:'currency',label:'Currency'}]" :busy="loading || !!error" />

    <div v-if="!company" class="page__card">
      <StatePanel icon="lucide-building" title="No Company is available to you" message="Collections are shown for one Company at a time, and your account can read none." />
    </div>

    <template v-else>
      <div v-if="state === 'ready' || state === 'empty'" class="bj-grid">
        <article v-for="item in TILES" :key="item.key" class="bj-card">
          <h2>{{ item.label }}</h2>
          <p v-if="tile(item.key)?.amount != null" class="bj-figure">{{ money(tile(item.key).amount, data.currency) }}</p>
          <p v-else-if="tile(item.key)?.count === 0" class="bj-figure bj-unavailable">Nothing scheduled</p>
          <p v-else class="bj-figure bj-unavailable">Unavailable</p>
          <p class="bj-muted">{{ tile(item.key)?.count ?? '—' }} {{ tile(item.key)?.count === 1 ? 'installment' : 'installments' }}</p>
        </article>
      </div>

      <p v-if="data?.notice && (state === 'ready' || state === 'empty')" class="bj-note">
        <span class="lucide-info" aria-hidden="true" /><span>{{ data.notice }}</span>
      </p>

      <div class="page__card">
        <StatePanel v-if="state === 'closed'" icon="lucide-lock" title="Collections are unavailable" :message="data.reason" />
        <ListStates
          v-else
          :state="state"
          :error="error"
          noun="installments"
          icon="lucide-calendar"
          :empty-message="`No installment from a confirmed contract falls due in ${monthText(month)}.`"
          @retry="load"
        >
          <div class="filter">
            <label for="show-state">Show</label>
            <select id="show-state" v-model="show" class="bj-select">
              <option value="all">All dates</option>
              <option value="past_due">Date passed</option>
              <option value="today">Due today</option>
              <option value="upcoming">Upcoming</option>
            </select>
          </div>
          <div class="bj-table-wrap">
            <table class="bj-table bj-table--stack">
              <thead>
                <tr>
                  <th scope="col">Due date</th>
                  <th scope="col">Contract</th>
                  <th scope="col">Customer</th>
                  <th scope="col">Type</th>
                  <th scope="col" class="bj-right">Amount</th>
                  <th scope="col">Date</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="event in events" :key="event.id">
                  <td data-label="Due date">{{ dateText(event.due_date) }}</td>
                  <td data-label="Contract">
                    <span>
                      <RouterLink class="bj-link" :to="{ name: 'contract-detail', params: { name: event.contract_id } }">{{ event.contract_id }}</RouterLink>
                      <span v-if="event.external_reference" class="bj-small">{{ event.external_reference }}</span>
                    </span>
                  </td>
                  <td data-label="Customer">{{ textValue(event.customer_display) }}</td>
                  <td data-label="Type">{{ event.row_type }}</td>
                  <td data-label="Amount" class="bj-right">
                    <span :class="{ 'bj-unavailable': event.amount == null }">{{ money(event.amount, event.currency) }}</span>
                  </td>
                  <td data-label="Date">
                    <span class="bj-chip" :class="'bj-chip--' + (STATE[event.date_state]?.tone || 'muted')">{{ STATE[event.date_state]?.text || event.date_state }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="bj-foot">
            <span>Showing {{ events.length }} of {{ data.events.length }} for {{ monthText(month) }}</span>
            <span>Payment status is not recorded against installments yet.</span>
          </p>
        </ListStates>
      </div>
    </template>
  </section>
</template>

<style scoped>
.month {
  min-width: 84px;
  font-size: 14px;
  text-align: center;
}
.filter {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  font-size: 13px;
  color: var(--bj-muted);
  border-bottom: 1px solid var(--bj-line);
}
</style>
