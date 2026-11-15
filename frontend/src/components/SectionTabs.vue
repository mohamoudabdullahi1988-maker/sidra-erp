<script setup>
import { computed } from 'vue'

import { canRead } from '../boot'
import { RECORDS, SECTIONS, listRoute } from '../records'

// The lists of one section the server lets this user read, as links. Hidden when there is one.
const props = defineProps({ section: { type: String, required: true }, current: { type: String, required: true } })
const tabs = computed(() =>
  (SECTIONS[props.section] ?? []).filter((key) => canRead(key)).map((key) => ({ key, title: RECORDS[key].title, to: { name: listRoute(key) } })),
)
</script>

<template>
  <nav v-if="tabs.length > 1" class="tabs" aria-label="Lists in this section">
    <RouterLink v-if="section === 'customers'" class="tabs__item" :to="{ name: 'customers' }">Dashboard</RouterLink>
    <RouterLink
      v-for="tab in tabs"
      :key="tab.key"
      :to="tab.to"
      class="tabs__item"
      :class="{ 'tabs__item--on': tab.key === current }"
      :aria-current="tab.key === current ? 'page' : undefined"
    >
      {{ tab.title }}
    </RouterLink>
  </nav>
</template>

<style scoped>
.tabs {
  display: flex;
  gap: 4px;
  margin: -8px 0 16px;
  overflow-x: auto;
  border-bottom: 1px solid var(--bj-line);
}
.tabs__item {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 8px 14px;
  font-size: 14px;
  font-weight: 500;
  color: var(--bj-muted);
  white-space: nowrap;
  text-decoration: none;
  border-bottom: 2px solid transparent;
}
.tabs__item:hover {
  color: var(--bj-ink);
}
.tabs__item--on {
  color: var(--bj-terracotta);
  border-bottom-color: var(--bj-terracotta);
}
</style>
