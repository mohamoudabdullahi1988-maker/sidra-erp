// What each sample screen shows, as data: tiles, charts, tables and the right-hand workflow.
// ShowcasePage.vue draws any of these, so a new screen is a new entry here, not a new component.
import * as D from './data.js'
import { monthLabel } from './format.js'

const M = D.MONTHS.map(monthLabel)
const CM = D.CASH_MONTHS.map(monthLabel)
const set = (name, filter) => ({ set: name, filter })

function cumulative(values) {
  let total = 0
  return values.map((v) => (total += v))
}
function seriesTotal(series) {
  return series[0].map((_, i) => series.reduce((s, row) => s + row[i], 0))
}
const thousands = (values) => values.map((v) => v * 1000)

const projectTotals = {
  budget: D.sum(D.PROJECTS, 'budget'),
  committed: D.sum(D.PROJECTS, 'committed'),
  forecast: D.sum(D.PROJECTS, 'forecast'),
  paid: D.sum(D.PROJECTS, 'paid'),
}
const PHASE_TONE = { Design: 'purple', Procurement: 'amber', Construction: 'blue', Handover: 'green' }
const phaseCounts = D.countBy(D.PROJECTS, 'phase', D.PHASES)
const actualSpend = seriesTotal(Object.values(D.SPEND))
const cashFlow = [...actualSpend, ...D.SPEND_FORECAST]

const projectMap = {
  type: 'map', title: 'Sites', span: 4,
  pins: D.PROJECTS.map((p) => ({ label: p.name, city: p.city, tone: PHASE_TONE[p.phase], sub: `${p.phase} · ${p.progress}%`, to: set('projects', { name: p.name }) })),
}
const phaseDonut = {
  type: 'donut', title: 'Projects by phase', span: 4, centre: 'projects', kind: 'count', to: set('projects'),
  segments: D.PHASES.map((ph) => ({ label: ph, value: phaseCounts[ph], tone: PHASE_TONE[ph], to: set('projects', { phase: ph }) })),
}
const cashFlowChart = {
  type: 'bars', title: 'Construction cash flow', note: 'Monthly spend, actual to Nov 2026 then forecast, with the cumulative total', span: 8, kind: 'money',
  labels: CM, forecastFrom: 12,
  series: [
    { name: 'Monthly spend', values: thousands(cashFlow), tone: 'blue' },
    { name: 'Cumulative', values: thousands(cumulative(cashFlow)), tone: 'orange', type: 'line', axis: 'right' },
  ],
}
const healthTable = { type: 'table', title: 'Project health', span: 12, set: 'projects', columns: ['name', 'city', 'phase', 'budget', 'forecast', 'progress', 'end', 'scope_health', 'time_health', 'cost_health', 'quality_health', 'safety_health'] }

// ---------------------------------------------------------------- construction tabs

