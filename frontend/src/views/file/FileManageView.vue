<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { FolderOpened } from '@element-plus/icons-vue'
import { useFileList } from '@/views/file/composables/useFileList'
import { useFolderTree } from '@/views/file/composables/useFolderTree'
import { fetchFolderTree } from '@/views/file/api/folder'
import { fetchFilePreview } from '@/views/file/api/file'

const {
  folders,
  selectedFolderId,
  loading: folderLoading,
  loadFolders,
  selectFolder,
  handleCreate,
  handleRename,
  handleDeleteFolder,
} = useFolderTree(() => loadFiles())

const {
  filteredFiles,
  total,
  keyword,
  filterType,
  filterVisibility,
  filterStatus,
  fileTypeOptions,
  statusOptions,
  loading,
  error,
  uploadStatus,
  loadFiles,
  resetFilters,
  handleUpload,
  handleMove,
  handleDelete,
  formatTime,
  visibilityLabel,
  fileTypeLabel,
  statusLabel,
} = useFileList(() => selectedFolderId.value)

const uploadVisibility = ref('private')
const selectedFile = ref(null)
const uploading = ref(false)
const uploadRef = ref(null)
const moveDialogVisible = ref(false)
const moveTargetFolderId = ref('')
const movingFile = ref(null)
const moveLoading = ref(false)
const flatFolders = ref([])
const previewVisible = ref(false)
const previewLoading = ref(false)
const previewData = ref(null)

function flattenFolders(nodes, depth = 0) {
  const items = []
  for (const node of nodes || []) {
    items.push({ id: node.id, name: node.name, depth })
    items.push(...flattenFolders(node.children, depth + 1))
  }
  return items
}

async function refreshFlatFolders() {
  const tree = await fetchFolderTree()
  flatFolders.value = flattenFolders(tree)
}

function onFolderNodeClick(data) {
  selectFolder(data.id)
}

function showAllFiles() {
  selectFolder(null)
}

function showRootFiles() {
  selectFolder('')
}

async function confirmUpload() {
  if (!selectedFile.value || uploading.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  uploading.value = true
  try {
    const folderId = selectedFolderId.value || null
    const success = await handleUpload(
      selectedFile.value,
      uploadVisibility.value,
      folderId === '' ? null : folderId,
    )
    if (success) {
      clearUploadSelection()
    }
  } finally {
    uploading.value = false
  }
}

function onUploadChange(uploadFile) {
  selectedFile.value = uploadFile.raw
}

function onUploadExceed() {
  ElMessage.warning('每次仅支持上传一个文件')
}

function clearUploadSelection() {
  selectedFile.value = null
  uploadRef.value?.clearFiles()
}

function statusTagType(status) {
  if (status === 'indexed') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'pending' || status === 'parsing' || status === 'processing') return 'warning'
  return 'info'
}

function openMoveDialog(row) {
  movingFile.value = row
  moveTargetFolderId.value = row.folder_id || ''
  moveDialogVisible.value = true
  refreshFlatFolders()
}

async function confirmMove() {
  if (!movingFile.value || moveLoading.value) return
  moveLoading.value = true
  try {
    await handleMove(movingFile.value.file_id, moveTargetFolderId.value)
    moveDialogVisible.value = false
  } finally {
    moveLoading.value = false
  }
}

async function openPreview(row) {
  previewVisible.value = true
  previewLoading.value = true
  previewData.value = { filename: row.filename }
  try {
    previewData.value = await fetchFilePreview(row.file_id)
  } catch (err) {
    ElMessage.error(err.message || '预览失败')
    previewVisible.value = false
  } finally {
    previewLoading.value = false
  }
}

const currentFolderLabel = computed(() => {
  if (selectedFolderId.value === null) return '全部文件'
  if (selectedFolderId.value === '') return '根目录'
  const find = (nodes) => {
    for (const n of nodes) {
      if (n.id === selectedFolderId.value) return n.name
      const child = find(n.children || [])
      if (child) return child
    }
    return null
  }
  return find(folders.value) || '当前文件夹'
})

