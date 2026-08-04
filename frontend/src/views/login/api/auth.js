import api from '@/api/index'

export function login({ username, password }) {
  return api.post('/api/auth/login', { username, password })
}

export function register({ username, password }) {
  return api.post('/api/auth/register', { username, password })
}

export function getMe() {
  return api.get('/api/users/me')
}

export function updateProfile(payload) {
  return api.put('/api/users/me', payload).then((res) => res.data)
}
