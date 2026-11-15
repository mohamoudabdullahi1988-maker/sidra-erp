// The sample lists a chart or tile opens (one level, read-only). Each list names its columns;
// `kind` only chooses how a value is drawn (format.js / SampleTable.vue).
import * as D from './data.js'

const flatProjects = D.PROJECTS.map(({ health, ...p }) => ({
  ...p,
  variance: p.forecast - p.budget,
  ...Object.fromEntries(Object.entries(health).map(([key, value]) => [`${key}_health`, value])),
}))

export const DATASETS = {
  projects: {
    title: 'Construction projects',
    section: 'build',
    columns: [
      ['id', 'Project'], ['name', 'Name'], ['scope', 'Scope'], ['city', 'Location'], ['phase', 'Phase', 'chip'],
      ['budget', 'Budget', 'money'], ['forecast', 'Forecast', 'money'], ['paid', 'Paid', 'money'], ['progress', 'Progress', 'progress'],
      ['end', 'Completion', 'date'], ['scope_health', 'Scope', 'rag'], ['time_health', 'Time', 'rag'], ['cost_health', 'Cost', 'rag'], ['quality_health', 'Quality', 'rag'], ['safety_health', 'Safety', 'rag'],
    ],
    rows: flatProjects,
  },
  milestones: {
    title: 'Milestones',
    section: 'build',
    columns: [['project', 'Project'], ['milestone', 'Milestone'], ['planned', 'Planned', 'date'], ['forecast', 'Forecast', 'date'], ['days_late', 'Days late', 'count'], ['status', 'Status', 'chip']],
    rows: D.MILESTONES,
  },
  cost: {
    title: 'Budget by cost category',
    section: 'build',
    columns: [['category', 'Category'], ['budget', 'Budget', 'money'], ['actual', 'Spent to date', 'money'], ['forecast', 'Forecast', 'money']],
    rows: D.COST_BUDGET,
  },
  variations: {
    title: 'Variation orders',
    section: 'build',
    columns: [['id', 'Variation'], ['project', 'Project'], ['description', 'Description'], ['type', 'Type'], ['value', 'Value', 'money'], ['status', 'Status', 'chip'], ['approver', 'Second approver'], ['raised', 'Raised', 'date']],
    rows: D.VARIATIONS,
  },
  inspections: {
    title: 'Inspections',
    section: 'build',
    columns: [['id', 'Report'], ['project', 'Project'], ['item', 'Inspected'], ['result', 'Result', 'chip'], ['open_defects', 'Open defects', 'count'], ['date', 'Date', 'date'], ['inspector', 'Inspector']],
    rows: D.INSPECTIONS,
  },
  risks: {
    title: 'Risk register',
    section: 'build',
    columns: [['id', 'Risk'], ['category', 'Category'], ['description', 'Description'], ['project', 'Project'], ['owner', 'Owner'], ['rating', 'Rating', 'chip'], ['status', 'Status', 'chip']],
    rows: D.RISKS,
  },
  stock: {
    title: 'Stock and materials',
    section: 'build',
    columns: [['item', 'Material'], ['unit', 'Unit'], ['on_hand', 'On hand', 'count'], ['reorder_level', 'Reorder level', 'count'], ['below_reorder', 'Below reorder', 'chip'], ['value', 'Stock value', 'money'], ['issued_this_month', 'Issued this month', 'count'], ['location', 'Location']],
    rows: D.STOCK,
  },
  subcontractors: {
    title: 'Subcontractors',
    section: 'build',
    columns: [['id', 'Code'], ['name', 'Subcontractor'], ['trade', 'Trade'], ['active_projects', 'Projects', 'count'], ['contract_value', 'Contract value', 'money'], ['paid', 'Paid', 'money'], ['retention', 'Retention held', 'money'], ['rating', 'Rating']],
    rows: D.SUBCONTRACTORS,
  },
  design_jobs: {
    title: 'Design and engineering jobs',
    section: 'design',
    columns: [['id', 'Job'], ['discipline', 'Service'], ['job', 'Description'], ['stage', 'Stage', 'chip'], ['lead', 'Lead'], ['fee', 'Fee', 'money'], ['billed', 'Billed', 'money'], ['due', 'Due', 'date']],
    rows: D.DESIGN_JOBS,
  },
  units: {
    title: 'Plots and units',
    section: 'realestate',
    columns: [['unit', 'Unit'], ['community', 'Community'], ['type', 'Type'], ['size_sqm', 'Size (m²)', 'count'], ['price', 'Price', 'moneyFull'], ['status', 'Status', 'chip']],
    rows: D.UNITS,
  },
  leads: {
    title: 'Leads',
    section: 'realestate',
    columns: [['id', 'Lead'], ['name', 'Name'], ['source', 'Channel'], ['interest', 'Interested in'], ['stage', 'Stage', 'chip'], ['agent', 'Agent'], ['created', 'Created', 'date']],
    rows: D.LEADS,
  },
  opportunities: {
    title: 'Opportunities',
    section: 'crm',
    columns: [['id', 'Opportunity'], ['party', 'Lead'], ['channel', 'Channel'], ['interest', 'Interested in'], ['stage', 'Stage', 'chip'], ['amount', 'Value', 'money'], ['closing', 'Expected closing', 'date']],
    rows: D.OPPORTUNITIES,
  },
  agents: {
    title: 'Sales agents',
    section: 'realestate',
    columns: [['agent', 'Agent'], ['leads', 'Leads', 'count'], ['contracts', 'Contracts', 'count'], ['conversion', 'Conversion', 'pct'], ['value', 'Contract value', 'money']],
    rows: D.AGENTS,
  },
  sale_contracts: {
    title: 'Sale contracts (latest)',
    section: 'realestate',
    columns: [['contract', 'Contract'], ['customer', 'Customer'], ['community', 'Community'], ['plan', 'Plan'], ['value', 'Value', 'moneyFull'], ['collected', 'Collected', 'moneyFull'], ['signed', 'Signed', 'date'], ['status', 'Status', 'chip']],
    rows: D.SALE_CONTRACTS,
  },
  overdue: {
    title: 'Overdue contracts',
    section: 'realestate',
    columns: [['contract', 'Contract'], ['customer', 'Customer'], ['community', 'Community'], ['bucket', 'Overdue for', 'chip'], ['overdue', 'Overdue amount', 'moneyFull'], ['installments_late', 'Installments late', 'count'], ['officer', 'Officer']],
    rows: D.OVERDUE,
  },
  bank_accounts: {
    title: 'Bank and cash accounts',
    section: 'finance',
    columns: [['account', 'Account'], ['kind', 'Type', 'chip'], ['currency', 'Currency'], ['balance', 'Balance', 'money']],
    rows: D.BANK_ACCOUNTS,
  },
  listings: {
    title: 'Brokerage listings',
    section: 'brokerage',
    columns: [['id', 'Listing'], ['type', 'Type'], ['area', 'Area'], ['owner', 'Owner'], ['asking', 'Asking price', 'moneyFull'], ['status', 'Status', 'chip'], ['days_listed', 'Days listed', 'count']],
    rows: D.LISTINGS,
  },
  deals: {
    title: 'Brokerage deals',
    section: 'brokerage',
    columns: [['deal', 'Deal'], ['listing', 'Listing'], ['type', 'Type'], ['area', 'Area'], ['price', 'Price', 'moneyFull'], ['commission', 'Commission (2.5%)', 'moneyFull'], ['status', 'Status', 'chip']],
    rows: D.DEALS,
  },
}

for (const set of Object.values(DATASETS)) {
  set.columns = set.columns.map(([key, label, kind]) => ({ key, label, kind: kind ?? 'text' }))
}

/** Rows of a list that match every filter (field -> value). */
export function filterRows(set, filter = {}) {
  const entries = Object.entries(filter).filter(([key]) => set.columns.some((c) => c.key === key) || set.rows[0]?.[key] !== undefined)
  return set.rows.filter((row) => entries.every(([key, value]) => String(row[key]) === String(value)))
}

/** A link to a sample list, optionally filtered: { name: 'sample', params, query }. */
export function sampleLink(set, filter) {
  return { name: 'sample', params: { set }, query: filter ?? {} }
}
