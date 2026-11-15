<script setup>
import TransactionGuide from '../components/TransactionGuide.vue'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LoadingIndicator } from 'frappe-ui'

import { ApiError, apiGet, apiPost, apiUpload } from '../api'
import StatePanel from '../components/StatePanel.vue'
import { companies, company as currentCompany } from '../company'
import { CONTRACT, CONTRACT_DOCTYPE } from '../contracts'
import { fileLink, money } from '../format'
import {
  ATTACH_METHOD,
  DOWN_PAYMENT_MODES,
  FILL_METHOD,
  FORM_METHOD,
  NUMERIC_TYPES,
  applies,
  blankParty,
  isDirty,
  ROW_TYPES,
  SAVE_METHOD,
  SIGNED_COPY_FIELD,
  blankForm,
  blankRow,
  blankUnit,
  formFromDoc,
  isRegisteredDraft,
  newRequestKey,
  payloadFromForm,
  savedDifference,
} from '../registration'

// Registers an External (registered) installment contract. Every rule is the server's: this
// page sends what was typed and shows what the server saved or why it refused.
const route = useRoute()
const router = useRouter()

const isNew = computed(() => !route.params.name)
const doc = ref(null) // the saved record, as last read from the server
const form = ref(blankForm(currentCompany.value))
const loading = ref(false)
const loadError = ref(null)
const saving = ref(false)
const saveError = ref(null)
const savedNote = ref('')
const uploading = ref(false)
const uploadError = ref('')
const chosenFile = ref(null)
let requestKey = newRequestKey()
let request = 0

const options = ref({ customers: [], units: [], profiles: [] })
const definition = ref(null) // the server's term, signing and party fields (get_registration_form)
const definitionError = ref('')
const filling = ref(false)
const fillError = ref('')
const replaceAsked = ref(false)

const editable = computed(() => isNew.value || isRegisteredDraft(doc.value))
const difference = computed(() => savedDifference(doc.value))
const separate = computed(() => form.value.down_payment_mode === 'Recorded separately')
const dirty = computed(() => isDirty(form.value, doc.value, definition.value))
const termValues = computed(() => ({ ...form.value, ...form.value.extra }))
const shownTerms = computed(() => (definition.value?.terms ?? []).filter((field) => applies(field, termValues.value)))
const partyField = (name) => definition.value?.parties?.find((field) => field.fieldname === name)
const partyRoles = computed(() => partyField('role')?.options ?? [])
const inputMode = (field) => (NUMERIC_TYPES.has(field.fieldtype) ? (field.fieldtype === 'Int' ? 'numeric' : 'decimal') : undefined)
const cash = (field) => (doc.value && field in doc.value ? money(doc.value[field], doc.value.currency) : 'Unavailable')

async function loadOptions() {
  // Suggestions only, from lists the server lets this user read. The server validates the value.
  const list = async (doctype, fields, filters) => {
    try {
      const result = await apiGet('/api/resource/' + encodeURIComponent(doctype), {
        fields,
        filters,
        limit_page_length: 500,
        order_by: 'name asc',
      })
      return Array.isArray(result.data) ? result.data : []
    } catch {
      return []
    }
  }
  const [customers, units, profiles] = await Promise.all([
    list('Customer', ['name', 'customer_name'], [['disabled', '=', 0]]),
    list('Sidra Unit', ['name', 'scheme', 'cash_price'], [['status', '=', 'Available']]),
    list('Sidra Contract Profile', ['name'], [['active', '=', 1]]),
  ])
  options.value = { customers, units, profiles }
}

async function loadDefinition() {
  try {
    const result = await apiGet('/api/method/' + FORM_METHOD)
    if (!Array.isArray(result.message?.terms)) throw new Error('unexpected')
    definition.value = result.message
    if (doc.value) form.value = formFromDoc(doc.value, definition.value)
  } catch {
    definitionError.value = 'The penalty, title and party fields could not be loaded, so they are not shown and will not be changed. Reload to try again, or edit them in Desk.'
  }
}

