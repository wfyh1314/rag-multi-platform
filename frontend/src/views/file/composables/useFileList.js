import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchFiles, uploadFile, deleteFile } from '@/views/file/api/file'
import { moveFileToFolder } from '@/views/file/api/folder'

const PROCESSING_STATUSES = new Set(['pending', 'parsing', 'processing'])
const POLL_INTERVAL_MS = 3000
const POLL_MAX_ATTEMPTS = 60

function debounce(fn, delay) {
  let timer = null
  return (...args) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}

function getFileExtension(filename) {
  if (!filename) return ''
  const idx = filename.lastIndexOf('.')
  if (idx === -1) return ''
  return filename.slice(idx + 1).toLowerCase()
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export function useFileList(getFolderId = () => null) {
  const files = ref([])
  const total = ref(0)
  const keyword = ref('')
  const filterType = ref('')
  const filterVisibility = ref('')
  const filterStatus = ref('')
  const loading = ref(false)
  const error = ref('')
  const uploadStatus = ref('')
  const pollingFileIds = ref(new Set())
  let backgroundPollTimer = null

  async function loadFiles() {
    loading.value = true
    error.value = ''
    try {
      const folderId = getFolderId()
      const params = { keyword: keyword.value || undefined }
      if (folderId !== null) {
        params.folder_id = folderId
      }
      const data = await fetchFiles(params)
      files.value = data.files || []
      total.value = data.total ?? files.value.length
    } catch (err) {
      error.value = err.message || '加载失败'
      files.value = []
      total.value = 0
    } finally {
      loading.value = false
    }
  }

  const debouncedLoad = debounce(loadFiles, 300)

  watch(keyword, () => {
    debouncedLoad()
  })

  const filteredFiles = computed(() => {
    return files.value.filter((file) => {
      if (filterType.value && getFileExtension(file.filename) !== filterType.value) {
        return false
      }
      if (filterVisibility.value && file.visibility !== filterVisibility.value) {
        return false
      }
      if (filterStatus.value && file.status !== filterStatus.value) {
        return false
      }
      return true
    })
  })

  const fileTypeOptions = computed(() => {
    const types = new Set(files.value.map((f) => getFileExtension(f.filename)).filter(Boolean))
    return Array.from(types).sort()
  })

  const statusOptions = computed(() => {
    const statuses = new Set(files.value.map((f) => f.status).filter(Boolean))
    return Array.from(statuses).sort()
  })

  function resetFilters() {
    keyword.value = ''
    filterType.value = ''
    filterVisibility.value = ''
    filterStatus.value = ''
    loadFiles()
  }

  function findFileById(fileId) {
    return files.value.find((file) => file.file_id === fileId)
  }

  async function pollFileUntilSettled(fileId, filename) {
    if (pollingFileIds.value.has(fileId)) return
    pollingFileIds.value.add(fileId)

    try {
      for (let attempt = 0; attempt < POLL_MAX_ATTEMPTS; attempt += 1) {
        await sleep(POLL_INTERVAL_MS)
        await loadFiles()
        const file = findFileById(fileId)
        if (!file) continue

        if (file.status === 'indexed') {
          uploadStatus.value = `解析完成: ${filename}（${file.chunk_count ?? 0} 块）`
          ElMessage.success(`「${filename}」索引完成`)
          return true
        }
        if (file.status === 'failed') {
          uploadStatus.value = file.message || `解析失败: ${filename}`
          ElMessage.error(`「${filename}」解析失败`)
          return false
        }
        uploadStatus.value = `解析中: ${filename}（${statusLabel(file.status)}）...`
      }
      uploadStatus.value = `解析超时，请稍后刷新列表: ${filename}`
      ElMessage.warning(`「${filename}」解析时间较长，请稍后刷新列表查看状态`)
      return false
    } finally {
      pollingFileIds.value.delete(fileId)
    }
  }

  async function pollProcessingFilesInList() {
    const pending = files.value.filter((file) => PROCESSING_STATUSES.has(file.status))
    await Promise.all(
      pending.map((file) => pollFileUntilSettled(file.file_id, file.filename)),
    )
  }

  function startBackgroundPolling() {
    if (backgroundPollTimer) return
    backgroundPollTimer = setInterval(async () => {
      const hasProcessing = files.value.some((file) => PROCESSING_STATUSES.has(file.status))
      if (!hasProcessing) return
      await loadFiles()
      await pollProcessingFilesInList()
    }, POLL_INTERVAL_MS)
  }

  function stopBackgroundPolling() {
    if (backgroundPollTimer) {
      clearInterval(backgroundPollTimer)
      backgroundPollTimer = null
    }
  }

  async function handleUpload(file, visibility = 'private', folderId = null) {
    if (!file) return false
    uploadStatus.value = '上传中...'
    try {
      const result = await uploadFile(file, visibility, folderId)
      if (result.status === 'indexed') {
        uploadStatus.value = `上传成功: ${result.filename}（${result.chunk_count ?? 0} 块）`
        await loadFiles()
        return true
      }
      if (PROCESSING_STATUSES.has(result.status)) {
        uploadStatus.value = `已提交后台解析: ${result.filename}`
        await loadFiles()
        await pollFileUntilSettled(result.file_id, result.filename)
        return true
      }
      uploadStatus.value = result.message || '上传失败'
      return false
    } catch (err) {
      uploadStatus.value = `上传失败: ${err.message}`
      return false
    }
  }

  async function handleMove(fileId, folderId) {
    if (!fileId) return
    loading.value = true
    try {
      await moveFileToFolder(fileId, folderId ?? '')
      ElMessage.success('文件已移动')
      await loadFiles()
    } catch (err) {
      ElMessage.error(err.message || '移动失败')
    } finally {
      loading.value = false
    }
  }

  async function handleDelete(fileId, filename) {
    if (!fileId) return
    try {
      await ElMessageBox.confirm(
        `确定删除「${filename}」？将同时删除本地文件与向量索引，且不可恢复。`,
        '删除确认',
        {
          type: 'warning',
          confirmButtonText: '删除',
          cancelButtonText: '取消',
          confirmButtonClass: 'el-button--danger',
        },
      )
    } catch {
      return
    }

    loading.value = true
    error.value = ''
    try {
      await deleteFile(fileId)
      ElMessage.success('文件已删除')
      await loadFiles()
    } catch (err) {
      const msg = err.message || '删除失败'
      error.value = msg
      ElMessage.error(msg)
    } finally {
      loading.value = false
    }
  }

  function formatTime(iso) {
    if (!iso) return '-'
    try {
      return new Date(iso).toLocaleString('zh-CN')
    } catch {
      return iso
    }
  }

  function visibilityLabel(value) {
    if (value === 'public') return '公共'
    if (value === 'department') return '部门'
    return '私有'
  }

  function fileTypeLabel(filename) {
    const ext = getFileExtension(filename)
    return ext || '-'
  }

  function statusLabel(status) {
    if (status === 'indexed') return '已索引'
    if (status === 'failed') return '失败'
    if (status === 'pending') return '等待解析'
    if (status === 'parsing') return '解析中'
    if (status === 'processing') return '处理中'
    return status || '-'
  }

  onMounted(async () => {
    await loadFiles()
    await pollProcessingFilesInList()
    startBackgroundPolling()
  })

  onBeforeUnmount(() => {
    stopBackgroundPolling()
  })

  return {
    files,
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
  }
}
