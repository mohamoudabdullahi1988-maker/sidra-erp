// Live records for the Construction screens (decision G25, step 1): the same tiles and charts as
// the sample screens, built from `api.construction_live.get_construction_live`. This file only
// arranges what the server returned; it decides no permission and invents no figure. A group the
// server marks unavailable is shown with its reason, never as zero.
import { detailRoute, listRoute } from '../records.js'

export const LIVE_METHOD = '/api/method/sidra_realestate.api.construction_live.get_construction_live'

/** Construction tabs that can show live records. */
export const LIVE_TABS = { executive: ['overview'], build: ['portfolio', 'schedule', 'cost', 'variations', 'quality'] }

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

// ---------------------------------------------------------------- Schedule and Cost & budget (issue #82)
const STAGE_TONE = { Completed: 'green', 'In Progress': 'blue', Planned: 'slate', Overdue: 'rose' }
const daysLate = (planned, today) => Math.round((Date.parse(today) - Date.parse(planned)) / 86400000)

function stagesOf(rows) {
  return rows.flatMap((job) => (job.stage_rows ?? []).map((st) => ({ ...st, job: job.name, site: jobLabel(job) })))
}

function schedule(data) {
  const jobs = data.jobs
  if (!jobs.available) return { kpis: [], widgets: [notice('Stages', jobs.reason)] }
  const stages = stagesOf(jobs.rows)
  if (!stages.length) return { kpis: [], widgets: [notice('Stages', `No job stages are recorded for ${data.company} yet.`)] }
  const list = { name: 'construction' }
  const state = (st) => (st.overdue ? 'Overdue' : st.status)
  const overdue = stages.filter((st) => st.overdue)
  const counts = {}
  for (const st of stages) counts[state(st)] = (counts[state(st)] ?? 0) + 1
  const upcoming = [...overdue, ...stages.filter((st) => !st.overdue && st.status === 'In Progress')].filter((st) => st.planned_start && st.planned_end).slice(0, 14)
  const widgets = [
    { type: 'donut', title: 'Stages by status', note: 'Overdue: not completed and past its planned end', span: 4, centre: 'stages', kind: 'count', to: list,
      segments: ['Completed', 'In Progress', 'Overdue', 'Planned'].filter((k) => counts[k]).map((label) => ({ label, value: counts[label], tone: STAGE_TONE[label], to: list })) },
  ]
  if (upcoming.length) {
    const from = upcoming.reduce((a, st) => (st.planned_start < a ? st.planned_start : a), upcoming[0].planned_start)
    const until = upcoming.reduce((a, st) => (st.planned_end > a ? st.planned_end : a), data.today > upcoming[0].planned_end ? data.today : upcoming[0].planned_end)
    widgets.push({ type: 'gantt', title: 'Overdue and current stages', span: 8, from, until, milestones: true, today: data.today,
      rows: upcoming.map((st) => ({ label: st.stage, sub: `${st.site} · ${state(st)}`, start: st.planned_start, end: st.planned_end, tone: STAGE_TONE[state(st)], to: jobLink(st.job) })) })
  } else widgets.push(notice('Overdue and current stages', 'No stage is overdue or in progress.', 8))
  widgets.push({
    type: 'table', title: 'Overdue stages', span: 12, to: list,
    columnDefs: [{ key: 'job', label: 'Job' }, { key: 'site', label: 'Site' }, { key: 'stage', label: 'Stage' }, { key: 'planned_end', label: 'Planned end', kind: 'date' }, { key: 'days_late', label: 'Days late', kind: 'count' }, { key: 'completion_pct', label: 'Recorded completion', kind: 'pct' }],
    rows: overdue.sort((a, b) => (a.planned_end > b.planned_end ? 1 : -1)).map((st) => ({ ...st, days_late: daysLate(st.planned_end, data.today), _to: jobLink(st.job) })),
  })
  return {
    kpis: [
      { label: 'Stages', value: stages.length, kind: 'count', tone: 'blue', to: list },
      { label: 'Completed', value: counts.Completed ?? 0, kind: 'count', tone: 'green', to: list },
      { label: 'In progress', value: counts['In Progress'] ?? 0, kind: 'count', tone: 'sky', to: list },
      { label: 'Overdue', value: overdue.length, kind: 'count', tone: 'rose', to: list },
      { label: 'Certified', value: stages.filter((st) => st.certified).length, kind: 'count', tone: 'purple', to: list },
    ],
    widgets,
  }
}

