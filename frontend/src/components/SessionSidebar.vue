<script setup>
defineProps({
  sessions: { type: Array, required: true },
  activeSessionId: { type: String, required: true },
})

const emit = defineEmits(['new-session', 'switch-session', 'delete-session'])
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h2>通用 RAG 助手</h2>
    </div>

    <button class="btn btn-primary btn-full" @click="emit('new-session')">
      + 新建对话
    </button>

    <div class="session-section">
      <h3>对话列表</h3>
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
          </button>
          <button
            class="btn btn-icon"
            title="删除对话"
            @click.stop="emit('delete-session', session.id)"
          >
            ×
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>
