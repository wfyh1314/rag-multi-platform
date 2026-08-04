import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/utils/token'
import ChatView from '@/views/chat/ChatView.vue'
import FileManageView from '@/views/file/FileManageView.vue'
import TagManageView from '@/views/tag/TagManageView.vue'
import AuditView from '@/views/audit/AuditView.vue'
import LoginView from '@/views/login/LoginView.vue'
import RegisterView from '@/views/login/RegisterView.vue'
import ProfileView from '@/views/login/ProfileView.vue'

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
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { public: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { requiresAuth: true, title: '个人资料', menu: 'profile' },
    },
    {
      path: '/',
      name: 'chat',
      component: ChatView,
      meta: { requiresAuth: true, title: '工作区', menu: 'workspace' },
    },
    {
      path: '/files',
      name: 'files',
      component: FileManageView,
      meta: { requiresAuth: true, title: '文件上传', menu: 'files' },
    },
    {
      path: '/tags',
      name: 'tags',
      component: TagManageView,
      meta: { requiresAuth: true, title: '打标签', menu: 'tags' },
    },
    {
      path: '/audit',
      name: 'audit',
      component: AuditView,
      meta: { requiresAuth: true, title: '审计日志', menu: 'audit' },
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

  if ((to.path === '/login' || to.path === '/register') && hasToken) {
    return '/'
  }

  return true
})

export default router
