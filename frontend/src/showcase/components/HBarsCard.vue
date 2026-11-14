<script setup>
import { computed } from 'vue'
import Card from './Card.vue'
import { tone } from '../charts'
import { formatValue } from '../format'
import { linkTo } from '../link'

const props = defineProps({ widget: { type: Object, required: true } })
const w = computed(() => props.widget)
const max = computed(() => {
  if (w.value.max) return w.value.max
  const totals = w.value.rows.map((r) => (w.value.stacked ? r.values.reduce((a, v) => a + v, 0) : Math.max(...r.values)))
  return Math.max(1, ...totals)
})
const share = (v) => `${Math.max(0, (v / max.value) * 100)}%`
const shown = (row) => (w.value.stacked ? row.values.reduce((a, v) => a + v, 0) : row.values[w.value.series.length > 1 ? row.values.length - 1 : 0])
const funnelShare = (row) => (w.value.funnel && w.value.rows[0].values[0] ? Math.round((row.values[0] / w.value.rows[0].values[0]) * 100) : null)
</script>

<template>
  <Card :title="w.title" :note="w.note" :to="w.to">
    <ul v-if="w.series.length > 1" class="keys">
      <li v-for="s in w.series" :key="s.name"><i :style="{ background: tone(s.tone) }" />{{ s.name }}</li>
    </ul>
    <ol class="rows">
      <li v-for="row in w.rows" :key="row.label">
        <RouterLink :to="linkTo(row.to) ?? ''" class="row">
          <span class="row__label" :title="row.label">{{ row.label }}</span>
          <span class="row__track" :class="{ 'row__track--grouped': !w.stacked && w.series.length > 1 }">
            <template v-if="w.stacked">
              <span class="stack">
                <span v-for="(v, i) in row.values" :key="i" class="seg" :style="{ width: share(v), background: tone(w.series[i].tone) }" :title="`${w.series[i].name}: ${formatValue(v, w.kind)}`" />
              </span>
            </template>
            <template v-else>
              <span v-for="(v, i) in row.values" :key="i" class="bar" :style="{ width: share(v), background: tone(row.tone ?? w.series[i]?.tone) }" :title="`${w.series[i]?.name}: ${formatValue(v, w.kind)}`" />
            </template>
            <span v-if="w.marker" class="marker" :style="{ left: share(w.marker) }" />
          </span>
          <strong class="row__value">
            {{ formatValue(shown(row), w.kind) }}<small v-if="funnelShare(row) !== null && funnelShare(row) < 100"> · {{ funnelShare(row) }}%</small>
          </strong>
        </RouterLink>
      </li>
    </ol>
  </Card>
</template>

<style scoped>
.keys { display: flex; flex-wrap: wrap; gap: 4px 14px; margin: 0 0 8px; padding: 0; list-style: none; font-size: 12px; color: var(--bj-muted); }
.keys li { display: inline-flex; align-items: center; gap: 6px; }
.keys i { width: 10px; height: 10px; border-radius: 3px; }
.rows { margin: 0; padding: 0; list-style: none; display: grid; gap: 4px; }
.row { display: grid; grid-template-columns: minmax(90px, 38%) 1fr auto; align-items: center; gap: 10px; padding: 5px 6px; border-radius: 6px; color: var(--bj-ink); text-decoration: none; font-size: 13px; }
.row:hover { background: var(--bj-ground); }
.row__label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.row__track { position: relative; display: flex; flex-direction: column; justify-content: center; gap: 2px; height: 16px; background: var(--bj-ground); border-radius: 4px; }
.row__track--grouped { height: 20px; background: none; }
.bar { display: block; height: 100%; min-width: 2px; border-radius: 4px; }
.row__track--grouped .bar { height: 8px; }
.stack { display: flex; height: 100%; border-radius: 4px; overflow: hidden; }
.seg { display: block; height: 100%; }
.marker { position: absolute; top: -3px; bottom: -3px; width: 2px; background: var(--bj-ink); opacity: 0.55; }
.row__value { min-width: 56px; text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; white-space: nowrap; }
.row__value small { font-weight: 400; color: var(--bj-muted); }
@media (max-width: 640px) { .row { grid-template-columns: minmax(80px, 34%) 1fr auto; } }
</style>
