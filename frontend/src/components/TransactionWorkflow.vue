<script setup>
import { computed, ref, watch, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { boot } from '../boot'
import { RECORDS } from '../records'
import { sectionLinks } from '../navigation'
import { loadForm } from '../forms'
const route = useRoute()
const section = computed(() => route.meta.section || route.name)
const line = computed(() => ({ construction: 'construction-hub', properties: 'realestate', sales: 'realestate', contracts: 'realestate', collections: 'realestate', finance: 'finance-hub' })[section.value] || section.value)
const links = computed(() => sectionLinks(line.value, boot.lists, boot.nav))
const key = computed(() => route.meta.list || (route.name === 'construction-detail' ? 'jobs' : null))
const form = ref(null), loading = ref(false), reason = ref('')
let request = 0
const steps = computed(() => {
  if (section.value === 'construction') return ['Capture the job and billing stages', 'Create and issue a quotation', 'Record client acceptance', 'General Manager approves the contract', 'Record inspections, variations and stage completion']
  if (section.value === 'customers') return ['Capture the lead and source channel', 'Contact the lead and update its status', 'Create an opportunity', 'Convert to a customer and verify KYC']
  if (['sales', 'properties', 'contracts', 'collections'].includes(section.value)) return ['Choose the buyer and available unit', 'Reserve and prepare a quotation', 'Register or generate the contract', 'Confirm using the record’s permitted actions', 'Review installments and title records']
  return ['Open a saved record', 'Review its details', 'Use the actions permitted to your role']
})
watch(() => route.fullPath, async () => {
  const id = ++request
  form.value = null; reason.value = ''; loading.value = false
  const config = RECORDS[key.value]
  if (!route.params.name || !config?.form || route.meta.create) return
  loading.value = true
  try { const result = await loadForm(config.doctype, route.params.name); if (id === request) form.value = result }
  catch { if (id === request) reason.value = 'The record’s permitted actions could not be loaded.' }
  finally { if (id === request) loading.value = false }
}, { immediate: true })
onBeforeUnmount(() => ++request)
function showActions() { document.querySelector('.ra')?.scrollIntoView({ behavior: 'smooth', block: 'center' }) }
</script>
<template>
  <section class="guide">
    <h2>{{ route.params.name || 'Transaction workflow' }}</h2>
    <p v-if="loading">Loading record actions…</p><p v-else-if="reason">{{ reason }}</p>
    <template v-if="form">
      <p><strong>Recorded status:</strong> {{ form.values.status || ({ 0: 'Draft', 1: 'Submitted', 2: 'Cancelled' })[form.values.docstatus] || 'Saved' }}</p>
      <h3>Available on this record</h3>
      <ul><li v-for="action in form.actions" :key="action.key || action.label">{{ action.label }}</li><li v-if="form.permissions.write">Edit</li><li v-if="form.permissions.submit">Submit</li><li v-if="form.permissions.cancel">Cancel</li></ul>
      <button v-if="!String(route.name).endsWith('-edit')" class="bj-btn" @click="showActions">Go to record actions</button>
    </template>
    <h3>Process guide</h3><p class="bj-sub">Guidance only. Completion and approval come from each saved record.</p>
    <ol><li v-for="step in steps" :key="step">{{ step }}</li></ol>
    <h3>Transactions and reports</h3><RouterLink v-for="link in links" :key="link.label" :to="link.to" class="guide-link">{{ link.label }} →</RouterLink>
  </section>
</template>
<style scoped>.guide { padding: 16px; overflow-wrap: anywhere; } h2 { font-size: 16px; } h3 { font-size: 13px; margin: 20px 0 10px; } p,li { font-size: 13px; line-height: 1.6; } ol,ul { padding-left: 20px; } li { margin-bottom: 10px; } .guide-link { display: block; padding: 10px; border: 1px solid var(--bj-line); border-radius: 8px; margin: 6px 0; color: var(--bj-terracotta); font-size: 13px; }</style>