const construction = {
  portfolio: {
    title: 'Construction portfolio',
    subtitle: 'Every live project: budget, progress and health',
    kpis: [
      { label: 'Total projects', value: D.PROJECTS.length, kind: 'count', tone: 'amber', to: set('projects') },
      { label: 'Budget', value: projectTotals.budget, kind: 'money', tone: 'sky', to: set('projects') },
      { label: 'Committed', value: projectTotals.committed, kind: 'money', tone: 'blue', to: set('projects') },
      { label: 'Forecast cost', value: projectTotals.forecast, kind: 'money', tone: 'teal', to: set('projects') },
      { label: 'Variance to budget', value: projectTotals.budget - projectTotals.forecast, kind: 'money', tone: 'orange', to: set('projects') },
      { label: 'Paid to date', value: projectTotals.paid, kind: 'money', tone: 'green', to: set('projects') },
    ],
    widgets: [
      projectMap,
      phaseDonut,
      {
        type: 'hbars', title: 'Budget vs forecast by project', span: 4, kind: 'money', to: set('projects'),
        series: [{ name: 'Budget', tone: 'sky' }, { name: 'Forecast', tone: 'orange' }],
        rows: D.PROJECTS.map((p) => ({ label: p.name, values: [p.budget, p.forecast], to: set('projects', { name: p.name }) })),
      },
      healthTable,
      {
        type: 'gantt', title: 'Project phases', span: 6, from: '2025-03-01', until: '2028-03-01',
        rows: D.PROJECTS.map((p) => ({ label: p.name, start: p.start, end: p.end, progress: p.progress, tone: PHASE_TONE[p.phase], to: set('milestones', { project: p.name }) })),
      },
      { ...cashFlowChart, span: 6 },
    ],
  },
  schedule: {
    title: 'Schedule',
    subtitle: 'Milestones across all projects',
    kpis: [
      { label: 'Milestones completed', value: D.MILESTONES.filter((m) => m.status === 'Completed').length, kind: 'count', tone: 'green', to: set('milestones', { status: 'Completed' }) },
      { label: 'On track (next 45 days)', value: D.MILESTONES.filter((m) => m.status === 'On track').length, kind: 'count', tone: 'blue', to: set('milestones', { status: 'On track' }) },
      { label: 'At risk', value: D.MILESTONES.filter((m) => m.status === 'At risk').length, kind: 'count', tone: 'amber', to: set('milestones', { status: 'At risk' }) },
      { label: 'Delayed', value: D.MILESTONES.filter((m) => m.status === 'Delayed').length, kind: 'count', tone: 'rose', to: set('milestones', { status: 'Delayed' }) },
    ],
    widgets: [
      {
        type: 'gantt', title: 'Rayan Gardens: milestone plan', span: 8, from: '2025-08-01', until: '2027-06-01', milestones: true,
        rows: D.MILESTONES.filter((m) => m.project === 'Rayan Gardens').map((m, i, all) => ({
          label: m.milestone, start: i ? all[i - 1].planned : '2025-08-01', end: m.forecast,
          tone: { Completed: 'green', 'On track': 'blue', 'At risk': 'amber', Delayed: 'rose', Upcoming: 'slate' }[m.status],
          sub: m.status, to: set('milestones', { project: m.project, milestone: m.milestone }),
        })),
      },
      {
        type: 'donut', title: 'Milestone status', span: 4, centre: 'milestones', kind: 'count', to: set('milestones'),
        segments: Object.entries(D.countBy(D.MILESTONES, 'status', ['Completed', 'On track', 'At risk', 'Delayed', 'Upcoming'])).map(([label, value]) => ({
          label, value, tone: { Completed: 'green', 'On track': 'blue', 'At risk': 'amber', Delayed: 'rose', Upcoming: 'slate' }[label], to: set('milestones', { status: label }),
        })),
      },
      {
        type: 'hbars', title: 'Progress by project', span: 6, kind: 'pct', max: 100,
        series: [{ name: 'Complete', tone: 'teal' }],
        rows: D.PROJECTS.map((p) => ({ label: p.name, values: [p.progress], to: set('milestones', { project: p.name }) })),
      },
      { type: 'table', title: 'Next milestones', span: 6, set: 'milestones', filter: { status: 'At risk' }, columns: ['project', 'milestone', 'planned', 'forecast', 'status'], extra: { status: 'Delayed' } },
    ],
  },
  cost: {
    title: 'Cost and budget',
    subtitle: 'Budget, spend and forecast by cost category',
    kpis: [
      { label: 'Approved budget', value: D.sum(D.COST_BUDGET, 'budget'), kind: 'money', tone: 'sky', to: set('cost') },
      { label: 'Spent to date', value: D.sum(D.COST_BUDGET, 'actual'), kind: 'money', tone: 'blue', to: set('cost') },
      { label: 'Forecast at completion', value: D.sum(D.COST_BUDGET, 'forecast'), kind: 'money', tone: 'teal', to: set('cost') },
      { label: 'Forecast overrun', value: D.sum(D.COST_BUDGET, 'forecast') - D.sum(D.COST_BUDGET, 'budget'), kind: 'money', tone: 'orange', to: set('cost') },
    ],
    widgets: [
      {
        type: 'bars', title: 'Budget, spent and forecast by category', span: 6, kind: 'money', labels: D.COST_BUDGET.map((c) => c.category), to: set('cost'),
        series: [
          { name: 'Budget', values: D.COST_BUDGET.map((c) => c.budget), tone: 'sky' },
          { name: 'Spent', values: D.COST_BUDGET.map((c) => c.actual), tone: 'blue' },
          { name: 'Forecast', values: D.COST_BUDGET.map((c) => c.forecast), tone: 'orange' },
        ],
      },
      {
        type: 'bars', title: 'Monthly spend by category', span: 6, kind: 'money', labels: M, stacked: true,
        series: Object.entries(D.SPEND).map(([name, values], i) => ({ name, values: thousands(values), tone: ['blue', 'teal', 'purple', 'amber'][i] })),
      },
      {
        type: 'hbars', title: 'Paid vs budget by project', span: 6, kind: 'money',
        series: [{ name: 'Paid', tone: 'green' }, { name: 'Budget', tone: 'sky' }],
        rows: D.PROJECTS.map((p) => ({ label: p.name, values: [p.paid, p.budget], to: set('projects', { name: p.name }) })),
      },
      { ...cashFlowChart, span: 6 },
    ],
  },
  variations: {
    title: 'Variation orders',
    subtitle: 'Additions to contract scope and their approvals',
    kpis: [
      { label: 'Variation orders', value: D.VARIATIONS.length, kind: 'count', tone: 'purple', to: set('variations') },
      { label: 'Approved value', value: D.sum(D.VARIATIONS.filter((v) => v.status === 'Approved'), 'value'), kind: 'money', tone: 'green', to: set('variations', { status: 'Approved' }) },
      { label: 'Awaiting approval', value: D.sum(D.VARIATIONS.filter((v) => v.status === 'Awaiting approval'), 'value'), kind: 'money', tone: 'amber', to: set('variations', { status: 'Awaiting approval' }) },
      { label: 'Average days to approve', value: 4.6, kind: 'count', tone: 'blue', suffix: ' days', to: set('variations', { status: 'Approved' }) },
    ],
    widgets: [
      {
        type: 'donut', title: 'Status', span: 4, centre: 'orders', kind: 'count', to: set('variations'),
        segments: Object.entries(D.countBy(D.VARIATIONS, 'status', ['Approved', 'Awaiting approval', 'Under review', 'Draft'])).map(([label, value]) => ({ label, value, tone: { Approved: 'green', 'Awaiting approval': 'amber', 'Under review': 'blue', Draft: 'slate' }[label], to: set('variations', { status: label }) })),
      },
      {
        type: 'hbars', title: 'Value by project', span: 8, kind: 'money',
        series: [{ name: 'Variation value', tone: 'purple' }],
        rows: Object.entries(D.VARIATIONS.reduce((acc, v) => ({ ...acc, [v.project]: (acc[v.project] ?? 0) + v.value }), {})).map(([label, value]) => ({ label, values: [value], to: set('variations', { project: label }) })),
      },
      { type: 'table', title: 'Variation register', span: 12, set: 'variations', columns: ['id', 'project', 'description', 'value', 'status', 'approver', 'raised'] },
    ],
    workflow: {
      title: 'Variation order',
      steps: [
        { label: 'Raised by site', state: 'done', note: 'Additions only (decision G11)' },
        { label: 'Priced by quantity surveyor', state: 'done' },
        { label: 'Second approval', state: 'current', note: 'Another Project Manager up to $1,000; General Manager above' },
        { label: 'Client sign-off', state: 'next' },
        { label: 'Instructed to site', state: 'next' },
      ],
    },
  },
  quality: {
    title: 'Quality and inspections',
    subtitle: 'Stage inspections, results and open defects',
    kpis: [
      { label: 'Inspections (90 days)', value: D.INSPECTIONS.length, kind: 'count', tone: 'blue', to: set('inspections') },
      { label: 'Passed first time', value: Math.round((D.INSPECTIONS.filter((i) => i.result !== 'Fail').length / D.INSPECTIONS.length) * 100), kind: 'pct', tone: 'green', to: set('inspections', { result: 'Pass' }) },
      { label: 'Failed', value: D.INSPECTIONS.filter((i) => i.result === 'Fail').length, kind: 'count', tone: 'rose', to: set('inspections', { result: 'Fail' }) },
      { label: 'Open defects', value: D.sum(D.INSPECTIONS, 'open_defects'), kind: 'count', tone: 'amber', to: set('inspections') },
    ],
    widgets: [
      {
        type: 'donut', title: 'Results', span: 4, centre: 'inspections', kind: 'count', to: set('inspections'),
        segments: Object.entries(D.countBy(D.INSPECTIONS, 'result', ['Pass', 'Pass with remarks', 'Fail'])).map(([label, value]) => ({ label, value, tone: { Pass: 'green', 'Pass with remarks': 'amber', Fail: 'rose' }[label], to: set('inspections', { result: label }) })),
      },
      {
        type: 'hbars', title: 'Open defects by project', span: 8, kind: 'count',
        series: [{ name: 'Open defects', tone: 'orange' }],
        rows: D.PROJECTS.filter((p) => D.INSPECTIONS.some((i) => i.project === p.name)).map((p) => ({ label: p.name, values: [D.sum(D.INSPECTIONS.filter((i) => i.project === p.name), 'open_defects')], to: set('inspections', { project: p.name }) })),
      },
      { type: 'table', title: 'Latest inspections', span: 12, set: 'inspections', columns: ['id', 'project', 'item', 'result', 'open_defects', 'date'] },
    ],
    workflow: {
      title: 'Stage inspection',
      steps: [
        { label: 'Inspection requested', state: 'done' },
        { label: 'Inspected on site', state: 'done' },
        { label: 'Report issued', state: 'current', note: 'Pass, pass with remarks or fail' },
        { label: 'Defects fixed and re-inspected', state: 'next' },
        { label: 'Stage certified', state: 'next' },
      ],
    },
  },
  risk: {
    title: 'Risk',
    subtitle: 'Project risks, owners and pending decisions',
    kpis: [
      { label: 'Open risks', value: D.RISKS.length, kind: 'count', tone: 'purple', to: set('risks') },
      { label: 'High', value: D.RISKS.filter((r) => r.rating === 'High').length, kind: 'count', tone: 'rose', to: set('risks', { rating: 'High' }) },
      { label: 'Medium', value: D.RISKS.filter((r) => r.rating === 'Medium').length, kind: 'count', tone: 'amber', to: set('risks', { rating: 'Medium' }) },
      { label: 'Low', value: D.RISKS.filter((r) => r.rating === 'Low').length, kind: 'count', tone: 'green', to: set('risks', { rating: 'Low' }) },
    ],
    widgets: [
      {
        type: 'donut', title: 'Risk status', span: 4, centre: 'risks', kind: 'count', to: set('risks'),
        segments: ['High', 'Medium', 'Low'].map((label) => ({ label, value: D.RISKS.filter((r) => r.rating === label).length, tone: { High: 'rose', Medium: 'amber', Low: 'green' }[label], to: set('risks', { rating: label }) })),
      },
      {
        type: 'bars', title: 'Pending items', span: 4, kind: 'count', labels: Object.keys(D.PENDING),
        series: [{ name: 'Pending', values: Object.values(D.PENDING), tone: 'purple', colours: ['purple', 'green', 'slate'] }],
      },
      {
        type: 'hbars', title: 'Risks by project', span: 4, kind: 'count', stacked: true,
        series: [{ name: 'High', tone: 'rose' }, { name: 'Medium', tone: 'amber' }, { name: 'Low', tone: 'green' }],
        rows: [...new Set(D.RISKS.map((r) => r.project))].map((project) => ({ label: project, values: ['High', 'Medium', 'Low'].map((rating) => D.RISKS.filter((r) => r.project === project && r.rating === rating).length), to: set('risks', { project }) })),
      },
      { type: 'table', title: 'Risk register', span: 12, set: 'risks', columns: ['category', 'description', 'project', 'owner', 'rating', 'status'] },
    ],
  },
  stock: {
    title: 'Stock and materials',
    subtitle: 'Yard stock, reorder alerts and materials issued to sites',
    kpis: [
      { label: 'Stock value', value: D.sum(D.STOCK, 'value'), kind: 'money', tone: 'teal', to: set('stock') },
      { label: 'Materials tracked', value: D.STOCK.length, kind: 'count', tone: 'blue', to: set('stock') },
      { label: 'Below reorder level', value: D.STOCK.filter((s) => s.below_reorder === 'Yes').length, kind: 'count', tone: 'rose', to: set('stock', { below_reorder: 'Yes' }) },
      { label: 'Issued this month', value: D.sum(Object.values(D.ISSUED_BY_SITE)), kind: 'money', tone: 'amber', to: set('stock') },
    ],
    widgets: [
      {
        type: 'hbars', title: 'Stock against reorder level', note: 'Percent of reorder level on hand; under 100% needs ordering', span: 6, kind: 'pct', marker: 100, max: 200,
        series: [{ name: 'On hand vs reorder level', tone: 'teal' }],
        rows: D.STOCK.map((s) => ({ label: s.item, values: [Math.min(200, Math.round((s.on_hand / s.reorder_level) * 100))], tone: s.below_reorder === 'Yes' ? 'rose' : undefined, to: set('stock', { item: s.item }) })),
      },
      {
        type: 'donut', title: 'Materials issued by site', span: 6, centre: 'this month', kind: 'money',
        segments: Object.entries(D.ISSUED_BY_SITE).map(([label, value], i) => ({ label, value, tone: ['blue', 'teal', 'purple', 'orange', 'green', 'amber'][i], to: set('projects', { name: label }) })),
      },
      { type: 'table', title: 'Stock list', span: 12, set: 'stock', columns: ['item', 'unit', 'on_hand', 'reorder_level', 'below_reorder', 'value', 'location'] },
    ],
    workflow: {
      title: 'Materials',
      steps: [
        { label: 'Site requests materials', state: 'done' },
        { label: 'Store checks stock', state: 'done' },
        { label: 'Purchase order if below reorder', state: 'current' },
        { label: 'Goods received at yard', state: 'next' },
        { label: 'Issued to site', state: 'next' },
      ],
    },
  },
  subcontractors: {
    title: 'Subcontractors',
    subtitle: 'Trades on site, contract values, payments and retention',
    kpis: [
      { label: 'Active subcontractors', value: D.SUBCONTRACTORS.length, kind: 'count', tone: 'blue', to: set('subcontractors') },
      { label: 'Contract value', value: D.sum(D.SUBCONTRACTORS, 'contract_value'), kind: 'money', tone: 'sky', to: set('subcontractors') },
      { label: 'Paid', value: D.sum(D.SUBCONTRACTORS, 'paid'), kind: 'money', tone: 'green', to: set('subcontractors') },
      { label: 'Retention held', value: D.sum(D.SUBCONTRACTORS, 'retention'), kind: 'money', tone: 'amber', to: set('subcontractors') },
    ],
    widgets: [
      {
        type: 'hbars', title: 'Contract value and paid by subcontractor', span: 7, kind: 'money',
        series: [{ name: 'Contract value', tone: 'sky' }, { name: 'Paid', tone: 'green' }],
        rows: D.SUBCONTRACTORS.map((s) => ({ label: s.name, values: [s.contract_value, s.paid], to: set('subcontractors', { name: s.name }) })),
      },
      {
        type: 'donut', title: 'Contract value by trade', span: 5, centre: 'committed', kind: 'money', to: set('subcontractors'),
        segments: D.SUBCONTRACTORS.map((s, i) => ({ label: s.trade, value: s.contract_value, tone: ['blue', 'teal', 'purple', 'orange', 'green', 'amber', 'rose', 'sky'][i], to: set('subcontractors', { trade: s.trade }) })),
      },
      { type: 'table', title: 'Subcontractor list', span: 12, set: 'subcontractors', columns: ['name', 'trade', 'active_projects', 'contract_value', 'paid', 'retention', 'rating'] },
    ],
  },
}

