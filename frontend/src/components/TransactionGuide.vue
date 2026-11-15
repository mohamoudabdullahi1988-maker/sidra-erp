<script setup>
import { computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { canRead } from '../boot'
import { claimPanel, releasePanel } from '../panel'
import { RECORDS, SECTIONS, listRoute } from '../records'
const route = useRoute()
const section = computed(() => route.meta.section)
const links = computed(() => (SECTIONS[section.value] || []).filter(canRead).map(key => ({ label: RECORDS[key].title, to: { name: listRoute(key) } })))
onMounted(claimPanel)
onBeforeUnmount(releasePanel)
</script>
<template><Teleport defer to="#berjaya-panel"><section class="guide"><h2>Transaction workflow</h2><p>Open a record to review its saved status and use the actions available to your role.</p><ol><li>Create or choose a record.</li><li>Review its details and required evidence.</li><li>Use the record's approval or submission actions.</li><li>Review its attachments, comments and change history.</li></ol><p>This guide does not indicate that a record has been approved.</p><h3>Related transactions</h3><RouterLink v-for="link in links" :key="link.label" :to="link.to">{{ link.label }} →</RouterLink></section></Teleport></template>
<style scoped>.guide { padding:16px;font-size:13px;line-height:1.6; } h2 { font-size:16px; } h3 { margin-top:20px; } li { margin:12px 0; } a { display:block;padding:10px;border-bottom:1px solid var(--bj-line);color:var(--bj-terracotta); }</style>
