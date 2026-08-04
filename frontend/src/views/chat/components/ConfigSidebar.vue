<script setup>
import { computed } from 'vue'
import { normalizeCollection } from '@/views/chat/composables/useChat'

const props = defineProps({
  models: { type: Array, required: true },
  selectedModel: { type: String, required: true },
  collections: { type: Array, required: true },
  pendingCollections: { type: Array, default: () => [] },
  selectedCollection: { type: String, required: true },
  tagCategories: { type: Array, default: () => [] },
  selectedTagIds: { type: Array, default: () => [] },
  chatMode: { type: String, default: 'stream' },
  maxLength: { type: Number, required: true },
  temperature: { type: Number, required: true },
})

const emit = defineEmits([
  'update:selectedModel',
  'update:selectedCollection',
  'update:selectedTagIds',
  'update:chatMode',
  'update:maxLength',
  'update:temperature',
  'clear',
])

const flatTags = computed(() => {
  const items = []
  for (const cat of props.tagCategories) {
    for (const tag of cat.tags || []) {
      items.push({
        id: tag.id,
        label: `${cat.name}: ${tag.name}`,
      })
    }
  }
  return items
})

function formatCollectionLabel(item) {
  const normalized = normalizeCollection(item)
  let scope = '私有'
  if (normalized.visibility === 'public') scope = '公共'
  else if (normalized.visibility === 'department') scope = '部门'
  return `${normalized.filename}（${scope}）`
}

function onTagChange(event) {
  const values = Array.from(event.target.selectedOptions).map((opt) => opt.value)
  emit('update:selectedTagIds', values)
}
</script>

<template>
  <aside class="info-sidebar">
    <div class="info-header">
      <h2>参数配置</h2>
    </div>

    <div class="info-content">
      <div class="info-section">
        <h3>问答模式</h3>
        <select
          class="select-box select-full"
          :value="chatMode"
          @change="emit('update:chatMode', $event.target.value)"
        >
          <option value="stream">流式 RAG（SSE）</option>
          <option value="agent">Agent（LangGraph 流式）</option>
        </select>
        <p class="tag-filter-hint">Agent 模式流式返回答案与引用来源</p>
      </div>

      <div class="info-section">
        <h3>LLM Model</h3>
        <select
          class="select-box select-full"
          :value="selectedModel"
          @change="emit('update:selectedModel', $event.target.value)"
        >
          <option v-for="model in models" :key="model.id" :value="model.id">
            {{ model.name }}
          </option>
        </select>
      </div>

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
          <option
            v-for="item in collections"
            :key="item.file_id"
            :value="item.file_id"
          >
            {{ formatCollectionLabel(item) }}
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
        <h3>标签筛选</h3>
        <select
          class="select-box select-full tag-filter-select"
          multiple
          :value="selectedTagIds"
          @change="onTagChange($event)"
        >
          <option v-for="tag in flatTags" :key="tag.id" :value="tag.id">
            {{ tag.label }}
          </option>
        </select>
        <p class="tag-filter-hint">按住 Ctrl 多选；不选则不过滤标签</p>
      </div>
    </div>
  </aside>
</template>
