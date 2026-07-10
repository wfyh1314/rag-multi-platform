<script setup>
import { ref } from 'vue'

defineProps({
  collections: { type: Array, required: true },
  pendingCollections: { type: Array, default: () => [] },
  selectedCollection: { type: String, required: true },
  maxLength: { type: Number, required: true },
  temperature: { type: Number, required: true },
  uploadStatus: { type: String, default: '' },
})

const emit = defineEmits([
  'update:selectedCollection',
  'update:maxLength',
  'update:temperature',
  'clear',
  'upload',
])

const isDragging = ref(false)
const fileInput = ref(null)

function onFileChange(e) {
  const file = e.target.files?.[0]
  if (file) emit('upload', file)
  e.target.value = ''
}

function onDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer.files?.[0]
  if (file) emit('upload', file)
}

function openFilePicker() {
  fileInput.value?.click()
}
</script>

<template>
  <aside class="info-sidebar">
    <div class="info-header">
      <h2>参数配置</h2>
    </div>

    <div class="info-content">
      <div class="info-section">
        <h3>模型回复最大长度</h3>
        <div class="slider-row">
          <input
            type="range"
            min="256"
            max="8000"
            step="256"
            :value="maxLength"
            @input="emit('update:maxLength', Number($event.target.value))"
          />
          <input
            type="number"
            class="slider-input"
            min="256"
            max="8000"
            step="256"
            :value="maxLength"
            @change="emit('update:maxLength', Number($event.target.value))"
          />
        </div>
      </div>

      <div class="info-section">
        <h3>温度</h3>
        <div class="slider-row">
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            :value="temperature"
            @input="emit('update:temperature', Number($event.target.value))"
          />
          <input
            type="number"
            class="slider-input"
            min="0"
            max="2"
            step="0.1"
            :value="temperature"
            @change="emit('update:temperature', Number($event.target.value))"
          />
        </div>
      </div>

      <button class="btn btn-secondary btn-full clear-btn" @click="emit('clear')">
        清除
      </button>

      <hr class="divider" />

      <div class="info-section">
        <h3>知识库</h3>
        <select
          class="select-box select-full"
          :value="selectedCollection"
          @change="emit('update:selectedCollection', $event.target.value)"
        >
          <option value="">不使用知识库</option>
          <option v-for="name in collections" :key="name" :value="name">
            {{ name }}
          </option>
          <option
            v-for="name in pendingCollections"
            :key="'pending-' + name"
            :value="name"
            disabled
          >
            {{ name }}（索引中...）
          </option>
        </select>
      </div>

      <div class="info-section">
        <h3>上传文件</h3>
        <input
          ref="fileInput"
          type="file"
          class="hidden-input"
          accept=".csv,.txt,.doc,.docx,.pdf,.md"
          @change="onFileChange"
        />
        <div
          class="upload-zone"
          :class="{ dragging: isDragging }"
          @click="openFilePicker"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="onDrop"
        >
          <div class="upload-icon">⬆</div>
          <p>将文件拖放到此处</p>
          <p class="upload-hint">- 或 - 点击上传</p>
        </div>
        <p v-if="uploadStatus" class="upload-status">{{ uploadStatus }}</p>
      </div>
    </div>
  </aside>
</template>
