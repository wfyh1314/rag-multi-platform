import api from '@/api/index'

export function fetchOperationLogs(params = {}) {
  return api.get('/api/audit/operations', { params }).then((res) => res.data)
}

export function fetchChatAuditLogs(params = {}) {
  return api.get('/api/audit/chats', { params }).then((res) => res.data)
}
