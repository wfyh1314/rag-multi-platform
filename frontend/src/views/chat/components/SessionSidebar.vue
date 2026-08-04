<script setup>
import { Box, Delete } from '@element-plus/icons-vue'

defineProps({
  sessions: { type: Array, required: true },
  activeSessionId: { type: String, required: true },
  showArchived: { type: Boolean, default: false },
})

const emit = defineEmits([
  'new-session',
  'switch-session',
  'delete-session',
  'archive-session',
  'toggle-archived',
])
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h2>通用 RAG 助手</h2>
    </div>

    <button class="btn btn-gradient btn-full" @click="emit('new-session')">
      + 新增对话
    </button>

    <div class="session-toolbar">
      <button type="button" class="session-archive-link" @click="emit('toggle-archived')">
        {{ showArchived ? '隐藏归档' : '显示归档' }}
      </button>
    </div>

    <div class="session-section">
      <h3>{{ showArchived ? '已归档对话' : '对话列表' }}</h3>
      <div class="session-list">
        <div
          v-for="session in sessions"
          :key="session.id"
          class="session-item"
        >
          <button
            class="session-btn"
            :class="{ 'btn-active': session.id === activeSessionId }"
            :title="session.title"
            @click="emit('switch-session', session.id)"
          >
            <span class="session-title">{{ session.title }}</span>
            <span v-if="session.isArchived" class="session-archived-tag">归档</span>
          </button>
          <button
            v-if="!showArchived"
            type="button"
            class="session-action-btn"
            title="归档对话"
            @click.stop="emit('archive-session', session.id)"
          >
            <el-icon><Box /></el-icon>
          </button>
          <button
            type="button"
            class="session-action-btn"
            title="删除对话"
            @click.stop="emit('delete-session', session.id)"
          >
            <el-icon><Delete /></el-icon>
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>
