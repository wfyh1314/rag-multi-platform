<script setup>
import { onMounted } from 'vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import SessionSidebar from '@/views/chat/components/SessionSidebar.vue'
import { useAppSidebarCollapse } from '@/composables/useAppSidebarCollapse'
import ChatPanel from '@/views/chat/components/ChatPanel.vue'
import ConfigSidebar from '@/views/chat/components/ConfigSidebar.vue'
import { useChat } from '@/views/chat/composables/useChat'

const {
  sessions,
  activeSessionId,
  messages,
  models,
  collections,
  selectedModel,
  selectedCollection,
  selectedTagIds,
  tagCategories,
  maxLength,
  temperature,
  chatMode,
  isStreaming,
  pendingCollections,
  init,
  newSession,
  switchSession,
  deleteSession,
  archiveSession,
  toggleShowArchived,
  showArchived,
  sendMessage,
  handleClear,
} = useChat()

const { collapsed: appSidebarCollapsed, toggle: toggleAppSidebar } = useAppSidebarCollapse()

onMounted(() => {
  init()
})
</script>

<template>
  <div class="app-container">
    <div class="session-sidebar-wrap">
      <SessionSidebar
        :sessions="sessions"
        :active-session-id="activeSessionId"
        :show-archived="showArchived"
        @new-session="newSession"
        @switch-session="switchSession"
        @delete-session="deleteSession"
        @archive-session="archiveSession"
        @toggle-archived="toggleShowArchived"
      />
      <button
        type="button"
        class="session-sidebar-toggle"
        :title="appSidebarCollapsed ? '展开菜单' : '收起菜单'"
        @click="toggleAppSidebar"
      >
        <el-icon>
          <ArrowRight v-if="appSidebarCollapsed" />
          <ArrowLeft v-else />
        </el-icon>
      </button>
    </div>

    <ChatPanel
      :messages="messages"
      :is-streaming="isStreaming"
      @send="sendMessage"
    />

    <ConfigSidebar
      :models="models"
      v-model:selected-model="selectedModel"
      :collections="collections"
      :pending-collections="pendingCollections"
      v-model:selected-collection="selectedCollection"
      v-model:selected-tag-ids="selectedTagIds"
      v-model:chat-mode="chatMode"
      :tag-categories="tagCategories"
      v-model:max-length="maxLength"
      v-model:temperature="temperature"
      @clear="handleClear"
    />
  </div>
</template>