function cost(data) {
  const jobs = data.jobs
  if (!jobs.available) return { kpis: [], widgets: [notice('Cost and budget', jobs.reason)] }
  const rows = jobs.rows
  if (!rows.length) return { kpis: [], widgets: [notice('Cost and budget', `No construction jobs are recorded for ${data.company} yet.`)] }
  const list = { name: 'construction' }
  const recorded = (key) => rows.filter((r) => r[key] !== null)
  const certifiedValue = (job) => {
    const amounts = (job.stage_rows ?? []).filter((st) => st.certified).map((st) => num(st.billing_amount))
    return amounts.some((a) => a === null) ? null : amounts.reduce((a, v) => a + v, 0)
  }
  const costRows = rows.filter((r) => r.boq_total !== null || r.current_contract_value !== null).slice(0, 12)
  const variations = rows.filter((r) => num(r.approved_variations) > 0)
  return {
    kpis: [
      { label: 'BOQ total', value: sumOf(recorded('boq_total'), 'boq_total'), kind: 'money', tone: 'sky', to: list },
      { label: 'Contract value', value: sumOf(recorded('contract_value'), 'contract_value'), kind: 'money', tone: 'blue', to: list },
      { label: 'Approved variations', value: sumOf(recorded('approved_variations'), 'approved_variations'), kind: 'money', tone: 'purple', to: { name: listRoute('variations') } },
      { label: 'Current contract value', value: sumOf(recorded('current_contract_value'), 'current_contract_value'), kind: 'money', tone: 'teal', to: list },
      { label: 'Certified milestones', value: rows.map(certifiedValue).every((v) => v !== null) ? rows.reduce((a, r) => a + certifiedValue(r), 0) : null, kind: 'money', tone: 'green', to: list },
    ],
    widgets: [
      costRows.length
        ? { type: 'hbars', title: 'BOQ total and current contract value by job', span: 7, kind: 'money', series: [{ name: 'BOQ total', tone: 'sky' }, { name: 'Current contract value', tone: 'teal' }],
            rows: costRows.map((r) => ({ label: jobLabel(r), values: [num(r.boq_total) ?? 0, num(r.current_contract_value) ?? 0], to: jobLink(r.name) })) }
        : notice('BOQ and contract value', 'No BOQ total or contract value is recorded yet.', 7),
      variations.length
        ? { type: 'hbars', title: 'Approved variations by job', span: 5, kind: 'money', series: [{ name: 'Approved variations', tone: 'purple' }], rows: variations.map((r) => ({ label: jobLabel(r), values: [num(r.approved_variations)], to: jobLink(r.name) })) }
        : notice('Approved variations', 'No variation order has been approved yet.', 5),
      {
        type: 'table', title: 'Cost by job', note: 'Milestones are payment stages, not invoices: nothing is invoiced yet (CON-07).', span: 12, to: list,
        columnDefs: [{ key: 'name', label: 'Job' }, { key: 'site', label: 'Site' }, { key: 'boq_total', label: 'BOQ total', kind: 'moneyFull' }, { key: 'contract_value', label: 'Contract value', kind: 'moneyFull' }, { key: 'approved_variations', label: 'Variations', kind: 'moneyFull' }, { key: 'current_contract_value', label: 'Current value', kind: 'moneyFull' }, { key: 'certified_value', label: 'Certified milestones', kind: 'moneyFull' }],
        rows: rows.map((r) => ({ ...r, site: jobLabel(r), certified_value: certifiedValue(r), _to: jobLink(r.name) })),
      },
    ],
  }
}

