// The period a dashboard shows (Mohamoud, 15 Nov 2026): quick presets or a custom From–To range.
// The choice lives in the address (?period=3m, or ?period=custom&from=…&to=…) so it can be shared.
// Live records are read for that period by the server (api/live_period.py); sample figures are fixed.

export const PRESETS = [
  { key: 'month', label: 'This month' },
  { key: '3m', label: 'Last 3 months' },
  { key: 'year', label: 'This year' },
  { key: '12m', label: 'Last 12 months' },
  { key: 'custom', label: 'Custom' },
]
export const DEFAULT_PERIOD = '12m'

const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
const DATE = /^\d{4}-\d{2}-\d{2}$/

/** { key, from, to } for the address's query; an unknown or broken choice falls back to 12 months. */
export function periodFrom(query, today = new Date()) {
  const key = PRESETS.some((p) => p.key === query?.period) ? query.period : DEFAULT_PERIOD
  const y = today.getFullYear()
  const m = today.getMonth()
  const to = iso(today)
  if (key === 'custom') {
    const from = DATE.test(query?.from ?? '') ? query.from : null
    const end = DATE.test(query?.to ?? '') ? query.to : to
    if (from && from <= end) return { key, from, to: end }
    return { ...periodFrom({}, today), key: 'custom' }
  }
  if (key === 'month') return { key, from: iso(new Date(y, m, 1)), to }
  if (key === '3m') return { key, from: iso(new Date(y, m - 2, 1)), to }
  if (key === 'year') return { key, from: iso(new Date(y, 0, 1)), to }
  return { key, from: iso(new Date(y, m - 11, 1)), to }
}

/** The server's own periods for the Executive dashboard figures (staff_dashboard.PERIODS). */
export function executivePeriod(key) {
  return key === 'month' ? 'this_month' : 'last_90_days'
}

export function periodLabel(period) {
  const preset = PRESETS.find((p) => p.key === period.key)
  return period.key === 'custom' ? `${period.from} to ${period.to}` : preset?.label ?? ''
}
