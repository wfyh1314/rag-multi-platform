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

const maxLengthOptions = [
  { value: 512, label: '512' },
  { value: 1024, label: '1024' },
  { value: 2048, label: '2048' },
  { value: 4096, label: '4096' },
  { value: 8000, label: '8000' },
]

const chatModeOptions = [
  { value: 'stream', label: '流式 RAG（SSE）' },
  { value: 'agent', label: 'Agent（LangGraph 流式）' },
]

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

const collectionOptions = computed(() => {
  const items = props.collections.map((item) => {
    const normalized = normalizeCollection(item)
    let scope = '私有'
    if (normalized.visibility === 'public') scope = '公共'
    else if (normalized.visibility === 'department') scope = '部门'
    return {
      value: normalized.file_id,
      label: `${normalized.filename}（${scope}）`,
    }
  })
  return [{ value: '', label: '全部知识库（自动检索）' }, ...items]
})

const permissionScopeText = computed(() => {
  if (!props.selectedCollection) {
    return '将自动检索您有权限访问的全部知识库'
  }
  const item = props.collections.find(
    (c) => normalizeCollection(c).file_id === props.selectedCollection,
  )
  if (!item) return '所选知识库不可用或索引中'
  const visibility = normalizeCollection(item).visibility || 'private'
  const map = {
    private: '私有 — 仅上传者可检索',
    department: '部门 — 同部门成员可检索',
    public: '公共 — 全员可检索',
  }
  return map[visibility] || visibility
})
</script>

<template>
  <aside class="info-sidebar">
    <div class="info-header">
      <h2>参数配置</h2>
    </div>

    <div class="info-content">
      <section class="panel-card config-panel-card">
        <h3 class="config-panel-title">模型设置</h3>
        <div class="config-field">
          <label class="config-field-label">问答模式</label>
          <el-select
            :model-value="chatMode"
            placeholder="选择模式"
            @update:model-value="emit('update:chatMode', $event)"
          >
            <el-option
              v-for="opt in chatModeOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </div>
        <div class="config-field">
          <label class="config-field-label">LLM 模型</label>
          <el-select
            :model-value="selectedModel"
            placeholder="选择模型"
            @update:model-value="emit('update:selectedModel', $event)"
          >
            <el-option
              v-for="model in models"
              :key="model.id"
              :label="model.name"
              :value="model.id"
            />
          </el-select>
        </div>
        <div class="config-field">
          <label class="config-field-label">最大输出长度</label>
          <el-select
            :model-value="maxLength"
            @update:model-value="emit('update:maxLength', Number($event))"
          >
            <el-option
              v-for="opt in maxLengthOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </div>
      </section>

      <section class="panel-card config-panel-card">
        <h3 class="config-panel-title">生成参数</h3>
        <div class="config-field">
          <label class="config-field-label">温度：{{ temperature }}</label>
          <el-slider
            :model-value="temperature"
            :min="0"
            :max="2"
            :step="0.1"
            @update:model-value="emit('update:temperature', $event)"
          />
        </div>
        <div class="config-field">
          <label class="config-field-label">标签筛选</label>
          <el-select
            :model-value="selectedTagIds"
            multiple
            collapse-tags
            collapse-tags-tooltip
            placeholder="不选则不过滤"
            @update:model-value="emit('update:selectedTagIds', $event)"
          >
            <el-option
              v-for="tag in flatTags"
              :key="tag.id"
              :label="tag.label"
              :value="tag.id"
            />
          </el-select>
        </div>
      </section>

      <section class="panel-card config-panel-card">
        <h3 class="config-panel-title">检索设置</h3>
        <div class="config-field">
          <label class="config-field-label">知识库</label>
          <el-select
            :model-value="selectedCollection"
            placeholder="选择知识库"
            :clearable="false"
            @update:model-value="emit('update:selectedCollection', $event)"
          >
            <el-option
              v-for="opt in collectionOptions"
              :key="opt.value || 'none'"
              :label="opt.label"
              :value="opt.value"
            />
            <el-option
              v-for="name in pendingCollections"
              :key="'pending-' + name"
              :label="`${name}（索引中...）`"
              :value="name"
              disabled
            />
          </el-select>
        </div>
        <div class="config-field">
          <label class="config-field-label">权限范围配置</label>
          <el-input
            :model-value="permissionScopeText"
            type="textarea"
            :rows="2"
            readonly
            resize="none"
          />
        </div>
      </section>

      <div class="config-clear-link">
        <el-button link type="primary" @click="emit('clear')">清空当前会话</el-button>
      </div>
    </div>
  </aside>
</template>
