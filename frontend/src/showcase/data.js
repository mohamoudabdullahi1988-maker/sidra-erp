// SAMPLE DATA for the client demonstration (Mohamoud, 14 Nov 2026): a broad, clearly labelled
// surface across every Sidra business line, to be replaced by real records after the client's
// go-ahead. Every figure here is fictional. Nothing is read from or written to the server, and no
// business rule is decided here; screens that show real records are unchanged.
//
// Sidra's own projects carry their public names (Masalaha Hagbad, Rayan Gardens, Safa Housing,
// Berbera Townhouses). Masalaha Hagbad uses 9 m x 24 m plots at the standard price (Mohamoud,
// 14 Nov 2026: the published $11,000 / $5,500 was a friends-and-family discount; standard is 30%
// more): $14,300 full / $7,150 half, interest-free from $325 a month over 22 months. Every other
// figure, and every client project and person, is invented.

export const TODAY = '2026-11-14'

/** Twelve reporting months, Dec 2025 to Nov 2026. */
export const MONTHS = monthRange('2025-12', 12)
/** Eighteen months for cash flow: twelve actual, six forecast. */
export const CASH_MONTHS = monthRange('2025-12', 18)

function monthRange(first, n) {
  const [y0, m0] = first.split('-').map(Number)
  return Array.from({ length: n }, (_, i) => {
    const m = m0 - 1 + i
    return `${y0 + Math.floor(m / 12)}-${String((m % 12) + 1).padStart(2, '0')}`
  })
}

/** Deterministic pseudo-random numbers, so every visit shows the same sample. */
function seeded(seed) {
  let s = seed >>> 0
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0
    return s / 4294967296
  }
}
const pick = (rand, list) => list[Math.floor(rand() * list.length)]
const k = (n) => n * 1000

const FIRST = ['Hodan', 'Abdi', 'Amina', 'Mohamed', 'Faisa', 'Ahmed', 'Sahra', 'Yusuf', 'Ifrah', 'Hassan', 'Nimco', 'Omar', 'Ubah', 'Khadar', 'Deeqa', 'Ismail', 'Hibo', 'Liban', 'Ayaan', 'Mustafe', 'Kaltun', 'Guled', 'Samira', 'Jama']
const INITIAL = 'ABCDFGHIJKMNORSWY'
function person(rand) {
  return `${pick(rand, FIRST)} ${pick(rand, INITIAL.split(''))}.`
}

// ---------------------------------------------------------------- construction projects

export const PROJECTS = [
  { id: 'P-01', name: 'Rayan Gardens', scope: 'Mid-market homes, Masalaha', client: 'Sidra development', city: 'Hargeisa', phase: 'Construction', budget: 4200000, committed: 3350000, forecast: 4380000, paid: 2610000, progress: 64, start: '2025-08-01', end: '2027-04-30', health: { scope: 'G', time: 'A', cost: 'A', quality: 'G', safety: 'G' } },
  { id: 'P-02', name: 'Masalaha Hagbad', scope: 'Plot servicing: roads, water, power', client: 'Sidra development', city: 'Hargeisa', phase: 'Construction', budget: 1650000, committed: 1420000, forecast: 1610000, paid: 1180000, progress: 78, start: '2025-06-15', end: '2026-12-20', health: { scope: 'G', time: 'G', cost: 'G', quality: 'G', safety: 'G' } },
  { id: 'P-03', name: 'Berbera Townhouses', scope: 'Off-plan coastal townhouses: stone walls, raised foundations, insulated', client: 'Sidra development', city: 'Berbera', phase: 'Procurement', budget: 3100000, committed: 1240000, forecast: 3260000, paid: 520000, progress: 18, start: '2026-05-01', end: '2028-02-28', health: { scope: 'G', time: 'A', cost: 'R', quality: 'G', safety: 'G' } },
  { id: 'P-04', name: 'Safa Housing', scope: 'Affordable homes built to be extended', client: 'Sidra development', city: 'Hargeisa', phase: 'Construction', budget: 2450000, committed: 2050000, forecast: 2520000, paid: 1620000, progress: 71, start: '2025-10-01', end: '2027-01-31', health: { scope: 'A', time: 'G', cost: 'A', quality: 'A', safety: 'G' } },
  { id: 'P-05', name: 'Gabiley Road Villas', scope: '6 private villas', client: 'Client contract', city: 'Gabiley', phase: 'Handover', budget: 980000, committed: 975000, forecast: 1010000, paid: 905000, progress: 96, start: '2025-03-01', end: '2026-11-30', health: { scope: 'G', time: 'A', cost: 'A', quality: 'G', safety: 'G' } },
  { id: 'P-06', name: 'Borama Clinic Extension', scope: 'Clinic wing and civil works', client: 'Client contract', city: 'Borama', phase: 'Design', budget: 760000, committed: 120000, forecast: 760000, paid: 64000, progress: 6, start: '2026-09-15', end: '2027-08-31', health: { scope: 'G', time: 'G', cost: 'G', quality: 'G', safety: 'G' } },
  { id: 'P-07', name: 'Sheikh Road Culverts', scope: 'Road drainage and box culverts', client: 'Municipal contract', city: 'Sheikh', phase: 'Construction', budget: 1460000, committed: 1180000, forecast: 1540000, paid: 860000, progress: 55, start: '2026-01-10', end: '2027-03-15', health: { scope: 'G', time: 'R', cost: 'A', quality: 'G', safety: 'A' } },
]

