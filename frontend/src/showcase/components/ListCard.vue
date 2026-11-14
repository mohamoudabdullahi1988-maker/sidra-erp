<script setup>
import Card from './Card.vue'
import { linkTo } from '../link'

defineProps({ widget: { type: Object, required: true } })
const ICON = { red: 'lucide-octagon-alert', amber: 'lucide-triangle-alert', blue: 'lucide-info' }
</script>

<template>
  <Card :title="widget.title" :note="widget.note">
    <ul class="items">
      <li v-for="item in widget.items" :key="item.text">
        <RouterLink :to="linkTo(item.to)" class="item" :class="'item--' + item.tone">
          <span class="item__icon" :class="ICON[item.tone]" aria-hidden="true" />
          <span>{{ item.text }}</span>
          <span class="item__go lucide-chevron-right" aria-hidden="true" />
        </RouterLink>
      </li>
    </ul>
  </Card>
</template>

<style scoped>
.items { margin: 0; padding: 0; list-style: none; display: grid; gap: 6px; }
.item { display: grid; grid-template-columns: 18px 1fr 16px; gap: 10px; align-items: center; padding: 9px 10px; border-radius: 8px; border-left: 4px solid; background: var(--bj-ground); font-size: 13px; color: var(--bj-ink); text-decoration: none; }
.item:hover { background: var(--bj-terracotta-tint); }
.item__icon, .item__go { width: 16px; height: 16px; }
.item__go { color: var(--bj-muted); }
.item--red { border-color: var(--bj-c-rose); }
.item--red .item__icon { color: var(--bj-c-rose); }
.item--amber { border-color: var(--bj-c-amber); }
.item--amber .item__icon { color: var(--bj-c-orange); }
.item--blue { border-color: var(--bj-c-blue); }
.item--blue .item__icon { color: var(--bj-c-blue); }
</style>
