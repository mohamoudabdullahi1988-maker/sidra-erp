import test from 'node:test'
import assert from 'node:assert/strict'

// The sample screens are data (src/showcase/pages.js). These checks keep every drill-down link,
// table column and chart series consistent, so no tile or chart opens an empty or broken list.
globalThis.window = { berjaya_boot: { nav: [], lists: {} } }
const { MODULES } = await import('../src/showcase/pages.js')
const { DATASETS, filterRows } = await import('../src/showcase/datasets.js')
const D = await import('../src/showcase/data.js')
const { niceScale, donutArcs, datePosition } = await import('../src/showcase/charts.js')
const { money, pct, date } = await import('../src/showcase/format.js')

function* links(page) {
  for (const k of page.kpis) yield [k.label, k.to]
  for (const w of page.widgets) {
    yield [w.title, w.to]
    for (const s of w.segments ?? []) yield [`${w.title} / ${s.label}`, s.to]
    for (const r of w.rows ?? []) yield [`${w.title} / ${r.label}`, r.to]
    for (const p of w.pins ?? []) yield [`${w.title} / ${p.label}`, p.to]
    for (const i of w.items ?? []) yield [`${w.title} / ${i.text}`, i.to]
  }
}
const pages = Object.entries(MODULES).flatMap(([m, mod]) => Object.entries(mod.tabs).map(([t, page]) => [`${m}/${t}`, page]))

test('every module has a label, route and a label for each tab', () => {
  for (const mod of Object.values(MODULES)) {
    assert.ok(mod.label && mod.route)
    for (const key of Object.keys(mod.tabs)) assert.ok(mod.tabLabels[key], `${mod.label}: ${key}`)
  }
})

test('every sample link opens a list with at least one row', () => {
  for (const [name, page] of pages) {
    for (const [label, to] of links(page)) {
      if (!to?.set) continue
      const set = DATASETS[to.set]
      assert.ok(set, `${name} ${label}: no list ${to.set}`)
      for (const key of Object.keys(to.filter ?? {})) assert.ok(key in set.rows[0], `${name} ${label}: ${to.set} has no field ${key}`)
      assert.ok(filterRows(set, to.filter).length > 0, `${name} ${label}: ${JSON.stringify(to)} matches no row`)
    }
  }
})

test('every table names columns its list has, and every page shows a workflow', () => {
  for (const [name, page] of pages) {
    assert.ok(page.workflow?.steps?.length, `${name}: no workflow`)
    for (const w of page.widgets.filter((w) => w.type === 'table')) {
      for (const key of w.columns) assert.ok(DATASETS[w.set].columns.some((c) => c.key === key), `${name}: ${w.set}.${key}`)
    }
    for (const w of page.widgets.filter((w) => w.type === 'bars')) {
      for (const s of w.series) assert.equal(s.values.length, w.labels.length, `${name} ${w.title} ${s.name}`)
    }
  }
})

test('tile figures agree with the rows behind them', () => {
  const units = DATASETS.units.rows
  const total = D.COMMUNITIES.reduce((a, c) => a + c.total, 0)
  assert.equal(units.length, total)
  assert.equal(units.filter((u) => u.status === 'Available').length, D.COMMUNITIES.reduce((a, c) => a + c.available, 0))
  for (const b of D.AGEING) {
    const rows = filterRows(DATASETS.overdue, { bucket: b.bucket })
    assert.equal(rows.length, b.contracts)
    assert.ok(Math.abs(D.sum(rows, 'overdue') - b.amount) <= b.contracts, b.bucket)
  }
  assert.equal(DATASETS.leads.rows.length, D.FUNNEL[0][1])
  for (const deal of D.DEALS) assert.equal(deal.commission, Math.round(deal.price * 0.025))
})

test('chart geometry', () => {
  assert.deepEqual(niceScale(870), { max: 1000, ticks: [0, 250, 500, 750, 1000] })
  assert.deepEqual(niceScale(0), { max: 1, ticks: [0, 1] })
  const arcs = donutArcs([1, 1, 2])
  assert.deepEqual(arcs.map((a) => a.share), [25, 25, 50])
  assert.equal(arcs[0].offset, 25)
  assert.equal(datePosition('2026-01-01', '2026-01-01', '2027-01-01'), 0)
  assert.equal(datePosition('2028-01-01', '2026-01-01', '2027-01-01'), 100)
})

