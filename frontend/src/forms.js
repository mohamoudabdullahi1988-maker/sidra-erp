// The record forms (decision G23). The server describes each form (api/forms.py get_form):
// sections, fields, which fields this user may change, and the DocType's show / read-only /
// mandatory rules as small trees. This file evaluates those trees exactly as the server does
// (services/form_rules.py) and shapes what a save sends. It decides no permission and no rule
// of its own: the server checks every value again when it is saved.

import { apiGet, apiPost } from './api.js'

const API = 'sidra_realestate.api.forms.'
export const FORM_METHODS = {
  get: API + 'get_form',
  save: API + 'save_form',
  submit: API + 'submit_form',
  cancel: API + 'cancel_form',
  remove: API + 'delete_form',
  action: API + 'run_action',
}

export const NUMERIC = new Set(['Int', 'Float', 'Currency', 'Percent', 'Rating', 'Duration'])
export const LONG_TEXT = new Set(['Small Text', 'Text', 'Long Text', 'Text Editor', 'JSON'])

export async function loadForm(doctype, name = null) {
  const response = await apiGet('/api/method/' + FORM_METHODS.get, name ? { doctype, name } : { doctype })
  if (!response.message || !Array.isArray(response.message.layout)) throw new Error('Unexpected form response.')
  return response.message
}

// ---------------------------------------------------------------------- rules
const plain = (value) => {
  if (value === null || value === undefined) return ''
  if (typeof value === 'boolean') return value ? '1' : '0'
  if (typeof value === 'number' && Number.isInteger(value)) return String(value)
  return String(value)
}
const same = (left, right) => {
  const a = plain(left)
  const b = plain(right)
  if (a === b) return true
  // "5" typed in a box and 5.0 from the server are the same number.
  return a !== '' && b !== '' && !Number.isNaN(Number(a)) && !Number.isNaN(Number(b)) && Number(a) === Number(b)
}
const truthy = (value) => {
  if (value === null || value === undefined || value === false) return false
  if (typeof value === 'number') return value !== 0
  if (typeof value === 'string') return value !== ''
  return true
}

function value(node, values) {
  if ('lit' in node) return node.lit
  if ('field' in node) return values?.[node.field]
  if ('not' in node) return !evaluate(node.not, values)
  if ('and' in node) return node.and.every((part) => evaluate(part, values))
  if ('or' in node) return node.or.some((part) => evaluate(part, values))
  if ('eq' in node) return same(value(node.eq[0], values), value(node.eq[1], values))
  if ('ne' in node) return !same(value(node.ne[0], values), value(node.ne[1], values))
  if ('in' in node) {
    const subject = value(node.in[1], values)
    return node.in[0].some((item) => same(item, subject))
  }
  throw new Error('Unknown rule node')
}

/** JavaScript truthiness of a rule tree for the given values. */
export function evaluate(tree, values) {
  return truthy(value(tree, values))
}

/** The values rules see: each field as its type (a number box gives a number, a check 1 or 0, a
 * blank null), as the server sees the saved record, plus `__islocal` for a new record. */
export function ruleValues(form, values) {
  const out = { ...(form?.values ?? {}) }
  for (const field of fieldsOf(form)) {
    if (field.fieldtype !== 'Table' && field.fieldname in (values ?? {})) out[field.fieldname] = typed(field, values[field.fieldname])
  }
  out.__islocal = form?.is_new ? 1 : 0
  return out
}

/** Shown unless its rule says otherwise; a rule the server could not read shows the field. */
export function isShown(item, values) {
  return !item?.show || evaluate(item.show, values)
}

/** Editable when the server allows it and its read-only rule (if any) does not apply now. */
export function isEditable(field, values) {
  if (!field?.editable) return false
  if (field.unparsed?.includes('read_only_depends_on')) return false
  return !field.read_only_rule || !evaluate(field.read_only_rule, values)
}

export function isRequired(field, values) {
  return Boolean(field?.reqd) || Boolean(field?.mandatory_rule && evaluate(field.mandatory_rule, values))
}

// ---------------------------------------------------------------------- values and saving
export function fieldsOf(form) {
  return (form?.layout ?? []).flatMap((section) => section.fields)
}

const blank = (value) => value === null || value === undefined || value === ''

