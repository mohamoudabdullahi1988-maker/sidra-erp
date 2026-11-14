<script setup>
import { computed } from 'vue'
import { recordAction } from '../link'

// The right-hand panel on a sample screen: the business process as steps, and buttons to the
// screens that hold its real records (shown only when the session may open them).
const props = defineProps({ flow: { type: Object, required: true }, records: { type: Array, default: () => [] } })
const actions = computed(() => [...(props.flow.actions ?? []), ...props.records].map(recordAction).filter(Boolean).filter((a, i, all) => all.findIndex((b) => b.label === a.label) === i))
const ICON = { done: 'lucide-circle-check-big', current: 'lucide-circle-dot', next: 'lucide-circle-dashed' }
const WORD = { done: 'Done', current: 'In progress', next: 'Next' }
</script>

<template>
  <section class="flow" aria-label="Workflow">
    <p class="flow__title">{{ flow.title }}</p>
    <p class="flow__sample"><span class="lucide-flask-conical" aria-hidden="true" />Illustrative process, sample data</p>
    <ol class="steps">
      <li v-for="step in flow.steps" :key="step.label" class="step" :class="'step--' + step.state">
        <span class="step__icon" :class="ICON[step.state]" aria-hidden="true" />
        <div>
          <p class="step__label">{{ step.label }}</p>
          <p class="step__word">{{ WORD[step.state] }}</p>
          <p v-if="step.note" class="step__note">{{ step.note }}</p>
        </div>
      </li>
    </ol>
    <div v-if="actions.length" class="actions">
      <p class="actions__title">Go to records</p>
      <RouterLink v-for="a in actions" :key="a.label" :to="a.to" class="action">{{ a.label }}<span class="lucide-arrow-right" aria-hidden="true" /></RouterLink>
    </div>
  </section>
</template>

<style scoped>
.flow { padding: 16px; }
.flow__title { margin: 0; font: 600 16px var(--bj-font-heading); }
.flow__sample { display: flex; align-items: center; gap: 6px; margin: 4px 0 14px; font-size: 12px; color: var(--bj-muted); }
.flow__sample span { width: 14px; height: 14px; }
.steps { margin: 0; padding: 0; list-style: none; }
.step { position: relative; display: grid; grid-template-columns: 22px 1fr; gap: 10px; padding-bottom: 16px; }
.step:not(:last-child)::before { content: ''; position: absolute; left: 10px; top: 24px; bottom: 2px; width: 2px; background: var(--bj-line); }
.step--done:not(:last-child)::before { background: var(--bj-state-completed); }
.step__icon { width: 22px; height: 22px; }
.step--done .step__icon { color: var(--bj-state-completed); }
.step--current .step__icon { color: var(--bj-state-current); }
.step--next .step__icon { color: var(--bj-state-pending); }
.step__label { margin: 1px 0 0; font-size: 14px; font-weight: 500; }
.step__word { margin: 1px 0 0; font-size: 12px; color: var(--bj-muted); }
.step--current .step__word { color: var(--bj-state-current); font-weight: 600; }
.step__note { margin: 4px 0 0; font-size: 12px; color: var(--bj-muted); }
.actions { display: grid; gap: 6px; margin-top: 8px; padding-top: 14px; border-top: 1px solid var(--bj-line); }
.actions__title { margin: 0 0 2px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; color: var(--bj-muted); }
.action { display: flex; justify-content: space-between; align-items: center; min-height: 40px; padding: 8px 12px; border: 1px solid var(--bj-line); border-radius: 8px; font-size: 14px; font-weight: 500; color: var(--bj-terracotta); text-decoration: none; }
.action:hover { background: var(--bj-terracotta-tint); }
.action span { width: 16px; height: 16px; }
</style>
