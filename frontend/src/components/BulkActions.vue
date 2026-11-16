<script setup>
import { computed, ref, watch } from 'vue'
import { apiGet, apiPost } from '../api'
import { typed } from '../forms'
import FormField from './FormField.vue'
const props = defineProps({ doctype: String, rows: Array, loading: Boolean })
const selected = defineModel({ default: () => [] })
const emit = defineEmits(['changed'])
const options = ref(null), error = ref(''), busy = ref(false), operation = ref('assign'), field = ref(''), value = ref(''), user = ref(''), done = ref(''), printHtml = ref(''), printFrame = ref(null)
const chosen = computed(() => options.value?.fields.find(f => f.fieldname === field.value))
let request = 0
async function review() {
  const id = ++request; busy.value = true; error.value = ''; done.value = ''; options.value = null
  try {
    const r = await apiGet('/api/method/sidra_realestate.api.record_operations.bulk_options', { doctype: props.doctype, names: selected.value })
    if (id === request) {
      options.value = r.message
      operation.value = r.message.can_assign ? 'assign' : r.message.fields.length ? 'update' : 'print'
      field.value = ''; value.value = ''
    }
  } catch(e) { if (id === request) error.value = e.message }
  finally { if (id === request) busy.value = false }
}
async function run() {
  busy.value = true; error.value = ''; printHtml.value = ''
  try {
    const r = await apiPost('sidra_realestate.api.record_operations.bulk_action', {
      doctype: props.doctype, records: options.value.records, operation: operation.value,
      field: field.value, value: chosen.value ? typed(chosen.value, value.value) : null, user: user.value,
    })
    if (operation.value === 'print') printHtml.value = r.html
    else { done.value = `${selected.value.length} records ${operation.value === 'assign' ? 'assigned' : 'updated'}.`; selected.value = []; options.value = null; emit('changed') }
  } catch(e) { error.value = e.message }
  finally { busy.value = false }
}
function selectLoaded() { selected.value = props.rows.slice(0, 50).map(r => r.name) }
watch(selected, () => { ++request; options.value = null; busy.value = false; printHtml.value = ''; error.value = '' }, { deep: true })
watch(() => props.loading, loading => { if (loading) selected.value = [] })
watch(() => props.rows, rows => { const names = new Set(rows.map(r => r.name)); selected.value = selected.value.filter(n => names.has(n)) })
watch(field, () => { value.value = '' })
</script>
<template>
  <section v-if="rows.length" class="bj-card bulk" aria-label="Bulk record actions">
    <div class="bj-toolbar"><strong>{{ selected.length }} selected</strong><button class="bj-btn" :disabled="loading || busy" @click="selectLoaded">Select loaded records (up to 50)</button><button class="bj-btn" :disabled="busy || !selected.length" @click="selected = []">Clear selection</button><button class="bj-btn" :disabled="loading || busy || !selected.length || selected.length > 50" @click="review">Review bulk actions</button></div>
    <p v-if="error" role="alert">{{ error }} Refresh the records and review the selection before retrying.</p><p v-if="done" role="status">{{ done }}</p>
    <form v-if="options" class="bulk-form" @submit.prevent="run">
      <label>Action<select aria-label="Bulk action" v-model="operation" class="bj-select"><option v-if="options.can_assign" value="assign">Assign</option><option v-if="options.fields.length" value="update">Update field</option><option v-if="options.can_print" value="print">Print</option></select></label>
      <FormField v-if="operation === 'assign'" v-model="user" :field="{ fieldname: 'bulk_user', label: 'Assign to', fieldtype: 'Link', options: 'User' }" editable required />
      <template v-if="operation === 'update'"><label>Field<select aria-label="Bulk field" v-model="field" class="bj-select"><option value="">Choose field</option><option v-for="f in options.fields" :key="f.fieldname" :value="f.fieldname">{{ f.label }}</option></select></label><FormField v-if="chosen" v-model="value" :field="chosen" editable /></template>
      <p>Applies to {{ selected.length }} selected records. Each record's permissions and validation rules apply.</p>
      <button class="bj-btn bj-btn--primary" :disabled="busy || (operation === 'assign' && (!user || !options.can_assign)) || (operation === 'update' && !chosen) || (operation === 'print' && !options.can_print)">Confirm {{ operation }}</button>
    </form>
    <div v-if="printHtml"><button class="bj-btn" @click="printFrame.contentWindow.print()">Print selected records / Save PDF</button><iframe ref="printFrame" title="Selected records print preview" sandbox="allow-same-origin allow-modals" :srcdoc="printHtml" /></div>
  </section>
</template>
<style scoped>.bulk { margin: 16px 0; }.bulk-form { display:flex;flex-wrap:wrap;align-items:end;gap:12px;margin-top:16px; } label { display:grid;gap:6px; } iframe { width:100%;height:500px;border:1px solid var(--bj-line);margin-top:12px; }</style>
