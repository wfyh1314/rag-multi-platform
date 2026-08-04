<script setup>
import { ref, nextTick, watch } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

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
    <div ref="messagesEl" class="chat-messages">
      <div v-if="!messages.length" class="empty-state">
        <div class="empty-state-icon">💬</div>
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

    <div class="chat-input-container">
      <div class="chat-input-wrapper">
        <input
          v-model="inputText"
          class="chat-input"
          type="text"
          placeholder="输入问题..."
          :disabled="isStreaming"
          @keydown="handleKeydown"
        />
        <button
          class="btn btn-send"
          :disabled="isStreaming || !inputText.trim()"
          @click="handleSend"
        >
          ➤
        </button>
      </div>
    </div>
  </main>
</template>