test('display formats', () => {
  assert.equal(money(14600000), '$14.6m')
  assert.equal(money(-480000), '-$480k')
  assert.equal(money(98800), '$98.8k')
  assert.equal(money(950), '$950')
  assert.equal(pct(91), '91%')
  assert.equal(date('2026-11-14'), '14 Nov 2026')
})

// ---------------------------------------------------------------- live records (G25 step 1)
const { livePage, LIVE_TABS } = await import('../src/showcase/live.js')
const sample = MODULES.build.tabs.portfolio
const LIVE = {
  company: 'Synthetic Homes',
  today: '2026-11-14',
  jobs: {
    available: true,
    rows: [
      { name: 'SCJ-1', customer: 'Synthetic Buyer', site: 'Plot 4', status: 'In Progress', point: [9.56, 44.06], current_contract_value: '20000.00', approved_variations: '800.00', start: '2026-01-01', end: '2026-12-31', progress: 40, stages: 3, stages_completed: 1, stages_overdue: 1 },
      { name: 'SCJ-2', customer: 'Synthetic Client', site: null, status: 'Quoted', point: null, current_contract_value: null, approved_variations: null, start: null, end: null, progress: null, stages: 0, stages_completed: 0, stages_overdue: 0 },
    ],
  },
  variations: { available: false, reason: 'Your role does not include variation orders.', rows: [] },
  inspections: { available: true, rows: [] },
}

test('live portfolio shows recorded figures only', () => {
  const page = livePage('portfolio', LIVE, sample)
  const tile = (label) => page.kpis.find((k) => k.label === label).value
  assert.equal(tile('Jobs'), 2)
  assert.equal(tile('Active'), 1)
  assert.equal(tile('Current contract value'), 20000) // a job with no recorded value is left out, not counted as 0
  assert.equal(tile('Average progress'), 40) // a job without stages has no progress
  const map = page.widgets.find((w) => w.type === 'map')
  assert.deepEqual(map.pins.map((p) => p.point), [[9.56, 44.06]])
  const gantt = page.widgets.find((w) => w.type === 'gantt')
  assert.equal(gantt.rows.length, 1)
  assert.match(page.subtitle, /Synthetic Homes/)
})

test('an unavailable or empty live group says why instead of showing zero', () => {
  const vo = livePage('variations', LIVE, MODULES.build.tabs.variations)
  assert.equal(vo.kpis.length, 0)
  assert.equal(vo.widgets[0].items[0].text, 'Your role does not include variation orders.')
  const ir = livePage('quality', LIVE, MODULES.build.tabs.quality)
  assert.match(ir.widgets[0].items[0].text, /No inspection reports are recorded for Synthetic Homes/)
  assert.deepEqual(LIVE_TABS.build, ['portfolio', 'schedule', 'cost', 'variations', 'quality', 'stock', 'subcontractors', 'risk'])
})

test('a missing value is a dash, never zero', () => {
  for (const fn of [money]) assert.equal(fn(null), '—')
  assert.equal(pct(undefined), '—')
})

