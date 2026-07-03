import axios from 'axios'

const api = axios.create({
  baseURL: window.baseUrl || '',
  timeout: 120000,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const data = error.response?.data
    let message = data?.message || error.message || '请求失败'
    if (!data?.message && data?.detail) {
      message = Array.isArray(data.detail)
        ? data.detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
        : String(data.detail)
    }
    return Promise.reject(new Error(message))
  },
)

export default api
