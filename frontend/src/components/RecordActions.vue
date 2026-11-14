<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { ApiError } from '../api'
import FormField from './FormField.vue'
import { changeState, fieldsOf, loadForm, runAction } from '../forms'
import { RECORDS, recordRoute } from '../records'

// What the signed-in user may do with this record, as the server's form says: Edit, Submit,
// Cancel, Delete and the record's own actions (Reserve unit, Verify, ...). Each runs only after
// a confirmation step on the page, and the server checks it again.
const props = defineProps({
  doctype: { type: String, required: true },
  name: { type: String, required: true },
  editRoute: { type: Object, default: null }, // router location of the edit page (null: no Edit button)
  listRoute: { type: Object, default: null }, // where to go after a delete
  reloadKey: { default: 0 }, // change it to reload the form (e.g. after the page reloads the record)
})
const emit = defineEmits(['changed', 'form'])
const router = useRouter()

const form = ref(null)
const pending = ref(null) // { kind: 'state' | 'action', step?, action?, title, message, tone }
const askValues = reactive({})
const busy = ref(false)
const error = ref(null)
const done = ref('')
let request = 0

const canEdit = computed(() => form.value?.permissions.write && fieldsOf(form.value).some((field) => field.editable))
const STEPS = {
  submit: { label: 'Submit', icon: 'lucide-send', tone: 'primary', message: 'Submitting makes this record final. It can then only be cancelled.' },
  cancel: { label: 'Cancel document', icon: 'lucide-ban', tone: 'danger', message: 'Cancelling keeps the record but marks it as no longer in effect.' },
  delete: { label: 'Delete', icon: 'lucide-trash-2', tone: 'danger', message: 'Deleting removes this record. This cannot be undone.' },
}
const steps = computed(() => Object.keys(STEPS).filter((step) => form.value?.permissions[step]))

async function load() {
  const id = ++request
  try {
    const result = await loadForm(props.doctype, props.name)
    if (id === request) {
      form.value = result
      emit('form', result)
    }
  } catch {
    if (id === request) {
      form.value = null
      emit('form', null)
    } // no form: no buttons, the page itself still shows the record
  }
}

function ask(kind, item) {
  // An action that only opens another form (e.g. "New inspection report" on a job).
  if (kind === 'action' && item.navigate) {
    const key = Object.keys(RECORDS).find((name) => RECORDS[name].doctype === item.navigate.doctype && RECORDS[name].form)
    if (key) router.push({ name: `${key}-new`, query: item.navigate.values })
    return
  }
  error.value = null
  done.value = ''
  for (const key of Object.keys(askValues)) delete askValues[key]
  if (kind === 'action') {
    for (const field of item.ask) askValues[field.fieldname] = field.default ?? ''
    pending.value = { kind, action: item, title: item.label, message: item.confirm, tone: item.tone }
  } else {
    pending.value = { kind, step: item, title: STEPS[item].label, message: STEPS[item].message, tone: STEPS[item].tone }
  }
}

async function go() {
  busy.value = true
  error.value = null
  try {
    if (pending.value.kind === 'action') {
      const result = await runAction(form.value, pending.value.action, { ...askValues })
      done.value = result?.message || `${pending.value.title}: done.`
      // An action that made another record (Revise draft) opens it.
      if (result?.open) {
        const key = Object.keys(RECORDS).find((name) => RECORDS[name].doctype === result.open.doctype)
        const target = key && recordRoute(key, result.open.name)
        if (target) {
          pending.value = null
          await router.push(target)
          return
        }
      }
    } else {
      const step = pending.value.step
      await changeState(form.value, step)
      if (step === 'delete') {
        await router.push(props.listRoute)
        return
      }
      done.value = { submit: 'Submitted.', cancel: 'Cancelled.' }[step]
    }
    pending.value = null
    // A "Saved." note from an earlier save no longer describes the page.
    if (router.currentRoute.value.query.saved) await router.replace({ query: {} })
    emit('changed')
    await load()
  } catch (err) {
    error.value = err instanceof ApiError ? err : new ApiError('server', err.message || 'Something went wrong.')
  } finally {
    busy.value = false
  }
}

