<script setup>
import { ref, watch } from 'vue'

import { apiGet, apiPost, apiUpload } from '../api'
import { dateTimeText, fileLink } from '../format'

// Attachments and comments on a record (Desk's sidebar and timeline, G23). The server decides who
// may see, attach, remove and comment; this panel draws what it says.
const props = defineProps({
  doctype: { type: String, required: true },
  name: { type: String, required: true },
  reloadKey: { default: 0 },
})

const API = 'sidra_realestate.api.record_extras.'
const extras = ref(null)
const error = ref('')
const text = ref('')
const busy = ref(false)
const actionError = ref('')
let request = 0

async function load() {
  const id = ++request
  error.value = ''
  try {
    const response = await apiGet('/api/method/' + API + 'get_extras', { doctype: props.doctype, name: props.name })
    if (id === request) extras.value = response.message
  } catch (err) {
    if (id === request) {
      extras.value = null
      error.value = err.message || 'Attachments and comments could not be loaded.'
    }
  }
}

async function comment() {
  if (!text.value.trim()) return
  busy.value = true
  actionError.value = ''
  try {
    await apiPost(API + 'add_comment', { doctype: props.doctype, name: props.name, text: text.value })
    text.value = ''
    await load()
  } catch (err) {
    actionError.value = err.message || 'The comment was not saved.'
  } finally {
    busy.value = false
  }
}

async function attach(event) {
  const file = event.target.files?.[0]
  if (!file) return
  busy.value = true
  actionError.value = ''
  try {
    await apiUpload(file, { doctype: props.doctype, docname: props.name, fieldname: '', isPrivate: true })
    await load()
  } catch (err) {
    actionError.value = err.message || 'The file was not attached.'
  } finally {
    busy.value = false
    event.target.value = ''
  }
}

async function remove(row) {
  busy.value = true
  actionError.value = ''
  try {
    await apiPost(API + 'remove_attachment', { doctype: props.doctype, name: props.name, file: row.name })
    await load()
  } catch (err) {
    actionError.value = err.message || 'The file was not removed.'
  } finally {
    busy.value = false
  }
}

const confirming = ref(null)
watch(() => [props.doctype, props.name, props.reloadKey], load, { immediate: true })
</script>

<template>
  <section class="bj-section rx" aria-label="Attachments and comments">
    <h2>Attachments and comments</h2>
    <div class="page__card bj-card">
      <p v-if="error" class="bj-muted" role="status">{{ error }}</p>
      <template v-else-if="extras">
        <div class="rx__files">
          <p v-if="!extras.attachments.length" class="bj-muted">No files attached.</p>
          <ul v-else class="rx__list">
            <li v-for="row in extras.attachments" :key="row.name" class="rx__file">
              <span class="lucide-paperclip" aria-hidden="true" />
              <a v-if="fileLink(row.file_url)" class="bj-link" :href="fileLink(row.file_url)" target="_blank" rel="noopener">{{ row.file_name }}</a>
              <span v-else>{{ row.file_name }}</span>
              <span class="bj-muted rx__meta">
                {{ row.field ? 'in the form' : '' }}{{ row.field ? ' · ' : '' }}{{ row.by }} · {{ dateTimeText(row.on) }}
              </span>
              <template v-if="row.can_remove">
                <button v-if="confirming !== row.name" type="button" class="bj-btn bj-btn--icon" :aria-label="`Remove ${row.file_name}`" :disabled="busy" @click="confirming = row.name">
                  <span class="lucide-trash-2" aria-hidden="true" />
                </button>
                <span v-else class="rx__confirm">
                  <button type="button" class="bj-btn" :disabled="busy" @click="remove(row); confirming = null">Remove</button>
                  <button type="button" class="bj-btn" :disabled="busy" @click="confirming = null">Keep</button>
                </span>
              </template>
            </li>
          </ul>
          <label v-if="extras.can_attach" class="rx__attach">
            <span class="lucide-upload" aria-hidden="true" />
            <span>Attach a file</span>
            <input type="file" aria-label="Attach a file" :disabled="busy" @change="attach" />
          </label>
        </div>

        <form class="rx__comment" @submit.prevent="comment">
          <label class="rx__label" for="rx-comment">Add a comment</label>
          <textarea id="rx-comment" v-model="text" class="bj-input rx__text" rows="2" maxlength="5000" />
          <button type="submit" class="bj-btn bj-btn--primary" :disabled="busy || !text.trim()">Comment</button>
        </form>
        <p v-if="actionError" class="rx__error" role="alert"><span class="lucide-triangle-alert" aria-hidden="true" />{{ actionError }}</p>

        <ol v-if="extras.comments.length" class="rx__timeline">
          <li v-for="row in extras.comments" :key="row.name" :class="{ 'rx__info': row.type === 'Info' }">
            <p class="rx__by"><strong>{{ row.by }}</strong> · {{ dateTimeText(row.on) }}</p>
            <p class="rx__body">{{ row.text }}</p>
          </li>
        </ol>
        <p v-else class="bj-muted">No comments yet.</p>
      </template>
      <p v-else class="bj-muted" role="status">Loading…</p>
    </div>
  </section>
</template>

<style scoped>
.rx__list {
  list-style: none;
  margin: 0 0 12px;
  padding: 0;
}
.rx__file {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 10px;
  min-height: 44px;
  border-bottom: 1px solid var(--bj-line);
}
.rx__meta {
  font-size: 12px;
}
.rx__confirm {
  display: inline-flex;
  gap: 6px;
}
.rx__attach {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 44px;
  padding: 8px 14px;
  font-size: 14px;
  font-weight: 500;
  border: 1px dashed var(--bj-line);
  border-radius: 8px;
  cursor: pointer;
}
.rx__attach input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}
.rx__comment {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px 12px;
  align-items: end;
  margin-top: 16px;
}
.rx__label {
  grid-column: 1 / -1;
  font-size: 13px;
  font-weight: 500;
  color: var(--bj-muted);
}
.rx__text {
  width: 100%;
  min-height: 44px;
  resize: vertical;
}
.rx__error {
  margin: 8px 0 0;
  color: var(--bj-state-blocked);
}
.rx__timeline {
  list-style: none;
  margin: 16px 0 0;
  padding: 0;
}
.rx__timeline li {
  padding: 10px 0;
  border-top: 1px solid var(--bj-line);
}
.rx__info .rx__body {
  color: var(--bj-muted);
}
.rx__by {
  margin: 0 0 4px;
  font-size: 12px;
  color: var(--bj-muted);
}
.rx__body {
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
</style>
