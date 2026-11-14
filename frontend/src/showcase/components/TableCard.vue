<script setup>
import { computed } from 'vue'
import Card from './Card.vue'
import SampleTable from './SampleTable.vue'
import { DATASETS, filterRows } from '../datasets'

const props = defineProps({ widget: { type: Object, required: true } })
const set = computed(() => DATASETS[props.widget.set])
const columns = computed(() => props.widget.columns.map((key) => set.value.columns.find((c) => c.key === key)).filter(Boolean))
const rows = computed(() => {
  let rows = filterRows(set.value, props.widget.filter)
  if (props.widget.extra) rows = [...rows, ...filterRows(set.value, props.widget.extra)]
  if (props.widget.sort) rows = [...rows].sort((a, b) => (a[props.widget.sort] > b[props.widget.sort] ? 1 : -1))
  return rows.slice(0, props.widget.limit ?? 8)
})
</script>

<template>
  <Card :title="widget.title" :note="widget.note" :to="{ set: widget.set, filter: widget.filter }">
    <SampleTable :columns="columns" :rows="rows" />
  </Card>
</template>
