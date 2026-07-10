import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/utils/token'
import ChatView from '@/views/chat/ChatView.vue'
import FileManageView from '@/views/file/FileManageView.vue'
import LoginView from '@/views/login/LoginView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true },
    },
    {
      path: '/',
      name: 'chat',
      component: ChatView,
      meta: { requiresAuth: true },
    },
    {
      path: '/files',
      name: 'files',
      component: FileManageView,
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to) => {
  const hasToken = !!getToken()

  if (to.meta.requiresAuth && !hasToken) {
    return {
      path: '/login',
      query: { redirect: to.fullPath },
    }
  }

  if (to.path === '/login' && hasToken) {
    return '/'
  }

  return true
})

export default router
