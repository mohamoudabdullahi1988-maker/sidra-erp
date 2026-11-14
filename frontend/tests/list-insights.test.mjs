import test from 'node:test'
import assert from 'node:assert/strict'
import { csv, distribution } from '../src/list-insights.js'
test('breakdown counts only supplied records and labels missing values',()=>{
 assert.deepEqual(distribution([{status:'Open'},{status:'Open'},{status:null}],'status'),[{label:'Open',value:2},{label:'Unavailable',value:1}])
 assert.deepEqual(distribution([],'status'),[])
})
test('CSV only exports configured readable columns and escapes quotes',()=>{
 assert.equal(csv([{name:'A,"B',internal_note:'not exported'}],[{field:'name',label:'Reference'}]),'"Reference"\r\n"A,""B"')
 assert.ok(!csv([{name:'A',internal_note:'not exported'}],[{field:'name',label:'Reference'}]).includes('not exported'))
})
test('CSV neutralizes spreadsheet formulas and preserves unavailable values',()=>{
 for(const value of ['=1+1','+CMD','-CMD','@SUM(A1)','  =CMD','\tCMD']) assert.ok(csv([{name:value}],[{field:'name',label:'Reference'}]).split('\r\n')[1].startsWith('"\''))
 assert.equal(csv([{}],[{field:'name',label:'Reference'}]),'"Reference"\r\n"Unavailable"')
})
