export class ApiError extends Error {
  constructor(message) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function apiPost(apiBase, path, body) {
  const url = apiBase.replace(/\/+$/, '') + path
  let resp
  try {
    resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch (err) {
    throw new ApiError(`Could not reach ${url}: ${err.message}`)
  }

  let data = {}
  try {
    data = await resp.json()
  } catch {
    // ignore JSON parse errors
  }

  if (!resp.ok) {
    const detail = typeof data?.detail === 'string'
      ? data.detail
      : String(data?.detail || `HTTP ${resp.status}`)
    throw new ApiError(detail)
  }

  return data
}

export async function checkHealth(apiBase) {
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 4000)
    const resp = await fetch(apiBase.replace(/\/+$/, '') + '/health', {
      signal: controller.signal,
    })
    clearTimeout(timeout)
    const data = await resp.json()
    return !!(resp.ok && data.model_loaded)
  } catch {
    return false
  }
}