const { executivePage, executiveExtras, validExecutive } = await import('../src/showcase/live.js')
const executiveData = {
  schema_version: 1, as_of: '2026-11-15T10:00:00', scope: { company_id: 'Synthetic Homes', company_name: 'Synthetic Homes' },
  summary: { units_available: 7, active_reservations: null, confirmed_contracts: 0 },
  property: { total: 9, counts: [{ status: 'Available', count: 7 }, { status: 'Reserved', count: 2 }] },
}
test('live Executive presents server counts and live links, preserving withheld and zero values', () => {
  const page = executivePage(executiveData, MODULES.executive.tabs.overview)
  assert.deepEqual(page.kpis.map(k => k.value), [7, null, 0])
  assert.equal(page.widgets[0].segments[0].value, 7)
  assert.equal(page.widgets[0].segments[0].to.name, 'properties')
  assert.equal(page.kpis[1].to.name, 'reservations-list')
  assert.equal(page.workflow, undefined)
  assert.match(page.subtitle, /Synthetic Homes/)
})
test('live Executive distinguishes unavailable inventory from an empty Company', () => {
  const page = (property) => executivePage({ ...executiveData, property }, MODULES.executive.tabs.overview)
  assert.match(page({ total: null, counts: [] }).widgets[0].items[0].text, /unavailable/)
  assert.match(page({ total: 0, counts: [] }).widgets[0].items[0].text, /No units/)
})
test('Executive rejects incompatible and wrong-Company responses', () => {
  assert.ok(validExecutive(executiveData, 'Synthetic Homes'))
  assert.ok(!validExecutive(executiveData, 'Other Company'))
  for (const data of [null, {}, { ...executiveData, schema_version: 2 }, { ...executiveData, property: {} }]) {
    assert.ok(!validExecutive(data, 'Synthetic Homes'))
  }
})

// ---------------------------------------------------------------- live Real Estate Sales (17 Nov demonstration)
const { realestatePage } = await import('../src/showcase/live.js')
const RE = {
  company: 'Synthetic Homes',
  today: '2026-11-15',
  units: { available: true, total: 6, status_counts: { Available: 3, Reserved: 1, Sold: 2 }, value_available: '36000.00', schemes: [{ scheme: 'S1', name: 'Masalaha Hagbad', counts: { Available: 3, Reserved: 1, Sold: 2 }, total: 6 }], points: [] },
  reservations: { available: true, counts: { Active: 1, Converted: 2 } },
  contracts: { available: true, rows: [
    { name: 'SSC-1', customer: 'Synthetic Buyer', type: 'Installment', source: 'Generated from profile', status: 'Confirmed', signed_on: '2026-11-05', agreed_price: '14300.00' },
    { name: 'SSC-2', customer: 'Synthetic Buyer 2', type: 'Cash', source: 'External (registered)', status: 'Draft', signed_on: null, agreed_price: null },
  ] },
  schedule: { available: true, months: [{ month: '2026-11', amount: '650.00', rows: 1 }, { month: '2026-12', amount: '650.00', rows: 1 }] },
  leads: { available: false, reason: 'Your role does not include leads.', status_counts: {}, source_counts: {} },
}

test('live Real Estate Sales shows recorded figures and says why a group is missing', () => {
  const inv = realestatePage('inventory', RE, MODULES.realestate.tabs.inventory)
  const tile = (page, label) => page.kpis.find((k) => k.label === label).value
  assert.equal(tile(inv, 'Plots and units'), 6)
  assert.equal(tile(inv, 'Value available'), 36000)
  assert.equal(inv.widgets[1].rows[0].label, 'Masalaha Hagbad')
  const con = realestatePage('contracts', RE, MODULES.realestate.tabs.contracts)
  assert.equal(tile(con, 'Agreed value (confirmed)'), 14300) // drafts are not counted
  assert.equal(tile(con, 'Scheduled, next 12 months'), 1300)
  const pipe = realestatePage('pipeline', RE, MODULES.realestate.tabs.pipeline)
  assert.equal(pipe.widgets[0].items[0].text, 'Your role does not include leads.')
  assert.equal(tile(pipe, 'Active reservations'), 1)
})