const BUILDERS = { portfolio, schedule, cost, variations, quality }

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
          segments: property.counts.map((row) => ({ label: row.status, value: row.count, tone: UNIT_TONE[row.status] ?? 'blue', to: { name: 'properties' } })) }]
  widgets.push(notice('Reporting period', `Confirmed contracts are for this month. Inventory and reservations are current. Snapshot: ${data.as_of}.`))
  const kpis = tiles.map(([label, key, route, tone]) => ({ label, value: summary[key] ?? null, kind: 'count', tone,
    to: { name: route === 'reservations' ? listRoute(route) : route } }))
  // The whole business (issue #83): construction and real estate from their own read-only
  // methods, loaded beside the dashboard. A source that failed or that the role cannot read says
  // why in its place; it never hides the others and is never shown as zero.
  if (data.extras) {
    const extra = executiveExtras(data.extras)
    kpis.push(...extra.kpis)
    // Rows of 12: inventory, sites and attention side by side, then sales, then the job table.
    if (widgets[0].type === 'donut') widgets[0] = { ...widgets[0], span: 4 }
    widgets.splice(widgets.length - 1, 0, ...extra.widgets)
    // The usual process, shown with numbered steps and no state on live records (FlowSteps).
    return { title: samplePage.title, subtitle: `Live records for ${data.scope.company_name}`, kpis, widgets, workflow: samplePage.workflow }
  }
  return { title: samplePage.title, subtitle: `Live records for ${data.scope.company_name}`, kpis, widgets }
}

/** Live Executive additions from construction_live and realestate_live answers ({ data } or { error }). */
export function executiveExtras({ construction, realestate }) {
  const kpis = []
  const widgets = []
  const attention = []
  let jobTable = null
  const c = construction?.data
  if (!c) widgets.push(notice('Construction', construction?.error || 'Construction records could not be loaded.', 4))
  else if (!c.jobs.available) widgets.push(notice('Construction', c.jobs.reason, 4))
  else {
    const jobs = c.jobs.rows
    const active = jobs.filter((r) => ACTIVE.has(r.status))
    const overdue = jobs.reduce((a, r) => a + r.stages_overdue, 0)
    kpis.push({ label: 'Active construction jobs', value: active.length, kind: 'count', tone: 'sky', to: { name: 'construction' } })
    if (jobs.length) {
      widgets.push({ type: 'map', title: 'Job sites', span: 4, empty: 'No job has a recorded location yet.',
        pins: jobs.filter((r) => r.point).map((r) => ({ label: jobLabel(r), point: r.point, tone: JOB_TONE[r.status], sub: r.status, to: jobLink(r.name) })) })
      jobTable = {
        type: 'table', title: 'Construction jobs', span: 12, to: { name: 'construction' },
        columnDefs: [{ key: 'name', label: 'Job' }, { key: 'site', label: 'Site' }, { key: 'status', label: 'Status', kind: 'chip' }, { key: 'progress', label: 'Progress', kind: 'progress' }, { key: 'stages_overdue', label: 'Overdue stages', kind: 'count' }],
        rows: [...jobs].sort((a, b) => b.stages_overdue - a.stages_overdue).slice(0, 8).map((r) => ({ ...r, site: jobLabel(r), _to: jobLink(r.name) })),
      }
    } else widgets.push(notice('Construction', `No construction jobs are recorded for ${c.company} yet.`, 4))
    if (overdue) attention.push({ tone: 'red', text: `${overdue} construction ${overdue === 1 ? 'stage is' : 'stages are'} overdue`, to: { name: 'construction-hub', params: { tab: 'schedule' }, query: { source: 'live' } } })
    if (c.variations.available) {
      const drafts = c.variations.rows.filter((r) => r.status === 'Draft').length
      if (drafts) attention.push({ tone: 'amber', text: `${drafts} variation ${drafts === 1 ? 'order awaits' : 'orders await'} approval`, to: { name: listRoute('variations') } })
    }
    if (c.inspections.available) {
      const failed = c.inspections.rows.filter((r) => r.result === 'Fail').length
      if (failed) attention.push({ tone: 'amber', text: `${failed} ${failed === 1 ? 'inspection' : 'inspections'} failed`, to: { name: listRoute('inspections') } })
    }
  }
  const r = realestate?.data
  if (!r) widgets.push(notice('Real estate sales', realestate?.error || 'Real estate records could not be loaded.', 6))
  else {
    if (r.units.available && r.units.total) {
      const statuses = UNIT_ORDER.filter((st) => r.units.status_counts[st])
      widgets.push({ type: 'hbars', title: 'Units by project', span: 6, kind: 'count', stacked: true, series: statuses.map((st) => ({ name: st, tone: UNIT_TONE[st] })),
        rows: r.units.schemes.map((sc) => ({ label: sc.name, values: statuses.map((st) => sc.counts[st] ?? 0), to: { name: 'properties' } })) })
    } else widgets.push(notice('Units by project', r.units.available ? `No units are recorded for ${r.company} yet.` : r.units.reason, 6))
    if (r.schedule.available) {
      kpis.push({ label: 'Installments due, 12 months', value: sumOf(r.schedule.months, 'amount'), kind: 'money', tone: 'teal', to: { name: 'realestate', params: { tab: 'contracts' }, query: { source: 'live' } } })
      widgets.push({ type: 'bars', title: 'Installments scheduled per month', note: 'Amounts due on confirmed contracts, not money received.', span: 6, kind: 'money',
        labels: r.schedule.months.map((m) => monthText(m.month)), series: [{ name: 'Scheduled', values: r.schedule.months.map((m) => Number(m.amount)), tone: 'sky' }] })
    } else widgets.push(notice('Installment schedule', r.schedule.reason, 6))
    if (r.leads.available) {
      kpis.push({ label: 'Leads', value: r.leads.total, kind: 'count', tone: 'purple', to: { name: listRoute('leads') } })
    }
    if (r.contracts.available) {
      const drafts = r.contracts.rows.filter((row) => row.status === 'Draft').length
      if (drafts) attention.push({ tone: 'blue', text: `${drafts} sale ${drafts === 1 ? 'contract is' : 'contracts are'} still in draft`, to: { name: 'contracts' } })
    }
  }
  // Attention sits beside the sites map (row 1); the job table closes the section.
  widgets.splice(1, 0, { type: 'list', title: 'Needs attention', span: 4, items: attention.length ? attention : [{ tone: 'blue', text: 'Nothing recorded needs attention.' }] })
  if (jobTable) widgets.push(jobTable)
  return { kpis, widgets }
}

