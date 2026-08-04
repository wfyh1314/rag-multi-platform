<script setup>
import { computed, onMounted } from 'vue'
import { useDocumentTags } from '@/views/tag/composables/useDocumentTags'

const props = defineProps({
  tagOptions: { type: Array, default: () => [] },
})

const {
  files,
  loading,
  rerunning,
  saving,
  error,
  selectedFileId,
  selectedFile,
  selectedTagIds,
  loadFiles,
  selectFile,
  saveSelectedTags,
  batchRerun,
  statusLabel,
  statusTagType,
} = useDocumentTags()

const autoTags = computed(() =>
  (selectedFile.value?.tags || []).filter((tag) => tag.source === 'auto')
)

onMounted(() => {
  loadFiles()
})

defineExpose({ loadFiles })
</script>

<template>
  <section class="page-card tag-document-panel">
    <div class="tag-panel-header">
      <h2 class="page-card-title">文档标签</h2>
      <div class="tag-panel-actions">
        <el-button :loading="rerunning" @click="batchRerun">批量重跑标签</el-button>
        <el-button :loading="loading" @click="loadFiles">刷新</el-button>
      </div>
    </div>

    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      :closable="false"
      class="tag-alert"
    />

    <div v-if="selectedFile" class="tag-selected-panel">
      <div class="tag-selected-header">
        <strong>{{ selectedFile.filename }}</strong>
        <el-button type="primary" size="small" :loading="saving" @click="saveSelectedTags">
          保存手动标签
        </el-button>
      </div>

      <div v-if="autoTags.length" class="tag-chip-group">
        <span class="tag-chip-label">自动标签</span>
        <el-tag v-for="tag in autoTags" :key="tag.tag_id" size="small" type="info">
          {{ tag.label }}
        </el-tag>
      </div>

      <div class="tag-manual-form">
        <span class="tag-chip-label">手动标签</span>
        <el-select
          v-model="selectedTagIds"
          multiple
          filterable
          collapse-tags
          collapse-tags-tooltip
          placeholder="选择要手动添加的标签"
          class="tag-manual-select"
        >
          <el-option
            v-for="option in tagOptions"
            :key="option.id"
            :label="option.label"
            :value="option.id"
          />
        </el-select>
      </div>
    </div>
    <p v-else class="tag-select-hint">从下方选择文档查看/管理标签</p>

    <div v-loading="loading" class="tag-document-list">
      <el-empty v-if="!loading && !files.length" description="暂无文档" />

      <button
        v-for="file in files"
        :key="file.file_id"
        type="button"
        class="tag-document-item"
        :class="{ 'tag-document-item--active': file.file_id === selectedFileId }"
        @click="selectFile(file)"
      >
        <div class="tag-document-item-header">
          <span class="tag-document-name">{{ file.filename }}</span>
          <el-tag :type="statusTagType(file.status)" size="small">
            {{ statusLabel(file.status) }}
          </el-tag>
        </div>
        <div v-if="file.tags?.length" class="tag-document-tags">
          <el-tag v-for="tag in file.tags" :key="tag.tag_id" size="small">
            {{ tag.label }}
          </el-tag>
        </div>
      </button>
    </div>
  </section>
</template>
