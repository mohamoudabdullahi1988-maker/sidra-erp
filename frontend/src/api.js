// Access to Frappe's standard REST API on the same origin, using the existing session cookie.
// Writes carry the session's CSRF token, which the server put on the page (window.csrf_token).
// No tokens are stored anywhere.

export class ApiError extends Error {
  constructor(kind, message, status = 0, type = '') {
    super(message)
    this.kind = kind // 'network' | 'denied' | 'server'
    this.status = status
    this.type = type // the server's exception class, e.g. 'StaleRecord', when it sent one
  }
}

export function loginUrl() {
  const back = window.location.pathname + window.location.search
  return '/login?redirect-to=' + encodeURIComponent(back)
}

async function stillSignedIn() {
  try {
    const res = await fetch('/api/method/frappe.auth.get_logged_user', {
      credentials: 'same-origin',
      headers: { Accept: 'application/json' },
    })
    if (!res.ok) return false
    const body = await res.json()
    return Boolean(body.message) && body.message !== 'Guest'
  } catch {
    // Unknown, not "signed out": do not bounce someone to the login page on a network fault.
    return true
  }
}

/** Strip the markup Frappe allows in messages; the text is shown as plain text. */
function plain(text) {
  return String(text)
    .replace(/<[^>]*>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .trim()
}

/** The messages frappe.throw / msgprint put in `_server_messages` (a JSON list of JSON strings). */
export function serverMessages(body) {
  if (!body || typeof body._server_messages !== 'string') return []
  try {
    return JSON.parse(body._server_messages)
      .map((entry) => {
        try {
          const parsed = typeof entry === 'string' ? JSON.parse(entry) : entry
          return parsed && typeof parsed === 'object' ? parsed.message : parsed
        } catch {
          return entry
        }
      })
      .filter((message) => typeof message === 'string' && message.trim())
      .map(plain)
  } catch {
    return []
  }
}

export function serverMessage(body) {
  if (!body || typeof body !== 'object') return ''
  if (Array.isArray(body.errors) && body.errors[0]?.message) return plain(body.errors[0].message)
  const messages = serverMessages(body)
  if (messages.length) return messages[messages.length - 1]
  if (typeof body.exception === 'string') return plain(body.exception.split(':').slice(1).join(':'))
  return ''
}

function exceptionType(body) {
  if (typeof body?.exc_type === 'string') return body.exc_type
  if (typeof body?.exception === 'string') return body.exception.split(':')[0].split('.').pop().trim()
  return ''
}

export async function apiGet(path, params = {}) {
  const url = new URL(path, window.location.origin)
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) continue
    url.searchParams.set(key, typeof value === 'object' ? JSON.stringify(value) : String(value))
  }

  let res
  try {
    res = await fetch(url, { credentials: 'same-origin', headers: { Accept: 'application/json' } })
  } catch {
    throw new ApiError('network', 'The server could not be reached.')
  }

  let body = null
  try {
    body = await res.json()
  } catch {
    body = null
  }

  if (res.status === 401 || res.status === 403) {
    if (!(await stillSignedIn())) {
      window.location.assign(loginUrl())
      // Navigation is under way; keep the caller in its loading state.
      return new Promise(() => {})
    }
    throw new ApiError('denied', serverMessage(body) || 'You do not have access to this.', res.status)
  }
  if (!res.ok || body === null) {
    throw new ApiError(
      'server',
      serverMessage(body) || `The server answered with an error (${res.status}).`,
      res.status,
    )
  }
  return body
}

async function send(path, init) {
  let res
  try {
    res = await fetch(new URL(path, window.location.origin), {
      method: 'POST',
      credentials: 'same-origin',
      ...init,
      headers: { Accept: 'application/json', 'X-Frappe-CSRF-Token': window.csrf_token || '', ...init.headers },
    })
  } catch {
    // The request may or may not have reached the server. Callers that change records send a
    // request key or the record's version, so trying again cannot apply the change twice.
    throw new ApiError('network', 'The server could not be reached. Nothing is known to have changed; try again.')
  }

  let body = null
  try {
    body = await res.json()
  } catch {
    body = null
  }

  const type = exceptionType(body)
  if (res.status === 401 || res.status === 403 || type === 'PermissionError') {
    if (res.status !== 417 && !(await stillSignedIn())) {
      window.location.assign(loginUrl())
      return new Promise(() => {})
    }
    throw new ApiError('denied', serverMessage(body) || 'You do not have permission to do this.', res.status, type)
  }
  if (!res.ok || body === null) {
    throw new ApiError(
      'server',
      serverMessage(body) || `The server answered with an error (${res.status}).`,
      res.status,
      type,
    )
  }
  return body
}

/** Call a whitelisted server method with POST. Returns the method's `message`. */
export async function apiPost(method, args = {}) {
  const body = await send('/api/method/' + method, {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(args),
  })
  return body.message
}

/** Upload one file through Frappe's own upload method. Returns the File. With a saved record it is
 * attached to that record's field; without one (a new record) it stays unattached and Frappe
 * attaches it to the record when the record is saved with it (attach_files_to_document). */
export async function apiUpload(file, { doctype, docname, fieldname, isPrivate = true } = {}) {
  const form = new FormData()
  form.append('file', file, file.name)
  form.append('is_private', isPrivate ? '1' : '0')
  if (doctype && docname) {
    form.append('doctype', doctype)
    form.append('docname', docname)
    form.append('fieldname', fieldname)
  }
  const body = await send('/api/method/upload_file', { body: form })
  return body.message
}
