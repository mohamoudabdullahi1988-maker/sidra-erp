<script setup>
import { ref, watch } from 'vue'

import CompanyPicker from '../components/CompanyPicker.vue'
import ListStates from '../components/ListStates.vue'
import SectionTabs from '../components/SectionTabs.vue'
import { canCreate } from '../boot'
import { company } from '../company'
import { JOB_DOCTYPE, jobTone } from '../construction'
import { dateText, money, textValue } from '../format'
import { useList } from '../list'

const STATUSES = ['Enquiry', 'Quoted', 'Contracted', 'In Progress', 'On Hold', 'Completed', 'Defects Period', 'Closed', 'Cancelled']
const status = ref('')
const newLink = canCreate('jobs')

const { rows, hasMore, loading, error, count, state, reload, loadMore } = useList(JOB_DOCTYPE, {
  fields: ['name', 'customer', 'service_type', 'status', 'site_location', 'plot_number', 'engineer', 'current_contract_value', 'currency', 'contract_end_date'],
  filters: () => ({ ...(company.value ? { company: company.value } : {}), ...(status.value ? { status: status.value } : {}) }),
  orderBy: 'modified desc',
})

watch([company, status], reload, { immediate: true })
</script>

<template>
  <section class="page">
    <header class="bj-head">
      <div>
        <h1 class="page__title">Construction</h1>
        <p class="bj-sub" aria-live="polite">
          <template v-if="count !== null">{{ count }} {{ count === 1 ? 'job' : 'jobs' }} on record{{ status ? ` with status ${status}` : '' }}</template>
          <template v-else>Construction jobs</template>
        </p>
      </div>
      <div class="bj-toolbar">
        <CompanyPicker />
        <label class="bj-label" for="job-status">Status</label>
        <select id="job-status" v-model="status" class="bj-select">
          <option value="">All statuses</option>
          <option v-for="name in STATUSES" :key="name" :value="name">{{ name }}</option>
        </select>
        <button type="button" class="bj-btn" :disabled="loading" @click="reload">Refresh</button>
        <RouterLink v-if="newLink" class="bj-btn bj-btn--primary" :to="{ name: 'jobs-new' }"><span class="lucide-plus" aria-hidden="true" />New job</RouterLink>
      </div>
    </header>

    <SectionTabs section="construction" current="jobs" />

    <div class="page__card">
      <ListStates :state="state" :error="error" noun="construction jobs" icon="lucide-hard-hat" @retry="reload">
        <div class="bj-table-wrap" :aria-busy="loading">
          <table class="bj-table bj-table--stack">
            <thead>
              <tr>
                <th scope="col">Job</th>
                <th scope="col">Client</th>
                <th scope="col">Service</th>
                <th scope="col">Site</th>
                <th scope="col">Status</th>
                <th scope="col" class="bj-right">Contract value</th>
                <th scope="col">Contract end</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.name">
                <td data-label="Job">
                  <RouterLink class="bj-link" :to="{ name: 'construction-detail', params: { name: row.name } }">{{ row.name }}</RouterLink>
                </td>
                <td data-label="Client">{{ textValue(row.customer) }}</td>
                <td data-label="Service">{{ row.service_type || '—' }}</td>
                <td data-label="Site">
                  <span>
                    {{ row.site_location || '—' }}
                    <span v-if="row.plot_number" class="bj-small">Plot {{ row.plot_number }}</span>
                  </span>
                </td>
                <td data-label="Status"><span class="bj-chip" :class="'bj-chip--' + jobTone(row.status)">{{ row.status || '—' }}</span></td>
                <td data-label="Contract value" class="bj-right">
                  <span v-if="!('current_contract_value' in row)" class="bj-unavailable">Unavailable</span>
                  <span v-else-if="!row.current_contract_value" class="bj-muted">Not contracted</span>
                  <span v-else>{{ money(row.current_contract_value, row.currency) }}</span>
                </td>
                <td data-label="Contract end">{{ dateText(row.contract_end_date) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <footer class="bj-foot">
          <span>Showing {{ rows.length }}<template v-if="count !== null"> of {{ count }}</template></span>
          <span v-if="error" role="alert">More jobs could not be loaded: {{ error.message }}</span>
          <button v-if="hasMore" type="button" class="bj-btn" :disabled="loading" @click="loadMore">Load more</button>
        </footer>
      </ListStates>
    </div>
  </section>
</template>
