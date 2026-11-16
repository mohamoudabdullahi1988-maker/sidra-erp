import test from 'node:test'
import assert from 'node:assert/strict'
import { recordRoute, exportUrl } from '../src/discovery.js'
test('search and report drill-down use actual record routes',()=>{
 assert.deepEqual(recordRoute('Sidra Sale Contract','SSC-1'),{name:'contract-detail',params:{name:'SSC-1'}})
 assert.deepEqual(recordRoute('Sidra Construction Job','JOB-1'),{name:'construction-detail',params:{name:'JOB-1'}})
 assert.equal(recordRoute('Unknown','x'),null)
})
test('export preserves exact filters and selected columns',()=>{
 const url = new URL(exportUrl('Lead',[['name','like','%A&B%']],['name']), 'https://example.invalid')
 assert.deepEqual(JSON.parse(url.searchParams.get('filters')),[['name','like','%A&B%']])
 assert.deepEqual(JSON.parse(url.searchParams.get('columns')),['name'])
})
