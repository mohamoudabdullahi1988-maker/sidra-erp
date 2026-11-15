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
  assert.deepEqual(LIVE_TABS.build, ['portfolio', 'variations', 'quality'])
})

test('a missing value is a dash, never zero', () => {
  for (const fn of [money]) assert.equal(fn(null), '—')
  assert.equal(pct(undefined), '—')
})

const { executivePage, validExecutive } = await import('../src/showcase/live.js')
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
