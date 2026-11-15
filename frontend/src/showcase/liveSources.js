import { apiGet } from '../api.js'
import { EXECUTIVE_METHOD, LIVE_METHOD, REALESTATE_METHOD, validExecutive } from './live.js'
import { executivePeriod } from './period.js'

const group = (value, rows = false) => value && typeof value.available === 'boolean' &&
  (value.available ? (!rows || Array.isArray(value.rows)) : typeof value.reason === 'string')

export function validLiveSource(data, company, kind) {
  if (data?.company !== company) return false
  if (kind === 'construction') return ['jobs', 'variations', 'inspections'].every((key) => group(data[key], true))
  if (kind === 'finance') return ['pnl', 'cash', 'receivables', 'payables'].every((key) => group(data[key]))
  if (kind === 'operations') return ['stock', 'suppliers'].every((key) => group(data[key], true))
  if (kind === 'crm') return group(data.leads, true) && (!data.leads.available || (!!data.leads.by_channel && Array.isArray(data.leads.months))) &&
    group(data.opportunities, true) && (!data.opportunities.available || Array.isArray(data.opportunities.stages)) && group(data.customers)
  if (kind !== 'realestate') return false
  return group(data.units) && (!data.units.available || (Array.isArray(data.units.schemes) && data.units.status_counts)) &&
    group(data.contracts, true) && group(data.reservations) && group(data.leads) &&
    (!data.leads.available || !!data.leads.status_counts) && group(data.schedule) && (!data.schedule.available || Array.isArray(data.schedule.months))
}

/** Capture Company once; start all three independent requests before awaiting any. */
export async function loadExecutiveSources(company, get = apiGet, period = null) {
  const range = period ? { from_date: period.from, to_date: period.to } : {}
  const answer = async (method, valid, params = {}) => {
    try {
      const response = await get(method, { company, ...params })
      if (!valid(response?.message)) return { error: 'The server sent incompatible records or another Company.' }
      return { data: response.message }
    } catch (error) { return { error: error.message || 'These records could not be loaded.' } }
  }
  const [dashboard, construction, realestate] = await Promise.all([
    answer(EXECUTIVE_METHOD, (d) => validExecutive(d, company), { period: period ? executivePeriod(period.key) : 'this_month' }),
    answer(LIVE_METHOD, (d) => validLiveSource(d, company, 'construction'), range),
    answer(REALESTATE_METHOD, (d) => validLiveSource(d, company, 'realestate'), range),
  ])
  return { ...(dashboard.data || { scope: { company_id: company, company_name: company }, summary: {}, property: { total: null, counts: [] }, as_of: null }),
    dashboard_error: dashboard.error, extras: { construction, realestate } }
}
