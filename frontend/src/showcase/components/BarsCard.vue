<script setup>
import { computed } from 'vue'
import Card from './Card.vue'
import { useWidth } from './useWidth'
import { niceScale, tone } from '../charts'
import { formatValue } from '../format'

const props = defineProps({ widget: { type: Object, required: true } })
const { el, width } = useWidth()
const H = 230
const PAD = { top: 12, bottom: 26, left: 52 }

const bars = computed(() => props.widget.series.filter((s) => s.type !== 'line'))
const lines = computed(() => props.widget.series.filter((s) => s.type === 'line'))
const right = computed(() => lines.value.some((s) => s.axis === 'right'))
const padRight = computed(() => (right.value ? 52 : 12))
const plotW = computed(() => width.value - PAD.left - padRight.value)
const plotH = H - PAD.top - PAD.bottom
const n = computed(() => props.widget.labels.length)
const band = computed(() => plotW.value / n.value)

const leftScale = computed(() => {
  const values = props.widget.stacked
    ? props.widget.labels.map((_, i) => bars.value.reduce((a, s) => a + s.values[i], 0))
    : bars.value.flatMap((s) => s.values)
  const leftLines = lines.value.filter((s) => s.axis !== 'right').flatMap((s) => s.values)
  return niceScale(Math.max(...values, ...leftLines, 0))
})
const rightScale = computed(() => niceScale(Math.max(...lines.value.filter((s) => s.axis === 'right').flatMap((s) => s.values), 0)))

const y = (v, scale) => PAD.top + plotH - (v / scale.max) * plotH
const step = computed(() => Math.max(1, Math.ceil(n.value / Math.max(1, Math.floor(plotW.value / 52)))))

const rects = computed(() => {
  const out = []
  const groupW = band.value * 0.7
  props.widget.labels.forEach((label, i) => {
    const x0 = PAD.left + band.value * i + (band.value - groupW) / 2
    const faded = props.widget.forecastFrom !== undefined && i >= props.widget.forecastFrom
    if (props.widget.stacked) {
      let base = 0
      for (const s of bars.value) {
        const v = s.values[i]
        out.push({ key: `${s.name}-${i}`, x: x0, w: groupW, y: y(base + v, leftScale.value), h: (v / leftScale.value.max) * plotH, fill: tone(s.tone), faded, title: `${label} · ${s.name}: ${formatValue(v, props.widget.kind)}` })
        base += v
      }
    } else {
      const w = groupW / bars.value.length
      bars.value.forEach((s, j) => {
        const v = s.values[i]
        out.push({ key: `${s.name}-${i}`, x: x0 + j * w, w: Math.max(1, w - 1), y: y(v, leftScale.value), h: (v / leftScale.value.max) * plotH, fill: tone(s.colours?.[i] ?? s.tone), faded, title: `${label} · ${s.name}: ${formatValue(v, props.widget.kind)}` })
      })
    }
  })
  return out
})

const paths = computed(() =>
  lines.value.map((s) => {
    const scale = s.axis === 'right' ? rightScale.value : leftScale.value
    const pts = s.values.map((v, i) => [PAD.left + band.value * (i + 0.5), y(v, scale)])
    return { name: s.name, stroke: tone(s.tone), d: pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(''), pts, values: s.values }
  }),
)
</script>

<template>
  <Card :title="widget.title" :note="widget.note" :to="widget.to">
    <ul class="keys">
      <li v-for="s in widget.series" :key="s.name"><i :class="{ line: s.type === 'line' }" :style="{ background: tone(s.tone) }" />{{ s.name }}</li>
      <li v-if="widget.forecastFrom !== undefined"><i class="faded" :style="{ background: tone(bars[0]?.tone) }" />Forecast</li>
    </ul>
    <div ref="el" class="plot">
      <svg :width="width" :height="H" :viewBox="`0 0 ${width} ${H}`" role="img" :aria-label="widget.title">
        <g class="grid">
          <g v-for="t in leftScale.ticks" :key="'l' + t">
            <line :x1="PAD.left" :x2="width - padRight" :y1="y(t, leftScale)" :y2="y(t, leftScale)" />
            <text :x="PAD.left - 6" :y="y(t, leftScale) + 4" text-anchor="end">{{ formatValue(t, widget.kind === 'pct' ? 'count' : widget.kind) }}</text>
          </g>
          <template v-if="right">
            <text v-for="t in rightScale.ticks" :key="'r' + t" :x="width - padRight + 6" :y="y(t, rightScale) + 4">{{ formatValue(t, widget.kind) }}</text>
          </template>
        </g>
        <rect v-for="r in rects" :key="r.key" class="bar" :x="r.x" :y="r.y" :width="r.w" :height="Math.max(0, r.h)" :fill="r.fill" :opacity="r.faded ? 0.42 : 1" rx="2"><title>{{ r.title }}</title></rect>
        <g v-for="p in paths" :key="p.name">
          <path :d="p.d" fill="none" :stroke="p.stroke" stroke-width="2.4" stroke-linejoin="round" />
          <circle v-for="(pt, i) in p.pts" :key="i" :cx="pt[0]" :cy="pt[1]" r="3.2" :fill="p.stroke" stroke="#fff" stroke-width="1.2"><title>{{ widget.labels[i] }} · {{ p.name }}: {{ formatValue(p.values[i], widget.kind) }}</title></circle>
        </g>
        <g class="axis">
          <text v-for="(label, i) in widget.labels" v-show="i % step === 0" :key="label" :x="PAD.left + band * (i + 0.5)" :y="H - 8" text-anchor="middle">{{ label }}</text>
        </g>
      </svg>
    </div>
  </Card>
</template>

<style scoped>
.keys { display: flex; flex-wrap: wrap; gap: 4px 14px; margin: 0 0 6px; padding: 0; list-style: none; font-size: 12px; color: var(--bj-muted); }
.keys li { display: inline-flex; align-items: center; gap: 6px; }
.keys i { width: 10px; height: 10px; border-radius: 3px; }
.keys i.line { height: 3px; width: 14px; border-radius: 2px; }
.keys i.faded { opacity: 0.42; }
.plot { width: 100%; overflow: hidden; }
svg { display: block; }
.grid line { stroke: var(--bj-line); stroke-width: 1; }
.grid text, .axis text { font-size: 11px; fill: var(--bj-muted); font-variant-numeric: tabular-nums; }
.bar { transition: opacity 0.12s; }
.bar:hover { opacity: 0.8; }
</style>
