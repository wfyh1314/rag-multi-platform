import api from '@/api/index'

export function login({ username, password, tenant_id }) {
  return api.post('/api/auth/login', { username, password, tenant_id })
}

export function getMe() {
  return api.get('/api/users/me')
}
