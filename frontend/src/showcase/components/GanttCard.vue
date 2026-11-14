<script setup>
import { computed } from 'vue'
import Card from './Card.vue'
import { useWidth } from './useWidth'
import { datePosition, dateTicks, tone } from '../charts'
import { TODAY } from '../data'
import { date, monthLabel } from '../format'
import { linkTo } from '../link'

const props = defineProps({ widget: { type: Object, required: true } })
const w = computed(() => props.widget)
const { el, width } = useWidth()
// Fewer axis labels on a narrow card, so they never overlap.
const ticks = computed(() =>
  dateTicks(w.value.from, w.value.until)
    .map((d) => ({ d, left: datePosition(d, w.value.from, w.value.until) }))
    .filter((_, i) => width.value >= 560 || i % 2 === 0),
)
const today = computed(() => datePosition(TODAY, w.value.from, w.value.until))
const bar = (row) => {
  const left = datePosition(row.start, w.value.from, w.value.until)
  return { left: `${left}%`, width: `${Math.max(1.2, datePosition(row.end, w.value.from, w.value.until) - left)}%` }
}
</script>

<template>
  <Card :title="w.title" :note="w.note" :to="w.to">
    <div ref="el" class="gantt">
      <div class="gantt__axis">
        <span class="gantt__corner" />
        <span class="gantt__scale">
          <span v-for="t in ticks" :key="t.d" class="tick" :style="{ left: t.left + '%' }">{{ monthLabel(t.d.slice(0, 7)) }}</span>
        </span>
      </div>
      <RouterLink v-for="row in w.rows" :key="row.label" :to="linkTo(row.to) ?? ''" class="gantt__row">
        <span class="gantt__label" :title="row.label"><span class="gantt__name">{{ row.label }}</span><small v-if="row.sub">{{ row.sub }}</small></span>
        <span class="gantt__lane">
          <span v-for="t in ticks" :key="t.d" class="gridline" :style="{ left: t.left + '%' }" />
          <span class="gantt__bar" :class="{ 'gantt__bar--ms': w.milestones }" :style="{ ...bar(row), background: tone(row.tone) }" :title="`${row.label}: ${date(row.start)} to ${date(row.end)}`">
            <span v-if="row.progress !== undefined" class="gantt__rest" :style="{ left: row.progress + '%' }" />
            <span v-if="row.progress !== undefined" class="gantt__pct">{{ row.progress }}%</span>
          </span>
          <span class="today" :style="{ left: today + '%' }" />
        </span>
      </RouterLink>
      <p class="gantt__legend"><i />Today, {{ date(TODAY) }}</p>
    </div>
  </Card>
</template>

<style scoped>
.gantt { display: grid; gap: 2px; font-size: 13px; }
.gantt__axis, .gantt__row { display: grid; grid-template-columns: minmax(110px, 30%) 1fr; gap: 10px; align-items: center; }
.gantt__scale { position: relative; height: 18px; }
.tick { position: absolute; transform: translateX(-50%); font-size: 11px; color: var(--bj-muted); white-space: nowrap; }
.gantt__row { padding: 4px 6px 4px 0; border-radius: 6px; color: var(--bj-ink); text-decoration: none; }
.gantt__row:hover { background: var(--bj-ground); }
.gantt__label { display: flex; flex-direction: column; min-width: 0; padding-left: 6px; }
.gantt__name { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.gantt__label small { font-size: 11px; color: var(--bj-muted); }
.gantt__lane { position: relative; height: 22px; }
.gridline { position: absolute; top: -4px; bottom: -4px; width: 1px; background: var(--bj-line); }
.gantt__bar { position: absolute; top: 3px; height: 16px; border-radius: 5px; overflow: hidden; }
.gantt__rest { position: absolute; top: 0; bottom: 0; right: 0; background: rgb(255 255 255 / 0.55); }
.gantt__pct { position: absolute; left: 6px; top: 0; font-size: 10.5px; line-height: 16px; font-weight: 600; color: #fff; }
.today { position: absolute; top: -6px; bottom: -6px; width: 2px; background: var(--bj-c-rose); }
.gantt__legend { display: flex; align-items: center; gap: 6px; margin: 6px 0 0; font-size: 12px; color: var(--bj-muted); }
.gantt__legend i { width: 2px; height: 12px; background: var(--bj-c-rose); }
</style>