// ---------------------------------------------------------------- live Schedule and Cost & budget (issue #82)
test('live Schedule and Cost show recorded stages and values only', () => {
  const data = {
    company: 'Synthetic Homes',
    today: '2026-11-15',
    jobs: { available: true, rows: [
      { name: 'SCJ-1', site: 'Rayan Gardens, plot 3', status: 'In Progress', boq_total: '40000.00', contract_value: '42000.00', approved_variations: '800.00', current_contract_value: '42800.00',
        stage_rows: [
          { stage: 'Foundation', status: 'Completed', planned_start: '2026-08-01', planned_end: '2026-09-01', completion_pct: 100, certified: true, overdue: false, billing_amount: '8560.00' },
          { stage: 'Structure', status: 'In Progress', planned_start: '2026-09-01', planned_end: '2026-11-01', completion_pct: 40, certified: false, overdue: true, billing_amount: '12840.00' },
          { stage: 'Roofing', status: 'Planned', planned_start: '2026-11-01', planned_end: '2027-01-01', completion_pct: 0, certified: false, overdue: false, billing_amount: '8560.00' },
        ] },
      { name: 'SCJ-2', site: null, customer: 'Synthetic Client', status: 'Enquiry', boq_total: null, contract_value: null, approved_variations: null, current_contract_value: null, stage_rows: [] },
    ] },
  }
  const tile = (page, label) => page.kpis.find((k) => k.label === label).value
  const sched = livePage('schedule', data, MODULES.build.tabs.schedule)
  assert.equal(tile(sched, 'Stages'), 3)
  assert.equal(tile(sched, 'Overdue'), 1)
  assert.equal(tile(sched, 'In progress'), 1) // overdue work can still be in progress
  assert.equal(tile(sched, 'Certified'), 1)
  const late = sched.widgets.find((w) => w.title === 'Overdue stages').rows
  assert.deepEqual(late.map((r) => [r.stage, r.days_late]), [['Structure', 14]])
  const cost = livePage('cost', data, MODULES.build.tabs.cost)
  assert.equal(tile(cost, 'BOQ total'), null) // an incomplete total stays unknown
  assert.equal(tile(cost, 'Current contract value'), null)
  assert.equal(tile(cost, 'Certified milestones'), 8560)
  const none = livePage('schedule', { ...data, jobs: { available: true, rows: [data.jobs.rows[1]] } }, MODULES.build.tabs.schedule)
  assert.match(none.widgets[0].items[0].text, /No job stages are recorded/)
})

// ---------------------------------------------------------------- live Executive: construction and sales (issue #83)
test('live Executive adds construction and sales, and a failed source says why without hiding the others', () => {
  const construction = { data: { company: 'Synthetic Homes', jobs: { available: true, summary: { active_jobs: 1, overdue_stages: 2 }, rows: [
    { name: 'SCJ-1', site: 'Rayan Gardens, plot 3', status: 'In Progress', progress: 40, stages_overdue: 2, point: [9.5, 44.1] },
    { name: 'SCJ-2', site: null, customer: 'Synthetic Client', status: 'Quoted', progress: null, stages_overdue: 0, point: null },
  ] }, variations: { available: true, rows: [{ name: 'SVO-1', status: 'Draft' }, { name: 'SVO-2', status: 'Approved' }] }, inspections: { available: false, reason: 'no', rows: [] } } }
  const page = executivePage({ ...executiveData, extras: { construction, realestate: { error: 'The server could not be reached.' } } }, MODULES.executive.tabs.overview)
  assert.deepEqual(page.kpis.slice(0, 3).map((k) => k.value), [7, null, 0]) // the dashboard's own tiles stay first
  assert.equal(page.kpis.find((k) => k.label === 'Active construction jobs').value, 1)
  assert.ok(page.widgets.some((w) => w.title === 'Real estate sales' && w.items[0].text === 'The server could not be reached.'))
  const attention = page.widgets.find((w) => w.title === 'Needs attention').items.map((i) => i.text)
  assert.ok(attention.some((text) => text.includes('2 overdue stages')))
  assert.ok(attention.some((text) => text.includes('SVO-1')))
  assert.ok(attention.some((text) => text.includes('unavailable')))
  assert.equal(page.widgets.at(-1).title, 'Reporting period')
  assert.ok(page.workflow?.steps?.length) // the usual process; live screens show no state on it
  const quiet = executiveExtras({ construction: { error: 'x' }, realestate: { error: 'y' } })
  assert.match(quiet.widgets.find((w) => w.title === 'Needs attention').items[0].text, /unavailable/)
  assert.equal(quiet.kpis.length, 0)
})