/** Approximate coordinates (longitude, latitude) for the schematic map. */
export const CITIES = {
  Hargeisa: [44.06, 9.56],
  Berbera: [45.03, 10.44],
  Burao: [45.53, 9.52],
  Gabiley: [43.63, 9.7],
  Borama: [43.18, 9.94],
  Sheikh: [45.2, 9.93],
  Erigavo: [47.37, 10.62],
}

export const PHASES = ['Design', 'Procurement', 'Construction', 'Handover']

const STAGES = ['Design approved', 'Permits issued', 'Foundations', 'Structure complete', 'Roofing', 'Services (MEP)', 'Finishes', 'Handover']

function addDays(iso, days) {
  const d = new Date(Date.parse(iso) + days * 86400000)
  return d.toISOString().slice(0, 10)
}

/** Key milestones per project, spread across the project's dates. */
export const MILESTONES = PROJECTS.flatMap((p) => {
  const span = (Date.parse(p.end) - Date.parse(p.start)) / 86400000
  const rand = seeded(p.id.charCodeAt(3) * 97)
  return STAGES.map((stage, i) => {
    const planned = addDays(p.start, Math.round((span * (i + 1)) / STAGES.length))
    const done = (i + 1) / STAGES.length <= p.progress / 100 + 0.04
    const slip = p.health.time === 'R' ? 21 : p.health.time === 'A' ? 9 : 0
    const forecast = done ? planned : addDays(planned, slip + Math.round(rand() * 4))
    let status = 'Upcoming'
    if (done) status = 'Completed'
    else if (planned <= addDays(TODAY, 45)) status = slip >= 21 ? 'Delayed' : slip ? 'At risk' : 'On track'
    return { project: p.name, milestone: stage, planned, forecast, status, days_late: done ? 0 : Math.max(0, Math.round((Date.parse(forecast) - Date.parse(planned)) / 86400000)) }
  })
})

/** Monthly construction spend by cost category, thousands of dollars. */
export const SPEND = {
  Materials: [210, 230, 260, 240, 280, 300, 290, 310, 320, 300, 330, 340],
  Labour: [120, 125, 130, 135, 140, 150, 145, 150, 155, 150, 160, 165],
  Subcontract: [90, 85, 100, 110, 120, 130, 140, 135, 150, 160, 155, 170],
  Equipment: [40, 35, 45, 50, 45, 55, 50, 60, 55, 50, 60, 55],
}
export const SPEND_FORECAST = [760, 780, 800, 740, 690, 650]

export const COST_BUDGET = [
  { category: 'Materials', budget: 6400000, actual: 3410000, forecast: 6650000 },
  { category: 'Labour', budget: 3300000, actual: 1725000, forecast: 3360000 },
  { category: 'Subcontract', budget: 3200000, actual: 1545000, forecast: 3290000 },
  { category: 'Equipment', budget: 1100000, actual: 600000, forecast: 1140000 },
  { category: 'Overheads', budget: 600000, actual: 479000, forecast: 640000 },
]

