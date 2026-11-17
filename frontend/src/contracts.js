import { apiGet } from './api.js'

export { fileLink, isAmount as numeric, money, recordLink, textValue } from './format.js'

// The one place the timeline method is named.
export const TIMELINE_METHOD = 'sidra_realestate.api.record_workflow.get_timeline'
export const CONTRACT_DOCTYPE = 'Sidra Sale Contract'
export const CONTRACT = '/api/resource/' + encodeURIComponent(CONTRACT_DOCTYPE)

export const STATUS = { 0: 'Draft', 1: 'Confirmed', 2: 'Cancelled' }
export const statusText = (value) => STATUS[value] || 'Unavailable'
export const statusTone = (value) => ({ 0: 'current', 1: 'completed', 2: 'blocked' })[value] || 'muted'

/** Cash contracts carry no source; the label says what the record is, nothing more. */
export function sourceText(row) {
  if (row?.source) return String(row.source)
  return row?.contract_type === 'Cash' ? 'Cash sale' : '—'
}

export async function timeline(name) {
  const response = await apiGet('/api/method/' + TIMELINE_METHOD, { doctype: CONTRACT_DOCTYPE, name })
  if (!response.message || !Array.isArray(response.message.stages)) throw new Error('Unexpected workflow response.')
  return response.message
}

/** What the signed-in user may do with this record, as the server evaluates it ({ write: 1, ... }). */
export async function permissions(name) {
  const response = await apiGet('/api/method/frappe.client.get_doc_permissions', { doctype: CONTRACT_DOCTYPE, docname: name })
  return response.message?.permissions ?? {}
}
