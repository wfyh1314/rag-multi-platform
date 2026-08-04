import api from '@/api/index'

export function fetchFolderTree() {
  return api.get('/api/folders').then((res) => res.data?.folders || [])
}

export function createFolder(name, parentId = null) {
  return api.post('/api/folders', { name, parent_id: parentId }).then((res) => res.data)
}

export function renameFolder(folderId, name) {
  return api.put(`/api/folders/${folderId}`, { name }).then((res) => res.data)
}

export function moveFolder(folderId, parentId = null) {
  return api.put(`/api/folders/${folderId}/move`, { parent_id: parentId }).then((res) => res.data)
}

export function deleteFolder(folderId) {
  return api.delete(`/api/folders/${folderId}`)
}

export function moveFileToFolder(fileId, folderId = '') {
  return api.put(`/api/files/${fileId}/move`, { file_id: fileId, folder_id: folderId }).then((res) => res.data)
}
