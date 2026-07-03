<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
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
  </nav>
</template>
