// Display helpers for the sample showcase screens (decision of 14 Nov 2026: a broad, labelled
// sample surface for the client demonstration). Pure functions; no business rule lives here.

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

// A missing value is shown as a dash, never as zero.
const missing = (value) => value === null || value === undefined || value === ''

/** $3.3m, $142k, $950 */
export function money(value) {
  if (missing(value)) return '—'
  const n = Number(value)
  if (!Number.isFinite(n)) return '—'
  const sign = n < 0 ? '-' : ''
  const a = Math.abs(n)
  if (a >= 1e6) return `${sign}$${trim(a / 1e6)}m`
  if (a >= 1e3) return `${sign}$${trim(a / 1e3, a >= 1e5 ? 0 : 1)}k`
  return `${sign}$${Math.round(a).toLocaleString('en-US')}`
}

/** $1,250,000 */
export function moneyFull(value) {
  if (missing(value)) return '—'
  const n = Number(value)
  if (!Number.isFinite(n)) return '—'
  return (n < 0 ? '-$' : '$') + Math.round(Math.abs(n)).toLocaleString('en-US')
}

function trim(n, digits = 1) {
  return Number(n.toFixed(digits)).toString()
}

export function count(value) {
  if (missing(value)) return '—'
  const n = Number(value)
  return Number.isFinite(n) ? Math.round(n).toLocaleString('en-US') : '—'
}

export function pct(value) {
  if (missing(value)) return '—'
  const n = Number(value)
  return Number.isFinite(n) ? `${trim(n)}%` : '—'
}

/** 2026-11-14 -> 14 Nov 2026 */
export function date(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}/.test(value)) return value ?? '—'
  const [y, m, d] = value.slice(0, 10).split('-').map(Number)
  return `${d} ${MONTHS[m - 1]} ${y}`
}

/** 2026-11 -> Nov 26 */
export function monthLabel(value) {
  const [y, m] = String(value).split('-').map(Number)
  return `${MONTHS[m - 1]} ${String(y).slice(2)}`
}

export function formatValue(value, kind) {
  switch (kind) {
    case 'money':
      return money(value)
    case 'moneyFull':
      return moneyFull(value)
    case 'pct':
      return pct(value)
    case 'date':
      return date(value)
    case 'count':
      return count(value)
    default:
      return value ?? '—'
  }
}

/** Days between two ISO dates (b - a). */
export function daysBetween(a, b) {
  return Math.round((Date.parse(b) - Date.parse(a)) / 86400000)
}
