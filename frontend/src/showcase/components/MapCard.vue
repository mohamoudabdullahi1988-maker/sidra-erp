<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import Card from './Card.vue'
import { useWidth } from './useWidth'
import { CITIES } from '../data'
import { OUTLINE, project, tone } from '../charts'
import { linkTo } from '../link'

const props = defineProps({ widget: { type: Object, required: true } })
const router = useRouter()
const { el, width } = useWidth(360)
const height = computed(() => Math.round(width.value * 0.6))
const outline = computed(() => OUTLINE.map((p) => project(p, width.value, height.value).map((v) => v.toFixed(1)).join(',')).join(' '))
const cities = computed(() => Object.entries(CITIES).map(([name, ll]) => ({ name, xy: project(ll, width.value, height.value) })))
// Pins in the same city fan out so each stays clickable.
const pins = computed(() => {
  const seen = {}
  return props.widget.pins.map((pin) => {
    const i = (seen[pin.city] = (seen[pin.city] ?? -1) + 1)
    const [x, y] = project(CITIES[pin.city], width.value, height.value)
    const angle = i * 2.1
    const r = i ? 9 + i * 3 : 0
    return { ...pin, x: x + Math.cos(angle) * r, y: y + Math.sin(angle) * r }
  })
})
const open = (pin) => pin.to && router.push(linkTo(pin.to))
</script>

<template>
  <Card :title="widget.title" note="Schematic map of Somaliland">
    <div ref="el" class="map">
      <svg :width="width" :height="height" :viewBox="`0 0 ${width} ${height}`" role="img" :aria-label="widget.title">
        <rect :width="width" :height="height" class="sea" rx="8" />
        <polygon :points="outline" class="land" />
        <g v-for="c in cities" :key="c.name" class="city">
          <circle :cx="c.xy[0]" :cy="c.xy[1]" r="1.8" />
          <text :x="c.xy[0] + 5" :y="c.xy[1] - 5">{{ c.name }}</text>
        </g>
        <g v-for="pin in pins" :key="pin.label" class="pin" @click="open(pin)">
          <circle :cx="pin.x" :cy="pin.y" r="11" :fill="tone(pin.tone)" opacity="0.22" />
          <circle :cx="pin.x" :cy="pin.y" r="6" :fill="tone(pin.tone)" stroke="#fff" stroke-width="2" />
          <title>{{ pin.label }} · {{ pin.sub }}</title>
        </g>
      </svg>
    </div>
    <ul class="pins">
      <li v-for="pin in widget.pins" :key="pin.label">
        <RouterLink :to="linkTo(pin.to) ?? ''"><i :style="{ background: tone(pin.tone) }" /><span>{{ pin.label }}</span><small>{{ pin.sub }}</small></RouterLink>
      </li>
    </ul>
  </Card>
</template>

<style scoped>
.map { width: 100%; }
svg { display: block; }
.sea { fill: var(--bj-map-sea); }
.land { fill: var(--bj-map-land); stroke: var(--bj-map-border); stroke-width: 1.2; stroke-linejoin: round; }
.city circle { fill: var(--bj-muted); }
.city text { font-size: 10px; fill: var(--bj-muted); }
.pin { cursor: pointer; }
.pins { margin: 8px 0 0; padding: 0; list-style: none; display: grid; gap: 1px; }
.pins a { display: grid; grid-template-columns: 10px 1fr auto; gap: 8px; align-items: center; padding: 3px 6px; border-radius: 6px; font-size: 12.5px; color: var(--bj-ink); text-decoration: none; }
.pins a:hover { background: var(--bj-ground); }
.pins i { width: 10px; height: 10px; border-radius: 50%; }
.pins span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pins small { color: var(--bj-muted); white-space: nowrap; }
</style>
