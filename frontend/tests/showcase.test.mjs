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
