<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { apiGet } from '../api'
import { claimPanel, releasePanel } from '../panel'
import WorkflowPanel from './WorkflowPanel.vue'
const props = defineProps({ doctype: String, name: String, reloadKey: { default: 0 } })
const timeline = ref(null), loading = ref(false), error = ref('')
let request = 0
async function load() {
  const id = ++request
  timeline.value = null; error.value = ''
  if (!props.name) return
  loading.value = true
  try {
    const r = await apiGet('/api/method/sidra_realestate.api.record_workflow.get_timeline', { doctype: props.doctype, name: props.name })
    if (id === request) timeline.value = r.message
  } catch (e) { if (id === request) error.value = e.message }
  finally { if (id === request) loading.value = false }
}
watch(() => [props.doctype, props.name, props.reloadKey], load, { immediate: true })
onMounted(claimPanel)
onBeforeUnmount(() => { ++request; releasePanel() })
</script>
<template>
  <Teleport defer to="#berjaya-panel">
    <WorkflowPanel :timeline="timeline" :loading="loading" :error="error" @refresh="load" />
    <div v-if="timeline?.actions?.length" class="next-actions"><h3>Available actions</h3><p>{{ timeline.actions.join(' · ') }}</p><a class="bj-btn" href="#record-actions">Go to record actions</a></div>
  </Teleport>
</template>
<style scoped>.next-actions { padding: 16px; font-size: 13px; }</style>
