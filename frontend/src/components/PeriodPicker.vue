<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { PRESETS, periodFrom } from '../showcase/period'

// Dashboard date selection: presets or a custom range, kept in the address.
const props = defineProps({ note: { type: String, default: '' } })
const route = useRoute()
const router = useRouter()
const period = computed(() => periodFrom(route.query))
const from = ref(period.value.from)
const to = ref(period.value.to)
watch(period, (p) => {
  from.value = p.from
  to.value = p.to
})

function choose(key) {
  const { period: _p, from: _f, to: _t, ...rest } = route.query
  if (key === 'custom') router.replace({ query: { ...rest, period: 'custom', from: period.value.from, to: period.value.to } })
  else router.replace({ query: { ...rest, period: key === '12m' ? undefined : key } })
}
function apply() {
  if (!from.value || !to.value || from.value > to.value) return
  router.replace({ query: { ...route.query, period: 'custom', from: from.value, to: to.value } })
}
</script>

<template>
  <div class="pp" role="group" aria-label="Period">
    <span class="pp__icon lucide-calendar-range" aria-hidden="true" />
    <div class="pp__presets">
      <button
        v-for="p in PRESETS"
        :key="p.key"
        type="button"
        :class="{ on: period.key === p.key }"
        :aria-pressed="period.key === p.key"
        @click="choose(p.key)"
      >{{ p.label }}</button>
    </div>
    <form v-if="period.key === 'custom'" class="pp__custom" @submit.prevent="apply">
      <label>From <input v-model="from" type="date" :max="to" required /></label>
      <label>To <input v-model="to" type="date" :min="from" required /></label>
      <button type="submit" class="pp__apply">Apply</button>
    </form>
    <p v-if="props.note" class="pp__note">{{ props.note }}</p>
  </div>
</template>

<style scoped>
.pp { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 12px; margin: 0 0 14px; }
.pp__icon { width: 16px; height: 16px; color: var(--bj-muted); }
.pp__presets { display: inline-flex; flex-wrap: wrap; gap: 2px; padding: 3px; border: 1px solid var(--bj-line); border-radius: 999px; background: var(--bj-card); }
.pp__presets button { min-height: 32px; padding: 4px 12px; border: 0; border-radius: 999px; background: none; font-size: 13px; font-weight: 500; color: var(--bj-muted); cursor: pointer; }
.pp__presets button.on { background: var(--bj-terracotta); color: #fff; }
.pp__custom { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; font-size: 13px; color: var(--bj-muted); }
.pp__custom input { min-height: 34px; margin-left: 4px; padding: 4px 8px; border: 1px solid var(--bj-line); border-radius: 8px; background: var(--bj-card); color: var(--bj-ink); font: inherit; }
.pp__apply { min-height: 34px; padding: 4px 14px; border: 0; border-radius: 8px; background: var(--bj-charcoal); color: #fff; font-size: 13px; font-weight: 500; cursor: pointer; }
.pp__note { flex-basis: 100%; margin: 0; font-size: 12px; color: var(--bj-muted); }
</style>
