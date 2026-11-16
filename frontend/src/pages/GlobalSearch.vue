<script setup>
import { ref } from 'vue'
import { apiGet } from '../api'
import { recordRoute } from '../discovery'
const query = ref(''), groups = ref([]), error = ref(''), busy = ref(false), searched = ref(false)
let lastQuery = ''
async function search(group = null) {
 busy.value = true; error.value = ''
 try {
  const text = group ? lastQuery : query.value.trim()
  const result = (await apiGet('/api/method/sidra_realestate.api.discovery.search', { text, doctype: group?.doctype, start: group?.rows.length ?? 0 })).message
  if (group) { group.rows.push(...(result[0]?.rows ?? [])); group.has_more = result[0]?.has_more ?? false }
  else { groups.value = result; lastQuery = text; searched.value = true }
 } catch (e) { error.value = e.message } finally { busy.value = false }
}
</script>
<template><section class="bj-section"><h1>Search all modules</h1><form class="search" @submit.prevent="search()"><label>Record ID, name or reference<input v-model="query" class="bj-input" minlength="2" maxlength="100" required /></label><button class="bj-btn" :disabled="busy">Search</button></form><p v-if="error" role="alert">{{ error }}</p><p v-if="busy" role="status">Searching…</p><p v-else-if="searched && !groups.length">No matching records you can access.</p><section v-for="group in groups" :key="group.doctype" class="bj-card"><h2>{{ group.doctype }}</h2><ul><li v-for="row in group.rows" :key="row.name"><RouterLink v-if="recordRoute(group.doctype, row.name)" :to="recordRoute(group.doctype, row.name)">{{ row.name }}</RouterLink><span v-else>{{ row.name }}</span></li></ul><button v-if="group.has_more" class="bj-btn" :disabled="busy" @click="search(group)">More {{ group.doctype }} results</button></section></section></template>
<style scoped>.search { display:flex;gap:12px;align-items:end;flex-wrap:wrap;margin-bottom:20px } label { display:grid;gap:8px;flex:1;min-width:200px } li { padding:8px;overflow-wrap:anywhere } .bj-card { margin:12px 0 }</style>