export const VARIATIONS = [
  ['VO-0141', 'Rayan Gardens', 'Boundary wall raised to 2.4 m', 18500, 'Approved', 'General Manager', '2026-09-02', 6],
  ['VO-0142', 'Rayan Gardens', 'Solar water heaters, block C', 42600, 'Approved', 'General Manager', '2026-09-18', 9],
  ['VO-0143', 'Safa Housing', 'Extra bedroom on ground floor, type B', 27400, 'Approved', 'General Manager', '2026-09-25', 4],
  ['VO-0144', 'Gabiley Road Villas', 'Additional power sockets, villa 3', 860, 'Approved', 'Project Manager', '2026-10-01', 1],
  ['VO-0145', 'Sheikh Road Culverts', 'Extra box culvert at km 4.2', 64800, 'Awaiting approval', 'General Manager', '2026-10-08', null],
  ['VO-0146', 'Safa Housing', 'Roof slab ready for a second storey', 31200, 'Awaiting approval', 'General Manager', '2026-10-15', null],
  ['VO-0147', 'Masalaha Hagbad', 'Additional street lighting, phase 2', 22900, 'Approved', 'General Manager', '2026-10-17', 7],
  ['VO-0148', 'Gabiley Road Villas', 'Perimeter landscaping', 9400, 'Approved', 'General Manager', '2026-10-21', 3],
  ['VO-0149', 'Rayan Gardens', 'Mosque access road', 38700, 'Awaiting approval', 'General Manager', '2026-10-29', null],
  ['VO-0150', 'Berbera Townhouses', 'Deeper foundations after soil report', 96500, 'Under review', 'Project Manager', '2026-11-03', null],
  ['VO-0151', 'Masalaha Hagbad', 'Water tank stand reinforcement', 740, 'Approved', 'Project Manager', '2026-11-05', 1],
  ['VO-0152', 'Sheikh Road Culverts', 'Gabion protection, river bend', 18200, 'Under review', 'Project Manager', '2026-11-09', null],
  ['VO-0153', 'Safa Housing', 'Rooftop water storage', 12600, 'Draft', 'Project Manager', '2026-11-11', null],
  ['VO-0154', 'Rayan Gardens', 'Gatehouse CCTV', 7900, 'Draft', 'Project Manager', '2026-11-13', null],
].map(([id, project, description, value, status, approver, raised, days]) => ({ id, project, description, type: 'Addition', value, status, approver, raised, days_to_approve: days }))

export const INSPECTIONS = [
  ['IR-0311', 'Rayan Gardens', 'Foundations, block D', 'Pass', '2026-09-04', 0],
  ['IR-0312', 'Safa Housing', 'Ground-floor slab, block 2', 'Pass with remarks', '2026-09-11', 1],
  ['IR-0313', 'Masalaha Hagbad', 'Water main pressure test', 'Pass', '2026-09-16', 0],
  ['IR-0314', 'Sheikh Road Culverts', 'Culvert C2 reinforcement', 'Fail', '2026-09-22', 2],
  ['IR-0315', 'Gabiley Road Villas', 'Electrical first fix, villa 4', 'Pass', '2026-09-29', 0],
  ['IR-0316', 'Rayan Gardens', 'Structure, block B', 'Pass', '2026-10-03', 0],
  ['IR-0317', 'Safa Housing', 'Blockwork, homes 14-20', 'Pass with remarks', '2026-10-08', 1],
  ['IR-0318', 'Masalaha Hagbad', 'Road base compaction, section 3', 'Pass', '2026-10-14', 0],
  ['IR-0319', 'Sheikh Road Culverts', 'Culvert C2 re-inspection', 'Pass', '2026-10-17', 0],
  ['IR-0320', 'Rayan Gardens', 'Roofing, villas 21-28', 'Fail', '2026-10-21', 3],
  ['IR-0321', 'Gabiley Road Villas', 'Final snag list, villas 1-3', 'Pass with remarks', '2026-10-27', 2],
  ['IR-0322', 'Safa Housing', 'Windows and doors, homes 1-8', 'Pass', '2026-11-02', 0],
  ['IR-0323', 'Berbera Townhouses', 'Raised foundations, townhouses 1-6', 'Pass', '2026-11-05', 0],
  ['IR-0324', 'Masalaha Hagbad', 'Power poles, section 4', 'Pass', '2026-11-09', 0],
  ['IR-0325', 'Sheikh Road Culverts', 'Culvert C4 formwork', 'Fail', '2026-11-11', 1],
  ['IR-0326', 'Rayan Gardens', 'Plastering, villas 9-16', 'Pass', '2026-11-13', 0],
].map(([id, project, item, result, date, defects]) => ({ id, project, item, result, date, open_defects: defects, inspector: 'Site Engineer' }))

