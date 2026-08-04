<script setup>
import { ref, nextTick, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { FolderOpened, ChatDotRound, Promotion } from '@element-plus/icons-vue'

const props = defineProps({
  messages: { type: Array, required: true },
  isStreaming: { type: Boolean, default: false },
})

const emit = defineEmits(['send'])

const inputText = ref('')
const messagesEl = ref(null)

marked.setOptions({ breaks: true })

function renderMarkdown(text) {
  if (!text) return ''
  const rawHtml = marked.parse(text)
  return DOMPurify.sanitize(rawHtml, { USE_PROFILES: { html: true } })
}

function copyText(text) {
  navigator.clipboard.writeText(text).catch(() => {})
}

function handleSend() {
  if (!inputText.value.trim() || props.isStreaming) return
  emit('send', inputText.value)
  inputText.value = ''
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

watch(() => props.messages, scrollToBottom, { deep: true })
</script>

<template>
  <main class="chat-container">
    <div class="chat-panel-card">
      <div ref="messagesEl" class="chat-messages">
        <div v-if="!messages.length" class="empty-state">
          <div class="empty-state-deco empty-state-deco--left" />
          <div class="empty-state-deco empty-state-deco--right" />
          <div class="empty-state-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M4 6.5C4 5.12 5.12 4 6.5 4h11C18.88 4 20 5.12 20 6.5v7c0 1.38-1.12 2.5-2.5 2.5H9l-4.5 3v-3H6.5C5.12 16 4 14.88 4 13.5v-7Z"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linejoin="round"
              />
              <circle cx="9" cy="10" r="1" fill="currentColor" />
              <circle cx="12" cy="10" r="1" fill="currentColor" />
              <circle cx="15" cy="10" r="1" fill="currentColor" />
            </svg>
          </div>
          <p class="empty-state-text">开始提问，或上传文档到知识库</p>
        </div>

        <div
          v-for="msg in messages"
          :key="msg.id"
          class="message"
          :class="msg.role"
        >
          <div class="message-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
          <div class="message-content">
            <div
              v-if="msg.role === 'assistant'"
              class="markdown-body"
              v-html="renderMarkdown(msg.content)"
            />
            <template v-else>{{ msg.content }}</template>
            <button
              v-if="msg.content"
              class="copy-btn"
              title="复制"
              @click="copyText(msg.content)"
            >
              📋
            </button>
            <div
              v-if="msg.role === 'assistant' && msg.sources?.length"
              class="message-sources"
            >
              <p class="sources-title">引用来源（{{ msg.sources.length }}）</p>
              <ul class="sources-list">
                <li v-for="(src, idx) in msg.sources" :key="idx">
                  <span class="source-index">[{{ idx + 1 }}]</span>
                  <span v-if="src.metadata?.modality === 'image'" class="source-modality">[图片]</span>
                  {{ (src.content || '').slice(0, 120) }}{{ (src.content || '').length > 120 ? '…' : '' }}
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div v-if="isStreaming" class="loading">
          <span class="loading-dot" />
          <span class="loading-dot" />
          <span class="loading-dot" />
        </div>
      </div>

      <div class="chat-toolbar">
        <div class="chat-toolbar-left">
          <RouterLink to="/files" class="chat-toolbar-btn" title="文件上传">
            <el-icon><FolderOpened /></el-icon>
          </RouterLink>
        </div>
        <div class="chat-toolbar-right">
          <span class="chat-toolbar-btn" title="对话模式">
            <el-icon><ChatDotRound /></el-icon>
          </span>
        </div>
      </div>

      <div class="chat-input-container">
        <div class="chat-input-wrapper">
          <textarea
            v-model="inputText"
            class="chat-textarea"
            rows="1"
            placeholder="输入问题..."
            :disabled="isStreaming"
            @keydown="handleKeydown"
          />
          <button
            class="btn btn-send"
            :disabled="isStreaming || !inputText.trim()"
            @click="handleSend"
          >
            <el-icon><Promotion /></el-icon>
            <span>发送</span>
          </button>
        </div>
      </div>
    </div>
  </main>
</template>