const constructionFlow = {
  title: 'Construction project',
  steps: [
    { label: 'Client brief and quotation', state: 'done' },
    { label: 'BOQ and contract', state: 'done' },
    { label: 'Mobilise and procure', state: 'done' },
    { label: 'Build by stages', state: 'current', note: 'Each stage inspected and certified' },
    { label: 'Variations approved', state: 'current' },
    { label: 'Handover and defects period', state: 'next' },
  ],
}
for (const page of Object.values(construction)) page.workflow ??= constructionFlow

// ---------------------------------------------------------------- design and engineering

function designTab(discipline, tone, flowTitle) {
  const jobs = D.DESIGN_JOBS.filter((j) => j.discipline === discipline)
  const stages = D.DESIGN_STAGES[discipline]
  const open = jobs.filter((j) => !['Completed', 'Issued'].includes(j.stage))
  const leads = [...new Set(jobs.map((j) => j.lead))]
  return {
    title: discipline,
    subtitle: `${discipline} jobs for Sidra projects and outside clients`,
    kpis: [
      { label: 'Open jobs', value: open.length, kind: 'count', tone, to: set('design_jobs', { discipline }) },
      { label: 'Fees agreed', value: D.sum(jobs, 'fee'), kind: 'money', tone: 'blue', to: set('design_jobs', { discipline }) },
      { label: 'Billed', value: D.sum(jobs, 'billed'), kind: 'money', tone: 'green', to: set('design_jobs', { discipline }) },
      { label: 'Still to bill', value: D.sum(jobs, 'fee') - D.sum(jobs, 'billed'), kind: 'money', tone: 'amber', to: set('design_jobs', { discipline }) },
    ],
    widgets: [
      {
        type: 'hbars', title: 'Jobs by stage', span: 6, kind: 'count',
        series: [{ name: 'Jobs', tone }],
        rows: stages.map((stage) => ({ label: stage, values: [jobs.filter((j) => j.stage === stage).length], to: set('design_jobs', { discipline, stage }) })),
      },
      {
        type: 'bars', title: 'Fees invoiced per month', span: 6, kind: 'money', labels: M,
        series: [
          { name: 'Fees', values: thousands(D.DESIGN_FEES[discipline]), tone },
          { name: 'Cumulative', values: thousands(cumulative(D.DESIGN_FEES[discipline])), tone: 'orange', type: 'line', axis: 'right' },
        ],
      },
      {
        type: 'donut', title: 'Workload by lead', span: 4, centre: 'jobs', kind: 'count',
        segments: leads.map((lead, i) => ({ label: lead, value: jobs.filter((j) => j.lead === lead).length, tone: ['blue', 'teal', 'purple', 'orange'][i], to: set('design_jobs', { discipline, lead }) })),
      },
      { type: 'table', title: `${discipline} jobs`, span: 8, set: 'design_jobs', filter: { discipline }, columns: ['id', 'job', 'stage', 'lead', 'fee', 'due'] },
    ],
    workflow: { title: flowTitle, steps: stages.map((label, i) => ({ label, state: i < 2 ? 'done' : i === 2 ? 'current' : 'next' })) },
  }
}

