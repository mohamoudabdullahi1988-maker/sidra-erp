<script setup>
import { computed } from 'vue'
import Card from './Card.vue'
import SampleTable from './SampleTable.vue'
import { DATASETS, filterRows } from '../datasets'

const props = defineProps({ widget: { type: Object, required: true } })
// Sample tables name a list in datasets.js; live tables bring their own rows and columns.
const inline = computed(() => Array.isArray(props.widget.rows))
const set = computed(() => DATASETS[props.widget.set])
const columns = computed(() =>
  inline.value
    ? props.widget.columnDefs.map((c) => ({ kind: 'text', ...c }))
    : props.widget.columns.map((key) => set.value.columns.find((c) => c.key === key)).filter(Boolean),
)
const rows = computed(() => {
  if (inline.value) return props.widget.rows.slice(0, props.widget.limit ?? 10)
  let rows = filterRows(set.value, props.widget.filter)
  if (props.widget.extra) rows = [...rows, ...filterRows(set.value, props.widget.extra)]
  if (props.widget.sort) rows = [...rows].sort((a, b) => (a[props.widget.sort] > b[props.widget.sort] ? 1 : -1))
  return rows.slice(0, props.widget.limit ?? 8)
})
</script>

<template>
  <Card :title="widget.title" :note="widget.note" :to="inline ? widget.to : { set: widget.set, filter: widget.filter }">
    <SampleTable :columns="columns" :rows="rows" />
  </Card>
</template>