export function validExecutive(data, company) {
  return data?.schema_version === 1 && data.scope?.company_id === company &&
    typeof data.scope.company_name === 'string' && typeof data.as_of === 'string' &&
    !!data.summary && !!data.property && Array.isArray(data.property.counts) &&
    data.property.counts.every((row) => typeof row.status === 'string' && Number.isFinite(row.count))
}

// ---------------------------------------------------------------- Real Estate Sales (17 Nov demonstration)
export const REALESTATE_METHOD = '/api/method/sidra_realestate.api.realestate_live.get_realestate_live'
LIVE_TABS.realestate = ['inventory', 'pipeline', 'contracts']

const UNIT_TONE = { Available: 'green', Reserved: 'amber', 'Under Contract': 'purple', Sold: 'blue', Blocked: 'slate' }
const UNIT_ORDER = ['Sold', 'Under Contract', 'Reserved', 'Available', 'Blocked']
const CONTRACT_TONE = { Confirmed: 'green', Draft: 'amber', Cancelled: 'slate' }
const MONTH = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const monthText = (ym) => `${MONTH[Number(ym.slice(5, 7)) - 1]} ${ym.slice(2, 4)}`

function inventory(data) {
  const u = data.units
  if (!u.available) return { kpis: [], widgets: [notice('Plots and units', u.reason)] }
  if (!u.total) return { kpis: [], widgets: [notice('Plots and units', `No units are recorded for ${data.company} yet.`)] }
  const units = { name: 'properties' }
  const count = (status) => u.status_counts[status] ?? 0
  const statuses = UNIT_ORDER.filter((s) => count(s))
  return {
    kpis: [
      { label: 'Plots and units', value: u.total, kind: 'count', tone: 'blue', to: units },
      { label: 'Available', value: count('Available'), kind: 'count', tone: 'green', to: units },
      { label: 'Reserved', value: count('Reserved'), kind: 'count', tone: 'amber', to: units },
      { label: 'Under contract or sold', value: count('Under Contract') + count('Sold'), kind: 'count', tone: 'purple', to: units },
      { label: 'Value available', value: u.value_available === null ? null : Number(u.value_available), kind: 'money', tone: 'teal', to: units },
    ],
    widgets: [
      { type: 'donut', title: 'Units by status', span: 4, centre: 'units', kind: 'count', to: units, segments: statuses.map((s) => ({ label: s, value: count(s), tone: UNIT_TONE[s], to: units })) },
      {
        type: 'hbars', title: 'Status by project', span: 8, kind: 'count', stacked: true,
        series: statuses.map((s) => ({ name: s, tone: UNIT_TONE[s] })),
        rows: u.schemes.map((s) => ({ label: s.name, values: statuses.map((st) => s.counts[st] ?? 0), to: units })),
      },
    ],
  }
}