const design = {
  overview: {
    title: 'Design and engineering',
    subtitle: 'End-to-end design and construction for the local climate: architecture, civil engineering and inspections',
    kpis: [
      { label: 'Open jobs', value: D.DESIGN_JOBS.filter((j) => !['Completed', 'Issued'].includes(j.stage)).length, kind: 'count', tone: 'purple', to: set('design_jobs') },
      { label: 'Fees agreed', value: D.sum(D.DESIGN_JOBS, 'fee'), kind: 'money', tone: 'blue', to: set('design_jobs') },
      { label: 'Billed', value: D.sum(D.DESIGN_JOBS, 'billed'), kind: 'money', tone: 'green', to: set('design_jobs') },
      { label: 'Fees (12 months)', value: D.sum(Object.values(D.DESIGN_FEES).flat()) * 1000, kind: 'money', tone: 'teal', to: set('design_jobs') },
    ],
    widgets: [
      {
        type: 'donut', title: 'Jobs by service', span: 4, centre: 'jobs', kind: 'count', to: set('design_jobs'),
        segments: Object.keys(D.DESIGN_STAGES).map((label, i) => ({ label, value: D.DESIGN_JOBS.filter((j) => j.discipline === label).length, tone: ['purple', 'blue', 'teal'][i], to: set('design_jobs', { discipline: label }) })),
      },
      {
        type: 'bars', title: 'Fees invoiced per month by service', span: 8, kind: 'money', labels: M, stacked: true,
        series: Object.entries(D.DESIGN_FEES).map(([name, values], i) => ({ name, values: thousands(values), tone: ['purple', 'blue', 'teal'][i] })),
      },
      { type: 'table', title: 'Jobs due soonest', span: 12, set: 'design_jobs', columns: ['id', 'discipline', 'job', 'stage', 'fee', 'billed', 'due'], sort: 'due' },
    ],
    workflow: {
      title: 'Design job',
      steps: [
        { label: 'Enquiry and fee proposal', state: 'done' },
        { label: 'Brief agreed', state: 'done' },
        { label: 'Design and calculations', state: 'current' },
        { label: 'Internal review', state: 'next' },
        { label: 'Issued to client and billed', state: 'next' },
      ],
    },
  },
  architecture: designTab('Architecture', 'purple', 'Architecture job'),
  civil: designTab('Civil engineering', 'blue', 'Engineering job'),
  inspection: designTab('Inspection services', 'teal', 'Inspection job'),
}

