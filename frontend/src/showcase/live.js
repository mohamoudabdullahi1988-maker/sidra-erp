// Live records for the Construction screens (decision G25, step 1): the same tiles and charts as
// the sample screens, built from `api.construction_live.get_construction_live`. This file only
// arranges what the server returned; it decides no permission and invents no figure. A group the
// server marks unavailable is shown with its reason, never as zero.
import { detailRoute, listRoute } from '../records.js'

export const LIVE_METHOD = '/api/method/sidra_realestate.api.construction_live.get_construction_live'

/** Construction tabs that can show live records. */
export const LIVE_TABS = { executive: ['overview'], build: ['portfolio', 'variations', 'quality'] }

const num = (value) => (value === null || value === undefined || value === '' ? null : Number(value))
const sumOf = (rows, key) => {
  const values = rows.map((r) => num(r[key]))
  return values.some((v) => v === null || Number.isNaN(v)) ? null : values.reduce((a, v) => a + v, 0)
}
const JOB_TONE = { Enquiry: 'slate', Quoted: 'sky', Contracted: 'purple', 'In Progress': 'blue', 'On Hold': 'amber', Completed: 'green', 'Defects Period': 'teal', Closed: 'slate', Cancelled: 'rose' }
const ACTIVE = new Set(['Contracted', 'In Progress', 'On Hold'])
const jobLink = (name) => ({ name: 'construction-detail', params: { name } })
const jobLabel = (row) => row.site || row.customer || row.name

function notice(title, text, span = 12) {
  return { type: 'list', title, span, items: [{ tone: 'blue', text }] }
}

function countSegments(rows, key, tones, to) {
  const counts = {}
  for (const row of rows) counts[row[key]] = (counts[row[key]] ?? 0) + 1
  return Object.entries(counts).map(([label, value]) => ({ label, value, tone: tones[label] ?? 'slate', to }))
}

function portfolio(data) {
  const jobs = data.jobs
  if (!jobs.available) return { kpis: [], widgets: [notice('Construction jobs', jobs.reason)] }
  const rows = jobs.rows
  if (!rows.length) return { kpis: [], widgets: [notice('Construction jobs', `No construction jobs are recorded for ${data.company} yet.`)] }
  const withProgress = rows.filter((r) => r.progress !== null)
  const list = { name: 'construction' }
  return {
    kpis: [
      { label: 'Jobs', value: rows.length, kind: 'count', tone: 'amber', to: list },
      { label: 'Active', value: rows.filter((r) => ACTIVE.has(r.status)).length, kind: 'count', tone: 'blue', to: list },
      { label: 'Current contract value', value: sumOf(rows.filter((r) => r.current_contract_value !== null), 'current_contract_value'), kind: 'money', tone: 'sky', to: list },
      { label: 'Approved variations', value: sumOf(rows.filter((r) => r.approved_variations !== null), 'approved_variations'), kind: 'money', tone: 'purple', to: list },
      { label: 'Overdue stages', value: rows.reduce((a, r) => a + r.stages_overdue, 0), kind: 'count', tone: 'rose', to: list },
      { label: 'Average progress', value: withProgress.length ? Math.round(withProgress.reduce((a, r) => a + r.progress, 0) / withProgress.length) : null, kind: 'pct', tone: 'green', to: list },
    ],
    widgets: [
      {
        type: 'map', title: 'Job sites', span: 4,
        pins: rows.filter((r) => r.point).map((r) => ({ label: jobLabel(r), point: r.point, tone: JOB_TONE[r.status], sub: `${r.status}${r.progress !== null ? ` · ${r.progress}%` : ''}`, to: jobLink(r.name) })),
        empty: 'No job has a recorded location yet.',
      },
      { type: 'donut', title: 'Jobs by status', span: 4, centre: 'jobs', kind: 'count', to: list, segments: countSegments(rows, 'status', JOB_TONE, list) },
      {
        type: 'hbars', title: 'Current contract value by job', span: 4, kind: 'money',
        series: [{ name: 'Contract value', tone: 'sky' }],
        rows: rows.filter((r) => r.current_contract_value !== null).slice(0, 10).map((r) => ({ label: jobLabel(r), values: [num(r.current_contract_value)], to: jobLink(r.name) })),
      },
      {
        type: 'table', title: 'Jobs', span: 12, to: list,
        columnDefs: [
          { key: 'name', label: 'Job' }, { key: 'customer', label: 'Customer' }, { key: 'site', label: 'Site' }, { key: 'status', label: 'Status', kind: 'chip' },
          { key: 'current_contract_value', label: 'Contract value', kind: 'money' }, { key: 'progress', label: 'Progress', kind: 'progress' },
          { key: 'stages_label', label: 'Stages done' }, { key: 'stages_overdue', label: 'Overdue stages', kind: 'count' }, { key: 'end', label: 'Ends', kind: 'date' },
        ],
        rows: rows.map((r) => ({ ...r, stages_label: r.stages ? `${r.stages_completed} of ${r.stages}` : 'No stages', _to: jobLink(r.name) })),
      },
      ...(() => {
        const dated = rows.filter((r) => r.start && r.end)
        if (!dated.length) return [notice('Job timeline', 'No job has start and end dates recorded yet.', 12)]
        const from = dated.reduce((a, r) => (r.start < a ? r.start : a), dated[0].start)
        const until = dated.reduce((a, r) => (r.end > a ? r.end : a), dated[0].end)
        return [{ type: 'gantt', title: 'Job timeline', span: 12, from, until, rows: dated.slice(0, 15).map((r) => ({ label: jobLabel(r), start: r.start, end: r.end, progress: r.progress ?? undefined, tone: JOB_TONE[r.status], to: jobLink(r.name) })), today: data.today }]
      })(),
    ],
  }
}

