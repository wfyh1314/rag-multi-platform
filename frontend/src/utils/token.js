const TOKEN_KEY = 'access_token'
const USER_KEY = 'user_info'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export function getStoredUser() {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function setStoredUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearStoredUser() {
  localStorage.removeItem(USER_KEY)
}

export function clearAuth() {
  clearToken()
  clearStoredUser()
}

export function getAuthHeaders() {
  const token = getToken()
  const headers = { 'Content-Type': 'application/json' }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  return headers
}