// ---------------------------------------------------------------- real estate sales

const inventory = D.COMMUNITIES.reduce((t, c) => ({ total: t.total + c.total, sold: t.sold + c.sold, reserved: t.reserved + c.reserved, available: t.available + c.available }), { total: 0, sold: 0, reserved: 0, available: 0 })
const STATUS_TONE = { Available: 'green', Reserved: 'amber', Sold: 'blue' }

const realestate = {
  inventory: {
    title: 'Inventory',
    subtitle: 'Masalaha Hagbad plots ($14,300 full, $7,150 half, from $325 a month over 22 months interest-free), Rayan Gardens, Safa Housing and Berbera Townhouses',
    kpis: [
      { label: 'Plots and units', value: inventory.total, kind: 'count', tone: 'blue', to: set('units') },
      { label: 'Available', value: inventory.available, kind: 'count', tone: 'green', to: set('units', { status: 'Available' }) },
      { label: 'Reserved', value: inventory.reserved, kind: 'count', tone: 'amber', to: set('units', { status: 'Reserved' }) },
      { label: 'Sold', value: inventory.sold, kind: 'count', tone: 'purple', to: set('units', { status: 'Sold' }) },
      { label: 'Value available', value: D.sum(D.UNITS.filter((u) => u.status === 'Available'), 'price'), kind: 'money', tone: 'teal', to: set('units', { status: 'Available' }) },
    ],
    widgets: [
      {
        type: 'donut', title: 'Occupancy of stock', span: 4, centre: 'plots and units', kind: 'count', to: set('units'),
        segments: ['Available', 'Reserved', 'Sold'].map((label) => ({ label, value: inventory[label.toLowerCase()], tone: STATUS_TONE[label], to: set('units', { status: label }) })),
      },
      {
        type: 'hbars', title: 'Status by community', span: 8, kind: 'count', stacked: true,
        series: [{ name: 'Sold', tone: 'blue' }, { name: 'Reserved', tone: 'amber' }, { name: 'Available', tone: 'green' }],
        rows: D.COMMUNITIES.map((c) => ({ label: `${c.name} (${c.kind.toLowerCase()})`, values: [c.sold, c.reserved, c.available], to: set('units', { community: c.name }) })),
      },
      {
        type: 'bars', title: 'Contracts signed per month', span: 8, kind: 'count', labels: M,
        series: [
          { name: 'Contracts', values: D.SALES_BY_MONTH, tone: 'blue' },
          { name: 'Cumulative', values: cumulative(D.SALES_BY_MONTH), tone: 'orange', type: 'line', axis: 'right' },
        ],
      },
      {
        type: 'map', title: 'Communities', span: 4,
        pins: D.COMMUNITIES.map((c, i) => ({ label: c.name, city: c.city, tone: ['blue', 'green', 'teal', 'purple'][i], sub: `${c.available} available`, to: set('units', { community: c.name, status: 'Available' }), nudge: i })),
      },
    ],
  },
  pipeline: {
    title: 'Sales pipeline',
    subtitle: 'From first enquiry to signed contract (last 90 days)',
    kpis: D.FUNNEL.map(([label, value], i) => ({ label, value, kind: 'count', tone: ['sky', 'blue', 'teal', 'amber', 'green'][i], to: set('leads', i ? { stage: label } : undefined) })),
    widgets: [
      {
        type: 'hbars', title: 'Sales funnel', note: 'Each stage counts the leads that reached it', span: 6, kind: 'count', funnel: true,
        series: [{ name: 'Leads', tone: 'blue' }],
        rows: D.FUNNEL.map(([label, value], i) => ({ label, values: [value], tone: ['sky', 'blue', 'teal', 'amber', 'green'][i], to: set('leads', i ? { stage: label } : undefined) })),
      },
      {
        type: 'donut', title: 'Where leads come from', span: 6, centre: 'leads', kind: 'count', to: set('leads'),
        segments: Object.entries(D.LEAD_SOURCES).map(([label, value], i) => ({ label, value, tone: ['purple', 'blue', 'teal', 'orange', 'sky'][i], to: set('leads', { source: label }) })),
      },
      {
        type: 'bars', title: 'New leads and contracts per month', span: 7, kind: 'count', labels: M,
        series: [
          { name: 'Leads', values: D.LEADS_BY_MONTH, tone: 'sky' },
          { name: 'Contracts', values: D.SALES_BY_MONTH, tone: 'green' },
        ],
      },
      { type: 'table', title: 'Sales agents', span: 5, set: 'agents', columns: ['agent', 'leads', 'contracts', 'conversion', 'value'] },
      {
        type: 'hbars', title: 'Diaspora buyer support', note: 'Overseas buyers helped to choose, view and buy remotely (90 days)', span: 7, kind: 'count', funnel: true,
        series: [{ name: 'Buyers', tone: 'purple' }],
        rows: D.DIASPORA_STEPS.map(([label, value], i) => ({ label, values: [value], tone: ['sky', 'blue', 'teal', 'purple', 'green'][i], to: set('leads', { source: 'Diaspora referral' }) })),
      },
      {
        type: 'donut', title: 'Diaspora buyers by country', span: 5, centre: 'buyers', kind: 'count', to: set('leads', { source: 'Diaspora referral' }),
        segments: Object.entries(D.DIASPORA_COUNTRIES).map(([label, value], i) => ({ label, value, tone: ['blue', 'rose', 'orange', 'teal', 'amber', 'slate'][i], to: set('leads', { source: 'Diaspora referral' }) })),
      },
    ],
    workflow: {
      title: 'Plot or home sale',
      steps: [
        { label: 'Lead and site visit', state: 'done' },
        { label: 'Quotation (cash or installments)', state: 'done' },
        { label: 'Reservation', state: 'current', note: 'Plot held for the buyer' },
        { label: 'Contract signed', state: 'next' },
        { label: 'Installments collected', state: 'next' },
        { label: 'Title transfer', state: 'next' },
      ],
      actions: [
        { label: 'Reservations', to: { name: 'reservations-list' }, list: 'reservations' },
        { label: 'Quotations', to: { name: 'sale_quotations-list' }, list: 'sale_quotations' },
      ],
    },
  },
  contracts: {
    title: 'Contracts and collections',
    subtitle: 'Installment contracts, money collected and what is overdue',
    kpis: [
      { label: 'Active contracts', value: D.CONTRACT_TOTALS.active, kind: 'count', tone: 'blue', to: set('sale_contracts') },
      { label: 'Contract value', value: D.CONTRACT_TOTALS.value, kind: 'money', tone: 'sky', to: set('sale_contracts') },
      { label: 'Collected to date', value: D.CONTRACT_TOTALS.collected, kind: 'money', tone: 'green', to: set('sale_contracts') },
      { label: 'Outstanding', value: D.CONTRACT_TOTALS.value - D.CONTRACT_TOTALS.collected, kind: 'money', tone: 'teal', to: set('sale_contracts') },
      { label: 'Overdue', value: D.sum(D.AGEING, 'amount'), kind: 'money', tone: 'rose', to: set('overdue') },
      { label: 'Collection rate (Nov)', value: Math.round((D.COLLECTIONS.collected[11] / D.COLLECTIONS.scheduled[11]) * 100), kind: 'pct', tone: 'amber', to: set('sale_contracts') },
    ],
    widgets: [
      {
        type: 'bars', title: 'Scheduled vs collected', note: 'Installments falling due each month and what was collected', span: 8, kind: 'money', labels: M,
        series: [
          { name: 'Scheduled', values: thousands(D.COLLECTIONS.scheduled), tone: 'sky' },
          { name: 'Collected', values: thousands(D.COLLECTIONS.collected), tone: 'green' },
          { name: 'Cumulative collected', values: thousands(cumulative(D.COLLECTIONS.collected)), tone: 'orange', type: 'line', axis: 'right' },
        ],
      },
      {
        type: 'donut', title: 'Overdue by age', span: 4, centre: 'overdue', kind: 'money', to: set('overdue'),
        segments: D.AGEING.map((b, i) => ({ label: b.bucket, value: b.amount, tone: ['amber', 'orange', 'rose', 'purple'][i], to: set('overdue', { bucket: b.bucket }) })),
      },
      {
        type: 'donut', title: 'Payment plans', span: 4, centre: 'contracts', kind: 'count', to: set('sale_contracts'),
        segments: Object.entries(D.PLAN_MIX).map(([label, value], i) => ({ label, value, tone: ['green', 'sky', 'orange', 'teal', 'purple'][i], to: set('sale_contracts', { plan: label }) })),
      },
      { type: 'table', title: 'Latest contracts', span: 8, set: 'sale_contracts', columns: ['contract', 'customer', 'community', 'plan', 'value', 'status'], limit: 6 },
    ],
    workflow: {
      title: 'Installment contract',
      steps: [
        { label: 'Terms frozen from the profile', state: 'done' },
        { label: 'Signed and registered', state: 'done' },
        { label: 'Down payment received', state: 'done' },
        { label: 'Monthly installments', state: 'current', note: 'Reminders before each due date' },
        { label: 'Paid in full', state: 'next' },
        { label: 'Title transferred', state: 'next' },
      ],
      actions: [
        { label: 'Contracts', to: { name: 'contracts' }, section: 'contracts' },
        { label: 'Collections calendar', to: { name: 'collections' }, section: 'collections' },
        { label: 'Title transfers', to: { name: 'title_transfers-list' }, list: 'title_transfers' },
      ],
    },
  },
}
const salesFlow = realestate.pipeline.workflow
realestate.inventory.workflow = {
  ...salesFlow,
  actions: [
    { label: 'Units', to: { name: 'properties' }, section: 'properties' },
    { label: 'Schemes', to: { name: 'schemes-list' }, list: 'schemes' },
    { label: 'Price history', to: { name: 'price_history-list' }, list: 'price_history' },
  ],
}

