import { RECORDS, SECTIONS, listRoute } from './records.js'

// The server's read flags control transaction links; dashboard/report routes check again.
export function sectionLinks(key, readable = {}, nav = []) {
  const links = []
  const add = (label, name, params) => links.push({ label, to: { name, ...(params ? { params } : {}) } })
  const records = (...sections) => {
    for (const section of sections) for (const list of SECTIONS[section] || []) {
      if (readable[list]?.read) add(RECORDS[list].title, listRoute(list))
    }
  }
  if (key === 'executive') add('Live dashboard', 'dashboard')
  if (key === 'construction-hub') {
    records('construction')
    for (const [tab, label] of [['schedule', 'Schedule report'], ['cost', 'Cost & budget'], ['risk', 'Risk overview'], ['stock', 'Stock & materials'], ['subcontractors', 'Subcontractors']]) add(label, 'construction-hub', { tab })
  }
  if (key === 'design') {
    for (const [tab, label] of [['overview', 'Overview'], ['architecture', 'Architecture'], ['civil', 'Civil engineering'], ['inspection', 'Inspection services']]) add(label, 'design', { tab })
    for (const list of ['jobs', 'construction_quotations', 'inspections']) if (readable[list]?.read) add(RECORDS[list].title, listRoute(list))
  }
  if (key === 'realestate') {
    records('properties', 'sales', 'contracts')
    if (nav.some((n) => n.key === 'collections')) add('Collections report', 'collections')
    add('Sales pipeline', 'realestate', { tab: 'pipeline' })
  }
  if (key === 'customers') { add('CRM dashboard', 'customers'); records('customers') }
  if (key === 'finance-hub') add('Ledger and financial reports', 'finance')
  if (key === 'setup') records('setup')
  if (key === 'brokerage') add('Overview · sample', 'brokerage')
  return links
}
