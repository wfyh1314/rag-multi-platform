import axios from 'axios'
import { clearAuth, getToken } from '@/utils/token'

const SUCCESS_CODE = 10000

const api = axios.create({
  baseURL: window.baseUrl || '',
  timeout: 120000,
})

function extractErrorMessage(data, fallback = '请求失败') {
  if (!data) return fallback
  if (data.message) return data.message
  if (data.description) return data.description
  if (data.detail) {
    return Array.isArray(data.detail)
      ? data.detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
      : String(data.detail)
  }
  return fallback
}

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body.code === 'number') {
      if (body.code === SUCCESS_CODE) {
        response.data = body.result ?? null
        return response
      }
      return Promise.reject(new Error(extractErrorMessage(body)))
    }
    return response
  },
  (error) => {
    const status = error.response?.status
    const data = error.response?.data

    if (status === 401) {
      clearAuth()
      const loginPath = '/login'
      if (window.location.pathname !== loginPath) {
        const redirect = encodeURIComponent(window.location.pathname + window.location.search)
        window.location.href = `${loginPath}?redirect=${redirect}`
      }
    }

    const message = extractErrorMessage(data, error.message || '请求失败')
    return Promise.reject(new Error(message))
  },
)

export default api
