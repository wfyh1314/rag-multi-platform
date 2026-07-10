<script setup>
import { ref } from 'vue'
import { useFileList } from '@/views/file/composables/useFileList'

const {
  files,
  total,
  keyword,
  loading,
  error,
  uploadStatus,
  loadFiles,
  handleUpload,
  handleDelete,
  formatTime,
} = useFileList()

const fileInput = ref(null)

function onFileChange(e) {
  const file = e.target.files?.[0]
  if (file) handleUpload(file)
  e.target.value = ''
}

function openFilePicker() {
  fileInput.value?.click()
}

function statusTagType(status) {
  return status === 'indexed' ? 'success' : 'info'
}
</script>

<template>
  <div class="file-manage-page">
    <header class="file-manage-header">
      <div class="file-manage-title">
        <h1>文件管理</h1>
        <span class="file-count">共 {{ total }} 个文件</span>
      </div>
      <div class="search-bar">
        <el-input
          v-model="keyword"
          placeholder="搜索文件名..."
          clearable
          style="width: 240px"
        />
        <el-button :loading="loading" @click="loadFiles">刷新</el-button>
        <input
          ref="fileInput"
          type="file"
          class="hidden-input"
          accept=".csv,.txt,.doc,.docx,.pdf,.md"
          @change="onFileChange"
        />
        <el-button type="primary" @click="openFilePicker">上传文件</el-button>
      </div>
    </header>

    <p v-if="uploadStatus" class="upload-status">{{ uploadStatus }}</p>
    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" class="file-alert" />

    <div class="file-table-wrapper">
      <el-table
        v-loading="loading"
        :data="files"
        stripe
        border
        style="width: 100%"
        empty-text="暂无文件，请上传"
      >
        <el-table-column prop="filename" label="文件名" min-width="180" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="分块数" width="90" align="center">
          <template #default="{ row }">
            {{ row.chunk_count ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column label="上传时间" min-width="170">
          <template #default="{ row }">
            {{ formatTime(row.uploaded_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="file_id" label="文件 ID" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="danger"
              link
              @click="handleDelete(row.file_id, row.filename)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>