watch(() => [props.doctype, props.name, props.reloadKey], load, { immediate: true })
// Keep the result of the last action on screen until the user starts another or leaves.
watch(() => props.name, () => (done.value = ''))
defineExpose({ reload: load })
</script>

<template>
  <div class="ra">
    <div v-if="form && (canEdit || steps.length || form.actions.length)" class="bj-toolbar">
      <RouterLink v-if="canEdit && editRoute" class="bj-btn" :to="editRoute"><span class="lucide-pencil" aria-hidden="true" />Edit</RouterLink>
      <button
        v-for="action in form.actions"
        :key="action.key"
        type="button"
        class="bj-btn"
:class="{ 'bj-btn--primary': action.tone === 'primary' && !action.navigate }"
        :disabled="busy"
        @click="ask('action', action)"
      >
        {{ action.label }}
      </button>
      <button v-for="step in steps" :key="step" type="button" class="bj-btn" :class="{ 'bj-btn--primary': step === 'submit' }" :disabled="busy" @click="ask('state', step)">
        <span :class="STEPS[step].icon" aria-hidden="true" />{{ STEPS[step].label }}
      </button>
    </div>

    <p v-if="done" class="bj-note ra__ok" role="status"><span class="lucide-circle-check-big" aria-hidden="true" />{{ done }}</p>

    <section v-if="pending" class="page__card bj-card ra__panel" :class="{ 'ra__panel--danger': pending.tone === 'danger' }" aria-labelledby="ra-title">
      <h2 id="ra-title">{{ pending.title }}: {{ name }}</h2>
      <p v-if="pending.message">{{ pending.message }}</p>
      <div v-if="pending.kind === 'action' && pending.action.ask.length" class="ra__ask">
        <FormField
          v-for="field in pending.action.ask"
          :key="field.fieldname"
          v-model="askValues[field.fieldname]"
          :field="field"
          editable
          :required="Boolean(field.reqd)"
        />
      </div>
      <div v-if="error" class="ra__error" role="alert">
        <span class="lucide-triangle-alert" aria-hidden="true" />
        <div>
          <p class="bj-strong">{{ error.type === 'StaleRecord' ? 'Someone else changed this record' : 'Not done' }}</p>
          <p>{{ error.message }}</p>
          <button v-if="error.type === 'StaleRecord'" type="button" class="bj-btn" @click="emit('changed'); load(); pending = null">Reload</button>
        </div>
      </div>
      <div class="bj-toolbar">
        <button type="button" class="bj-btn bj-btn--primary" :disabled="busy" @click="go">
          <span v-if="busy" class="ra__spin" aria-hidden="true" />{{ pending.title }}
        </button>
        <button type="button" class="bj-btn" :disabled="busy" @click="pending = null">Back</button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.ra__panel {
  margin: 16px 0;
  border-color: var(--bj-terracotta);
}
.ra__panel--danger {
  border-color: var(--bj-state-blocked);
}
.ra__panel h2 {
  margin: 0 0 8px;
}
.ra__panel > p {
  margin: 0 0 12px;
}
.ra__ask {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px 16px;
  margin-bottom: 12px;
}
.ra__error {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin: 0 0 12px;
  padding: 12px 14px;
  color: var(--bj-state-blocked);
  border: 1px solid var(--bj-state-blocked);
  border-radius: 12px;
}
.ra__error p {
  margin: 0 0 6px;
  color: var(--bj-ink);
}
.ra__ok {
  margin: 12px 0;
}
.ra__ok > span {
  color: var(--bj-state-completed);
}
.ra__spin {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: ra-spin 0.8s linear infinite;
}
@keyframes ra-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