export const RISKS = [
  ['R-01', 'Regulatory compliance', 'Permit for Berbera Townhouses phase 2 not yet issued', 'Berbera Townhouses', 'Project Manager', 'High', 'Open'],
  ['R-02', 'Design errors', 'Drawings revision for the extension option', 'Safa Housing', 'Design Lead', 'Medium', 'Mitigating'],
  ['R-03', 'Scope creep', 'Buyer requests for early extensions', 'Safa Housing', 'Project Manager', 'Medium', 'Open'],
  ['R-04', 'Labour shortages', 'Skilled tilers scarce during Hajj season', 'Rayan Gardens', 'Site Manager', 'Low', 'Monitoring'],
  ['R-05', 'Material delivery', 'Cement shipments delayed at Berbera port', 'All projects', 'Procurement Officer', 'High', 'Mitigating'],
  ['R-06', 'Schedule delays', 'Culvert C4 behind after failed inspection', 'Sheikh Road Culverts', 'Project Manager', 'High', 'Open'],
  ['R-07', 'Cost overruns', 'Steel price up 9% since budget', 'All projects', 'Quantity Surveyor', 'Medium', 'Monitoring'],
  ['R-08', 'Equipment downtime', 'Concrete pump due for overhaul', 'Rayan Gardens', 'Plant Manager', 'Low', 'Monitoring'],
  ['R-09', 'Weather disruption', 'Gu rains may flood Sheikh river crossing', 'Sheikh Road Culverts', 'Site Manager', 'Medium', 'Open'],
  ['R-10', 'Safety hazards', 'Work at height on townhouse roofs', 'Safa Housing', 'Safety Officer', 'Medium', 'Mitigating'],
  ['R-11', 'Stakeholder disputes', 'Neighbour boundary claim, Masalaha section 5', 'Masalaha Hagbad', 'Legal Officer', 'Low', 'Open'],
  ['R-12', 'Currency movement', 'Shilling movement on local labour rates', 'All projects', 'Finance Manager', 'Low', 'Monitoring'],
].map(([id, category, description, project, owner, rating, status]) => ({ id, category, description, project, owner, rating, status }))

export const PENDING = { Decisions: 5, Actions: 3, 'Change requests': 4 }

export const STOCK = [
  ['Cement (50 kg bags)', 'bags', 2450, 3000, 9.2, 3820, 'Central yard, Hargeisa'],
  ['Rebar 12 mm', 'tonnes', 38, 25, 780, 21, 'Central yard, Hargeisa'],
  ['Rebar 16 mm', 'tonnes', 21, 25, 790, 18, 'Central yard, Hargeisa'],
  ['Concrete blocks 15 cm', 'pieces', 18400, 10000, 0.85, 12600, 'Central yard, Hargeisa'],
  ['Sand', 'm³', 420, 300, 18, 380, 'Berbera yard'],
  ['Aggregate 20 mm', 'm³', 310, 250, 26, 290, 'Berbera yard'],
  ['Roofing sheets', 'sheets', 640, 500, 14, 410, 'Central yard, Hargeisa'],
  ['Timber formwork', 'm³', 22, 15, 310, 9, 'Central yard, Hargeisa'],
  ['PVC pipe 110 mm', 'lengths', 180, 200, 11, 140, 'Central yard, Hargeisa'],
  ['Floor tiles', 'm²', 2100, 1500, 12, 950, 'Central yard, Hargeisa'],
  ['Paint (20 L)', 'drums', 96, 120, 48, 70, 'Central yard, Hargeisa'],
  ['Electrical cable 2.5 mm', 'rolls', 74, 60, 42, 38, 'Burao store'],
].map(([item, unit, on_hand, reorder, cost, issued, location]) => ({
  item, unit, on_hand, reorder_level: reorder, unit_cost: cost, value: Math.round(on_hand * cost), issued_this_month: issued, location,
  below_reorder: on_hand < reorder ? 'Yes' : 'No',
}))

/** Materials issued to each site this month, by value. */
export const ISSUED_BY_SITE = { 'Rayan Gardens': 61200, 'Masalaha Hagbad': 18400, 'Berbera Townhouses': 22900, 'Safa Housing': 39800, 'Gabiley Road Villas': 6100, 'Sheikh Road Culverts': 27300 }

export const SUBCONTRACTORS = [
  ['SC-01', 'Ridge Steel Works', 'Steel fixing', 3, 486000, 352000, 4.6],
  ['SC-02', 'Golis Electrical', 'Electrical', 4, 312000, 205000, 4.4],
  ['SC-03', 'Saahil Plumbing', 'Plumbing', 3, 228000, 161000, 4.1],
  ['SC-04', 'Maan Aluminium & Glass', 'Glazing', 2, 174000, 98000, 3.9],
  ['SC-05', 'Daallo Roofing', 'Roofing', 2, 196000, 151000, 4.3],
  ['SC-06', 'Nugaal Earthworks', 'Earthworks', 3, 268000, 214000, 4.0],
  ['SC-07', 'Oog Tiling', 'Tiling', 2, 142000, 63000, 3.6],
  ['SC-08', 'Laas Painting', 'Painting', 3, 98000, 41000, 4.2],
].map(([id, name, trade, projects, value, paid, rating]) => ({ id, name, trade, active_projects: projects, contract_value: value, paid, retention: Math.round(paid * 0.05), rating }))

