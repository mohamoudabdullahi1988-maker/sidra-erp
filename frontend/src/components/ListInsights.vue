<script setup>
import { computed, ref } from 'vue'
import DashboardChart from './DashboardChart.vue'
import { csv, distribution, label } from '../list-insights.js'
const props = defineProps({ rows: {type:Array,default:()=>[]}, columns:{type:Array,default:()=>[{field:'name',label:'Reference'},{field:'status',label:'Status'}]}, group:{type:String,default:'status'}, busy:Boolean, title:{type:String,default:'Loaded records'} })
const query=ref(''), sort=ref(''), descending=ref(false)
const shown=computed(()=>{
 const term=query.value.trim().toLowerCase()
 const rows=props.rows.filter(row=>!term || props.columns.some(c=>label(row[c.field]).toLowerCase().includes(term)))
 return sort.value ? rows.toSorted((a,b)=>label(a[sort.value]).localeCompare(label(b[sort.value]),undefined,{numeric:true})*(descending.value?-1:1)) : rows
})
const chart=computed(()=>distribution(shown.value,props.group))
function download() {
 const url=URL.createObjectURL(new Blob(['\ufeff'+csv(shown.value,props.columns)],{type:'text/csv;charset=utf-8;'}))
 const a=document.createElement('a');a.href=url;a.download='berjaya-loaded-records.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)
}
</script>
<template>
 <details v-if="rows.length && !busy" class="insights">
  <summary>{{ title }} · visual summary and export ({{ rows.length }})</summary>
  <p class="bj-muted small">Only records already loaded on this page. Search and sort below affect this preview and export, not the full list. Load more records in the main list to expand coverage.</p>
  <div class="bj-toolbar">
   <label class="bj-label">Find in loaded records<input v-model="query" class="bj-input" type="search"></label>
   <label class="bj-label">Sort preview<select v-model="sort" class="bj-select"><option value="">Original order</option><option v-for="column in columns" :key="column.field" :value="column.field">{{ column.label }}</option></select></label>
   <button type="button" class="bj-btn" @click="descending=!descending">{{ descending?'Descending':'Ascending' }}</button>
   <button type="button" class="bj-btn" :disabled="!shown.length" @click="download">Export {{ shown.length }} rows (CSV)</button>
  </div>
  <div class="insights-content">
   <DashboardChart :title="`Breakdown by ${columns.find(c=>c.field===group)?.label || group}`" :rows="chart" kind="count" note="Counts of the previewed records; not a company-wide total." />
   <div class="bj-table-wrap"><table class="bj-table"><caption>{{ shown.length }} matching loaded records</caption><thead><tr><th v-for="column in columns" :key="column.field" scope="col">{{ column.label }}</th></tr></thead><tbody><tr v-for="(row,index) in shown" :key="index"><td v-for="column in columns" :key="column.field">{{ label(row[column.field]) }}</td></tr></tbody></table><p v-if="!shown.length">No loaded records match.</p></div>
  </div>
 </details>
</template>
<style scoped>
.insights { border:1px solid var(--bj-line);border-radius:12px;background:var(--bj-card);padding:16px;margin:16px 0; }
summary { min-height:44px;cursor:pointer;font-weight:600;padding:10px 0; }
.insights-content { display:grid;grid-template-columns:minmax(240px,1fr) minmax(0,2fr);gap:16px;margin-top:16px; }
.bj-label { display:grid;gap:6px; }.bj-table td { overflow-wrap:anywhere; }
@media(max-width:800px) { .insights-content { grid-template-columns:1fr; } }
</style>