test('all Executive sources start together and dashboard failure does not hide others', async () => {
  const { loadExecutiveSources } = await import('../src/showcase/liveSources.js')
  const pending = []
  const promise = loadExecutiveSources('Synthetic Homes', (method, params) => new Promise((resolve, reject) => pending.push({ method, params, resolve, reject })))
  assert.equal(pending.length, 3)
  assert.ok(pending.every((p) => p.params.company === 'Synthetic Homes'))
  pending[0].reject(new Error('Dashboard restricted'))
  pending[1].resolve({ message: LIVE })
  pending[2].resolve({ message: RE })
  const result = await promise
  assert.equal(result.dashboard_error, 'Dashboard restricted')
  assert.equal(result.extras.construction.data.company, 'Synthetic Homes')
  const page = executivePage(result, MODULES.executive.tabs.overview)
  assert.ok(page.widgets.some((w) => w.title === 'Job sites'))
  assert.ok(page.widgets.some((w) => w.title === 'Dashboard summary'))
})

test('wrong Company and malformed sources are isolated, never rendered', async () => {
  const { loadExecutiveSources } = await import('../src/showcase/liveSources.js')
  const result = await loadExecutiveSources('Synthetic Homes', async () => ({ message: { ...LIVE, company: 'Other Company' } }))
  assert.ok(result.dashboard_error)
  assert.ok(result.extras.construction.error)
  assert.ok(result.extras.realestate.error)
  assert.equal(result.scope.company_id, 'Synthetic Homes')
  const malformed = await loadExecutiveSources('Synthetic Homes', async () => ({ message: { company: 'Synthetic Homes', jobs: {} } }))
  assert.ok(malformed.extras.construction.error)
})

test('Executive shows expiry records, lead statuses and group denial reasons', () => {
  const realestate = structuredClone(RE)
  realestate.reservations = { available: true, expiring: [{ name: 'RES-1', expires_on: '2026-11-20' }] }
  realestate.leads = { available: true, total: 4, status_counts: { Open: 4 } }
  realestate.contracts.status_counts = { Confirmed: 8, Draft: 1 }
  realestate.schedule.total = '1234.56'
  const page = executiveExtras({ construction: { data: LIVE }, realestate: { data: realestate } })
  assert.equal(page.kpis.find((k) => k.label === 'Confirmed contracts').value, 8)
  assert.equal(page.kpis.find((k) => k.label === 'Installments due, 12 months').value, '1234.56')
  assert.ok(page.widgets.some((w) => w.title === 'Leads by status'))
  assert.ok(page.widgets.some((w) => w.title === 'Variation orders' && w.items[0].text === LIVE.variations.reason))
  const expiring = page.widgets.find((w) => w.title === 'Needs attention').items.find((i) => i.text.includes('RES-1'))
  assert.equal(expiring.to.params.name, 'RES-1')
})

