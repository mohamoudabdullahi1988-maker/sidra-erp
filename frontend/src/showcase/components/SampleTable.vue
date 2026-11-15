<script setup>
import { formatValue } from '../format'

// Draws sample rows; `kind` only chooses the look of a value.
defineProps({ columns: { type: Array, required: true }, rows: { type: Array, required: true } })

const CHIP = {
  green: ['Confirmed', 'Completed', 'On track', 'Approved', 'Pass', 'Available', 'Paid in full', 'Low', 'Issued', 'Commission collected', 'Sold', 'Contracts', 'Current', 'Handover', 'No'],
  amber: ['Draft', 'At risk', 'Awaiting approval', 'Pass with remarks', 'Reserved', 'Medium', 'Under offer', 'Mitigating', 'Procurement', 'Offer accepted', 'Reservations', '1-30 days', '31-60 days'],
  red: ['Delayed', 'Fail', 'High', 'Overdue', 'Commission due', 'Yes', '61-90 days', '90+ days', 'Open'],
  blue: ['Construction', 'Under review', 'Active', 'Upcoming', 'Monitoring', 'Quotations', 'Site visits'],
}
function chip(value) {
  for (const [toneName, values] of Object.entries(CHIP)) if (values.includes(value)) return toneName
  return 'grey'
}
const RAG = { G: 'Good', A: 'Watch', R: 'Problem' }
</script>

<template>
  <div class="table-wrap">
    <table class="sample-table">
      <thead>
        <tr><th v-for="c in columns" :key="c.key" :class="'k-' + c.kind">{{ c.label }}</th></tr>
      </thead>
      <tbody>
        <tr v-for="(row, i) in rows" :key="i">
          <td v-for="(c, ci) in columns" :key="c.key" :class="'k-' + c.kind">
            <RouterLink v-if="ci === 0 && row._to" :to="row._to" class="cell-link">{{ formatValue(row[c.key], c.kind) }}</RouterLink>
            <span v-else-if="c.kind === 'rag'" class="rag" :class="'rag--' + row[c.key]" :title="RAG[row[c.key]]"><span class="sr">{{ RAG[row[c.key]] }}</span></span>
            <span v-else-if="c.kind === 'chip'" class="chip" :class="'chip--' + chip(row[c.key])">{{ row[c.key] }}</span>
            <span v-else-if="c.kind === 'progress' && row[c.key] !== null && row[c.key] !== undefined" class="progress"><span class="progress__bar"><span :style="{ width: row[c.key] + '%' }" /></span>{{ row[c.key] }}%</span>
            <template v-else>{{ formatValue(row[c.key], c.kind) }}</template>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-wrap { position: relative; overflow-x: auto; } /* contains the hidden .sr labels, so they scroll with the table and never widen the page */
.sample-table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { position: sticky; top: 0; background: var(--bj-card); padding: 8px 10px; text-align: left; font-size: 11.5px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; color: var(--bj-muted); border-bottom: 1px solid var(--bj-line); white-space: nowrap; }
td { padding: 8px 10px; border-bottom: 1px solid var(--bj-line); white-space: nowrap; color: var(--bj-ink); }
tbody tr:nth-child(even) td { background: rgb(244 246 243 / 0.55); }
tbody tr:hover td { background: var(--bj-terracotta-tint); }
.k-money, .k-moneyFull, .k-count, .k-pct { text-align: right; font-variant-numeric: tabular-nums; }
.k-rag { text-align: center; }
.cell-link { color: var(--bj-terracotta); font-weight: 500; text-decoration: none; }
.cell-link:hover { text-decoration: underline; }
.rag { display: inline-block; width: 12px; height: 12px; border-radius: 50%; }
.rag--G { background: var(--bj-c-green); }
.rag--A { background: var(--bj-c-amber); }
.rag--R { background: var(--bj-c-rose); }
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
.chip { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 500; }
.chip--green { background: var(--bj-chip-green-bg); color: var(--bj-chip-green-ink); }
.chip--amber { background: var(--bj-chip-amber-bg); color: var(--bj-chip-amber-ink); }
.chip--red { background: var(--bj-chip-red-bg); color: var(--bj-chip-red-ink); }
.chip--blue { background: var(--bj-chip-blue-bg); color: var(--bj-chip-blue-ink); }
.chip--grey { background: var(--bj-ground); color: var(--bj-muted); }
.progress { display: inline-flex; align-items: center; gap: 8px; font-variant-numeric: tabular-nums; }
.progress__bar { width: 70px; height: 7px; border-radius: 4px; background: var(--bj-ground); overflow: hidden; }
.progress__bar span { display: block; height: 100%; background: var(--bj-c-teal); }
</style>
