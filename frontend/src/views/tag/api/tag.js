import api from '@/api/index'

export function fetchTagCategories() {
  return api.get('/api/tag-categories').then((res) => res.data)
}

export function createTagCategory(name) {
  return api.post('/api/tag-categories', { name }).then((res) => res.data)
}

export function updateTagCategory(categoryId, name) {
  return api.put(`/api/tag-categories/${categoryId}`, { name }).then((res) => res.data)
}

export function deleteTagCategory(categoryId) {
  return api.delete(`/api/tag-categories/${categoryId}`).then((res) => res.data)
}

export function createTag(categoryId, payload) {
  return api.post(`/api/tag-categories/${categoryId}/tags`, payload).then((res) => res.data)
}

export function updateTag(tagId, payload) {
  return api.put(`/api/tags/${tagId}`, payload).then((res) => res.data)
}

export function deleteTag(tagId) {
  return api.delete(`/api/tags/${tagId}`).then((res) => res.data)
}

export function fetchFilesWithTags(keyword = '') {
  return api
    .get('/api/files/with-tags', {
      params: { keyword: keyword || undefined },
    })
    .then((res) => res.data)
}

export function fetchFileTags(fileId) {
  return api.get(`/api/files/${fileId}/tags`).then((res) => res.data)
}

export function updateFileTags(fileId, tagIds) {
  return api.put(`/api/files/${fileId}/tags`, { tag_ids: tagIds }).then((res) => res.data)
}

export function rerunFileTags(fileIds = null) {
  return api
    .post('/api/files/tags/rerun', { file_ids: fileIds || undefined })
    .then((res) => res.data)
}
