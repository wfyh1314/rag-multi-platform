import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  fetchFilesWithTags,
  fetchFileTags,
  updateFileTags,
  rerunFileTags,
} from '@/views/tag/api/tag'

export function useDocumentTags() {
  const files = ref([])
  const total = ref(0)
  const keyword = ref('')
  const loading = ref(false)
  const rerunning = ref(false)
  const saving = ref(false)
  const error = ref('')
  const selectedFileId = ref('')
  const selectedFile = ref(null)
  const selectedTagIds = ref([])

  async function loadFiles() {
    loading.value = true
    error.value = ''
    try {
      const data = await fetchFilesWithTags(keyword.value)
      files.value = data.files || []
      total.value = data.total ?? files.value.length

      if (selectedFileId.value) {
        const current = files.value.find((item) => item.file_id === selectedFileId.value)
        if (current) {
          selectedFile.value = current
          selectedTagIds.value = (current.tags || [])
            .filter((tag) => tag.source === 'manual')
            .map((tag) => tag.tag_id)
        } else {
          clearSelection()
        }
      }
    } catch (err) {
      error.value = err.message || '加载文档列表失败'
      files.value = []
      total.value = 0
    } finally {
      loading.value = false
    }
  }

  function clearSelection() {
    selectedFileId.value = ''
    selectedFile.value = null
    selectedTagIds.value = []
  }

  async function selectFile(file) {
    selectedFileId.value = file.file_id
    selectedFile.value = file
    try {
      const data = await fetchFileTags(file.file_id)
      selectedTagIds.value = (data.tags || [])
        .filter((tag) => tag.source === 'manual')
        .map((tag) => tag.tag_id)
    } catch (err) {
      ElMessage.error(err.message || '加载文档标签失败')
    }
  }

  async function saveSelectedTags() {
    if (!selectedFileId.value || saving.value) return
    saving.value = true
    try {
      await updateFileTags(selectedFileId.value, selectedTagIds.value)
      ElMessage.success('标签已保存')
      await loadFiles()
    } catch (err) {
      ElMessage.error(err.message || '保存失败')
    } finally {
      saving.value = false
    }
  }

  async function batchRerun() {
    if (rerunning.value) return
    rerunning.value = true
    try {
      const data = await rerunFileTags()
      ElMessage.success(`重跑完成：${data.success_count}/${data.total}`)
      await loadFiles()
    } catch (err) {
      ElMessage.error(err.message || '批量重跑失败')
    } finally {
      rerunning.value = false
    }
  }

  function statusLabel(status) {
    if (status === 'indexed') return '已索引'
    if (status === 'failed') return '失败'
    return '已上传'
  }

  function statusTagType(status) {
    if (status === 'indexed') return 'success'
    if (status === 'failed') return 'danger'
    return 'info'
  }

  return {
    files,
    total,
    keyword,
    loading,
    rerunning,
    saving,
    error,
    selectedFileId,
    selectedFile,
    selectedTagIds,
    loadFiles,
    clearSelection,
    selectFile,
    saveSelectedTags,
    batchRerun,
    statusLabel,
    statusTagType,
  }
}