// ---------------------------------------------------------------- design and engineering

export const DESIGN_JOBS = [
  ['DE-201', 'Architecture', 'Villa for a diaspora client, Jigjiga Yar', 'Concept', 'Architect 1', 8500, 4250, '2026-12-05'],
  ['DE-202', 'Architecture', 'Rayan Gardens phase 2 masterplan', 'Design development', 'Architect 2', 24000, 12000, '2027-01-20'],
  ['DE-203', 'Architecture', 'Berbera Townhouses interiors', 'Construction drawings', 'Architect 1', 18000, 13500, '2026-11-28'],
  ['DE-204', 'Architecture', 'Office fit-out, Burao', 'Permit drawings', 'Architect 3', 6200, 3100, '2026-12-12'],
  ['DE-205', 'Architecture', 'Diaspora client villa, Masalaha', 'Brief', 'Architect 2', 5400, 0, '2027-01-10'],
  ['DE-206', 'Architecture', 'School block, Gabiley', 'Completed', 'Architect 3', 11800, 11800, '2026-10-30'],
  ['DE-207', 'Architecture', 'Hotel facade refresh, Hargeisa', 'Concept', 'Architect 1', 9600, 2880, '2026-12-22'],
  ['DE-208', 'Civil engineering', 'Sheikh Road culvert hydraulics', 'Review', 'Engineer 1', 21500, 15050, '2026-11-25'],
  ['DE-209', 'Civil engineering', 'Masalaha Hagbad drainage design', 'Issued', 'Engineer 2', 16400, 16400, '2026-10-18'],
  ['DE-210', 'Civil engineering', 'Borama clinic structural design', 'Calculations', 'Engineer 1', 14200, 5680, '2026-12-15'],
  ['DE-211', 'Civil engineering', 'Warehouse slab, Berbera', 'Design', 'Engineer 3', 7300, 2190, '2026-12-08'],
  ['DE-212', 'Civil engineering', 'Topographic survey, Erigavo', 'Survey', 'Surveyor', 4800, 1440, '2026-11-30'],
  ['DE-213', 'Civil engineering', 'Retaining wall, Rayan Gardens', 'Issued', 'Engineer 2', 6900, 6900, '2026-10-22'],
  ['DE-214', 'Inspection services', 'Pre-purchase inspection, villa', 'Report', 'Inspector 1', 650, 650, '2026-11-18'],
  ['DE-215', 'Inspection services', 'Structural audit, 3-storey block', 'On site', 'Inspector 2', 2400, 1200, '2026-11-21'],
  ['DE-216', 'Inspection services', 'Bank valuation support, plots', 'Scheduled', 'Inspector 1', 900, 0, '2026-11-24'],
  ['DE-217', 'Inspection services', 'Fire safety inspection, hotel', 'Issued', 'Inspector 2', 1800, 1800, '2026-11-06'],
  ['DE-218', 'Inspection services', 'Defects inspection, apartment', 'Requested', 'Inspector 1', 550, 0, '2026-11-27'],
].map(([id, discipline, job, stage, lead, fee, billed, due]) => ({ id, discipline, job, stage, lead, fee, billed, due }))

export const DESIGN_STAGES = {
  Architecture: ['Brief', 'Concept', 'Design development', 'Permit drawings', 'Construction drawings', 'Completed'],
  'Civil engineering': ['Survey', 'Design', 'Calculations', 'Review', 'Issued'],
  'Inspection services': ['Requested', 'Scheduled', 'On site', 'Report', 'Issued'],
}

/** Fees invoiced per month, thousands of dollars. */
export const DESIGN_FEES = {
  Architecture: [18, 22, 19, 24, 21, 26, 28, 23, 25, 30, 29, 31],
  'Civil engineering': [14, 15, 16, 18, 17, 20, 22, 21, 23, 25, 24, 26],
  'Inspection services': [3, 3, 3, 3, 4, 4, 5, 4, 4, 5, 5, 5],
}

// ---------------------------------------------------------------- real estate sales

