<script setup>
import { computed, ref, watch } from 'vue'
import { apiGet, apiPost } from '../api'
import { recordRoute } from '../records'
import FormField from './FormField.vue'
const props = defineProps({ doctype: String, name: String, reloadKey: { default: 0 } })
const emit = defineEmits(['changed'])
const data = ref(null), error = ref(''), busy = ref(false), kind = ref('Contact'), target = ref(''), primary = ref(false)
const isCustomer = computed(() => props.doctype === 'Customer')
const targetType = computed(() => isCustomer.value ? kind.value : 'Customer')
let request = 0
async function load() {
  const id = ++request; data.value = null; error.value = ''
  try { const r = await apiGet('/api/method/sidra_realestate.api.customer_connections.get_connections', { doctype: props.doctype, name: props.name }); if (id === request) data.value = r.message }
  catch(e) { if (id === request) error.value = e.message }
}
async function link(operation = 'link', row = null, makePrimary = primary.value) {
  busy.value = true; error.value = ''
  const type = row?.doctype || targetType.value, name = row?.name || target.value
  try {
    await apiPost('sidra_realestate.api.customer_connections.link_customer', {
      customer: isCustomer.value ? props.name : name,
      doctype: isCustomer.value ? type : props.doctype,
      name: isCustomer.value ? name : props.name, operation, primary: makePrimary ? 1 : 0,
    })
    target.value = ''; primary.value = false; await load(); emit('changed')
  } catch(e) { error.value = e.message } finally { busy.value = false }
}
watch(kind, () => { target.value = '' })
watch(() => [props.doctype, props.name, props.reloadKey], load, { immediate: true })
const keyFor = type => ({ Customer: 'customers', Contact: 'contacts', Address: 'addresses' })[type]
</script>
<template>
  <section class="bj-section"><h2>Customer connections</h2><div class="bj-card">
    <p v-if="error" role="alert">{{ error }}</p>
    <template v-if="data">
      <p v-if="!data.rows.length">No linked records available.</p>
      <ul><li v-for="row in data.rows" :key="row.doctype + row.name">
        <RouterLink class="bj-link" :to="recordRoute(keyFor(row.doctype), row.name)">{{ row.doctype }}: {{ row.name }}</RouterLink>
        <span v-if="row.primary"> · Primary</span>
        <template v-if="data.can_write"><button v-if="isCustomer && !row.primary" class="bj-btn" :disabled="busy" @click="link('link', row, true)">Make primary</button><button class="bj-btn" :disabled="busy" @click="link('unlink', row, false)">Unlink</button></template>
      </li></ul>
      <form v-if="data.can_write" class="bj-toolbar" @submit.prevent="link()">
        <label v-if="isCustomer">Type<select v-model="kind" class="bj-select"><option>Contact</option><option>Address</option></select></label>
        <FormField v-model="target" :field="{ fieldname: 'connection', label: `Link ${targetType}`, fieldtype: 'Link', options: targetType }" editable required />
        <label><input v-model="primary" type="checkbox" /> Make primary for customer</label>
        <button class="bj-btn" :disabled="busy || !target">Link</button>
        <RouterLink v-if="isCustomer" class="bj-btn" :to="{ name: `${keyFor(kind)}-new`, query: { link_customer: name } }">New {{ kind }}</RouterLink>
      </form>
    </template>
  </div></section>
</template>
<style scoped>li { margin: 12px 0; overflow-wrap: anywhere; } label { display:grid; gap:6px; font-size:13px; }</style>