onMounted(async () => {
  await loadFolders()
  await refreshFlatFolders()
})
</script>

<template>
  <div class="file-manage-page">
    <header class="page-header">
      <h1 class="page-header-title">文件管理</h1>
      <p class="page-header-subtitle">
        支持文件夹组织、TXT/MD/PDF/DOC 等格式上传，自动解析并建立向量索引
      </p>
    </header>

    <div class="file-manage-layout">
      <aside class="folder-sidebar page-card">
        <div class="folder-sidebar-header">
          <h2 class="page-card-title">文件夹</h2>
        </div>
        <div class="folder-sidebar-actions">
          <el-button class="folder-create-btn" type="primary" @click="handleCreate(selectedFolderId || null)">
            新建文件夹
          </el-button>
        </div>
        <div class="folder-quick-nav">
          <el-button
            link
            :type="selectedFolderId === null ? 'primary' : 'default'"
            @click="showAllFiles"
          >
            全部文件
          </el-button>
          <el-button
            link
            :type="selectedFolderId === '' ? 'primary' : 'default'"
            @click="showRootFiles"
          >
            根目录
          </el-button>
        </div>
        <div class="folder-tree-scroll">
          <el-tree
            v-loading="folderLoading"
            :data="folders"
            node-key="id"
            :props="{ label: 'name', children: 'children' }"
            highlight-current
            default-expand-all
          >
            <template #default="{ data }">
              <div class="folder-tree-row">
                <span class="folder-tree-node" @click="onFolderNodeClick(data)">
                  <el-icon><FolderOpened /></el-icon>
                  <span>{{ data.name }}</span>
                </span>
                <el-dropdown trigger="click" @command="(cmd) => cmd === 'rename' ? handleRename(data) : handleDeleteFolder(data)">
                  <el-button link size="small" class="folder-tree-more" @click.stop>⋯</el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="rename">重命名</el-dropdown-item>
                      <el-dropdown-item command="delete">删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
          </el-tree>
        </div>
      </aside>

      <div class="file-manage-main">
        <p v-if="uploadStatus" class="upload-status">{{ uploadStatus }}</p>
        <el-alert
          v-if="error"
          :title="error"
          type="error"
          show-icon
          :closable="false"
          class="file-alert"
        />

        <section class="page-card file-upload-card">
          <h2 class="page-card-title">上传文件</h2>
          <p class="upload-folder-hint">当前目录：{{ currentFolderLabel }}</p>
          <div class="upload-form-row">
            <label class="upload-form-label">
              文档类型
              <span class="required-mark">*</span>
            </label>
            <el-select
              v-model="uploadVisibility"
              class="upload-visibility-select"
              placeholder="请选择文档类型"
              :disabled="uploading"
            >
              <el-option label="私有文档（仅自己可见）" value="private" />
              <el-option label="部门文档（同部门可见）" value="department" />
              <el-option label="共享知识库（全员可见）" value="public" />
            </el-select>
          </div>

          <el-upload
            ref="uploadRef"
            drag
            class="inline-upload"
            :auto-upload="false"
            :limit="1"
            accept=".csv,.txt,.doc,.docx,.pdf,.md"
            :disabled="uploading"
            :on-change="onUploadChange"
            :on-exceed="onUploadExceed"
          >
            <div class="inline-upload-content">
              <div class="inline-upload-icon">↑</div>
              <p class="inline-upload-text">拖拽文件到此处 或 点击选择文件</p>
              <p class="inline-upload-hint">支持 csv、txt、doc、docx、pdf、md</p>
            </div>
          </el-upload>

          <div class="upload-actions">
            <el-button :disabled="uploading" @click="clearUploadSelection">清空</el-button>
            <el-button
              type="primary"
              :loading="uploading"
              :disabled="!selectedFile"
              @click="confirmUpload"
            >
              开始上传
            </el-button>
          </div>
        </section>

        <section class="page-card file-list-card">
          <div class="file-list-card-header">
            <h2 class="page-card-title">已导入文档 · {{ currentFolderLabel }}</h2>
          </div>

          <div class="filter-bar">
            <el-input
              v-model="keyword"
              placeholder="搜索文档名称..."
              clearable
              class="filter-item filter-search"
            />
            <el-select v-model="filterType" clearable placeholder="所有类型" class="filter-item">
              <el-option label="所有类型" value="" />
              <el-option
                v-for="type in fileTypeOptions"
                :key="type"
                :label="type"
                :value="type"
              />
            </el-select>
            <el-select
              v-model="filterVisibility"
              clearable
              placeholder="所有可见性"
              class="filter-item"
            >
              <el-option label="所有可见性" value="" />
              <el-option label="私有" value="private" />
              <el-option label="部门" value="department" />
              <el-option label="公共" value="public" />
            </el-select>
            <el-select v-model="filterStatus" clearable placeholder="所有状态" class="filter-item">
              <el-option label="所有状态" value="" />
              <el-option
                v-for="status in statusOptions"
                :key="status"
                :label="statusLabel(status)"
                :value="status"
              />
            </el-select>
            <el-button @click="resetFilters">重置</el-button>
          </div>

          <div class="file-table-wrapper">
            <el-table
              v-loading="loading"
              :data="filteredFiles"
              stripe
              style="width: 100%"
              empty-text="暂无文件，请上传"
            >
              <el-table-column prop="filename" label="文档名称" min-width="200" show-overflow-tooltip />
              <el-table-column label="类型" width="80" align="center">
                <template #default="{ row }">{{ fileTypeLabel(row.filename) }}</template>
              </el-table-column>
              <el-table-column label="可见性" width="80" align="center">
                <template #default="{ row }">{{ visibilityLabel(row.visibility) }}</template>
              </el-table-column>
              <el-table-column label="状态" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="statusTagType(row.status)" size="small">
                    {{ statusLabel(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="标签" min-width="160">
                <template #default="{ row }">
                  <span v-if="!row.tags?.length">-</span>
                  <div v-else class="file-tag-list">
                    <el-tag v-for="tag in row.tags" :key="tag.tag_id" size="small">
                      {{ tag.label }}
                    </el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="chunk_count" label="分块" width="70" align="center">
                <template #default="{ row }">{{ row.chunk_count ?? '-' }}</template>
              </el-table-column>
              <el-table-column label="创建时间" min-width="160">
                <template #default="{ row }">{{ formatTime(row.uploaded_at) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="180" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" link @click="openPreview(row)">预览</el-button>
                  <el-button type="primary" link @click="openMoveDialog(row)">移动</el-button>
                  <el-button type="danger" link @click="handleDelete(row.file_id, row.filename)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <p class="file-list-count">共 {{ filteredFiles.length }} / {{ total }} 个文档</p>
          </div>
        </section>
      </div>
    </div>

    <el-dialog v-model="previewVisible" :title="previewData?.filename || '文件预览'" width="640px" destroy-on-close>
      <div v-loading="previewLoading" class="preview-dialog-body">
        <pre v-if="previewData?.preview" class="preview-text">{{ previewData.preview }}</pre>
        <p v-else class="preview-empty">暂无预览内容</p>
        <p v-if="previewData?.chunk_count" class="preview-meta">共 {{ previewData.chunk_count }} 个分块</p>
      </div>
    </el-dialog>

    <el-dialog v-model="moveDialogVisible" title="移动文件" width="420px" destroy-on-close>
      <p v-if="movingFile" class="move-dialog-hint">将「{{ movingFile.filename }}」移动到：</p>
      <el-select v-model="moveTargetFolderId" placeholder="根目录" clearable class="move-folder-select">
        <el-option label="根目录" value="" />
        <el-option
          v-for="item in flatFolders"
          :key="item.id"
          :label="`${'　'.repeat(item.depth)}${item.name}`"
          :value="item.id"
          :disabled="item.id === movingFile?.file_id"
        />
      </el-select>
      <template #footer>
        <el-button @click="moveDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="moveLoading" @click="confirmMove">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