export const COMMUNITIES = [
  { name: 'Masalaha Hagbad', kind: 'Plots, 9 × 24 m', city: 'Hargeisa', total: 240, sold: 186, reserved: 14, price: 14300, fixed: [['Full plot', 14300], ['Half plot', 7150]] },
  { name: 'Rayan Gardens', kind: 'Homes', city: 'Hargeisa', total: 72, sold: 41, reserved: 8, price: 68000 },
  { name: 'Safa Housing', kind: 'Expandable homes', city: 'Hargeisa', total: 60, sold: 44, reserved: 6, price: 38000 },
  { name: 'Berbera Townhouses', kind: 'Townhouses (off-plan)', city: 'Berbera', total: 40, sold: 11, reserved: 6, price: 86000 },
].map((c) => ({ ...c, available: c.total - c.sold - c.reserved }))

export const UNITS = COMMUNITIES.flatMap((c, ci) => {
  const rand = seeded(31 + ci)
  const prefix = c.name.split(' ').map((w) => w[0]).join('')
  return Array.from({ length: c.total }, (_, i) => {
    const status = i < c.sold ? 'Sold' : i < c.sold + c.reserved ? 'Reserved' : 'Available'
    if (c.fixed) {
      // The published offer: full plots 9 x 24 m, half plots 9 x 12 m, fixed prices.
      const [type, price] = c.fixed[i % 3 === 2 ? 1 : 0]
      return { unit: `${prefix}-${String(i + 1).padStart(3, '0')}`, community: c.name, type, size_sqm: type === 'Full plot' ? 216 : 108, price, status }
    }
    const size = c.kind.startsWith('Townhouses') ? 140 + Math.round(rand() * 60) : 90 + Math.round(rand() * 110)
    const price = Math.round((c.price * (0.85 + rand() * 0.3)) / 100) * 100
    return { unit: `${prefix}-${String(i + 1).padStart(3, '0')}`, community: c.name, type: c.kind, size_sqm: size, price, status }
  })
})

export const SALES_BY_MONTH = [18, 15, 22, 24, 27, 21, 26, 29, 25, 31, 28, 33]

export const FUNNEL = [
  ['Leads', 486],
  ['Site visits', 212],
  ['Quotations', 131],
  ['Reservations', 58],
  ['Contracts', 41],
]

// Lead channels: how each lead first reached Sidra (ERPNext Lead Source on live records).
export const LEAD_SOURCES = { WhatsApp: 128, 'Diaspora referral': 104, Facebook: 71, 'Walk In': 64, 'Phone Call': 52, Email: 29, Instagram: 21, Website: 17 }
export const CHANNEL_TONES = ['green', 'purple', 'blue', 'orange', 'teal', 'sky', 'rose', 'slate']
export const LEADS_BY_MONTH = [31, 28, 36, 39, 42, 37, 44, 46, 41, 49, 45, 48]

export const LEADS = (() => {
  const rand = seeded(7)
  const stages = FUNNEL.map(([s]) => s)
  const rows = []
  let n = 1
  for (const [source, total] of Object.entries(LEAD_SOURCES)) {
    for (let i = 0; i < total; i++) {
      const r = rand()
      const stage = r < 0.084 ? stages[4] : r < 0.12 ? stages[3] : r < 0.27 ? stages[2] : r < 0.44 ? stages[1] : stages[0]
      rows.push({ id: `L-${String(n++).padStart(4, '0')}`, name: person(rand), source, interest: pick(rand, COMMUNITIES).name, stage, agent: `Sales agent ${1 + Math.floor(rand() * 5)}`, created: addDays('2026-08-16', Math.floor(rand() * 90)) })
    }
  }
  return rows.sort((a, b) => (a.created < b.created ? 1 : -1))
})()

/** CRM opportunities by sales stage (ERPNext's standard stages): count and value in USD. */
export const OPPORTUNITY_STAGES = [
  ['Prospecting', 64, 812000],
  ['Qualification', 41, 598000],
  ['Needs Analysis', 27, 402000],
  ['Proposal/Price Quote', 19, 311000],
  ['Negotiation/Review', 11, 176000],
]
export const OPPORTUNITIES = (() => {
  const rand = seeded(11)
  const rows = []
  let n = 1
  for (const [stage, count, value] of OPPORTUNITY_STAGES) {
    for (let i = 0; i < count; i++) {
      const lead = LEADS[Math.floor(rand() * LEADS.length)]
      rows.push({ id: `OPP-${String(n++).padStart(4, '0')}`, party: lead.name, channel: lead.source, interest: lead.interest, stage, amount: Math.round(value / count / 100) * 100, closing: addDays(TODAY, 7 + Math.floor(rand() * 80)) })
    }
  }
  return rows
})()
export const CRM_CUSTOMERS = { total: 412, kyc_verified: 356, kyc_draft: 31 }

