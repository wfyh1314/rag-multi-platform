import api from '@/api/index'
export { uploadFile } from '@/views/chat/api/chat'

export function fetchFiles(params = {}) {
  return api
    .get('/api/files/with-tags', {
      params,
      timeout: 10000,
    })
    .then((res) => res.data)
}

export function deleteFile(fileId) {
  return api.delete(`/api/files/${fileId}`).then((res) => res.data)
}

export function fetchFilePreview(fileId) {
  return api.get(`/api/files/${fileId}/preview`).then((res) => res.data)
}