function pipeline(data) {
  const l = data.leads
  const r = data.reservations
  const widgets = []
  const kpis = []
  if (l.available) {
    const list = { name: listRoute('leads') }
    kpis.push({ label: 'Leads', value: l.total, kind: 'count', tone: 'sky', to: list })
    if (l.total) {
      widgets.push({ type: 'donut', title: 'Leads by status', span: 6, centre: 'leads', kind: 'count', to: list, segments: Object.entries(l.status_counts).map(([label, value], i) => ({ label, value, tone: ['sky', 'blue', 'teal', 'amber', 'green', 'purple', 'slate'][i % 7], to: list })) })
      widgets.push({ type: 'hbars', title: 'Where leads come from', span: 6, kind: 'count', series: [{ name: 'Leads', tone: 'purple' }], rows: Object.entries(l.source_counts).map(([label, value]) => ({ label, values: [value], to: list })) })
    } else widgets.push(notice('Leads', `No leads are recorded for ${data.company} yet.`))
  } else widgets.push(notice('Leads', l.reason))
  if (r.available) {
    const list = { name: listRoute('reservations') }
    kpis.push({ label: 'Active reservations', value: r.counts.Active ?? 0, kind: 'count', tone: 'amber', to: list })
    kpis.push({ label: 'Reservations converted', value: r.counts.Converted ?? 0, kind: 'count', tone: 'green', to: list })
  } else widgets.push(notice('Reservations', r.reason))
  return { kpis, widgets }
}

function contracts(data) {
  const c = data.contracts
  if (!c.available) return { kpis: [], widgets: [notice('Sale contracts', c.reason)] }
  if (!c.rows.length) return { kpis: [], widgets: [notice('Sale contracts', `No sale contracts are recorded for ${data.company} yet.`)] }
  const list = { name: 'contracts' }
  const confirmed = c.rows.filter((r) => r.status === 'Confirmed')
  const s = data.schedule
  return {
    kpis: [
      { label: 'Sale contracts', value: c.rows.length, kind: 'count', tone: 'blue', to: list },
      { label: 'Confirmed', value: confirmed.length, kind: 'count', tone: 'green', to: list },
      { label: 'Drafts', value: c.rows.filter((r) => r.status === 'Draft').length, kind: 'count', tone: 'amber', to: list },
      { label: 'Agreed value (confirmed)', value: sumOf(confirmed.filter((r) => r.agreed_price !== null), 'agreed_price'), kind: 'money', tone: 'sky', to: list },
      { label: 'Scheduled, next 12 months', value: s.available ? sumOf(s.months, 'amount') : null, kind: 'money', tone: 'teal', to: { name: 'collections' } },
    ],
    widgets: [
      s.available
        ? { type: 'bars', title: 'Installments scheduled per month', note: 'Confirmed contracts. Amounts due, not money received: payments are not recorded yet.', span: 8, kind: 'money', labels: s.months.map((m) => monthText(m.month)), series: [{ name: 'Scheduled', values: s.months.map((m) => Number(m.amount)), tone: 'sky' }] }
        : notice('Installment schedule', s.reason, 8),
      { type: 'donut', title: 'Contracts by status', span: 4, centre: 'contracts', kind: 'count', to: list, segments: countSegments(c.rows, 'status', CONTRACT_TONE, list) },
      {
        type: 'table', title: 'Latest contracts', span: 12, to: list,
        columnDefs: [{ key: 'name', label: 'Contract' }, { key: 'customer', label: 'Customer' }, { key: 'type', label: 'Type' }, { key: 'source', label: 'Source' }, { key: 'status', label: 'Status', kind: 'chip' }, { key: 'agreed_price', label: 'Agreed price', kind: 'moneyFull' }, { key: 'signed_on', label: 'Signed', kind: 'date' }],
        rows: c.rows.map((r) => ({ ...r, _to: { name: 'contract-detail', params: { name: r.name } } })),
      },
    ],
  }
}

