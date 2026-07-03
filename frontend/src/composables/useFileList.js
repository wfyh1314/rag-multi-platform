import { ref, watch, onMounted } from 'vue'
import { fetchFiles, uploadFile } from '@/api/file'

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
    formatTime,
  }
}
