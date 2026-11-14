<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import Card from './Card.vue'
import { donutArcs, tone } from '../charts'
import { formatValue } from '../format'
import { linkTo } from '../link'

const props = defineProps({ widget: { type: Object, required: true } })
const router = useRouter()
const total = computed(() => props.widget.segments.reduce((a, s) => a + s.value, 0))
const arcs = computed(() => donutArcs(props.widget.segments.map((s) => s.value)))
const open = (segment) => segment.to && router.push(linkTo(segment.to))
</script>

<template>
  <Card :title="widget.title" :note="widget.note" :to="widget.to">
    <div class="donut">
      <svg viewBox="0 0 42 42" class="donut__svg" role="img" :aria-label="widget.title">
        <circle cx="21" cy="21" r="15.915" fill="none" stroke="var(--bj-ground)" stroke-width="6" />
        <circle
          v-for="(segment, i) in widget.segments"
          :key="segment.label"
          class="donut__arc"
          cx="21" cy="21" r="15.915" fill="none" stroke-width="6"
          :stroke="tone(segment.tone)"
          :stroke-dasharray="arcs[i].dash"
          :stroke-dashoffset="arcs[i].offset"
          @click="open(segment)"
        ><title>{{ segment.label }}: {{ formatValue(segment.value, widget.kind) }}</title></circle>
        <text x="21" y="21.5" text-anchor="middle" class="donut__total">{{ formatValue(total, widget.kind) }}</text>
        <text x="21" y="26" text-anchor="middle" class="donut__caption">{{ widget.centre }}</text>
      </svg>
      <ul class="legend">
        <li v-for="(segment, i) in widget.segments" :key="segment.label">
          <RouterLink :to="linkTo(segment.to) ?? ''" class="legend__row">
            <i :style="{ background: tone(segment.tone) }" />
            <span class="legend__label">{{ segment.label }}</span>
            <strong>{{ formatValue(segment.value, widget.kind) }}</strong>
            <small>{{ Math.round(arcs[i].share) }}%</small>
          </RouterLink>
        </li>
      </ul>
    </div>
  </Card>
</template>

<style scoped>
.donut { display: flex; flex-direction: column; align-items: center; gap: 12px; }
.donut__svg { width: min(190px, 70%); transform: rotate(0deg); }
.donut__arc { cursor: pointer; transition: stroke-width 0.12s; }
.donut__arc:hover { stroke-width: 7.4; }
.donut__total { font: 600 6px var(--bj-font-heading); fill: var(--bj-ink); }
.donut__caption { font-size: 2.6px; fill: var(--bj-muted); }
.legend { width: 100%; margin: 0; padding: 0; list-style: none; display: grid; gap: 2px; }
.legend__row { display: grid; grid-template-columns: 10px 1fr auto 38px; align-items: center; gap: 8px; padding: 4px 6px; border-radius: 6px; font-size: 13px; color: var(--bj-ink); text-decoration: none; }
.legend__row:hover { background: var(--bj-ground); }
.legend__row i { width: 10px; height: 10px; border-radius: 3px; }
.legend__label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.legend__row strong { font-weight: 600; font-variant-numeric: tabular-nums; }
.legend__row small { color: var(--bj-muted); text-align: right; font-variant-numeric: tabular-nums; }
</style>
