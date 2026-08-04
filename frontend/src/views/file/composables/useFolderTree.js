import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  fetchFolderTree,
  createFolder,
  renameFolder,
  deleteFolder,
} from '@/views/file/api/folder'

export function useFolderTree(onFolderChange) {
  const folders = ref([])
  const selectedFolderId = ref(null)
  const loading = ref(false)

  async function loadFolders() {
    loading.value = true
    try {
      folders.value = await fetchFolderTree()
    } catch (err) {
      ElMessage.error(err.message || '加载文件夹失败')
      folders.value = []
    } finally {
      loading.value = false
    }
  }

  function selectFolder(folderId) {
    selectedFolderId.value = folderId
    onFolderChange?.(folderId)
  }

  async function handleCreate(parentId = null) {
    try {
      const { value } = await ElMessageBox.prompt('请输入文件夹名称', '新建文件夹', {
        confirmButtonText: '创建',
        cancelButtonText: '取消',
        inputPattern: /\S+/,
        inputErrorMessage: '名称不能为空',
      })
      await createFolder(value.trim(), parentId)
      ElMessage.success('文件夹已创建')
      await loadFolders()
    } catch {
      // 用户取消
    }
  }

  async function handleRename(folder) {
    try {
      const { value } = await ElMessageBox.prompt('请输入新名称', '重命名文件夹', {
        confirmButtonText: '保存',
        cancelButtonText: '取消',
        inputValue: folder.name,
        inputPattern: /\S+/,
        inputErrorMessage: '名称不能为空',
      })
      await renameFolder(folder.id, value.trim())
      ElMessage.success('已重命名')
      await loadFolders()
    } catch {
      // 用户取消
    }
  }

  async function handleDeleteFolder(folder) {
    try {
      await ElMessageBox.confirm(
        `确定删除文件夹「${folder.name}」？仅空文件夹可删除。`,
        '删除确认',
        { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
      )
      await deleteFolder(folder.id)
      if (selectedFolderId.value === folder.id) {
        selectFolder(null)
      }
      ElMessage.success('文件夹已删除')
      await loadFolders()
    } catch {
      // 用户取消或后端校验失败
    }
  }

  return {
    folders,
    selectedFolderId,
    loading,
    loadFolders,
    selectFolder,
    handleCreate,
    handleRename,
    handleDeleteFolder,
  }
}
