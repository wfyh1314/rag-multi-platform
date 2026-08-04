<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ChatDotRound, CollectionTag, Upload, Document, User } from '@element-plus/icons-vue'
import { useAuth } from '@/composables/useAuth'

const route = useRoute()
const { user, logout, initAuth } = useAuth()

const displayName = computed(() => user.value?.real_name || user.value?.username || '用户')

onMounted(() => {
  initAuth()
})
</script>

<template>
  <aside class="app-sidebar">
    <div class="app-sidebar-brand">
      <div class="app-sidebar-logo">RAG</div>
      <span class="app-sidebar-title">通用 RAG 知识库</span>
    </div>

    <nav class="app-sidebar-nav">
      <div class="app-sidebar-section">
        <div class="app-sidebar-section-title">知识库管理</div>
        <router-link
          to="/files"
          class="app-sidebar-link"
          :class="{ active: route.meta.menu === 'files' }"
        >
          <el-icon class="app-sidebar-link-icon"><Upload /></el-icon>
          <span>文件上传</span>
        </router-link>
        <router-link
          to="/tags"
          class="app-sidebar-link"
          :class="{ active: route.meta.menu === 'tags' }"
        >
          <el-icon class="app-sidebar-link-icon"><CollectionTag /></el-icon>
          <span>打标签</span>
        </router-link>
        <router-link
          to="/audit"
          class="app-sidebar-link"
          :class="{ active: route.meta.menu === 'audit' }"
        >
          <el-icon class="app-sidebar-link-icon"><Document /></el-icon>
          <span>审计日志</span>
        </router-link>
      </div>

      <div class="app-sidebar-section">
        <div class="app-sidebar-section-title">工作区管理</div>
        <router-link
          to="/"
          class="app-sidebar-link"
          :class="{ active: route.meta.menu === 'workspace' }"
        >
          <el-icon class="app-sidebar-link-icon"><ChatDotRound /></el-icon>
          <span>工作区</span>
        </router-link>
      </div>
    </nav>

    <div class="app-sidebar-footer">
      <router-link to="/profile" class="app-sidebar-profile-link">
        <el-icon><User /></el-icon>
        <span>{{ displayName }}</span>
      </router-link>
      <el-button link type="primary" @click="logout">退出登录</el-button>
    </div>
  </aside>
</template>
