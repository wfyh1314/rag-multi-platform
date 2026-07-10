import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { login as loginApi, getMe } from '@/views/login/api/auth'
import { clearAuth, getStoredUser, getToken, setStoredUser, setToken } from '@/utils/token'

const token = ref(getToken())
const user = ref(getStoredUser())
let initPromise = null

export function useAuth() {
  const router = useRouter()

  const isAuthenticated = computed(() => !!token.value)

  async function login(credentials) {
    const { data } = await loginApi(credentials)
    token.value = data.access_token
    user.value = data.user
    setToken(data.access_token)
    setStoredUser(data.user)
    return data
  }

  function logout() {
    token.value = ''
    user.value = null
    clearAuth()
    router.push('/login')
  }

  async function fetchMe() {
    if (!token.value) return null
    try {
      const { data } = await getMe()
      user.value = data
      setStoredUser(data)
      return data
    } catch {
      logout()
      return null
    }
  }

  async function initAuth() {
    if (!token.value) return
    if (!initPromise) {
      initPromise = fetchMe().finally(() => {
        initPromise = null
      })
    }
    return initPromise
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    logout,
    fetchMe,
    initAuth,
  }
}