/** A typed value as the server expects it. */
export function typed(field, value) {
  if (field.fieldtype === 'Check') return value ? 1 : 0
  if (NUMERIC.has(field.fieldtype)) {
    if (blank(value)) return null
    const number = Number(String(value).replace(/,/g, ''))
    return Number.isFinite(number) ? number : String(value) // the server refuses what is not a number
  }
  if (blank(value)) return null
  return typeof value === 'string' ? value : value
}

/** Starting values for the form: the saved record, or the defaults of a new one. */
export function initialValues(form) {
  const values = {}
  for (const field of fieldsOf(form)) {
    const saved = form.values?.[field.fieldname]
    if (field.fieldtype === 'Table') {
      values[field.fieldname] = (Array.isArray(saved) ? saved : []).map((row) => rowValues(field, row))
    } else if (field.fieldtype === 'Check') {
      values[field.fieldname] = Boolean(Number(saved))
    } else {
      values[field.fieldname] = saved === null || saved === undefined ? '' : saved
    }
  }
  return values
}

function rowValues(field, row) {
  const values = { name: row?.name ?? null }
  for (const column of field.columns ?? []) {
    const saved = row?.[column.fieldname]
    values[column.fieldname] = column.fieldtype === 'Check' ? Boolean(Number(saved)) : saved === null || saved === undefined ? '' : saved
  }
  return values
}

export function blankRow(field) {
  return rowValues(field, null)
}

function tablePayload(field, rows) {
  return (rows ?? []).map((row) => {
    const out = {}
    if (row.name) out.name = row.name
    for (const column of field.columns ?? []) {
      if (column.editable) out[column.fieldname] = typed(column, row[column.fieldname])
    }
    return out
  })
}

/** What a save sends: for a new record every editable field that has a value, for a saved one
 * only the editable fields that changed. A field read-only by rule is never sent. */
export function payload(form, values, start) {
  const out = {}
  const rules = ruleValues(form, values)
  for (const field of fieldsOf(form)) {
    if (!field.editable) continue
    const name = field.fieldname
    if (field.fieldtype === 'Table') {
      const now = tablePayload(field, values[name])
      const before = tablePayload(field, start?.[name])
      if (JSON.stringify(now) !== JSON.stringify(before) || (form.is_new && now.length)) out[name] = now
      continue
    }
    if (!isEditable(field, rules)) continue
    const now = typed(field, values[name])
    const before = typed(field, start?.[name])
    if (form.is_new ? now !== null && !(field.fieldtype === 'Check' && now === 0) : JSON.stringify(now) !== JSON.stringify(before)) {
      out[name] = now
    }
  }
  return out
}

export const isDirty = (form, values, start) => Object.keys(payload(form, values, start)).length > 0

export function saveForm(form, values, start, requestKey) {
  const args = { doctype: form.doctype, data: payload(form, values, start) }
  if (form.is_new) args.request_key = requestKey
  else Object.assign(args, { name: form.name, expected_modified: form.modified })
  return apiPost(FORM_METHODS.save, args)
}

export function runAction(form, action, args = {}) {
  return apiPost(FORM_METHODS.action, {
    doctype: form.doctype,
    name: form.name,
    action: action.key,
    args,
    expected_modified: form.modified,
  })
}

export function changeState(form, step) {
  const method = { submit: FORM_METHODS.submit, cancel: FORM_METHODS.cancel, delete: FORM_METHODS.remove }[step]
  return apiPost(method, { doctype: form.doctype, name: form.name, expected_modified: form.modified })
}

/** Missing required values, by label, for a hint before saving (the server decides). */
export function missing(form, values) {
  const rules = ruleValues(form, values)
  const out = []
  for (const section of form?.layout ?? []) {
    if (!isShown(section, rules)) continue
    for (const field of section.fields) {
      if (!field.editable || field.fieldtype === 'Table' || !isShown(field, rules)) continue
      if (isRequired(field, rules) && blank(values[field.fieldname]) && field.fieldtype !== 'Check') out.push(field.label)
    }
  }
  return out
}

/** Resolve a picker target using the server-provided Dynamic Link allowlist. */
export function linkTarget(field, values = {}) {
  if (field?.fieldtype === 'Link') return field.options || null
  if (field?.fieldtype !== 'Dynamic Link') return null
  const target = values[field.options]
  return field.allowed_doctypes?.includes(target) ? target : null
}
