import { ref, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchFiles, uploadFile, deleteFile } from '@/api/file'

function debounce(fn, delay) {
  let timer = null
  return (...args) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}

export function useFileList() {
  const files = ref([])
  const total = ref(0)
  const keyword = ref('')
  const loading = ref(false)
  const error = ref('')
  const uploadStatus = ref('')

  async function loadFiles() {
    loading.value = true
    error.value = ''
    try {
      const data = await fetchFiles(keyword.value)
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

  async function handleUpload(file) {
    if (!file) return
    uploadStatus.value = '上传中...'
    try {
      const result = await uploadFile(file)
      if (result.status === 'indexed') {
        uploadStatus.value = `上传成功: ${result.filename}（${result.chunk_count ?? 0} 块）`
        await loadFiles()
      } else {
        uploadStatus.value = result.message || '上传失败'
      }
    } catch (err) {
      uploadStatus.value = `上传失败: ${err.message}`
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

  onMounted(() => {
    loadFiles()
  })

  return {
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
  }
}
