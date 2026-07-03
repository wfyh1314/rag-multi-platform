<script setup>
import { ref, nextTick, watch } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  messages: { type: Array, required: true },
  models: { type: Array, required: true },
  selectedModel: { type: String, required: true },
  isStreaming: { type: Boolean, default: false },
  sessionTitle: { type: String, default: '新对话' },
})

const emit = defineEmits(['send', 'update:selectedModel'])

const inputText = ref('')
const messagesEl = ref(null)

marked.setOptions({ breaks: true })

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
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
    <header class="chat-header">
      <div class="header-left">
        <h1>基于知识库的智能问答 </h1>
        <!-- <p class="session-name">基于知识库的智能问答</p> -->
      </div>
      <div class="control-group model-select-group">
        <label for="model-select">LLM Model</label>
        <select
          id="model-select"
          class="select-box"
          :value="selectedModel"
          @change="emit('update:selectedModel', $event.target.value)"
        >
          <option v-for="model in models" :key="model.id" :value="model.id">
            {{ model.name }}
          </option>
        </select>
      </div>
    </header>

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
