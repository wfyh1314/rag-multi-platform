<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const route = useRoute()
const { user, logout, initAuth } = useAuth()

const displayName = computed(() => user.value?.real_name || user.value?.username || '用户')

onMounted(() => {
  initAuth()
})
</script>

<template>
  <nav class="app-nav">
    <div class="app-nav-brand">通用 RAG 知识库</div>
    <div class="app-nav-links">
      <router-link to="/" class="app-nav-link" :class="{ active: route.path === '/' }">
        对话
      </router-link>
      <router-link to="/files" class="app-nav-link" :class="{ active: route.path === '/files' }">
        文件管理
      </router-link>
    </div>
    <div class="app-nav-user">
      <span class="app-nav-user-name">{{ displayName }}</span>
      <el-button link type="primary" @click="logout">退出登录</el-button>
    </div>
  </nav>
</template>

<style scoped>
.app-nav-user {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
  padding-right: 20px;
}

.app-nav-user-name {
  color: #374151;
  font-size: 14px;
}
</style>