async function load() {
  const id = ++request
  saveError.value = null
  uploadError.value = ''
  loadError.value = null
  if (isNew.value) {
    doc.value = null
    form.value = blankForm(currentCompany.value)
    requestKey = newRequestKey()
    return
  }
  loading.value = true
  try {
    const result = await apiGet(`${CONTRACT}/${encodeURIComponent(route.params.name)}`)
    if (!result.data?.name) throw new ApiError('server', 'The server sent an unexpected answer.')
    if (id !== request) return
    doc.value = result.data
    form.value = formFromDoc(result.data, definition.value)
  } catch (err) {
    if (id === request) loadError.value = err instanceof ApiError ? err : new ApiError('server', 'Something went wrong.')
  } finally {
    if (id === request) loading.value = false
  }
}

async function save() {
  saving.value = true
  saveError.value = null
  savedNote.value = ''
  try {
    const args = { data: payloadFromForm(form.value, definition.value) }
    if (isNew.value) args.request_key = requestKey
    else Object.assign(args, { contract: doc.value.name, expected_modified: doc.value.modified })
    const result = await apiPost(SAVE_METHOD, args)
    if (isNew.value) {
      await router.replace({ name: 'contract-edit', params: { name: result.name }, query: { saved: '1' } })
    } else {
      await load()
      savedNote.value = 'Saved. The totals below are the server’s.'
    }
  } catch (err) {
    saveError.value = err instanceof ApiError ? err : new ApiError('server', 'Something went wrong.')
  } finally {
    saving.value = false
  }
}

function pickFile(event) {
  chosenFile.value = event.target.files?.[0] ?? null
  uploadError.value = ''
}

async function attach() {
  if (!chosenFile.value || !doc.value) return
  uploading.value = true
  uploadError.value = ''
  try {
    const file = await apiUpload(chosenFile.value, {
      doctype: CONTRACT_DOCTYPE,
      docname: doc.value.name,
      fieldname: SIGNED_COPY_FIELD,
      isPrivate: true,
    })
    if (!file?.file_url) throw new ApiError('server', 'The server did not return the uploaded file.')
    await apiPost(ATTACH_METHOD, {
      contract: doc.value.name,
      file_url: file.file_url,
      expected_modified: doc.value.modified,
    })
    chosenFile.value = null
    await load()
    savedNote.value = 'Signed copy attached.'
  } catch (err) {
    uploadError.value = err.message || 'The file could not be attached.'
  } finally {
    uploading.value = false
  }
}

async function fill(replace = false) {
  if (!doc.value) return
  if (doc.value.schedule?.length && !replace) {
    replaceAsked.value = true
    return
  }
  filling.value = true
  fillError.value = ''
  try {
    await apiPost(FILL_METHOD, { contract: doc.value.name, expected_modified: doc.value.modified, replace: replace ? 1 : 0 })
    replaceAsked.value = false
    await load()
    savedNote.value = 'Schedule filled from the saved terms. Check each row against the signed contract.'
  } catch (err) {
    fillError.value = err.message || 'The schedule could not be filled.'
  } finally {
    filling.value = false
  }
}

const addParty = () => form.value.parties.push(blankParty())
const removeParty = (index) => form.value.parties.splice(index, 1)
const addRow = () => form.value.schedule.push(blankRow())
const removeRow = (index) => form.value.schedule.splice(index, 1)
const addUnit = () => form.value.units.push(blankUnit())
const removeUnit = (index) => form.value.units.splice(index, 1)

watch(
  () => route.params.name,
  () => {
    savedNote.value = route.query.saved ? 'Draft saved. Attach the signed copy below, then confirm from the contract page.' : ''
    load()
  },
  { immediate: true },
)
loadOptions()
loadDefinition()
onBeforeUnmount(() => ++request)
</script>

