<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import { apiGet } from '../api'
import { listRoute } from '../records'
import { company } from '../company'
import { canRead, canCreate } from '../boot'
import CompanyPicker from '../components/CompanyPicker.vue'
import StatePanel from '../components/StatePanel.vue'
import SectionTabs from '../components/SectionTabs.vue'
import KpiTile from '../showcase/components/KpiTile.vue'
import DonutCard from '../showcase/components/DonutCard.vue'
const data = ref(null), error = ref(''), loading = ref(false)
let request = 0
async function load() {
  const id = ++request
  data.value = null; error.value = ''; loading.value = true
  try {
    if (!company.value) throw new Error('No Company is available to your account.')
    const selected = company.value
    const response = await apiGet('/api/method/sidra_realestate.api.crm_live.get_crm_live', { company: selected })
    if (response?.message?.company !== selected) throw new Error('The server returned another Company.')
    if (id === request) data.value = response.message
  } catch (e) { if (id === request) error.value = e.message || 'CRM could not be loaded.' }
  finally { if (id === request) loading.value = false }
}
const tones = ['blue', 'teal', 'amber', 'purple', 'sky', 'orange', 'green', 'rose']
const chart = (group, key, title, list) => ({ title, kind: 'count', centre: 'records', segments: Object.entries(group[key] || {}).map(([label, value], i) => ({ label, value, tone: tones[i % tones.length], to: { name: listRoute(list) } })) })
watch(company, load, { immediate: true })
onBeforeUnmount(() => ++request)
</script>
<template>
  <section class="page">
    <header class="bj-head"><div><h1 class="page__title">CRM dashboard</h1><p class="bj-sub">Live records for {{ company }} · leads, opportunities and acquisition channels</p></div><div class="bj-toolbar"><CompanyPicker /><button class="bj-btn" :disabled="loading" @click="load">Refresh</button><RouterLink v-if="canCreate('leads')" class="bj-btn bj-btn--primary" :to="{ name: 'leads-new' }">New lead</RouterLink></div></header>
    <SectionTabs section="customers" current="crm" />
    <StatePanel v-if="loading" title="Loading CRM…" />
    <StatePanel v-else-if="error" title="CRM could not be loaded" :message="error" />
    <template v-else-if="data">
      <section v-for="key in ['leads', 'opportunities']" :key="key" class="crm-section">
        <template v-if="data[key]?.available">
          <KpiTile :tile="{ label: key === 'leads' ? 'Leads' : 'Opportunities', value: data[key].total, kind: 'count', tone: key === 'leads' ? 'blue' : 'teal', to: { name: listRoute(key) } }" />
          <p v-if="!data[key].total" class="bj-note">No {{ key }} are recorded for this Company yet.</p>
          <div v-else class="crm-charts"><DonutCard :widget="chart(data[key], 'status_counts', key === 'leads' ? 'Leads by status' : 'Opportunities by status', key)" /><DonutCard :widget="chart(data[key], 'channel_counts', key === 'leads' ? 'Lead channels' : 'Opportunity channels', key)" /></div>
        </template>
        <StatePanel v-else :title="key === 'leads' ? 'Leads' : 'Opportunities'" :message="data[key]?.reason || 'Unavailable'" />
      </section>
    </template>
    <article class="bj-card"><h2>Email, WhatsApp and other channels</h2><p>Choose a Source on a lead or opportunity to record how they found Sidra: Email, WhatsApp, Phone, Website, Walk-in, Referral, Facebook or Instagram. Existing sources remain available.</p><p>Open a lead, customer or contact to use its saved email or phone number. WhatsApp needs a country code. External messages are not synced into Berjaya.</p><RouterLink v-if="canRead('leads')" class="bj-link" :to="{ name: listRoute('leads') }">Open leads →</RouterLink></article>
  </section>
</template>
<style scoped>.crm-section { margin-bottom: 20px; display: grid; gap: 16px; } .crm-charts { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 16px; } article p { margin: 12px 0; color: var(--bj-muted); } @media(max-width: 700px) { .crm-charts { grid-template-columns: minmax(0,1fr); } }</style>