// ---------------------------------------------------------------- brokerage

const commissionDue = D.sum(D.DEALS.filter((d) => d.status === 'Commission due'), 'commission')
const brokerage = {
  overview: {
    title: 'Brokerage',
    subtitle: 'Verified off-market plots and owners’ properties, sold for a 2.5% commission, with title deed transfer once paid',
    kpis: [
      { label: 'Active listings', value: D.LISTINGS.filter((l) => l.status === 'Active').length, kind: 'count', tone: 'blue', to: set('listings', { status: 'Active' }) },
      { label: 'Under offer', value: D.LISTINGS.filter((l) => l.status === 'Under offer').length, kind: 'count', tone: 'amber', to: set('listings', { status: 'Under offer' }) },
      { label: 'Sold', value: D.LISTINGS.filter((l) => l.status === 'Sold').length, kind: 'count', tone: 'green', to: set('listings', { status: 'Sold' }) },
      { label: 'Commission (12 months)', value: D.sum(D.COMMISSIONS) * 1000, kind: 'money', tone: 'purple', to: set('deals') },
      { label: 'Commission due', value: commissionDue, kind: 'money', tone: 'rose', to: set('deals', { status: 'Commission due' }) },
    ],
    widgets: [
      {
        type: 'donut', title: 'Listings by type', span: 4, centre: 'listings', kind: 'count', to: set('listings'),
        segments: ['Land', 'Villa', 'Apartment', 'Commercial'].map((label, i) => ({ label, value: D.LISTINGS.filter((l) => l.type === label).length, tone: ['teal', 'blue', 'purple', 'orange'][i], to: set('listings', { type: label }) })),
      },
      {
        type: 'bars', title: 'Commission earned per month', span: 8, kind: 'money', labels: M,
        series: [
          { name: 'Commission', values: thousands(D.COMMISSIONS), tone: 'purple' },
          { name: 'Cumulative', values: thousands(cumulative(D.COMMISSIONS)), tone: 'orange', type: 'line', axis: 'right' },
        ],
      },
      {
        type: 'hbars', title: 'Listings by area', span: 5, kind: 'count', stacked: true,
        series: [{ name: 'Active', tone: 'blue' }, { name: 'Under offer', tone: 'amber' }, { name: 'Sold', tone: 'green' }],
        rows: [...new Set(D.LISTINGS.map((l) => l.area))].map((area) => ({ label: area, values: ['Active', 'Under offer', 'Sold'].map((s) => D.LISTINGS.filter((l) => l.area === area && l.status === s).length), to: set('listings', { area }) })),
      },
      { type: 'table', title: 'Deals', span: 7, set: 'deals', columns: ['deal', 'type', 'area', 'price', 'commission', 'status'] },
    ],
    workflow: {
      title: 'Brokerage deal',
      steps: [
        { label: 'Owner lists property', state: 'done' },
        { label: 'Viewings', state: 'done' },
        { label: 'Offer accepted', state: 'current' },
        { label: 'Sale agreement', state: 'next' },
        { label: 'Commission due on buyer’s first payment', state: 'next', note: '2.5% of the price (draft brokerage spec)' },
        { label: 'Title deed transferred once paid', state: 'next' },
      ],
    },
  },
}

