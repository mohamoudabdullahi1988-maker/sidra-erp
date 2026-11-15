// Only explicit contact links. Local numbers need a country code before WhatsApp can open.
export function contactLinks(doc = {}) {
  if (doc.status === 'Do Not Contact' || doc.unsubscribed || doc.email_unsubscribed) return []
  const links = []
  const email = String(doc.email_id || '').trim()
  if (/^[^\s@?&#]+@[^\s@?&#]+\.[^\s@?&#]+$/.test(email)) links.push({ label: 'Email', href: `mailto:${encodeURIComponent(email)}` })
  const raw = String(doc.whatsapp_no || doc.mobile_no || doc.phone || '').trim()
  const number = raw.replace(/[\s().-]/g, '').replace(/^00/, '+')
  if (/^\+?[1-9]\d{6,14}$/.test(number)) links.push({ label: 'Call', href: `tel:${number}` })
  if (/^\+[1-9]\d{6,14}$/.test(number)) links.push({ label: 'WhatsApp', href: `https://wa.me/${number.slice(1)}` })
  return links
}