<template>
  <TransactionGuide />
  <section class="page">
    <nav class="bj-crumb" aria-label="Breadcrumb">
      <RouterLink class="bj-link" :to="{ name: 'contracts' }">Contracts</RouterLink>
      <span aria-hidden="true">/</span>
      <template v-if="!isNew">
        <RouterLink class="bj-link" :to="{ name: 'contract-detail', params: { name: route.params.name } }">{{ route.params.name }}</RouterLink>
        <span aria-hidden="true">/</span>
        <span>Edit</span>
      </template>
      <span v-else>Register external contract</span>
    </nav>

    <div v-if="loading" class="page__card bj-loading" role="status"><LoadingIndicator /><span>Loading contract…</span></div>

    <div v-else-if="loadError" class="page__card">
      <StatePanel
        v-if="loadError.kind === 'denied'"
        icon="lucide-lock"
        title="This contract is unavailable to you"
        message="Your account does not have permission to read this contract."
      />
      <StatePanel v-else icon="lucide-triangle-alert" tone="blocked" title="The contract could not be loaded" :message="loadError.message">
        <button type="button" class="bj-btn bj-btn--primary" @click="load">Try again</button>
      </StatePanel>
    </div>

    <div v-else-if="!editable" class="page__card">
      <StatePanel
        icon="lucide-lock"
        title="This contract cannot be edited here"
        message="Only a draft registered (External) installment contract is edited on this screen."
      >
        <RouterLink class="bj-btn" :to="{ name: 'contract-detail', params: { name: route.params.name } }">Back to the contract</RouterLink>
      </StatePanel>
    </div>

    <form v-else class="reg" novalidate @submit.prevent="save">
      <header class="bj-head">
        <div>
          <h1 class="page__title">{{ isNew ? 'Register external contract' : `Edit ${doc.name}` }}</h1>
          <p class="bj-sub">A contract signed outside the system, entered as signed. The server checks every value when you save.</p>
        </div>
        <div class="bj-toolbar">
          <button type="submit" class="bj-btn bj-btn--primary" :disabled="saving">
            <span v-if="saving" class="reg__spin" aria-hidden="true" />{{ isNew ? 'Create draft' : 'Save draft' }}
          </button>
        </div>
      </header>

      <p v-if="savedNote" class="bj-note reg__ok" role="status"><span class="lucide-circle-check-big" aria-hidden="true" />{{ savedNote }}</p>
      <div v-if="saveError" class="reg__error" role="alert">
        <span class="lucide-triangle-alert" aria-hidden="true" />
        <div>
          <p class="bj-strong">{{ saveError.type === 'StaleRecord' ? 'Someone else changed this contract' : 'Not saved' }}</p>
          <p>{{ saveError.message }}</p>
          <button v-if="saveError.type === 'StaleRecord'" type="button" class="bj-btn" @click="load">Reload (your unsaved changes are lost)</button>
        </div>
      </div>

      <section class="bj-section">
        <h2>Contract</h2>
        <div class="page__card bj-card reg__grid">
          <label class="reg__field">
            <span class="reg__label">Customer</span>
            <input v-model="form.customer" class="bj-input" list="reg-customers" autocomplete="off" required />
          </label>
          <label class="reg__field">
            <span class="reg__label">Company</span>
            <select v-model="form.company" class="bj-select" aria-label="Company" :disabled="!isNew">
              <option v-for="name in companies" :key="name" :value="name">{{ name }}</option>
              <option v-if="form.company && !companies.includes(form.company)" :value="form.company">{{ form.company }}</option>
            </select>
          </label>
          <label class="reg__field">
            <span class="reg__label">External reference (the contract's own number)</span>
            <input v-model="form.external_reference" class="bj-input" autocomplete="off" />
          </label>
          <label class="reg__field">
            <span class="reg__label">Signed on</span>
            <input v-model="form.signed_on" class="bj-input" type="date" />
          </label>
          <label class="reg__field">
            <span class="reg__label">Agreed price</span>
            <input v-model="form.agreed_price" class="bj-input" inputmode="decimal" />
          </label>
          <label class="reg__field">
            <span class="reg__label">Contract profile (optional)</span>
            <input v-model="form.contract_profile" class="bj-input" list="reg-profiles" autocomplete="off" />
          </label>
          <label class="reg__field">
            <span class="reg__label">Down payment</span>
            <select v-model="form.down_payment_mode" class="bj-select" aria-label="Down payment">
              <option v-for="mode in DOWN_PAYMENT_MODES" :key="mode" :value="mode">{{ mode }}</option>
            </select>
          </label>
          <label v-if="separate" class="reg__field">
            <span class="reg__label">Down payment amount (recorded separately)</span>
            <input v-model="form.down_payment" class="bj-input" inputmode="decimal" />
          </label>
          <label class="reg__field">
            <span class="reg__label">Installments</span>
            <input v-model="form.installments" class="bj-input" inputmode="numeric" />
          </label>
          <label class="reg__field">
            <span class="reg__label">Due day of the month</span>
            <input v-model="form.due_day" class="bj-input" inputmode="numeric" />
          </label>
          <label class="reg__field">
            <span class="reg__label">Grace months</span>
            <input v-model="form.grace_months" class="bj-input" inputmode="numeric" />
          </label>
          <label class="reg__field reg__field--wide">
            <span class="reg__label">Terms summary</span>
            <textarea v-model="form.terms_summary" class="bj-input reg__text" rows="3" />
          </label>
        </div>
      </section>

      <p v-if="definitionError" class="reg__error" role="alert"><span class="lucide-triangle-alert" aria-hidden="true" />{{ definitionError }}</p>

      <section v-if="definition" class="bj-section">
        <h2>Agent and notary</h2>
        <div class="page__card bj-card reg__grid">
          <label v-for="field in definition.signing" :key="field.fieldname" class="reg__field">
            <span class="reg__label">{{ field.label }}</span>
            <input v-model="form.extra[field.fieldname]" class="bj-input" :aria-label="field.label" autocomplete="off" />
          </label>
        </div>
        <p class="bj-foot">Recorded where the signed contract has them.</p>
      </section>

      <section v-if="definition" class="bj-section">
        <h2>Penalty, default and title terms</h2>
        <div class="page__card bj-card reg__grid">
          <label v-for="field in shownTerms" :key="field.fieldname" class="reg__field">
            <span class="reg__label">{{ field.label }}</span>
            <select v-if="field.fieldtype === 'Select'" v-model="form.extra[field.fieldname]" class="bj-select" :aria-label="field.label">
              <option value="">—</option>
              <option v-for="option in field.options" :key="option" :value="option">{{ option }}</option>
            </select>
            <input v-else v-model="form.extra[field.fieldname]" class="bj-input" :aria-label="field.label" :inputmode="inputMode(field)" autocomplete="off" />
          </label>
        </div>
        <p class="bj-foot">As the signed contract states them. Recorded only: no penalty or refund is applied.</p>
      </section>

      <section v-if="definition" class="bj-section">
        <h2>Seller, guarantor and witnesses</h2>
        <div class="page__card bj-card">
          <p v-if="!form.parties.length" class="bj-muted">No parties entered.</p>
          <div v-else class="bj-table-wrap">
            <table class="bj-table bj-table--stack">
              <thead>
                <tr>
                  <th scope="col">{{ partyField('role')?.label || 'Role' }}</th>
                  <th scope="col">{{ partyField('full_name')?.label || 'Full name' }}</th>
                  <th scope="col">{{ partyField('phone')?.label || 'Phone' }}</th>
                  <th scope="col">{{ partyField('id_number')?.label || 'ID number' }}</th>
                  <th scope="col">{{ partyField('pledged_property')?.label || 'Pledged property' }}</th>
                  <th scope="col"><span class="sr-only">Remove</span></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, index) in form.parties" :key="index">
                  <td data-label="Role">
                    <select v-model="row.role" class="bj-select" :aria-label="`Role of party ${index + 1}`">
                      <option v-for="role in partyRoles" :key="role" :value="role">{{ role }}</option>
                    </select>
                  </td>
                  <td data-label="Name"><input v-model="row.full_name" class="bj-input" :aria-label="`Name of party ${index + 1}`" autocomplete="off" /></td>
                  <td data-label="Phone"><input v-model="row.phone" class="bj-input" :aria-label="`Phone of party ${index + 1}`" inputmode="tel" autocomplete="off" /></td>
                  <td data-label="ID number"><input v-model="row.id_number" class="bj-input" :aria-label="`ID number of party ${index + 1}`" autocomplete="off" /></td>
                  <td data-label="Pledged property">
                    <input v-if="row.role === 'Seller Guarantor'" v-model="row.pledged_property" class="bj-input" :aria-label="`Pledged property of party ${index + 1}`" autocomplete="off" />
                    <span v-else class="bj-muted">—</span>
                  </td>
                  <td><button type="button" class="bj-btn bj-btn--icon" :aria-label="`Remove party ${index + 1}`" @click="removeParty(index)"><span class="lucide-trash-2" aria-hidden="true" /></button></td>
                </tr>
              </tbody>
            </table>
          </div>
          <button type="button" class="bj-btn" @click="addParty"><span class="lucide-plus" aria-hidden="true" />Add party</button>
        </div>
      </section>

      <section class="bj-section">
        <h2>Property</h2>
        <div class="page__card bj-card">
          <div class="bj-table-wrap">
            <table class="bj-table bj-table--stack">
              <thead>
                <tr><th scope="col">Unit</th><th scope="col">Allocated price</th><th scope="col"><span class="sr-only">Remove</span></th></tr>
              </thead>
              <tbody>
                <tr v-for="(row, index) in form.units" :key="index">
                  <td data-label="Unit"><input v-model="row.unit" class="bj-input" list="reg-units" :aria-label="`Unit ${index + 1}`" autocomplete="off" /></td>
                  <td data-label="Allocated price"><input v-model="row.allocated_price" class="bj-input" inputmode="decimal" :aria-label="`Allocated price ${index + 1}`" /></td>
                  <td><button type="button" class="bj-btn bj-btn--icon" :aria-label="`Remove unit ${index + 1}`" @click="removeUnit(index)"><span class="lucide-trash-2" aria-hidden="true" /></button></td>
                </tr>
              </tbody>
            </table>
          </div>
          <button type="button" class="bj-btn" @click="addUnit"><span class="lucide-plus" aria-hidden="true" />Add unit</button>
        </div>
      </section>

      <section class="bj-section">
        <h2>Installment schedule</h2>
        <div class="page__card bj-card">
          <p class="bj-muted">Enter the rows exactly as the signed contract states them.</p>
          <div v-if="doc" class="reg__fill">
            <button type="button" class="bj-btn" :disabled="filling || dirty" @click="fill(false)">
              <span v-if="filling" class="reg__spin" aria-hidden="true" /><span v-else class="lucide-wand-sparkles" aria-hidden="true" />Fill schedule from saved terms
            </button>
            <span v-if="dirty" class="bj-muted">Save your changes first: the server fills from the saved price, installments, due day and dates.</span>
          </div>
          <div v-if="replaceAsked" class="reg__replace" role="alertdialog" aria-labelledby="replace-title">
            <p id="replace-title" class="bj-strong">Replace the {{ doc.schedule.length }} saved rows?</p>
            <p>The server proposes new rows from the saved terms. The current rows are removed.</p>
            <div class="bj-toolbar">
              <button type="button" class="bj-btn bj-btn--primary" :disabled="filling" @click="fill(true)">Replace rows</button>
              <button type="button" class="bj-btn" :disabled="filling" @click="replaceAsked = false">Keep current rows</button>
            </div>
          </div>
          <p v-if="fillError" class="reg__error" role="alert"><span class="lucide-triangle-alert" aria-hidden="true" />{{ fillError }}</p>
          <div class="bj-table-wrap">
            <table class="bj-table bj-table--stack">
              <thead>
                <tr><th scope="col">No.</th><th scope="col">Type</th><th scope="col">Due date</th><th scope="col">Amount</th><th scope="col"><span class="sr-only">Remove</span></th></tr>
              </thead>
              <tbody>
                <tr v-for="(row, index) in form.schedule" :key="index">
                  <td data-label="No.">{{ index + 1 }}</td>
                  <td data-label="Type">
                    <select v-model="row.row_type" class="bj-select" :aria-label="`Type of row ${index + 1}`">
                      <option v-for="type in ROW_TYPES" :key="type" :value="type">{{ type }}</option>
                    </select>
                  </td>
                  <td data-label="Due date"><input v-model="row.due_date" class="bj-input" type="date" :aria-label="`Due date of row ${index + 1}`" /></td>
                  <td data-label="Amount"><input v-model="row.amount" class="bj-input" inputmode="decimal" :aria-label="`Amount of row ${index + 1}`" /></td>
                  <td><button type="button" class="bj-btn bj-btn--icon" :aria-label="`Remove row ${index + 1}`" @click="removeRow(index)"><span class="lucide-trash-2" aria-hidden="true" /></button></td>
                </tr>
              </tbody>
            </table>
          </div>
          <button type="button" class="bj-btn" @click="addRow"><span class="lucide-plus" aria-hidden="true" />Add row</button>
        </div>
      </section>

      <section v-if="doc" class="bj-section">
        <h2>Totals as last saved</h2>
        <div class="page__card bj-card">
          <dl class="bj-kv">
            <div><dt>Amount due</dt><dd>{{ cash('amount_due') }}</dd></div>
            <div><dt>Schedule total</dt><dd>{{ cash('schedule_total') }}</dd></div>
            <div><dt>Difference</dt><dd>{{ cash('schedule_difference') }}</dd></div>
          </dl>
          <p v-if="difference !== null" class="bj-note" role="status">
            <span class="lucide-info" aria-hidden="true" />
            <span>The saved schedule differs from the amount due. Whether it can be confirmed is shown in the workflow on the contract page.</span>
          </p>
          <p class="bj-foot">Calculated by the server when the draft was saved. Unsaved edits are not included.</p>
        </div>
      </section>

      <section v-if="doc" class="bj-section">
        <h2>Original signed contract</h2>
        <div class="page__card bj-card">
          <p v-if="fileLink(doc.signed_copy)">
            Attached: <a class="bj-link" :href="fileLink(doc.signed_copy)" target="_blank" rel="noopener">{{ doc.signed_copy.split('/').pop() }}</a>
          </p>
          <p v-else class="bj-muted">No file attached yet. Confirmation needs the scan of the signed original.</p>
          <div class="bj-toolbar">
            <input class="reg__file" type="file" accept=".pdf,image/*" aria-label="Signed copy file" @change="pickFile" />
            <button type="button" class="bj-btn" :disabled="!chosenFile || uploading" @click="attach">
              <span v-if="uploading" class="reg__spin" aria-hidden="true" />{{ doc.signed_copy ? 'Replace signed copy' : 'Attach signed copy' }}
            </button>
          </div>
          <p v-if="uploadError" class="reg__error" role="alert"><span class="lucide-triangle-alert" aria-hidden="true" />{{ uploadError }}</p>
          <p class="bj-foot">Kept as a private file on this contract only.</p>
        </div>
      </section>

      <datalist id="reg-customers">
        <option v-for="row in options.customers" :key="row.name" :value="row.name">{{ row.customer_name }}</option>
      </datalist>
      <datalist id="reg-units">
        <option v-for="row in options.units" :key="row.name" :value="row.name">{{ row.scheme }}</option>
      </datalist>
      <datalist id="reg-profiles">
        <option v-for="row in options.profiles" :key="row.name" :value="row.name" />
      </datalist>
    </form>
  </section>
