<script setup>
import { computed } from 'vue'
import { formatValue } from '../format'
import { linkTo } from '../link'

const props = defineProps({ tile: { type: Object, required: true } })
const text = computed(() => formatValue(props.tile.value, props.tile.kind) + (props.tile.suffix ?? ''))
</script>

<template>
  <RouterLink :to="linkTo(tile.to) ?? ''" class="kpi" :class="'kpi--' + (tile.tone || 'blue')">
    <span class="kpi__label">{{ tile.label }}</span>
    <strong class="kpi__value">{{ text }}</strong>
    <span class="kpi__go lucide-arrow-up-right" aria-hidden="true" />
  </RouterLink>
</template>

<style scoped>
.kpi { position: relative; display: flex; flex-direction: column; justify-content: space-between; gap: 10px; min-height: 92px; padding: 12px 14px; border-radius: 10px; color: #fff; text-decoration: none; overflow: hidden; transition: transform 0.12s ease, box-shadow 0.12s ease; }
.kpi:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgb(31 35 38 / 0.16); }
.kpi__label { font-size: 12px; font-weight: 600; letter-spacing: 0.01em; opacity: 0.92; padding-right: 18px; }
.kpi__value { font: 600 28px/1 var(--bj-font-heading); letter-spacing: -0.02em; font-variant-numeric: tabular-nums; }
.kpi__go { position: absolute; top: 12px; right: 12px; width: 14px; height: 14px; opacity: 0.7; }
.kpi--blue { background: var(--bj-c-blue); }
.kpi--sky { background: var(--bj-c-sky); }
.kpi--teal { background: var(--bj-c-teal); }
.kpi--green { background: var(--bj-c-green); }
.kpi--amber { background: var(--bj-c-amber); color: var(--bj-ink); }
.kpi--orange { background: var(--bj-c-orange); }
.kpi--rose { background: var(--bj-c-rose); }
.kpi--purple { background: var(--bj-c-purple); }
.kpi--slate { background: var(--bj-c-slate); }
.kpi--terracotta { background: var(--bj-c-terracotta); }
</style>
