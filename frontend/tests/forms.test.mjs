import test from 'node:test'
import assert from 'node:assert/strict'

import { evaluate, initialValues, isEditable, isShown, missing, payload, ruleValues, typed } from '../src/forms.js'

// The same trees services/form_rules.py produces (see test_engine_form_rules.py).
const EQ = (field, value) => ({ eq: [{ field }, { lit: value }] })
const NE = (field, value) => ({ ne: [{ field }, { lit: value }] })

test('rules evaluate as on the server', () => {
  const external = { and: [EQ('contract_type', 'Installment'), EQ('source', 'External (registered)')] }
  assert.equal(evaluate(external, { contract_type: 'Installment', source: 'External (registered)' }), true)
  assert.equal(evaluate(external, { contract_type: 'Installment', source: 'Generated from profile' }), false)
  const either = { or: [NE('source', 'External (registered)'), NE('down_payment_mode', 'Recorded separately')] }
  assert.equal(evaluate(either, { source: 'External (registered)', down_payment_mode: 'Recorded separately' }), false)
  assert.equal(evaluate(either, { source: 'External (registered)', down_payment_mode: 'None' }), true)
  assert.equal(evaluate({ not: { not: { field: 'current_contract' } } }, { current_contract: 'SSC-1' }), true)
  assert.equal(evaluate({ not: { field: '__islocal' } }, { __islocal: 1 }), false)
  assert.equal(evaluate({ field: 'title_refund_after_days' }, { title_refund_after_days: 0 }), false)
  assert.equal(evaluate({ in: [['House', 'Apartment'], { field: 'unit_type' }] }, { unit_type: 'House' }), true)
  assert.equal(evaluate(NE('title_penalty_type', 'None'), { title_penalty_type: null }), true)
  assert.equal(evaluate(EQ('n', 5), { n: '5.0' }), true)
  assert.throws(() => evaluate({ mystery: 1 }, {}))
})

const FORM = {
  doctype: 'Sidra Unit',
  name: 'U-1',
  is_new: false,
  modified: '2026-11-14 10:00:00',
  values: { unit_code: 'U-1', cash_price: 12000, area_sqm: 200, unit_type: 'Plot', company: 'C', bedrooms: null },
  layout: [
    {
      label: 'Unit',
      fields: [
        { fieldname: 'unit_code', label: 'Unit Code', fieldtype: 'Data', editable: true, reqd: true },
        { fieldname: 'company', label: 'Company', fieldtype: 'Link', editable: false },
        { fieldname: 'cash_price', label: 'Cash Price', fieldtype: 'Currency', editable: true, read_only_rule: { not: { field: '__islocal' } } },
        { fieldname: 'area_sqm', label: 'Area', fieldtype: 'Float', editable: true },
        { fieldname: 'unit_type', label: 'Type', fieldtype: 'Select', editable: true, options: ['Plot', 'House'] },
      ],
    },
    {
      label: 'House',
      show: { in: [['House', 'Apartment'], { field: 'unit_type' }] },
      fields: [{ fieldname: 'bedrooms', label: 'Bedrooms', fieldtype: 'Int', editable: true, reqd: true }],
    },
  ],
}

test('a saved record sends only the editable fields that changed', () => {
  const values = initialValues(FORM)
  const start = JSON.parse(JSON.stringify(values))
  assert.deepEqual(payload(FORM, values, start), {})
  values.area_sqm = '216'
  values.cash_price = '99' // read-only by rule on a saved unit: never sent
  values.company = 'Other' // not editable: never sent
  assert.deepEqual(payload(FORM, values, start), { area_sqm: 216 })
})

test('a new record sends its filled editable fields, and the rule allows the price', () => {
  const form = { ...FORM, is_new: true, name: null, values: {} }
  const values = initialValues(form)
  Object.assign(values, { unit_code: 'U-2', cash_price: '12,000', unit_type: 'Plot' })
  assert.deepEqual(payload(form, values, initialValues(form)), { unit_code: 'U-2', cash_price: 12000, unit_type: 'Plot' })
  const cash = FORM.layout[0].fields[2]
  assert.equal(isEditable(cash, ruleValues(form, values)), true)
  assert.equal(isEditable(cash, ruleValues(FORM, values)), false)
})

test('sections and required hints follow the rules', () => {
  const values = initialValues(FORM)
  assert.equal(isShown(FORM.layout[1], ruleValues(FORM, values)), false)
  assert.deepEqual(missing(FORM, values), [])
  values.unit_type = 'House'
  assert.equal(isShown(FORM.layout[1], ruleValues(FORM, values)), true)
  assert.deepEqual(missing(FORM, values), ['Bedrooms'])
  values.unit_code = ''
  assert.deepEqual(missing(FORM, values), ['Unit Code', 'Bedrooms'])
})

test('values take their field type before rules see them', () => {
  assert.equal(typed({ fieldtype: 'Int' }, ''), null)
  assert.equal(typed({ fieldtype: 'Currency' }, '1,250.50'), 1250.5)
  assert.equal(typed({ fieldtype: 'Check' }, true), 1)
  assert.equal(typed({ fieldtype: 'Float' }, 'abc'), 'abc') // the server refuses it
  const rules = ruleValues({ ...FORM, is_new: true }, { area_sqm: '0', unit_type: 'Plot' })
  assert.equal(rules.area_sqm, 0)
  assert.equal(rules.__islocal, 1)
})

test('a field whose read-only rule the server could not read stays read-only', () => {
  const field = { fieldname: 'x', fieldtype: 'Data', editable: true, unparsed: ['read_only_depends_on'] }
  assert.equal(isEditable(field, {}), false)
})

test('dynamic picker resolves the dependent field and refuses other doctypes', async () => {
  const { linkTarget } = await import('../src/forms.js')
  const field = { fieldtype: 'Dynamic Link', options: 'opportunity_from', allowed_doctypes: ['Lead', 'Customer', 'Prospect'] }
  for (const target of field.allowed_doctypes) assert.equal(linkTarget(field, { opportunity_from: target }), target)
  for (const target of ['User', 'Company', '', null]) assert.equal(linkTarget(field, { opportunity_from: target }), null)
  assert.equal(linkTarget(field, {}), null)
  assert.equal(linkTarget({ ...field, allowed_doctypes: undefined }, { opportunity_from: 'Lead' }), null)
  assert.equal(linkTarget({ fieldtype: 'Link', options: 'Company' }), 'Company')
})
