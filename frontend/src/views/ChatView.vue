<script setup>
import { onMounted } from 'vue'
import SessionSidebar from '@/components/SessionSidebar.vue'
import ChatPanel from '@/components/ChatPanel.vue'
import ConfigSidebar from '@/components/ConfigSidebar.vue'
import { useChat } from '@/composables/useChat'

const {
  sessions,
  activeSessionId,
  activeSession,
  messages,
  models,
  collections,
  selectedModel,
  selectedCollection,
  maxLength,
  temperature,
  isStreaming,
  uploadStatus,
  pendingCollections,
  init,
  newSession,
  switchSession,
  deleteSession,
  sendMessage,
  handleClear,
  handleUpload,
} = useChat()

onMounted(() => {
  init()
})
</script>

<template>
  <div class="app-container">
    <SessionSidebar
      :sessions="sessions"
      :active-session-id="activeSessionId"
      @new-session="newSession"
      @switch-session="switchSession"
      @delete-session="deleteSession"
    />

    <ChatPanel
      :messages="messages"
      :models="models"
      v-model:selected-model="selectedModel"
      :is-streaming="isStreaming"
      :session-title="activeSession?.title || '新对话'"
      @send="sendMessage"
    />

    <ConfigSidebar
      :collections="collections"
      :pending-collections="pendingCollections"
      v-model:selected-collection="selectedCollection"
      v-model:max-length="maxLength"
      v-model:temperature="temperature"
      :upload-status="uploadStatus"
      @clear="handleClear"
      @upload="handleUpload"
    />
  </div>
</template>
