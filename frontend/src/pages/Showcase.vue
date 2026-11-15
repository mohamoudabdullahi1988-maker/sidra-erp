<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LoadingIndicator } from 'frappe-ui'

import KpiTile from '../showcase/components/KpiTile.vue'
import DonutCard from '../showcase/components/DonutCard.vue'
import BarsCard from '../showcase/components/BarsCard.vue'
import HBarsCard from '../showcase/components/HBarsCard.vue'
import GanttCard from '../showcase/components/GanttCard.vue'
import MapCard from '../showcase/components/MapCard.vue'
import TableCard from '../showcase/components/TableCard.vue'
import ListCard from '../showcase/components/ListCard.vue'
import FlowSteps from '../showcase/components/FlowSteps.vue'
import { MODULES } from '../showcase/pages'
import { recordAction } from '../showcase/link'
import { claimPanel, releasePanel } from '../panel'
import { ApiError, apiGet } from '../api'
import { company } from '../company'
import StatePanel from '../components/StatePanel.vue'
import CompanyPicker from '../components/CompanyPicker.vue'
import { EXECUTIVE_METHOD, executivePage, validExecutive, LIVE_METHOD, LIVE_TABS, livePage } from '../showcase/live'

// A sample screen (client demonstration): drawn from showcase/pages.js. Every figure is fictional
// and labelled as such; real records keep their own screens, linked from here.
const WIDGETS = { donut: DonutCard, bars: BarsCard, hbars: HBarsCard, gantt: GanttCard, map: MapCard, table: TableCard, list: ListCard }

const route = useRoute()
const module = computed(() => MODULES[route.meta.showcase])
const tabKeys = computed(() => Object.keys(module.value.tabs))
const tab = computed(() => (tabKeys.value.includes(route.params.tab) ? route.params.tab : tabKeys.value[0]))
const samplePage = computed(() => module.value.tabs[tab.value])

// Sample data is the default (the client demonstration). Where a tab can show live records the
// header offers a switch; the choice is in the address (?source=live), so it can be shared.
const router = useRouter()
const canGoLive = computed(() => (LIVE_TABS[route.meta.showcase] ?? []).includes(tab.value))
const live = computed(() => canGoLive.value && route.query.source === 'live')
const liveData = ref(null)
const liveError = ref(null)
const loading = ref(false)
let request = 0
async function loadLive() {
  const id = ++request
  liveData.value = null
  liveError.value = null
  loading.value = false
  if (!live.value) return
  if (!company.value) {
    liveError.value = 'No Company is available to your account.'
    return
  }
  loading.value = true
  liveError.value = null
  try {
    const body = await apiGet(route.meta.showcase === 'executive' ? EXECUTIVE_METHOD : LIVE_METHOD, { company: company.value, ...(route.meta.showcase === 'executive' ? { period: 'this_month' } : {}) })
    if (id !== request) return
    if (!body?.message || typeof body.message !== 'object') throw new ApiError('server', 'The server sent an unexpected answer.')
    if (route.meta.showcase === 'executive' && !validExecutive(body.message, company.value)) throw new ApiError('server', 'The server sent an incompatible dashboard response.')
    liveData.value = body.message
  } catch (error) {
    if (id !== request) return
    liveData.value = null
    liveError.value = error instanceof ApiError ? error.message : 'The live records could not be loaded.'
  } finally {
    if (id === request) loading.value = false
  }
}
watch([live, () => company.value, () => route.meta.showcase, tab], loadLive, { immediate: true })
const page = computed(() => (live.value && liveData.value ? (route.meta.showcase === 'executive' ? executivePage(liveData.value, samplePage.value) : livePage(tab.value, liveData.value, samplePage.value)) : samplePage.value))
const showWidgets = computed(() => !live.value || (liveData.value && !loading.value))
function setSource(source) {
  router.replace({ query: { ...route.query, source: source === 'live' ? 'live' : undefined } })
}
const records = computed(() => (module.value.records ?? []).map(recordAction).filter(Boolean))

onMounted(claimPanel)
onBeforeUnmount(releasePanel)
</script>