// ---------------------------------------------------------------- executive

const incomeTotals = seriesTotal(Object.values(D.INCOME))
const executive = {
  overview: {
    title: 'Executive overview',
    subtitle: 'All Sidra business lines at a glance, December 2025 to November 2026',
    kpis: [
      { label: 'Group income (12 months)', value: D.sum(incomeTotals) * 1000, kind: 'money', tone: 'amber', to: set('sale_contracts') },
      { label: 'Installments collected', value: D.sum(D.COLLECTIONS.collected) * 1000, kind: 'money', tone: 'green', to: set('sale_contracts') },
      { label: 'Construction portfolio', value: projectTotals.budget, kind: 'money', tone: 'sky', to: set('projects') },
      { label: 'Active projects', value: D.PROJECTS.length, kind: 'count', tone: 'blue', to: set('projects') },
      { label: 'Units available', value: inventory.available, kind: 'count', tone: 'teal', to: set('units', { status: 'Available' }) },
      { label: 'Overdue installments', value: D.sum(D.AGEING, 'amount'), kind: 'money', tone: 'rose', to: set('overdue') },
    ],
    widgets: [
      {
        type: 'bars', title: 'Income by business line', note: 'Monthly, stacked, with the cumulative total', span: 8, kind: 'money', labels: M, stacked: true,
        series: [
          ...Object.entries(D.INCOME).map(([name, values], i) => ({ name, values: thousands(values), tone: ['blue', 'teal', 'purple', 'orange'][i] })),
          { name: 'Cumulative', values: thousands(cumulative(incomeTotals)), tone: 'rose', type: 'line', axis: 'right' },
        ],
      },
      {
        type: 'donut', title: 'Income mix', span: 4, centre: '12 months', kind: 'money',
        segments: Object.entries(D.INCOME).map(([label, values], i) => ({ label, value: D.sum(values) * 1000, tone: ['blue', 'teal', 'purple', 'orange'][i], to: { name: ['realestate', 'construction-hub', 'design', 'brokerage'][i] } })),
      },
      { ...projectMap, title: 'Projects and communities', span: 4 },
      {
        type: 'hbars', title: 'Sales funnel (90 days)', span: 4, kind: 'count', funnel: true,
        series: [{ name: 'Leads', tone: 'blue' }],
        rows: D.FUNNEL.map(([label, value], i) => ({ label, values: [value], tone: ['sky', 'blue', 'teal', 'amber', 'green'][i], to: set('leads', i ? { stage: label } : undefined) })),
      },
      { type: 'list', title: 'Needs attention', span: 4, items: D.ATTENTION },
      { ...healthTable, title: 'Construction projects' },
    ],
    workflow: {
      title: 'How work flows at Sidra',
      steps: [
        { label: 'Lead or client enquiry', state: 'done' },
        { label: 'Design and engineering', state: 'done' },
        { label: 'Quotation and contract', state: 'done' },
        { label: 'Construction by stages', state: 'current' },
        { label: 'Sale, installments and collections', state: 'current' },
        { label: 'Handover and title', state: 'next' },
      ],
      actions: [
        { label: 'Live dashboard (real records)', to: { name: 'dashboard' } },
        { label: 'Construction portfolio', to: { name: 'construction-hub' } },
        { label: 'Real estate sales', to: { name: 'realestate' } },
        { label: 'Finance', to: { name: 'finance' }, section: 'finance' },
      ],
    },
  },
}

// ---------------------------------------------------------------- finance