const REALESTATE_BUILDERS = { inventory, pipeline, contracts }
export function realestatePage(tab, data, samplePage) {
  const built = REALESTATE_BUILDERS[tab](data)
  return { ...samplePage, subtitle: `Live records for ${data.company}`, kpis: built.kpis, widgets: built.widgets }
}

// ---------------------------------------------------------------- Finance, Design & Engineering, Subcontractors, Stock (15 Nov 2026)
export const FINANCE_METHOD = '/api/method/sidra_realestate.api.finance_live.get_finance_live'
export const OPERATIONS_METHOD = '/api/method/sidra_realestate.api.finance_live.get_operations_live'
LIVE_TABS.build.push('stock', 'subcontractors')
LIVE_TABS.design = ['overview', 'inspection']
LIVE_TABS.finance = ['overview']

const ledger = { name: 'finance' }

function finance(data) {
  const p = data.pnl
  const kpis = []
  const widgets = []
  if (p.available) {
    const inc = p.months.map((m) => num(m.income))
    const exp = p.months.map((m) => num(m.expense))
    const sum = (xs) => (xs.some((x) => x === null) ? null : xs.reduce((a, x) => a + x, 0))
    kpis.push(
      { label: 'Income (12 months)', value: sum(inc), kind: 'money', tone: 'blue', to: ledger },
      { label: 'Expenses (12 months)', value: sum(exp), kind: 'money', tone: 'orange', to: ledger },
      { label: 'Net', value: sum(inc) === null || sum(exp) === null ? null : sum(inc) - sum(exp), kind: 'money', tone: 'green', to: ledger },
    )
    widgets.push({ type: 'bars', title: 'Income and expenses per month', note: 'From the ledger (posted entries).', span: 8, kind: 'money', labels: p.months.map((m) => monthText(m.month)),
      series: [{ name: 'Income', values: inc.map((v) => v ?? 0), tone: 'blue' }, { name: 'Expenses', values: exp.map((v) => v ?? 0), tone: 'orange' }] })
    widgets.push(p.expense_accounts.length
      ? { type: 'donut', title: 'Expenses by account', span: 4, centre: '12 months', kind: 'money', to: ledger, segments: p.expense_accounts.map((a, i) => ({ label: a.account, value: num(a.amount) ?? 0, tone: ['blue', 'teal', 'purple', 'orange', 'amber', 'rose', 'sky', 'slate'][i % 8], to: ledger })) }
      : notice('Expenses by account', 'No expense is posted in the last 12 months.', 4))
  } else widgets.push(notice('Income and expenses', p.reason))
  const c = data.cash
  if (c.available) {
    kpis.push({ label: 'Cash and bank', value: sumOf(c.accounts, 'balance'), kind: 'money', tone: 'teal', to: ledger })
    widgets.push(c.accounts.length
      ? { type: 'table', title: 'Bank and cash accounts', span: 6, to: ledger, columnDefs: [{ key: 'account', label: 'Account' }, { key: 'type', label: 'Type', kind: 'chip' }, { key: 'balance', label: 'Balance', kind: 'money' }], rows: c.accounts }
      : notice('Bank and cash accounts', 'No bank or cash account is set up for this Company.', 6))
  } else widgets.push(notice('Bank and cash', c.reason, 6))
  for (const [key, title, tone, label] of [['receivables', 'Owed to Sidra, by age', 'sky', 'Owed to Sidra'], ['payables', 'Sidra owes, by age', 'rose', 'Sidra owes']]) {
    const g = data[key]
    if (!g.available) { widgets.push(notice(title, g.reason, 6)); continue }
    kpis.push({ label, value: sumOf(g.buckets, 'amount'), kind: 'money', tone, to: ledger })
    widgets.push({ type: 'hbars', title, note: 'Submitted invoices with an amount outstanding', span: 6, kind: 'money', series: [{ name: label, tone }],
      rows: g.buckets.map((b, i) => ({ label: `${b.age} (${b.count})`, values: [num(b.amount) ?? 0], tone: ['green', 'amber', 'orange', 'rose', 'purple'][i], to: ledger })) })
  }
  return { kpis, widgets }
}