const VO_TONE = { Approved: 'green', Draft: 'amber', Cancelled: 'slate' }
function variations(data) {
  const vo = data.variations
  if (!vo.available) return { kpis: [], widgets: [notice('Variation orders', vo.reason)] }
  const rows = vo.rows
  const list = { name: listRoute('variations') }
  if (!rows.length) return { kpis: [], widgets: [notice('Variation orders', `No variation orders are recorded for ${data.company} yet.`)] }
  const byJob = {}
  for (const r of rows.filter((r) => r.status !== 'Cancelled')) byJob[r.job] = (byJob[r.job] ?? 0) + (num(r.amount) ?? 0)
  return {
    kpis: [
      { label: 'Variation orders', value: rows.length, kind: 'count', tone: 'purple', to: list },
      { label: 'Approved value', value: sumOf(rows.filter((r) => r.status === 'Approved'), 'amount'), kind: 'money', tone: 'green', to: list },
      { label: 'Awaiting approval (drafts)', value: sumOf(rows.filter((r) => r.status === 'Draft'), 'amount'), kind: 'money', tone: 'amber', to: list },
      { label: 'Cancelled', value: rows.filter((r) => r.status === 'Cancelled').length, kind: 'count', tone: 'slate', to: list },
    ],
    widgets: [
      { type: 'donut', title: 'Status', span: 4, centre: 'orders', kind: 'count', to: list, segments: countSegments(rows, 'status', VO_TONE, list) },
      { type: 'hbars', title: 'Value by job (not cancelled)', span: 8, kind: 'money', series: [{ name: 'Value', tone: 'purple' }], rows: Object.entries(byJob).map(([job, value]) => ({ label: job, values: [value], to: jobLink(job) })) },
      {
        type: 'table', title: 'Variation orders', span: 12, to: list,
        columnDefs: [{ key: 'name', label: 'Variation' }, { key: 'job', label: 'Job' }, { key: 'description', label: 'Description' }, { key: 'amount', label: 'Value', kind: 'money' }, { key: 'status', label: 'Status', kind: 'chip' }, { key: 'raised', label: 'Raised', kind: 'date' }, { key: 'approved_on', label: 'Approved', kind: 'date' }],
        rows: rows.map((r) => ({ ...r, _to: { name: detailRoute('variations'), params: { name: r.name } } })),
      },
    ],
  }
}

