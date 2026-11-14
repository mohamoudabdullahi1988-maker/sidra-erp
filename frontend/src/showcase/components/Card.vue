<script setup>
import { linkTo } from '../link'

defineProps({ title: String, note: String, to: Object })
</script>

<template>
  <article class="sc-card">
    <header class="sc-card__head">
      <div>
        <h2 class="sc-card__title">{{ title }}</h2>
        <p v-if="note" class="sc-card__note">{{ note }}</p>
      </div>
      <RouterLink v-if="to" :to="linkTo(to)" class="sc-card__more">View list<span class="lucide-chevron-right" aria-hidden="true" /></RouterLink>
    </header>
    <div class="sc-card__body"><slot /></div>
  </article>
</template>

<style scoped>
.sc-card { display: flex; flex-direction: column; min-width: 0; height: 100%; background: var(--bj-card); border: 1px solid var(--bj-line); border-radius: 12px; box-shadow: 0 1px 2px rgb(31 35 38 / 0.04); }
.sc-card__head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; padding: 14px 16px 6px; }
.sc-card__title { margin: 0; font-size: 15px; font-weight: 600; color: var(--bj-ink); }
.sc-card__note { margin: 2px 0 0; font-size: 12px; color: var(--bj-muted); }
.sc-card__more { display: inline-flex; align-items: center; gap: 2px; flex: none; font-size: 12px; font-weight: 500; color: var(--bj-terracotta); text-decoration: none; white-space: nowrap; }
.sc-card__more span { width: 14px; height: 14px; }
.sc-card__body { flex: 1; min-height: 0; padding: 6px 16px 16px; }
</style>
