<script setup>
import { ref, watch } from 'vue'
import { apiGet, apiPost, apiUpload } from '../api'
import { fileLink } from '../format'
const props = defineProps({ doctype: String, name: String })
const rows = ref([]), more = ref(false), canSend = ref(false), files = ref([]), selected = ref([]), recipients = ref(''), cc = ref(''), subject = ref(''), content = ref(''), reply = ref(null), busy = ref(false), error = ref(''), notice = ref('')
let generation = 0
async function load(append = false) {
 const id = ++generation; error.value = ''
 try {
  const [messages,extras] = await Promise.all([apiGet('/api/method/sidra_realestate.api.conversations.messages', { doctype: props.doctype, name: props.name, start: append ? rows.value.length : 0 }),apiGet('/api/method/sidra_realestate.api.record_extras.get_extras',{doctype:props.doctype,name:props.name})])
  if (id !== generation) return
  rows.value = append ? [...rows.value,...messages.message.rows] : messages.message.rows; more.value = messages.message.has_more; canSend.value = messages.message.can_send; files.value = extras.message.attachments
 } catch(e) { if (id === generation) error.value = e.message }
}
function replyTo(row) { reply.value = row.name; recipients.value = row.direction === 'Received' ? row.sender : row.recipients; subject.value = /^re:/i.test(row.subject) ? row.subject : 'Re: '+row.subject; cc.value = ''; content.value = ''; selected.value = [] }
async function send() {
 busy.value = true; error.value = ''; notice.value = ''
 try { const result = (await apiPost('sidra_realestate.api.conversations.send',{doctype:props.doctype,name:props.name,recipients:recipients.value,cc:cc.value,subject:subject.value,content:content.value,attachments:selected.value,in_reply_to:reply.value})); notice.value = 'Email submitted to the outgoing queue. Refresh to check delivery.' + (result.emails_not_sent_to ? ` Not sent to: ${result.emails_not_sent_to}` : ''); content.value = ''; reply.value = null; selected.value = []; await load() }
 catch(e) { error.value = e.message } finally { busy.value = false }
}
async function upload(event) {
 const file = event.target.files?.[0]; if (!file) return
 busy.value = true; error.value = ''
 try { await apiUpload(file,{doctype:props.doctype,docname:props.name,fieldname:'',isPrivate:true}); await load() } catch(e) {error.value = e.message} finally {busy.value=false;event.target.value=''}
}
watch(()=>[props.doctype,props.name],()=>{ rows.value=[]; files.value=[];selected.value=[];recipients.value='';cc.value='';subject.value='';content.value='';reply.value=null;notice.value='';canSend.value=false; load() },{immediate:true})
</script>
<template><section class="bj-section"><h2>Email conversations</h2><div class="bj-card"><p v-if="error" role="alert">{{error}}</p><p v-if="notice" role="status">{{notice}}</p><button class="bj-btn" :disabled="busy" @click="load()">Refresh delivery history</button><details v-if="canSend" :open="!!reply"><summary>{{ reply ? 'Reply to email' : 'Compose email' }}</summary><form @submit.prevent="send"><label>To<input v-model="recipients" class="bj-input" required placeholder="Recipient email addresses" /></label><label>CC<input v-model="cc" class="bj-input" /></label><label>Subject<input v-model="subject" class="bj-input" required maxlength="500" /></label><label>Message<textarea v-model="content" class="bj-input" rows="6" required maxlength="100000" /></label><fieldset><legend>Attachments to send</legend><p v-if="!files.length">No files attached to this record.</p><label v-for="file in files" :key="file.name" class="file"><input v-model="selected" type="checkbox" :value="file.name" />{{file.file_name}}</label><label>Upload attachment<input type="file" :disabled="busy" @change="upload" /></label></fieldset><div><button type="submit" class="bj-btn bj-btn--primary" :disabled="busy">{{busy ? 'Working…' : 'Send email'}}</button><button v-if="reply" type="button" class="bj-btn" @click="reply=null">Compose new instead</button></div></form></details><p v-else class="bj-muted">Your role cannot send email from this record.</p><p v-if="!rows.length && !error">No email conversations linked to this record.</p><article v-for="row in rows" :key="row.name"><h3>{{ row.subject }}</h3><p>{{row.direction}} · {{row.on}} · {{row.status || 'Delivery status not available'}}</p><p>From: {{row.sender}} · To: {{row.recipients}}<span v-if="row.cc"> · CC: {{row.cc}}</span></p><details><summary>Read message</summary><p class="body">{{row.content}}</p><ul><li v-for="file in row.attachments" :key="file.name"><a v-if="fileLink(file.file_url)" :href="fileLink(file.file_url)" target="_blank" rel="noopener">{{file.file_name}}</a></li></ul></details><button v-if="canSend" class="bj-btn" :disabled="busy" @click="replyTo(row)">Reply</button></article><button v-if="more" class="bj-btn" :disabled="busy" @click="load(true)">Older emails</button></div></section></template>
<style scoped>form,label { display:grid;gap:8px } form { gap:14px;margin:16px 0 }.file { display:flex;align-items:center;gap:8px }.body { white-space:pre-wrap;overflow-wrap:anywhere } article { border-top:1px solid var(--bj-line);padding:16px 0;overflow-wrap:anywhere } summary { cursor:pointer;min-height:44px;padding:10px 0 } input,textarea { max-width:100% } fieldset { min-width:0 }</style>