const RESULT_TONE = { Pass: 'green', 'Pass with defects': 'amber', Fail: 'rose', 'Not recorded': 'slate' }
function quality(data) {
  const ir = data.inspections
  if (!ir.available) return { kpis: [], widgets: [notice('Inspection reports', ir.reason)] }
  const rows = ir.rows
  const list = { name: listRoute('inspections') }
  if (!rows.length) return { kpis: [], widgets: [notice('Inspection reports', `No inspection reports are recorded for ${data.company} yet.`)] }
  const byJob = {}
  for (const r of rows) byJob[r.job] = (byJob[r.job] ?? 0) + 1
  return {
    kpis: [
      { label: 'Inspection reports', value: rows.length, kind: 'count', tone: 'blue', to: list },
      { label: 'Pass', value: rows.filter((r) => r.result === 'Pass').length, kind: 'count', tone: 'green', to: list },
      { label: 'Pass with defects', value: rows.filter((r) => r.result === 'Pass with defects').length, kind: 'count', tone: 'amber', to: list },
      { label: 'Fail', value: rows.filter((r) => r.result === 'Fail').length, kind: 'count', tone: 'rose', to: list },
    ],
    widgets: [
      { type: 'donut', title: 'Results', span: 4, centre: 'reports', kind: 'count', to: list, segments: countSegments(rows, 'result', RESULT_TONE, list) },
      { type: 'hbars', title: 'Reports by job', span: 8, kind: 'count', series: [{ name: 'Reports', tone: 'blue' }], rows: Object.entries(byJob).map(([job, value]) => ({ label: job, values: [value], to: jobLink(job) })) },
      {
        type: 'table', title: 'Inspection reports', span: 12, to: list,
        columnDefs: [{ key: 'name', label: 'Report' }, { key: 'job', label: 'Job' }, { key: 'stage', label: 'Stage' }, { key: 'date', label: 'Date', kind: 'date' }, { key: 'result', label: 'Result', kind: 'chip' }, { key: 'status', label: 'Status', kind: 'chip' }, { key: 'next_action_due', label: 'Next action due', kind: 'date' }],
        rows: rows.map((r) => ({ ...r, _to: { name: detailRoute('inspections'), params: { name: r.name } } })),
      },
    ],
  }
}

const BUILDERS = { portfolio, variations, quality }

/** A live page for a Construction tab, in the shape pages.js uses (title etc. come from the sample page). */
export function livePage(tab, data, samplePage) {
  const built = BUILDERS[tab](data)
  return { ...samplePage, subtitle: `Live records for ${data.company}`, kpis: built.kpis, widgets: built.widgets }
}


export const EXECUTIVE_METHOD = '/api/method/sidra_realestate.api.staff_dashboard.get_dashboard'

/** Present the server's counts without substituting sample figures or calculating business totals. */
export function executivePage(data, samplePage) {
  const summary = data.summary
  const tiles = [
    ['Units available', 'units_available', 'properties', 'green'],
    ['Active reservations', 'active_reservations', 'reservations', 'blue'],
    ['Contracts confirmed this month', 'confirmed_contracts', 'contracts', 'purple'],
  ]
  const property = data.property
  const widgets = property.total == null
    ? [notice('Property inventory', 'Property inventory is unavailable to your account.')]
    : property.total === 0
      ? [notice('Property inventory', 'No units are visible for this Company.')]
      : [{ type: 'donut', title: 'Units by status', span: 6, kind: 'count', centre: 'units',
          segments: property.counts.map((row) => ({ label: row.status, value: row.count, tone: JOB_TONE[row.status] ?? 'blue', to: { name: 'properties' } })) }]
  widgets.push(notice('Reporting period', `Confirmed contracts are for this month. Inventory and reservations are current. Snapshot: ${data.as_of}.`))
  return { title: samplePage.title, subtitle: `Live records for ${data.scope.company_name}`,
    kpis: tiles.map(([label, key, route, tone]) => ({ label, value: summary[key] ?? null, kind: 'count', tone,
      to: { name: route === 'reservations' ? listRoute(route) : route } })), widgets }
}

export function validExecutive(data, company) {
  return data?.schema_version === 1 && data.scope?.company_id === company &&
    typeof data.scope.company_name === 'string' && typeof data.as_of === 'string' &&
    !!data.summary && !!data.property && Array.isArray(data.property.counts) &&
    data.property.counts.every((row) => typeof row.status === 'string' && Number.isFinite(row.count))
}
