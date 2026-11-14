<script setup>
import { computed, ref } from 'vue'

import { apiGet, apiUpload } from '../api'
import { dateText, dateTimeText, fileLink, money, percentText } from '../format'
import { LONG_TEXT, NUMERIC } from '../forms'

// One field of a record form. It draws the value and an input that fits the field's type; it
// checks nothing itself (the server does, on save).
const props = defineProps({
  field: { type: Object, required: true },
  modelValue: { default: null },
  editable: { type: Boolean, default: false },
  required: { type: Boolean, default: false },
  currency: { type: String, default: null },
  doctype: { type: String, default: null }, // for uploads: the record the file belongs to
  docname: { type: String, default: null },
  compact: { type: Boolean, default: false }, // inside a table row: no label above
  label: { type: String, default: null }, // accessible name, when compact
})
const emit = defineEmits(['update:modelValue'])

const id = `ff-${Math.random().toString(36).slice(2, 9)}`
const type = computed(() => props.field.fieldtype)
// Select options are plain values, or { value, label } pairs (e.g. the stages to certify).
const options = computed(() =>
  (Array.isArray(props.field.options) ? props.field.options : []).map((option) =>
    option && typeof option === 'object' ? { value: option.value, label: option.label } : { value: option, label: option || '—' },
  ),
)
const name = computed(() => props.label || props.field.label)
const value = computed({
  get: () => props.modelValue,
  set: (next) => emit('update:modelValue', next),
})

// Link suggestions from Frappe's own permission-checked search; the server validates the value.
const suggestions = ref([])
let searchTimer = null
let searchRequest = 0
function search(text) {
  if (type.value !== 'Link' || !props.field.options) return
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    const id = ++searchRequest
    try {
      const response = await apiGet('/api/method/frappe.desk.search.search_link', {
        doctype: props.field.options,
        txt: text || '',
        page_length: 20,
        filters: props.field.link_filters || undefined,
      })
      if (id === searchRequest) suggestions.value = Array.isArray(response.message) ? response.message : []
    } catch {
      if (id === searchRequest) suggestions.value = []
    }
  }, 200)
}

// Datetime: Frappe sends "YYYY-MM-DD HH:MM:SS"; the browser's box uses "YYYY-MM-DDTHH:MM".
const datetimeBox = computed({
  get: () => (value.value ? String(value.value).replace(' ', 'T').slice(0, 16) : ''),
  set: (next) => (value.value = next ? next.replace('T', ' ') + ':00' : ''),
})

const uploading = ref(false)
const uploadError = ref('')
async function upload(event) {
  const file = event.target.files?.[0]
  if (!file || !props.docname) return
  uploading.value = true
  uploadError.value = ''
  try {
    const saved = await apiUpload(file, { doctype: props.doctype, docname: props.docname, fieldname: props.field.fieldname, isPrivate: true })
    if (!saved?.file_url) throw new Error('The server did not return the uploaded file.')
    value.value = saved.file_url
  } catch (err) {
    uploadError.value = err.message || 'The file could not be uploaded.'
  } finally {
    uploading.value = false
    event.target.value = ''
  }
}

const display = computed(() => {
  const v = props.modelValue
  if (type.value === 'Check') return v ? 'Yes' : 'No'
  if (v === null || v === undefined || v === '') return '—'
  if (type.value === 'Currency') return money(v, props.currency)
  if (type.value === 'Percent') return percentText(v)
  if (type.value === 'Date') return dateText(v)
  if (type.value === 'Datetime') return dateTimeText(v)
  if (type.value === 'Geolocation') return 'Map location recorded'
  return String(v)
})
</script>

