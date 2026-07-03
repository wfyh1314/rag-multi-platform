import api from './index'
export { uploadFile } from './chat'

export function fetchFiles(keyword = '') {
  return api
    .get('/api/files', {
      params: { keyword: keyword || undefined },
      timeout: 10000,
    })
    .then((res) => res.data)
}

export function deleteFile(fileId) {
  return api.delete(`/api/files/${fileId}`).then((res) => res.data)
}