const SERVICE_TONE = { 'Design Only': 'purple', 'Inspection Only': 'teal' }
const OPEN = (r) => !['Completed', 'Closed', 'Cancelled'].includes(r.status)

function designOverview(data) {
  const jobs = data.jobs
  if (!jobs.available) return { kpis: [], widgets: [notice('Design and inspection jobs', jobs.reason)] }
  const rows = jobs.rows.filter((r) => SERVICE_TONE[r.service_type])
  if (!rows.length) return { kpis: [], widgets: [notice('Design and inspection jobs', `No Design Only or Inspection Only jobs are recorded for ${data.company} yet.`)] }
  const list = { name: 'construction' }
  return {
    kpis: [
      { label: 'Design jobs', value: rows.filter((r) => r.service_type === 'Design Only').length, kind: 'count', tone: 'purple', to: list },
      { label: 'Inspection jobs', value: rows.filter((r) => r.service_type === 'Inspection Only').length, kind: 'count', tone: 'teal', to: list },
      { label: 'Open', value: rows.filter(OPEN).length, kind: 'count', tone: 'blue', to: list },
      { label: 'Contract value', value: sumOf(rows.filter((r) => r.current_contract_value !== null), 'current_contract_value'), kind: 'money', tone: 'green', to: list },
    ],
    widgets: [
      { type: 'donut', title: 'Jobs by service', span: 4, centre: 'jobs', kind: 'count', to: list, segments: countSegments(rows, 'service_type', SERVICE_TONE, list) },
      { type: 'donut', title: 'Jobs by status', span: 4, centre: 'jobs', kind: 'count', to: list, segments: countSegments(rows, 'status', JOB_TONE, list) },
      notice('Where these come from', 'Construction jobs whose service type is Design Only or Inspection Only. Architecture and civil engineering are not told apart in the records yet.', 4),
      { type: 'table', title: 'Design and inspection jobs', span: 12, to: list,
        columnDefs: [{ key: 'name', label: 'Job' }, { key: 'customer', label: 'Client' }, { key: 'service_type', label: 'Service', kind: 'chip' }, { key: 'status', label: 'Status', kind: 'chip' }, { key: 'current_contract_value', label: 'Value', kind: 'money' }, { key: 'end', label: 'Due', kind: 'date' }],
        rows: rows.map((r) => ({ ...r, _to: jobLink(r.name) })) },
    ],
  }
}

function designInspection(data) {
  const jobs = data.jobs.available ? data.jobs.rows.filter((r) => r.service_type === 'Inspection Only') : []
  const ir = data.inspections
  const kpis = [{ label: 'Inspection jobs', value: data.jobs.available ? jobs.length : null, kind: 'count', tone: 'teal', to: { name: 'construction' } }]
  const widgets = []
  if (ir.available) {
    const list = { name: listRoute('inspections') }
    kpis.push({ label: 'Inspection reports', value: ir.rows.length, kind: 'count', tone: 'blue', to: list }, { label: 'Failed', value: ir.rows.filter((r) => r.result === 'Fail').length, kind: 'count', tone: 'rose', to: list })
    widgets.push(ir.rows.length ? { type: 'donut', title: 'Report results', span: 4, centre: 'reports', kind: 'count', to: list, segments: countSegments(ir.rows, 'result', RESULT_TONE, list) } : notice('Inspection reports', 'No inspection reports are recorded yet.', 4))
  } else widgets.push(notice('Inspection reports', ir.reason, 4))
  widgets.push(jobs.length
    ? { type: 'table', title: 'Inspection jobs', span: 8, to: { name: 'construction' }, columnDefs: [{ key: 'name', label: 'Job' }, { key: 'customer', label: 'Client' }, { key: 'site', label: 'Site' }, { key: 'status', label: 'Status', kind: 'chip' }], rows: jobs.map((r) => ({ ...r, _to: jobLink(r.name) })) }
    : notice('Inspection jobs', data.jobs.available ? 'No Inspection Only jobs are recorded yet.' : data.jobs.reason, 8))
  return { kpis, widgets }
}

