import { canOpen, canRead } from '../boot'
import { listRoute } from '../records'

/** A sample link ({ set, filter }) or a router location, as a router location. */
export function linkTo(to) {
  if (!to) return null
  if (to.set) return { name: 'sample', params: { set: to.set }, query: to.filter ?? {} }
  return to
}

/** A button to real records, if this user's session allows it (the server decides; see boot.js). */
export function recordAction(action) {
  if (action.list && !canRead(action.list)) return null
  if (action.section && !canOpen(action.section)) return null
  return { label: action.label, to: action.list && !action.to ? { name: listRoute(action.list) } : action.to }
}
