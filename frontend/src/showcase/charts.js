// Geometry for the sample charts. Pure functions so they can be unit tested.

export const tone = (name) => `var(--bj-c-${name || 'blue'})`

/** A "nice" axis maximum and tick values for a data maximum. */
export function niceScale(max, ticks = 4) {
  if (!(max > 0)) return { max: 1, ticks: [0, 1] }
  const raw = max / ticks
  const mag = 10 ** Math.floor(Math.log10(raw))
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw)
  const top = Math.ceil(max / step) * step
  return { max: top, ticks: Array.from({ length: Math.round(top / step) + 1 }, (_, i) => i * step) }
}

/** Donut segments as stroke-dasharray offsets on a circle of circumference 100. */
export function donutArcs(values) {
  const total = values.reduce((a, v) => a + Math.max(0, v), 0)
  let offset = 0
  return values.map((v) => {
    const share = total ? (Math.max(0, v) / total) * 100 : 0
    const arc = { share, dash: `${share} ${100 - share}`, offset: 25 - offset }
    offset += share
    return arc
  })
}

/** Position of a date between two dates, 0-100. */
export function datePosition(value, from, until) {
  const a = Date.parse(from)
  const b = Date.parse(until)
  const t = Date.parse(value)
  return Math.max(0, Math.min(100, ((t - a) / (b - a)) * 100))
}

/** First day of each quarter (or month when the span is short) between two dates, for axis labels. */
export function dateTicks(from, until) {
  const start = new Date(from)
  const end = new Date(until)
  const months = (end.getUTCFullYear() - start.getUTCFullYear()) * 12 + end.getUTCMonth() - start.getUTCMonth()
  const step = months > 24 ? 6 : months > 10 ? 3 : 1
  const out = []
  const d = new Date(Date.UTC(start.getUTCFullYear(), start.getUTCMonth() + 1, 1))
  while (d < end) {
    if (d.getUTCMonth() % step === 0) out.push(d.toISOString().slice(0, 10))
    d.setUTCMonth(d.getUTCMonth() + 1)
  }
  return out
}

/** Schematic outline of Somaliland (longitude, latitude), for the sites map. Approximate. */
export const OUTLINE = [
  [43.0, 11.45], [43.45, 11.35], [44.0, 10.95], [44.6, 10.42], [45.03, 10.44], [45.8, 10.86], [46.6, 10.75],
  [47.4, 11.18], [48.2, 11.15], [48.95, 11.25], [48.95, 10.6], [48.4, 9.6], [47.6, 8.8], [47.0, 8.0],
  [46.0, 8.0], [44.95, 8.4], [44.0, 9.0], [43.3, 9.55], [42.9, 10.0], [42.95, 10.98],
]
export const BOUNDS = { west: 42.6, east: 49.3, north: 11.7, south: 7.7 }

export function project([lon, lat], width, height) {
  return [((lon - BOUNDS.west) / (BOUNDS.east - BOUNDS.west)) * width, ((BOUNDS.north - lat) / (BOUNDS.north - BOUNDS.south)) * height]
}
