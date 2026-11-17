<script setup>
import { ref, watch } from 'vue'
import { apiGet, apiPost } from '../api'
import FormField from './FormField.vue'
const props = defineProps({ doctype: String, name: String, reloadKey: { default: 0 } })
const tools = ref(null), error = ref(''), user = ref(''), description = ref(''), date = ref(''), busy = ref(false)
let request = 0
async function load() {
 const id = ++request; error.value = ''
 try { const r = await apiGet('/api/method/sidra_realestate.api.record_tools.get_tools', { doctype: props.doctype, name: props.name }); if (id === request) tools.value = r.message }
 catch(e) { if (id === request) { tools.value = null; error.value = e.message } }
}
async function assign() {
 busy.value = true; error.value = ''
 try { await apiPost('sidra_realestate.api.record_tools.assign', { doctype: props.doctype, name: props.name, user: user.value, description: description.value, due_date: date.value || null }); user.value = ''; await load() }
 catch(e) { error.value = e.message } finally { busy.value = false }
}
const print = () => `/printview?doctype=${encodeURIComponent(props.doctype)}&name=${encodeURIComponent(props.name)}&trigger_print=1`
watch(() => [props.doctype, props.name, props.reloadKey], load, { immediate: true })
</script>
<template>
 <section class="bj-section"><h2>Record tools</h2><div class="bj-card">
 <p v-if="error" role="alert">{{ error }}</p>
 <template v-if="tools">
 <a v-if="tools.can_print" class="bj-btn" :href="print()" target="_blank" rel="noopener">Print / Save as PDF</a>
 <h3>Assignments</h3><ul><li v-for="a in tools.assignments" :key="a.name">{{ a.allocated_to }} · {{ a.description }} <span v-if="a.date">· Due {{ a.date }}</span></li></ul><p v-if="!tools.assignments.length">No open assignments.</p>
 <form v-if="tools.can_assign" class="assign" @submit.prevent="assign"><FormField v-model="user" :field="{ fieldname: 'user', label: 'Assign to', fieldtype: 'Link', options: 'User' }" editable required /><label>Task<input v-model="description" class="bj-input" maxlength="500" /></label><label>Due date<input v-model="date" class="bj-input" type="date" /></label><button class="bj-btn" :disabled="busy || !user">Assign</button></form>

 </template></div></section>
</template>
<style scoped>h3,details { margin-top: 18px; } .assign { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;align-items:end;margin:16px 0; } label { display:grid;gap:6px;font-size:13px; } article { border-top:1px solid var(--bj-line);padding:10px 0;overflow-wrap:anywhere; } summary { cursor:pointer;min-height:44px; }</style>
