export function label(value) {
  return value === undefined || value === null || value === '' ? 'Unavailable' : String(value)
}
export function distribution(rows, field) {
  const groups = new Map()
  for (const row of rows) { const key = label(row[field]); groups.set(key, (groups.get(key) || 0) + 1) }
  return [...groups].map(([label, value]) => ({ label, value })).sort((a,b) => b.value-a.value || a.label.localeCompare(b.label))
}
export function csv(rows, columns) {
  const cell = value => {
    let text = label(value)
    if (/^[\s]*[=+\-@]/.test(text) || /^[\t\r\n]/.test(text)) text = "'" + text
    return '"' + text.replaceAll('"','""') + '"'
  }
  return [columns.map(c=>cell(c.label)).join(','), ...rows.map(row=>columns.map(c=>cell(row[c.field])).join(','))].join('\r\n')
}
