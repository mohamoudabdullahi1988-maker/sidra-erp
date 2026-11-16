<script setup>
import { ref, watch } from 'vue'
import { apiGet } from '../api'
const props = defineProps({doctype:String,name:String,reloadKey:{default:0}})
const rows = ref([]), more = ref(false), busy = ref(false), error = ref(''), versionsVisible = ref(false)
let generation = 0
async function load(append = false) {
 const id = ++generation; busy.value = true; error.value = ''
 try { const data = (await apiGet('/api/method/sidra_realestate.api.activity.timeline',{doctype:props.doctype,name:props.name,start:append ? rows.value.length : 0})).message; if (id !== generation) return; rows.value=append ? [...rows.value,...data.rows] : data.rows; more.value=data.has_more;versionsVisible.value=data.versions_visible }
 catch(e){if(id===generation)error.value=e.message}finally{if(id===generation)busy.value=false}
}
watch(()=>[props.doctype,props.name,props.reloadKey],()=>{rows.value=[];load()},{immediate:true})
</script>
<template><section class="bj-section"><h2>Activity timeline</h2><div class="bj-card"><button class="bj-btn" :disabled="busy" @click="load()">Refresh activity</button><p v-if="error" role="alert">{{error}}</p><p class="bj-muted">Recorded comments, workflow events, emails, attachments and changes, newest first. Changes are available where tracking was enabled.<span v-if="!versionsVisible"> Field change details require write access.</span></p><ol><li v-for="row in rows" :key="row.key"><strong>{{row.kind}}</strong> · {{row.by}} · {{row.on}}<p>{{row.text}}</p></li></ol><p v-if="busy" role="status">Loading activity…</p><button v-if="more" class="bj-btn" :disabled="busy" @click="load(true)">Older activity</button></div></section></template>
<style scoped>ol { padding:0;list-style:none } li { border-bottom:1px solid var(--bj-line);padding:12px 0;overflow-wrap:anywhere } p { white-space:pre-wrap }</style>