</template>

<style scoped>
.reg__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px 18px;
}
.reg__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.reg__label {
  font-size: 13px;
  font-weight: 500;
  color: var(--bj-muted);
}
.reg__field .bj-input,
.reg__field .bj-select {
  width: 100%;
}
.reg__field--wide {
  grid-column: 1 / -1;
}
.reg__text {
  min-height: 88px;
  resize: vertical;
}
.reg .bj-table .bj-input,
.reg .bj-table .bj-select {
  width: 100%;
  min-width: 120px;
}
.reg .bj-card > .bj-btn,
.reg .bj-card > .bj-toolbar {
  margin-top: 12px;
}
.reg__error {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin: 12px 0;
  padding: 12px 14px;
  color: var(--bj-state-blocked);
  background: var(--bj-card);
  border: 1px solid var(--bj-state-blocked);
  border-radius: 12px;
}
.reg__error p {
  margin: 0 0 6px;
  color: var(--bj-ink);
}
.reg__ok {
  margin: 12px 0;
}
.reg__ok > span {
  color: var(--bj-state-completed);
}
.reg__fill {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  margin: 8px 0 12px;
}
.reg__replace {
  margin: 0 0 12px;
  padding: 12px 14px;
  background: var(--bj-terracotta-tint);
  border-radius: 8px;
}
.reg__replace p {
  margin: 0 0 8px;
}
.reg__file {
  font: inherit;
  font-size: 14px;
  min-height: 44px;
}
.reg__spin {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: reg-spin 0.8s linear infinite;
}
@keyframes reg-spin {
  to {
    transform: rotate(360deg);
  }
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}
</style>