function subcontractors(data) {
  const s = data.suppliers
  if (!s.available) return { kpis: [], widgets: [notice('Suppliers and subcontractors', s.reason)] }
  if (!s.rows.length) return { kpis: [], widgets: [notice('Suppliers and subcontractors', `No purchase invoices are recorded for ${data.company} yet.`)] }
  return {
    kpis: [
      { label: 'Suppliers invoicing', value: s.rows.length, kind: 'count', tone: 'blue', to: ledger },
      { label: 'Purchase invoices', value: s.rows.reduce((a, r) => a + r.invoices, 0), kind: 'count', tone: 'sky', to: ledger },
      { label: 'Invoiced', value: sumOf(s.rows, 'invoiced'), kind: 'money', tone: 'teal', to: ledger },
      { label: 'Still owed', value: sumOf(s.rows, 'owed'), kind: 'money', tone: 'rose', to: ledger },
    ],
    widgets: [
      { type: 'hbars', title: 'Invoiced and owed by supplier', span: 7, kind: 'money', series: [{ name: 'Invoiced', tone: 'teal' }, { name: 'Owed', tone: 'rose' }], rows: s.rows.slice(0, 10).map((r) => ({ label: r.name, values: [num(r.invoiced) ?? 0, num(r.owed) ?? 0], to: ledger })) },
      { type: 'table', title: 'Suppliers', span: 5, to: ledger, columnDefs: [{ key: 'name', label: 'Supplier' }, { key: 'group', label: 'Group' }, { key: 'invoices', label: 'Invoices', kind: 'count' }, { key: 'owed', label: 'Owed', kind: 'money' }], rows: s.rows },
    ],
  }
}

function stock(data) {
  const s = data.stock
  if (!s.available) return { kpis: [], widgets: [notice('Stock', s.reason)] }
  if (!s.rows.length) return { kpis: [{ label: 'Warehouses', value: s.warehouses, kind: 'count', tone: 'blue', to: ledger }], widgets: [notice('Stock on hand', `No stock is recorded in ERPNext for ${data.company} yet. Stock is kept in ERPNext's own Stock module; it appears here once goods are received.`)] }
  return {
    kpis: [
      { label: 'Items in stock', value: new Set(s.rows.map((r) => r.item)).size, kind: 'count', tone: 'blue', to: ledger },
      { label: 'Warehouses', value: s.warehouses, kind: 'count', tone: 'sky', to: ledger },
      { label: 'Stock value', value: sumOf(s.rows.filter((r) => r.value !== null), 'value'), kind: 'money', tone: 'teal', to: ledger },
    ],
    widgets: [
      { type: 'hbars', title: 'Stock value by item', span: 6, kind: 'money', series: [{ name: 'Value', tone: 'teal' }], rows: s.rows.filter((r) => r.value !== null).slice(0, 12).map((r) => ({ label: r.name, values: [num(r.value)], to: ledger })) },
      { type: 'table', title: 'Stock on hand', span: 6, to: ledger, columnDefs: [{ key: 'name', label: 'Item' }, { key: 'warehouse', label: 'Warehouse' }, { key: 'qty', label: 'Quantity', kind: 'count' }, { key: 'uom', label: 'Unit' }, { key: 'value', label: 'Value', kind: 'money' }], rows: s.rows },
    ],
  }
}

/** Which server method a live screen reads (Executive is handled by Showcase.vue itself). */
export function liveMethod(module, tab) {
  if (module === 'realestate') return REALESTATE_METHOD
  if (module === 'finance') return FINANCE_METHOD
  if (module === 'build' && (tab === 'stock' || tab === 'subcontractors')) return OPERATIONS_METHOD
  return LIVE_METHOD
}

const MORE_BUILDERS = { finance: { overview: finance }, design: { overview: designOverview, inspection: designInspection }, build: { stock, subcontractors } }

/** The live page for any module and tab other than Executive. */
export function livePageFor(module, tab, data, samplePage) {
  if (module === 'realestate') return realestatePage(tab, data, samplePage)
  const builder = MORE_BUILDERS[module]?.[tab]
  if (!builder) return livePage(tab, data, samplePage)
  const built = builder(data)
  return { ...samplePage, subtitle: `Live records for ${data.company}`, kpis: built.kpis, widgets: built.widgets }
}