<template>
  <div class="page sc">
    <header class="sc__head">
      <div class="sc__titles">
        <p class="sc__module">{{ module.label }}</p>
        <h1 class="page__title">
          {{ page.title }}
          <span v-if="live" class="sample-badge sample-badge--live"><span class="lucide-database" aria-hidden="true" />Live records</span>
          <span v-else class="sample-badge"><span class="lucide-flask-conical" aria-hidden="true" />Sample data</span>
        </h1>
        <p class="sc__subtitle">{{ page.subtitle }}</p>
      </div>
      <nav v-if="records.length" class="sc__records" aria-label="Real records">
        <RouterLink v-for="r in records" :key="r.label" :to="r.to" class="sc__record">{{ r.label }}<span class="lucide-arrow-up-right" aria-hidden="true" /></RouterLink>
      </nav>
    </header>

    <nav v-if="tabKeys.length > 1" class="sc__tabs" aria-label="Screens in this module">
      <RouterLink
        v-for="key in tabKeys"
        :key="key"
        :to="{ name: module.route, params: { tab: key }, query: live && (LIVE_TABS[route.meta.showcase] ?? []).includes(key) ? { source: 'live' } : {} }"
        class="sc__tab"
        :class="{ 'sc__tab--on': key === tab }"
        :aria-current="key === tab ? 'page' : undefined"
      >{{ module.tabLabels[key] }}</RouterLink>
    </nav>

    <div v-if="canGoLive" class="sc__source" role="group" aria-label="What the screen shows">
      <CompanyPicker v-if="live" />
      <button v-if="live" type="button" :disabled="loading" @click="loadLive">Refresh</button>
      <button type="button" :class="{ on: !live }" :aria-pressed="!live" @click="setSource('sample')">Sample data</button>
      <button type="button" :class="{ on: live }" :aria-pressed="live" @click="setSource('live')">Live records</button>
    </div>

    <p v-if="live && loading" class="sc__state" role="status"><LoadingIndicator class="h-4 w-4" />Loading live records…</p>
    <StatePanel v-else-if="live && liveError" icon="lucide-triangle-alert" tone="blocked" title="Live records could not be loaded" :message="liveError" />

    <section v-if="showWidgets && page.kpis.length" class="sc__kpis" :style="{ '--n': page.kpis.length }" aria-label="Key figures">
      <KpiTile v-for="tile in page.kpis" :key="tile.label" :tile="tile" />
    </section>

    <section v-if="showWidgets" class="sc__grid">
      <div v-for="(widget, i) in page.widgets" :key="tab + i" class="sc__cell" :style="{ '--span': widget.span ?? 6 }">
        <component :is="WIDGETS[widget.type]" :widget="widget" />
      </div>
    </section>

    <p v-if="live" class="sc__foot"><span class="lucide-database" aria-hidden="true" />Live records for {{ company }}, as your role may read them. Nothing on this screen changes a record.</p>
    <p v-else class="sc__foot"><span class="lucide-flask-conical" aria-hidden="true" />Every figure on this screen is fictional sample data for demonstration. It is not read from Sidra’s records.</p>

    <Teleport defer to="#berjaya-panel">
      <FlowSteps v-if="page.workflow" :flow="page.workflow" :records="module.records" :sample="!live" />
    </Teleport>
  </div>
</template>

<style scoped>
.sc { max-width: 1440px; }
.sc__head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 12px 20px; margin-bottom: 14px; }
.sc__module { margin: 0 0 2px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--bj-terracotta); }
.page__title { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; font-size: 24px; }
.sc__subtitle { margin: 4px 0 0; font-size: 14px; color: var(--bj-muted); }
.sample-badge { display: inline-flex; align-items: center; gap: 5px; padding: 3px 9px; border-radius: 999px; background: var(--bj-terracotta-tint); color: var(--bj-terracotta); font: 600 12px var(--bj-font-body); letter-spacing: 0; }
.sample-badge span { width: 13px; height: 13px; }
.sample-badge--live { background: var(--bj-chip-green-bg); color: var(--bj-chip-green-ink); }
.sc__source { display: inline-flex; gap: 2px; margin: 0 0 14px; padding: 3px; border: 1px solid var(--bj-line); border-radius: 999px; background: var(--bj-card); }
.sc__source button { min-height: 32px; padding: 4px 14px; border: 0; border-radius: 999px; background: none; font-size: 13px; font-weight: 500; color: var(--bj-muted); cursor: pointer; }
.sc__source button.on { background: var(--bj-charcoal); color: #fff; }
.sc__state { display: flex; align-items: center; gap: 8px; color: var(--bj-muted); font-size: 14px; }
.sc__records { display: flex; flex-wrap: wrap; gap: 8px; }
.sc__record { display: inline-flex; align-items: center; gap: 6px; min-height: 36px; padding: 6px 12px; border: 1px solid var(--bj-line); border-radius: 8px; background: var(--bj-card); font-size: 13px; font-weight: 500; color: var(--bj-ink); text-decoration: none; }
.sc__record:hover { border-color: var(--bj-terracotta); color: var(--bj-terracotta); }
.sc__record span { width: 14px; height: 14px; color: var(--bj-muted); }
.sc__tabs { display: flex; gap: 4px; margin: 0 0 16px; overflow-x: auto; border-bottom: 1px solid var(--bj-line); scrollbar-width: thin; }
.sc__tab { display: inline-flex; align-items: center; min-height: 42px; padding: 8px 14px; font-size: 14px; font-weight: 500; color: var(--bj-muted); white-space: nowrap; text-decoration: none; border-bottom: 2px solid transparent; }
.sc__tab:hover { color: var(--bj-ink); }
.sc__tab--on { color: var(--bj-terracotta); border-bottom-color: var(--bj-terracotta); }
.sc__kpis { display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }
.sc__grid { display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 14px; }
.sc__cell { grid-column: span var(--span); min-width: 0; }
.sc__foot { display: flex; align-items: center; gap: 6px; margin: 18px 0 4px; font-size: 12px; color: var(--bj-muted); }
.sc__foot span { width: 14px; height: 14px; flex: none; }
@media (max-width: 1280px) {
  .sc__kpis { grid-template-columns: repeat(min(var(--n), 3), minmax(0, 1fr)); }
  .sc__cell { grid-column: span max(6, var(--span)); }
}
@media (max-width: 900px) {
  .sc__cell { grid-column: span 12; }
}
@media (max-width: 640px) {
  .sc__kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
  .page__title { font-size: 20px; }
}
</style>
