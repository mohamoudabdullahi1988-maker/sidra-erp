<script setup>
// Notes the server's form gives for a record (Desk's form intros): plain text, a tone, and
// optionally one link (e.g. the import template).
defineProps({ notes: { type: Array, default: () => [] } })
</script>

<template>
  <p v-for="(note, index) in notes" :key="index" class="bj-note fn" :class="{ 'fn--warning': note.tone === 'warning' }" role="note">
    <span :class="note.tone === 'warning' ? 'lucide-triangle-alert' : 'lucide-info'" aria-hidden="true" />
    <span>
      {{ note.text }}
      <a v-if="note.link" class="bj-link" :href="note.link.url" target="_blank" rel="noopener">{{ note.link.label }}</a>
    </span>
  </p>
</template>

<style scoped>
.fn {
  margin: 12px 0;
}
.fn--warning > span:first-child {
  color: var(--bj-state-blocked);
}
</style>