const incomeByMonth = seriesTotal(Object.values(D.INCOME))
const expenseByMonth = seriesTotal(Object.values(D.EXPENSES))
const netByMonth = incomeByMonth.map((v, i) => v - expenseByMonth[i])
const finance = {
  overview: {
    title: 'Finance overview',
    subtitle: 'Income, expenses, cash and what is owed, December 2025 to November 2026',
    kpis: [
      { label: 'Income (12 months)', value: D.sum(incomeByMonth) * 1000, kind: 'money', tone: 'blue', to: { name: 'finance' } },
      { label: 'Expenses (12 months)', value: D.sum(expenseByMonth) * 1000, kind: 'money', tone: 'orange', to: { name: 'finance' } },
      { label: 'Net profit', value: D.sum(netByMonth) * 1000, kind: 'money', tone: 'green', to: { name: 'finance' } },
      { label: 'Cash and bank', value: D.sum(D.BANK_ACCOUNTS, 'balance'), kind: 'money', tone: 'teal', to: set('bank_accounts') },
      { label: 'Owed to Sidra', value: D.sum(D.RECEIVABLES, 'amount'), kind: 'money', tone: 'sky', to: set('overdue') },
      { label: 'Sidra owes', value: D.sum(D.PAYABLES, 'amount'), kind: 'money', tone: 'rose', to: set('subcontractors') },
    ],
    widgets: [
      {
        type: 'bars', title: 'Income and expenses', note: 'Monthly, with net profit', span: 8, kind: 'money', labels: M,
        series: [
          { name: 'Income', values: thousands(incomeByMonth), tone: 'blue' },
          { name: 'Expenses', values: thousands(expenseByMonth), tone: 'orange' },
          { name: 'Net profit', values: thousands(netByMonth), tone: 'green', type: 'line', axis: 'right' },
        ],
      },
      {
        type: 'donut', title: 'Where the money goes', span: 4, centre: '12 months', kind: 'money',
        segments: [
          ...Object.entries(D.SPEND).map(([label, values], i) => ({ label, value: D.sum(values) * 1000, tone: ['blue', 'teal', 'purple', 'amber'][i], to: set('cost') })),
          { label: 'Salaries & admin', value: D.sum(D.EXPENSES['Salaries & admin']) * 1000, tone: 'slate' },
          { label: 'Sales & marketing', value: D.sum(D.EXPENSES['Sales & marketing']) * 1000, tone: 'rose' },
        ],
      },
      {
        type: 'bars', title: 'Cash and bank at month end', span: 6, kind: 'money', labels: M,
        series: [{ name: 'Balance', values: thousands(D.CASH_BALANCE), tone: 'teal' }],
      },
      {
        type: 'hbars', title: 'Owed to Sidra, by age', note: 'Installments and client billings', span: 6, kind: 'money',
        series: [{ name: 'Receivable', tone: 'sky' }],
        rows: D.RECEIVABLES.map((r, i) => ({ label: r.age, values: [r.amount], tone: ['green', 'amber', 'orange', 'rose', 'purple'][i], to: i ? set('overdue', { bucket: r.age }) : set('sale_contracts') })),
      },
      {
        type: 'hbars', title: 'Sidra owes, by age', note: 'Suppliers and subcontractors', span: 6, kind: 'money',
        series: [{ name: 'Payable', tone: 'rose' }],
        rows: D.PAYABLES.map((r, i) => ({ label: r.age, values: [r.amount], tone: ['green', 'amber', 'orange', 'rose'][i], to: set('subcontractors') })),
      },
      { type: 'table', title: 'Bank and cash accounts', span: 6, set: 'bank_accounts', columns: ['account', 'kind', 'balance'] },
    ],
    workflow: {
      title: 'Money in and out',
      steps: [
        { label: 'Invoice or installment falls due', state: 'done' },
        { label: 'Payment received and receipted', state: 'done' },
        { label: 'Allocated to the installment or invoice', state: 'current' },
        { label: 'Reconciled with the bank', state: 'next' },
        { label: 'Month-end close', state: 'next', note: 'ERPNext is the only ledger (decision G4)' },
      ],
      actions: [{ label: 'Ledger and invoices (live)', to: { name: 'finance' }, section: 'finance' }],
    },
  },
}

/** Each sample module: its menu label, route name, tabs (key -> page), and links to real records. */
export const MODULES = {
  executive: { label: 'Executive', route: 'executive', icon: 'lucide-gauge', tabs: executive, tabLabels: { overview: 'Overview' } },
  build: {
    label: 'Construction', route: 'construction-hub', icon: 'lucide-hard-hat', tabs: construction,
    tabLabels: { portfolio: 'Portfolio', schedule: 'Schedule', cost: 'Cost & budget', variations: 'Variations', quality: 'Quality & inspections', risk: 'Risk', stock: 'Stock & materials', subcontractors: 'Subcontractors' },
    records: [
      { label: 'Construction jobs', to: { name: 'construction' }, section: 'construction' },
      { label: 'Variation records', to: { name: 'variations-list' }, list: 'variations' },
      { label: 'Inspection reports', to: { name: 'inspections-list' }, list: 'inspections' },
    ],
  },
  design: {
    label: 'Design & Engineering', route: 'design', icon: 'lucide-drafting-compass', tabs: design,
    tabLabels: { overview: 'Overview', architecture: 'Architecture', civil: 'Civil engineering', inspection: 'Inspection services' },
  },
  realestate: {
    label: 'Real Estate Sales', route: 'realestate', icon: 'lucide-building-2', tabs: realestate,
    tabLabels: { inventory: 'Inventory', pipeline: 'Pipeline', contracts: 'Contracts & collections' },
    records: [
      { label: 'Units', to: { name: 'properties' }, section: 'properties' },
      { label: 'Reservations', to: { name: 'reservations-list' }, list: 'reservations' },
      { label: 'Contracts', to: { name: 'contracts' }, section: 'contracts' },
      { label: 'Collections', to: { name: 'collections' }, section: 'collections' },
    ],
  },
  brokerage: { label: 'Brokerage', route: 'brokerage', icon: 'lucide-key-round', tabs: brokerage, tabLabels: { overview: 'Overview' } },
  finance: {
    label: 'Finance', route: 'finance-hub', icon: 'lucide-landmark', tabs: finance, tabLabels: { overview: 'Overview' },
    records: [{ label: 'Ledger and invoices (live)', to: { name: 'finance' }, section: 'finance' }],
  },
}