// ---------------------------------------------------------------- live Finance, Design, Subcontractors, Stock
const { livePageFor, liveMethod } = await import('../src/showcase/live.js')
test('live Finance, Design, Subcontractors and Stock read their own sources and say why when empty', () => {
  assert.match(liveMethod('finance', 'overview'), /finance_live.get_finance_live/)
  assert.match(liveMethod('build', 'stock'), /get_operations_live/)
  assert.match(liveMethod('design', 'overview'), /construction_live/)
  const tile = (page, label) => page.kpis.find((k) => k.label === label).value
  const fin = livePageFor('finance', 'overview', {
    company: 'Synthetic Homes',
    pnl: { available: true, months: [{ month: '2026-10', income: '1000.00', expense: '400.00' }, { month: '2026-11', income: '500.00', expense: '100.00' }], expense_accounts: [] },
    cash: { available: true, accounts: [{ account: 'Bank', type: 'Bank', balance: '900.00' }] },
    receivables: { available: true, buckets: [{ age: 'Not yet due', amount: '300.00', count: 1 }] },
    payables: { available: false, reason: 'Your role does not include Purchase Invoice.', buckets: [] },
  }, MODULES.finance.tabs.overview)
  assert.equal(tile(fin, 'Income (12 months)'), 1500)
  assert.equal(tile(fin, 'Net'), 1000)
  assert.equal(tile(fin, 'Cash and bank'), 900)
  assert.ok(fin.widgets.some((w) => w.items?.[0]?.text === 'Your role does not include Purchase Invoice.'))
  const jobs = { available: true, rows: [
    { name: 'J1', service_type: 'Design Only', status: 'In Progress', current_contract_value: '5000.00' },
    { name: 'J2', service_type: 'Inspection Only', status: 'Completed', current_contract_value: null },
    { name: 'J3', service_type: 'Full Construction', status: 'In Progress', current_contract_value: '90000.00' },
  ] }
  const des = livePageFor('design', 'overview', { company: 'Synthetic Homes', jobs, inspections: { available: true, rows: [] } }, MODULES.design.tabs.overview)
  assert.equal(tile(des, 'Design jobs'), 1)
  assert.equal(tile(des, 'Open'), 1)
  assert.equal(tile(des, 'Contract value'), 5000) // full construction jobs are not design work
  const emptyStock = livePageFor('build', 'stock', { company: 'Synthetic Homes', stock: { available: true, warehouses: 2, rows: [] }, suppliers: { available: true, rows: [] } }, MODULES.build.tabs.stock)
  assert.match(emptyStock.widgets[0].items[0].text, /No stock is recorded/)
  const subs = livePageFor('build', 'subcontractors', { company: 'Synthetic Homes', suppliers: { available: true, rows: [{ supplier: 'S1', name: 'Synthetic Supplier', invoices: 3, invoiced: '6000.00', owed: '1500.00' }] }, stock: {} }, MODULES.build.tabs.subcontractors)
  assert.equal(tile(subs, 'Still owed'), 1500)
})

test('live Risk register counts open risks only and says why when missing', () => {
  const tile = (page, label) => page.kpis.find((k) => k.label === label).value
  const risks = { available: true, rows: [
    { name: 'RSK-1', project: 'Masalaha Hagbad', category: 'Weather disruption', rating: 'High', status: 'Open' },
    { name: 'RSK-2', project: 'All projects', category: 'Cost overruns', rating: 'Medium', status: 'Mitigating' },
    { name: 'RSK-3', project: 'All projects', category: 'Currency movement', rating: 'Low', status: 'Closed' },
  ] }
  const page = livePageFor('build', 'risk', { company: 'Synthetic Homes', risks }, MODULES.build.tabs.risk)
  assert.equal(tile(page, 'Open risks'), 2)
  assert.equal(tile(page, 'High'), 1)
  assert.equal(tile(page, 'Low'), 0) // the closed risk is not open
  assert.equal(page.widgets.find((w) => w.type === 'table').rows.length, 3)
  const hidden = livePageFor('build', 'risk', { company: 'Synthetic Homes', risks: { available: false, reason: 'Your role does not include the risk register.', rows: [] } }, MODULES.build.tabs.risk)
  assert.equal(hidden.kpis.length, 0)
  assert.equal(hidden.widgets[0].items[0].text, 'Your role does not include the risk register.')
  const empty = livePageFor('build', 'risk', { company: 'Synthetic Homes', risks: { available: true, rows: [] } }, MODULES.build.tabs.risk)
  assert.match(empty.widgets[0].items[0].text, /No risks are recorded for Synthetic Homes/)
  assert.match(liveMethod('build', 'risk'), /construction_live/)
})