/** Diaspora buyer support: where overseas buyers live, and remote steps completed (90 days). */
export const DIASPORA_COUNTRIES = { 'United Kingdom': 54, 'United States': 38, Canada: 21, 'Nordic countries': 29, 'Gulf states': 17, Other: 6 }
export const DIASPORA_STEPS = [
  ['Enquiries from abroad', 165],
  ['Video viewings', 74],
  ['Plots or homes chosen remotely', 39],
  ['Contracts signed remotely', 23],
  ['Title deeds handed over', 9],
]

export const AGENTS = [
  ['Sales agent 1', 118, 14, 1420000],
  ['Sales agent 2', 104, 11, 1180000],
  ['Sales agent 3', 97, 7, 690000],
  ['Sales agent 4', 89, 5, 520000],
  ['Sales agent 5', 78, 4, 410000],
].map(([agent, leads, contracts, value]) => ({ agent, leads, contracts, value, conversion: Math.round((contracts / leads) * 1000) / 10 }))

export const COLLECTIONS = {
  scheduled: [420, 430, 440, 455, 470, 480, 490, 505, 515, 520, 535, 550],
  collected: [395, 402, 401, 428, 436, 447, 463, 470, 462, 488, 497, 501],
}

export const AGEING = [
  { bucket: '1-30 days', amount: 128000, contracts: 31 },
  { bucket: '31-60 days', amount: 76000, contracts: 14 },
  { bucket: '61-90 days', amount: 44000, contracts: 7 },
  { bucket: '90+ days', amount: 36000, contracts: 5 },
]

export const PLAN_MIX = { Cash: 47, '12 months': 38, '22 months, interest-free': 58, '24 months': 49, '36 months': 22 }

export const CONTRACT_TOTALS = { active: 214, value: 9420000, collected: 6310000 }

export const OVERDUE = AGEING.flatMap((b, bi) => {
  const rand = seeded(101 + bi)
  const weights = Array.from({ length: b.contracts }, () => 0.5 + rand())
  const sum = weights.reduce((a, w) => a + w, 0)
  return weights.map((w, i) => ({
    contract: `SC-2026-${String(400 + bi * 40 + i).padStart(5, '0')}`,
    customer: person(rand),
    community: pick(rand, COMMUNITIES).name,
    bucket: b.bucket,
    overdue: Math.round((b.amount * w) / sum),
    installments_late: bi + 1,
    officer: `Collections officer ${1 + Math.floor(rand() * 3)}`,
  }))
})

export const SALE_CONTRACTS = (() => {
  const rand = seeded(55)
  const plans = Object.keys(PLAN_MIX)
  return Array.from({ length: 40 }, (_, i) => {
    const c = pick(rand, COMMUNITIES)
    const land = Boolean(c.fixed)
    const value = land ? c.fixed[rand() < 0.35 ? 1 : 0][1] : Math.round((c.price * (0.85 + rand() * 0.3)) / 100) * 100
    const plan = land ? '22 months, interest-free' : pick(rand, plans.filter((p) => p !== '22 months, interest-free'))
    const paidShare = plan === 'Cash' ? 1 : 0.2 + rand() * 0.6
    return {
      contract: `SC-2026-${String(380 - i).padStart(5, '0')}`,
      customer: person(rand),
      community: c.name,
      plan,
      value,
      collected: Math.round(value * paidShare),
      signed: addDays('2026-11-12', -Math.floor(i * 4.5)),
      status: plan === 'Cash' ? 'Paid in full' : rand() < 0.12 ? 'Overdue' : 'Current',
    }
  })
})()

// ---------------------------------------------------------------- brokerage

const LISTING_AREAS = ['Jigjiga Yar', 'Masalaha', 'Ga’an Libah', 'New Hargeisa', 'Berbera old town', 'Burao centre', 'Gabiley road']
export const LISTINGS = (() => {
  const rand = seeded(77)
  const types = [['Land', 18000], ['Villa', 145000], ['Apartment', 72000], ['Commercial', 210000]]
  return Array.from({ length: 28 }, (_, i) => {
    const [type, base] = types[i % 7 === 0 ? 3 : i % 3 === 0 ? 1 : i % 4 === 0 ? 2 : 0]
    const r = rand()
    return {
      id: `BL-${String(510 + i)}`,
      type,
      area: pick(rand, LISTING_AREAS),
      owner: person(rand),
      asking: Math.round((base * (0.7 + rand() * 0.7)) / 500) * 500,
      status: r < 0.6 ? 'Active' : r < 0.8 ? 'Under offer' : 'Sold',
      days_listed: 5 + Math.floor(rand() * 120),
    }
  })
})()

