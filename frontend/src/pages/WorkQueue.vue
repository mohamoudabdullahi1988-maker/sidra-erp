<script setup>
import { ref, onMounted } from 'vue'
import { apiGet, apiPost } from '../api'
import { RECORDS, recordRoute } from '../records'
const data = ref(null), error = ref(''), busy = ref(false)
async function load() { error.value = ''; busy.value = true; try { const r = await apiGet('/api/method/sidra_realestate.api.work_queue.get_queue'); data.value = r.message } catch(e) { error.value = e.message } finally { busy.value = false } }
async function action(method, name) { busy.value = true; error.value = ''; try { await apiPost('sidra_realestate.api.work_queue.' + method, { name }); await load() } catch(e) { error.value = e.message } finally { busy.value = false } }
function link(task) { const key = Object.keys(RECORDS).find(k => RECORDS[k].doctype === task.reference_type); return key ? recordRoute(key, task.reference_name) : null }
onMounted(load)
</script>
<template><section class="page"><header class="bj-head"><div><h1 class="page__title">My work</h1><p class="bj-sub">Your open assignments and latest notifications (up to 100 each).</p></div><button class="bj-btn" :disabled="busy" @click="load">Refresh</button></header><p v-if="error" role="alert">{{ error }}</p><template v-if="data"><h2>Open tasks</h2><p v-if="!data.tasks.length">No open assignments.</p><article v-for="task in data.tasks" :key="task.name" class="bj-card item"><p class="task">{{ task.description }}</p><p>{{ task.priority }} · {{ task.date ? `Due ${task.date}` : 'No due date' }}</p><RouterLink v-if="link(task)" class="bj-link" :to="link(task)">Open {{ task.reference_name }} →</RouterLink><button class="bj-btn" :disabled="busy" @click="action('complete_task', task.name)">Mark complete</button></article><h2>Notifications</h2><p v-if="!data.notifications.length">No notifications.</p><article v-for="n in data.notifications" :key="n.name" class="bj-card item"><strong>{{ n.read ? 'Read' : 'Unread' }}</strong><p>{{ n.subject }}</p><p>{{ n.creation }}</p><button v-if="!n.read" class="bj-btn" :disabled="busy" @click="action('read_notification', n.name)">Mark read</button></article></template></section></template>
<style scoped>h2 { margin:24px 0 14px; } .item { margin-bottom:12px;display:grid;gap:10px;overflow-wrap:anywhere; } .task { white-space:pre-wrap; }</style>
