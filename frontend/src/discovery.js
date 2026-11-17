import { RECORDS, detailRoute } from './records.js'
export function recordRoute(doctype, name) {
 const entry = Object.entries(RECORDS).find(([, value]) => value.doctype === doctype && !value.single)
 if (!entry) return null
 return { name: detailRoute(entry[0]), params: { name } }
}
export function exportUrl(doctype, filters, columns) {
 return '/api/method/sidra_realestate.api.discovery.export_report?' + new URLSearchParams({ doctype, filters: JSON.stringify(filters), columns: JSON.stringify(columns) })
}