export const DEALS = LISTINGS.filter((l) => l.status !== 'Active').map((l, i) => {
  const price = Math.round(l.asking * 0.96)
  return {
    deal: `BD-${String(220 + i)}`,
    listing: l.id,
    type: l.type,
    area: l.area,
    price,
    commission: Math.round(price * 0.025), // 2.5 %, as in docs/BROKERAGE_v0.1.md
    status: l.status === 'Sold' ? (i % 3 === 0 ? 'Commission due' : 'Commission collected') : 'Offer accepted',
  }
})

export const COMMISSIONS = [8, 10, 9, 12, 11, 14, 13, 15, 12, 16, 14, 18]

// ---------------------------------------------------------------- group (executive)

/** Group income by business line per month, thousands of dollars. */
export const INCOME = {
  'Real estate sales': [310, 280, 350, 390, 420, 380, 450, 470, 430, 510, 490, 540],
  Construction: [180, 200, 190, 230, 250, 240, 260, 280, 270, 300, 290, 310],
  'Design & engineering': [35, 40, 38, 45, 42, 50, 55, 48, 52, 60, 58, 62],
  Brokerage: COMMISSIONS,
}

export const ATTENTION = [
  { tone: 'red', text: 'Sheikh Road Culverts is three weeks behind on culvert C4', to: { set: 'milestones', filter: { project: 'Sheikh Road Culverts' } } },
  { tone: 'red', text: 'Berbera Townhouses forecast is 5% over budget', to: { set: 'projects', filter: { name: 'Berbera Townhouses' } } },
  { tone: 'amber', text: '4 materials are below their reorder level', to: { set: 'stock', filter: { below_reorder: 'Yes' } } },
  { tone: 'amber', text: '3 variation orders await General Manager approval', to: { set: 'variations', filter: { status: 'Awaiting approval' } } },
  { tone: 'amber', text: '5 contracts are more than 90 days overdue', to: { set: 'overdue', filter: { bucket: '90+ days' } } },
  { tone: 'blue', text: '3 failed inspections need a re-inspection', to: { set: 'inspections', filter: { result: 'Fail' } } },
]

export function sum(rows, key) {
  return rows.reduce((total, row) => total + (Number(key ? row[key] : row) || 0), 0)
}

export function countBy(rows, key, order) {
  const out = {}
  for (const label of order ?? []) out[label] = 0
  for (const row of rows) out[row[key]] = (out[row[key]] ?? 0) + 1
  return out
}

// ---------------------------------------------------------------- finance (sample overview)

/** Group operating expenses per month, thousands of dollars (construction spend plus overheads). */
export const EXPENSES = {
  'Construction costs': MONTHS.map((_, i) => Object.values(SPEND).reduce((a, s) => a + s[i], 0)),
  'Salaries & admin': [52, 52, 53, 53, 54, 55, 55, 56, 56, 57, 58, 58],
  'Sales & marketing': [14, 12, 16, 18, 19, 17, 21, 22, 20, 24, 23, 26],
}

/** Bank and cash balances at the end of each month, thousands of dollars. */
export const CASH_BALANCE = [1180, 1210, 1260, 1240, 1310, 1290, 1350, 1380, 1340, 1420, 1460, 1515]

export const BANK_ACCOUNTS = [
  ['Operating account', 'USD', 742000, 'Bank'],
  ['Installment collections account', 'USD', 516000, 'Bank'],
  ['Construction payments account', 'USD', 198000, 'Bank'],
  ['Mobile money (merchant)', 'USD', 41000, 'Mobile money'],
  ['Petty cash, Hargeisa office', 'USD', 9000, 'Cash'],
  ['Petty cash, Berbera site', 'USD', 9000, 'Cash'],
].map(([account, currency, balance, kind]) => ({ account, currency, balance, kind }))

/** Money owed to Sidra by age: installments and client billings, dollars. */
export const RECEIVABLES = [
  { age: 'Not yet due', amount: 2826000 },
  { age: '1-30 days', amount: 151000 },
  { age: '31-60 days', amount: 88000 },
  { age: '61-90 days', amount: 47000 },
  { age: '90+ days', amount: 41000 },
]

/** Money Sidra owes suppliers and subcontractors by age, dollars. */
export const PAYABLES = [
  { age: 'Not yet due', amount: 312000 },
  { age: '1-30 days', amount: 96000 },
  { age: '31-60 days', amount: 21000 },
  { age: '60+ days', amount: 6000 },
]