test('live Executive lists open high risks and risks past their review date', () => {
  const data = { company: 'Synthetic Homes', today: '2026-11-15', jobs: { available: true, rows: [] }, variations: { available: true, rows: [] }, inspections: { available: true, rows: [] },
    risks: { available: true, rows: [
      { rating: 'High', status: 'Open', review_date: '2026-11-10' },
      { rating: 'High', status: 'Mitigating', review_date: '2026-12-01' },
      { rating: 'Low', status: 'Monitoring', review_date: '2026-11-01' },
      { rating: 'High', status: 'Closed', review_date: '2026-10-01' },
    ] } }
  const attention = (construction) => executiveExtras({ construction: { data: construction }, realestate: { error: 'y' } }).widgets.find((w) => w.title === 'Needs attention').items
  const items = attention(data)
  assert.deepEqual(items.slice(0, 2).map((i) => i.text), ['2 high risks are open', '2 risks are past their review date'])
  assert.equal(items[0].to.params.tab, 'risk')
  // An older server without the risk register adds no risk item.
  const { risks, ...older } = data
  assert.ok(!attention(older).some((i) => /risk/.test(i.text)))
  // A role that may not read the register is told why, not shown an all-clear.
  const denied = executiveExtras({ construction: { data: { ...data, risks: { available: false, reason: 'Your role does not include the risk register.', rows: [] } } }, realestate: { error: 'y' } })
  assert.ok(denied.widgets.some((w) => w.title === 'Risk register' && w.items[0].text === 'Your role does not include the risk register.'))
})

test('additional live sources accept denied groups and reject another Company', async () => {
  const { validLiveSource } = await import('../src/showcase/liveSources.js')
  const denied = { available: false, reason: 'Restricted' }
  const finance = { company: 'Synthetic Homes', pnl: denied, cash: denied, receivables: denied, payables: denied }
  const operations = { company: 'Synthetic Homes', stock: { available: true, rows: [] }, suppliers: denied }
  assert.equal(validLiveSource(finance, 'Synthetic Homes', 'finance'), true)
  assert.equal(validLiveSource(operations, 'Synthetic Homes', 'operations'), true)
  assert.equal(validLiveSource(finance, 'Other Company', 'finance'), false)
  assert.equal(validLiveSource({ ...operations, stock: {} }, 'Synthetic Homes', 'operations'), false)
})

test('CRM dashboard: sample channels, live leads by channel and opportunities, and why a group is missing', async () => {
  assert.equal(MODULES.crm.route, 'crm-hub')
  const sampleKpi = (label) => MODULES.crm.tabs.overview.kpis.find((k) => k.label === label).value
  assert.equal(sampleKpi('Leads'), Object.values((await import('../src/showcase/data.js')).LEAD_SOURCES).reduce((a, v) => a + v, 0))
  assert.match(liveMethod('crm', 'overview'), /crm_live.get_crm_live/)
  const data = {
    company: 'Synthetic Homes',
    leads: { available: true, total: 3, by_channel: { WhatsApp: 2, Email: 1 }, by_status: { Lead: 2, Open: 1 }, months: [{ month: '2026-11', count: 3 }], rows: [{ name: 'CRM-LEAD-1', lead: 'Synthetic Lead', channel: 'WhatsApp', status: 'Lead', created: '2026-11-14' }] },
    opportunities: { available: true, total: 2, open: 1, open_amount: '14300.00', stages: [{ stage: 'Prospecting', count: 2, amount: '20000.00' }], rows: [] },
    customers: { available: true, total: 40, kyc: null },
  }
  const { validLiveSource } = await import('../src/showcase/liveSources.js')
  assert.equal(validLiveSource(data, 'Synthetic Homes', 'crm'), true)
  assert.equal(validLiveSource({ ...data, leads: { available: true, rows: [] } }, 'Synthetic Homes', 'crm'), false)
  const page = livePageFor('crm', 'overview', data, MODULES.crm.tabs.overview)
  const tile = (label) => page.kpis.find((k) => k.label === label)?.value
  assert.equal(tile('Leads'), 3)
  assert.equal(tile('From WhatsApp'), 2)
  assert.equal(tile('Open opportunity value'), 14300)
  assert.equal(tile('KYC verified'), undefined) // KYC is restricted (G12): no tile rather than a zero
  assert.deepEqual(page.widgets.find((w) => w.title === 'Leads by channel').segments.map((s) => [s.label, s.value]), [['WhatsApp', 2], ['Email', 1]])
  const denied = livePageFor('crm', 'overview', { ...data, opportunities: { available: false, reason: 'Your role does not include opportunities.', rows: [] } }, MODULES.crm.tabs.overview)
  assert.ok(denied.widgets.some((w) => w.items?.[0]?.text === 'Your role does not include opportunities.'))
})
