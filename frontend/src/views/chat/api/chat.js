import api from '@/api/index'
import { getAuthHeaders } from '@/utils/token'

export function fetchModels() {
  return api.get('/api/models', { timeout: 10000 }).then((res) => {
    const models = res.data.models || []
    return models.map((m) =>
      typeof m === 'string' ? { id: m, name: m } : { id: m.id, name: m.name || m.id },
    )
  })
}

export function fetchCollections() {
  return api.get('/api/collections', { timeout: 10000 }).then((res) => res.data)
}

export function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000,
  }).then((res) => res.data)
}

export function clearHistory(sessionId) {
  return api.post('/api/history/clear', { session_id: sessionId })
}

export async function streamChat(params, onChunk, onDone, onError) {
  const baseUrl = window.baseUrl || ''
  const history = params.history || []
  const body = {
    query: params.query ?? params.question,
    session_id: params.session_id,
    collection: params.collection,
    model: params.model,
    history,
    temperature: params.temperature,
    max_length: params.max_length,
  }

  const response = await fetch(`${baseUrl}/api/chat/stream`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    let message = `请求失败: ${response.status}`
    try {
      const errData = await response.json()
      if (typeof errData.code === 'number' && errData.code !== 10000) {
        message = errData.message || errData.description || message
      } else if (errData.message) {
        message = errData.message
      } else if (errData.detail) {
        message = Array.isArray(errData.detail)
          ? errData.detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
          : String(errData.detail)
      }
    } catch {
      // ignore parse error
    }
    throw new Error(message)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const data = JSON.parse(line.slice(6))
        if (data.error) {
          onError?.(data.error)
          return
        }
        if (data.done) {
          onDone?.()
          return
        }
        if (data.content) {
          onChunk?.(data.content)
        }
      } catch {
        // 忽略格式错误的 SSE 行
      }
    }
  }
  onDone?.()
}

export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