<template>
  <div class="ff" :class="{ 'ff--compact': compact, 'ff--wide': !compact && LONG_TEXT.has(type) }">
    <label v-if="!compact" class="ff__label" :for="id">
      {{ field.label }}<span v-if="required && editable" class="ff__req" aria-hidden="true"> *</span>
    </label>

    <template v-if="editable">
      <label v-if="type === 'Check'" class="ff__check">
        <input :id="id" v-model="value" type="checkbox" :aria-label="name" />
        <span v-if="!compact">{{ field.description || 'Yes' }}</span>
      </label>
      <select v-else-if="type === 'Select'" :id="id" v-model="value" class="bj-select ff__input" :aria-label="name" :required="required">
        <option v-if="!options.some((option) => option.value === '')" value="" disabled>Choose…</option>
        <option v-for="option in options" :key="option.value" :value="option.value">{{ option.label }}</option>
      </select>
      <template v-else-if="type === 'Link'">
        <input
          :id="id"
          v-model="value"
          class="bj-input ff__input"
          :list="`${id}-list`"
          :aria-label="name"
          :required="required"
          autocomplete="off"
          @focus="search(value)"
          @input="search(value)"
        />
        <datalist :id="`${id}-list`">
          <option v-for="item in suggestions" :key="item.value" :value="item.value">{{ item.description }}</option>
        </datalist>
      </template>
      <textarea v-else-if="LONG_TEXT.has(type)" :id="id" v-model="value" class="bj-input ff__input ff__text" :aria-label="name" rows="3" />
      <input v-else-if="type === 'Date'" :id="id" v-model="value" class="bj-input ff__input" type="date" :aria-label="name" :required="required" />
      <input v-else-if="type === 'Datetime'" :id="id" v-model="datetimeBox" class="bj-input ff__input" type="datetime-local" :aria-label="name" />
      <input v-else-if="type === 'Time'" :id="id" v-model="value" class="bj-input ff__input" type="time" step="1" :aria-label="name" />
      <input
        v-else-if="NUMERIC.has(type)"
        :id="id"
        v-model="value"
        class="bj-input ff__input"
        :inputmode="type === 'Int' ? 'numeric' : 'decimal'"
        :aria-label="name"
        :required="required"
        autocomplete="off"
      />
      <div v-else-if="type === 'Attach' || type === 'Attach Image'" class="ff__attach">
        <a v-if="fileLink(value)" class="bj-link" :href="fileLink(value)" target="_blank" rel="noopener">{{ String(value).split('/').pop() }}</a>
        <span v-else class="bj-muted">No file</span>
        <template v-if="docname">
          <input :id="id" type="file" :aria-label="name" :disabled="uploading" @change="upload" />
          <span v-if="uploading" class="bj-muted" role="status">Uploading…</span>
        </template>
        <span v-else class="bj-muted">Save first, then attach the file.</span>
        <span v-if="uploadError" class="ff__error" role="alert">{{ uploadError }}</span>
      </div>
      <input v-else :id="id" v-model="value" class="bj-input ff__input" :type="type === 'Phone' ? 'tel' : 'text'" :aria-label="name" :required="required" autocomplete="off" />
    </template>

    <p v-else :id="id" class="ff__value" :class="{ 'bj-muted': display === '—' }">
      <a v-if="(type === 'Attach' || type === 'Attach Image') && fileLink(modelValue)" class="bj-link" :href="fileLink(modelValue)" target="_blank" rel="noopener">{{ String(modelValue).split('/').pop() }}</a>
      <template v-else>{{ display }}</template>
    </p>

    <p v-if="field.description && type !== 'Check' && !compact" class="ff__help">{{ field.description }}</p>
  </div>
</template>

<style scoped>
.ff {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}
.ff--wide {
  grid-column: 1 / -1;
}
.ff__label {
  font-size: 13px;
  font-weight: 500;
  color: var(--bj-muted);
}
.ff__req {
  color: var(--bj-state-blocked);
}
.ff__input {
  width: 100%;
}
.ff--compact .ff__input {
  min-width: 110px;
}
.ff__text {
  min-height: 88px;
  resize: vertical;
}
.ff__value {
  margin: 0;
  min-height: 24px;
  overflow-wrap: anywhere;
}
.ff__check {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
  cursor: pointer;
}
.ff__check input {
  width: 20px;
  height: 20px;
}
.ff__attach {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  min-height: 44px;
}
.ff__help {
  margin: 0;
  font-size: 12px;
  color: var(--bj-muted);
}
.ff__error {
  color: var(--bj-state-blocked);
  font-size: 13px;
}
</style>
