<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import SampleTable from '../showcase/components/SampleTable.vue'
import { DATASETS, filterRows } from '../showcase/datasets'
import { MODULES } from '../showcase/pages'

// One level down from a sample chart or tile: the fictional rows behind it, read-only.
const route = useRoute()
const router = useRouter()
const set = computed(() => DATASETS[route.params.set])
const filter = computed(() => Object.fromEntries(Object.entries(route.query).filter(([, v]) => typeof v === 'string')))
const search = ref('')
const rows = computed(() => {
  if (!set.value) return []
  const term = search.value.trim().toLowerCase()
  const rows = filterRows(set.value, filter.value)
  return term ? rows.filter((row) => Object.values(row).some((v) => String(v).toLowerCase().includes(term))) : rows
})
const module = computed(() => MODULES[set.value?.section])
const label = (key) => set.value.columns.find((c) => c.key === key)?.label ?? key
function clear(key) {
  const query = { ...route.query }
  delete query[key]
  router.replace({ query })
}
</script>

<template>
  <div class="page">
    <template v-if="set">
      <p class="crumbs">
        <a href="#" @click.prevent="router.back()"><span class="lucide-arrow-left" aria-hidden="true" />Back</a>
        <span v-if="module">· {{ module.label }}</span>
      </p>
      <h1 class="page__title">{{ set.title }} <span class="sample-badge"><span class="lucide-flask-conical" aria-hidden="true" />Sample data</span></h1>
      <div class="bar">
        <div class="filters">
          <button v-for="(value, key) in filter" :key="key" type="button" class="filter" @click="clear(key)">
            {{ label(key) }}: <strong>{{ value }}</strong><span class="lucide-x" aria-hidden="true" />
          </button>
          <span class="count">{{ rows.length }} {{ rows.length === 1 ? 'row' : 'rows' }}</span>
        </div>
        <input v-model="search" type="search" class="search" placeholder="Search these rows" aria-label="Search these rows" />
      </div>
      <div class="page__card">
        <SampleTable :columns="set.columns" :rows="rows" />
        <p v-if="!rows.length" class="empty">No sample rows match.</p>
      </div>
      <p class="foot">Read-only fictional rows for the demonstration. Real records are created and kept in their own screens.</p>
    </template>
    <p v-else>This sample list does not exist.</p>
  </div>
</template>

<style scoped>
.crumbs { display: flex; gap: 8px; margin: 0 0 6px; font-size: 13px; color: var(--bj-muted); }
.crumbs a { display: inline-flex; align-items: center; gap: 4px; color: var(--bj-terracotta); text-decoration: none; }
.crumbs a span { width: 14px; height: 14px; }
.page__title { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.sample-badge { display: inline-flex; align-items: center; gap: 5px; padding: 3px 9px; border-radius: 999px; background: var(--bj-terracotta-tint); color: var(--bj-terracotta); font: 600 12px var(--bj-font-body); }
.sample-badge span { width: 13px; height: 13px; }
.bar { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; margin-top: 14px; }
.filters { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.filter { display: inline-flex; align-items: center; gap: 6px; padding: 5px 10px; border: 1px solid var(--bj-line); border-radius: 999px; background: var(--bj-card); font-size: 13px; cursor: pointer; }
.filter span { width: 13px; height: 13px; color: var(--bj-muted); }
.count { font-size: 13px; color: var(--bj-muted); }
.search { min-height: 38px; width: min(280px, 100%); padding: 6px 12px; border: 1px solid var(--bj-line); border-radius: 8px; font-size: 14px; background: var(--bj-card); }
.page__card { max-height: calc(100vh - 260px); overflow: auto; }
.empty { padding: 16px; color: var(--bj-muted); }
.foot { margin: 12px 0 0; font-size: 12px; color: var(--bj-muted); }
</style>
