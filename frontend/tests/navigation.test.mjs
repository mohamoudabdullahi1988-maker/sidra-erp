import test from 'node:test'
import assert from 'node:assert/strict'
import { sectionLinks } from '../src/navigation.js'
import { contactLinks } from '../src/channels.js'

test('navigation shows only permitted transactions, alongside report routes', () => {
  const links = sectionLinks('construction-hub', { jobs: { read: true }, variations: { read: false } })
  assert.ok(links.some((l) => l.to.name === 'construction'))
  assert.ok(!links.some((l) => l.label === 'Variation orders'))
  assert.ok(links.some((l) => l.to.params?.tab === 'schedule'))
  const crm = sectionLinks('customers', { leads: { read: true } })
  assert.deepEqual(crm.map((l) => l.to.name), ['customers', 'leads-list'])
})
test('contact channels require valid details and honour Do Not Contact', () => {
  assert.deepEqual(contactLinks({ status: 'Do Not Contact', email_id: 'buyer@example.com', mobile_no: '+252 63 1234567' }), [])
  assert.deepEqual(contactLinks({ email_id: 'buyer@example.com', mobile_no: '+252 63 1234567' }).map((l) => l.label), ['Email', 'Call', 'WhatsApp'])
  assert.ok(!contactLinks({ mobile_no: '0631234567' }).some((l) => l.label === 'WhatsApp'))
  assert.deepEqual(contactLinks({ email_id: 'buyer@example.com?bcc=other@example.com', mobile_no: 'javascript:alert(1)' }), [])
})
