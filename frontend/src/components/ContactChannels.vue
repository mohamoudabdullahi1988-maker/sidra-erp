<script setup>
import { computed } from 'vue'
import { contactLinks } from '../channels'
const props = defineProps({ doc: { type: Object, required: true } })
const links = computed(() => contactLinks(props.doc))
</script>
<template>
  <section class="bj-card channels">
    <h2>Contact channels</h2>
    <p v-if="doc.status === 'Do Not Contact'">This lead is marked Do Not Contact.</p>
    <template v-else>
      <div class="bj-toolbar"><a v-for="link in links" :key="link.label" class="bj-btn" :href="link.href" :target="link.label === 'WhatsApp' ? '_blank' : undefined" rel="noopener noreferrer">{{ link.label }}</a></div>
      <p class="bj-sub">Opens your email, phone or WhatsApp app. Add a phone number with its country code for WhatsApp. Messages are not sent or synced by Berjaya.</p>
    </template>
  </section>
</template>
<style scoped>.channels { margin: 16px 0; } .channels h2 { margin-bottom: 12px; }</style>
