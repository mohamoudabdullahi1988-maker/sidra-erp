import { createRouter, createWebHistory } from 'vue-router'

import { canCreate, canOpen, canRead } from './boot'
import { GENERIC, RECORDS, SECTIONS, detailRoute, listRoute } from './records'

const RecordList = () => import('./pages/RecordList.vue')
const RecordDetail = () => import('./pages/RecordDetail.vue')
const RecordEdit = () => import('./pages/RecordEdit.vue')
const Showcase = () => import('./pages/Showcase.vue')

// Every generic list and its record page, from records.js. Static paths such as
// /construction/quotations rank above /construction/:name, so they never collide.
// A list whose records open another page (design jobs open the job page) gets no record page of
// its own: a second route with the same name would replace that page's route.
const generic = GENERIC.flatMap((key) => [
  { path: RECORDS[key].path, name: listRoute(key), component: RecordList, meta: { list: key, section: RECORDS[key].section } },
  ...(RECORDS[key].detailRoute ? [] : [{ path: `${RECORDS[key].path}/:name`, name: detailRoute(key), component: RecordDetail, meta: { list: key, section: RECORDS[key].section } }]),
])

// Create and edit pages for every list the server's form engine serves (G23), and the generic
// record page for a list whose list is a page of its own (units).
const forms = Object.keys(RECORDS)
  .filter((key) => RECORDS[key].form && !RECORDS[key].single)
  .flatMap((key) => [
    { path: RECORDS[key].formPaths?.new ?? `${RECORDS[key].path}/new`, name: `${key}-new`, component: RecordEdit, meta: { list: key, section: RECORDS[key].section, create: true } },
    { path: RECORDS[key].formPaths?.edit ?? `${RECORDS[key].path}/:name/edit`, name: `${key}-edit`, component: RecordEdit, meta: { list: key, section: RECORDS[key].section } },
  ])
// A single record (Contract settings) is its own page: its form.
const singles = Object.keys(RECORDS)
  .filter((key) => RECORDS[key].single)
  .map((key) => ({ path: RECORDS[key].path, name: listRoute(key), component: RecordEdit, meta: { list: key, section: RECORDS[key].section } }))
const pageDetails = Object.keys(RECORDS)
  .filter((key) => RECORDS[key].page && RECORDS[key].detail && !RECORDS[key].detailRoute)
  .map((key) => ({ path: `${RECORDS[key].path}/:name`, name: detailRoute(key), component: RecordDetail, meta: { list: key, section: RECORDS[key].section } }))

/** A section without a page of its own opens its first list this user may read. */
function firstList(section) {
  const key = SECTIONS[section].find((name) => canRead(name))
  return key ? { name: listRoute(key) } : { name: 'no-access' }
}

const routes = [
  { path: '/my-work', name: 'my-work', component: () => import('./pages/WorkQueue.vue') },
  {
    path: '/',
    name: 'home',
    redirect: () => {
      // The sample Executive overview is the landing screen for the client demonstration.
      return { name: 'executive' }
    },
  },
  // Sample screens for the client demonstration (14 Nov 2026): fictional, labelled data only.
  { path: '/executive', name: 'executive', component: Showcase, meta: { showcase: 'executive' } },
  { path: '/build/:tab?', name: 'construction-hub', component: Showcase, meta: { showcase: 'build' } },
  { path: '/design/:tab?', name: 'design', component: Showcase, meta: { showcase: 'design' } },
  { path: '/real-estate/:tab?', name: 'realestate', component: Showcase, meta: { showcase: 'realestate' } },
  { path: '/crm', name: 'crm-hub', component: Showcase, meta: { showcase: 'crm' } },
  { path: '/brokerage', name: 'brokerage', component: Showcase, meta: { showcase: 'brokerage' } },
  { path: '/finance-overview', name: 'finance-hub', component: Showcase, meta: { showcase: 'finance' } },
  { path: '/sample/:set', name: 'sample', component: () => import('./pages/SampleList.vue'), meta: { showcase: 'sample' } },
  { path: '/dashboard', name: 'dashboard', component: () => import('./pages/Dashboard.vue') },
  { path: '/properties', name: 'properties', component: () => import('./pages/Properties.vue'), meta: { list: 'units', section: 'properties' } },
  { path: '/customers-section', name: 'customers', redirect: () => firstList('customers') },
  { path: '/sales', name: 'sales', redirect: () => firstList('sales') },
  { path: '/setup', name: 'setup', redirect: () => firstList('setup') },
  { path: '/contracts', name: 'contracts', component: () => import('./pages/Contracts.vue'), meta: { list: 'contracts', section: 'contracts' } },
  { path: '/contracts/new', name: 'contract-new', component: () => import('./pages/ContractEdit.vue'), meta: { list: 'contracts', section: 'contracts', create: true } },
  { path: '/contracts/:name/edit', name: 'contract-edit', component: () => import('./pages/ContractEdit.vue'), meta: { list: 'contracts', section: 'contracts' } },
  { path: '/contracts/:name', name: 'contract-detail', component: () => import('./pages/ContractDetail.vue'), meta: { section: 'contracts' } },
  { path: '/collections', name: 'collections', component: () => import('./pages/Collections.vue'), meta: { section: 'collections' } },
  { path: '/construction', name: 'construction', component: () => import('./pages/Construction.vue'), meta: { list: 'jobs', section: 'construction' } },
  { path: '/construction/:name', name: 'construction-detail', component: () => import('./pages/ConstructionDetail.vue'), meta: { section: 'construction' } },
  { path: '/finance', name: 'finance', component: () => import('./pages/Finance.vue'), meta: { section: 'finance' } },
  ...forms,
  ...singles,
  ...generic,
  ...pageDetails,
  { path: '/no-access', name: 'no-access', component: () => import('./pages/NoAccess.vue') },
  { path: '/:rest(.*)*', name: 'not-found', component: () => import('./pages/NotFound.vue') },
]

const router = createRouter({
  history: createWebHistory('/berjaya'),
  routes,
})

const OPEN_TO_ALL = new Set(['home', 'no-access', 'not-found', 'my-work'])

// Convenience only: the server refuses the data whatever this guard does. A list page needs the
// server's read permission for that list; any other page needs its section in the navigation.
router.beforeEach((to) => {
  if (OPEN_TO_ALL.has(to.name)) return true
  // Sample screens hold no Sidra record, so every staff member who reached /berjaya may see them.
  if (to.meta.showcase) return true
  if (to.meta.list && !canRead(to.meta.list)) return { name: 'no-access' }
  if (to.meta.create && !canCreate(to.meta.list)) return { name: 'no-access' }
  if (canOpen(to.meta.section ?? to.name)) return true
  return { name: 'no-access' }
})

export default router
