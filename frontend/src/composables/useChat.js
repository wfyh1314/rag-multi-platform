import { ref, computed, watch } from 'vue'
import { fetchModels, fetchCollections, uploadFile, clearHistory, streamChat } from '@/api/chat'

const STORAGE_KEY = 'rag_sessions'

function createMessage(role, content = '') {
  return {
    id: `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    role,
    content,
  }
}

function ensureMessageIds(sessions) {
  for (const session of sessions) {
    if (!Array.isArray(session.messages)) continue
    for (const msg of session.messages) {
      if (!msg.id) {
        msg.id = `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
      }
    }
  }
  return sessions
}

function createSession(title = '新对话') {
  return {
    id: `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    title,
    messages: [],
    createdAt: Date.now(),
  }
}

function loadSessions() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const data = JSON.parse(raw)
      if (Array.isArray(data.sessions) && data.sessions.length) {
        return {
          sessions: ensureMessageIds(data.sessions),
          activeId: data.activeId || data.sessions[0].id,
        }
      }
    }
  } catch {
    // 忽略解析失败
  }
  const session = createSession()
  return { sessions: [session], activeId: session.id }
}

function saveSessions(sessions, activeId) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ sessions, activeId }))
}

export function useChat() {
  const stored = loadSessions()
  const sessions = ref(stored.sessions)
  const activeSessionId = ref(stored.activeId)

  const models = ref([])
  const collections = ref([])
  const selectedModel = ref('qwen-max')
  const selectedCollection = ref('')
  const maxLength = ref(4000)
  const temperature = ref(0.7)
  const isStreaming = ref(false)
  const uploadStatus = ref('')
  const pendingCollections = ref([])

  const activeSession = computed(() =>
    sessions.value.find((s) => s.id === activeSessionId.value),
  )

  const messages = computed(() => activeSession.value?.messages ?? [])

  watch([sessions, activeSessionId], () => {
    saveSessions(sessions.value, activeSessionId.value)
  }, { deep: true })

  function applyCollectionsData(data) {
    collections.value = data.collections || []
    pendingCollections.value = data.pending || []
  }

  async function init() {
    try {
      const [modelList, collectionData] = await Promise.all([
        fetchModels(),
        fetchCollections(),
      ])
      models.value = modelList
      applyCollectionsData(collectionData)
      if (modelList.length && !modelList.find((m) => m.id === selectedModel.value)) {
        selectedModel.value = modelList[0].id
      }
    } catch (err) {
      console.error('初始化失败:', err)
    }
  }

  async function refreshCollections() {
    try {
      const data = await fetchCollections()
      applyCollectionsData(data)
      return data
    } catch (err) {
      console.error('刷新知识库失败:', err)
      return null
    }
  }

  function newSession() {
    const session = createSession()
    sessions.value.unshift(session)
    activeSessionId.value = session.id
  }

  function switchSession(id) {
    activeSessionId.value = id
  }

  function deleteSession(id) {
    const idx = sessions.value.findIndex((s) => s.id === id)
    if (idx === -1) return
    sessions.value.splice(idx, 1)
    if (sessions.value.length === 0) {
      const session = createSession()
      sessions.value.push(session)
      activeSessionId.value = session.id
    } else if (activeSessionId.value === id) {
      activeSessionId.value = sessions.value[0].id
    }
  }

  function updateSessionTitle(sessionId, text) {
    const session = sessions.value.find((s) => s.id === sessionId)
    if (session && session.title === '新对话') {
      session.title = text.slice(0, 20) + (text.length > 20 ? '...' : '')
    }
  }

  async function sendMessage(text) {
    const question = text.trim()
    if (!question || isStreaming.value || !activeSession.value) return

    const sessionId = activeSessionId.value
    const session = sessions.value.find((s) => s.id === sessionId)
    if (!session) return

    session.messages.push(createMessage('user', question))
    updateSessionTitle(sessionId, question)

    session.messages.push(createMessage('assistant', ''))
    const assistantIndex = session.messages.length - 1
    isStreaming.value = true

    function getAssistantMessage() {
      const target = sessions.value.find((s) => s.id === sessionId)
      if (!target) return null
      const msg = target.messages[assistantIndex]
      return msg?.role === 'assistant' ? msg : null
    }

    function appendAssistantChunk(chunk) {
      const msg = getAssistantMessage()
      if (msg) msg.content += chunk
    }

    function setAssistantContent(content) {
      const msg = getAssistantMessage()
      if (msg) msg.content = content
    }

    const history = session.messages
      .slice(0, -2)
      .filter((m) => m.content)
      .map((m) => ({ role: m.role, content: m.content }))

    try {
      await streamChat(
        {
          query: question,
          history,
          collection: selectedCollection.value,
          model: selectedModel.value,
          max_length: maxLength.value,
          temperature: temperature.value,
          session_id: sessionId,
        },
        appendAssistantChunk,
        () => {
          isStreaming.value = false
        },
        (error) => {
          setAssistantContent(`错误: ${error}`)
          isStreaming.value = false
        },
      )
    } catch (err) {
      setAssistantContent(`错误: ${err.message}`)
      isStreaming.value = false
    }
  }

  async function handleClear() {
    if (!activeSession.value) return
    try {
      await clearHistory(activeSessionId.value)
      activeSession.value.messages = []
    } catch (err) {
      console.error('清除历史失败:', err)
    }
  }

  async function handleUpload(file) {
    uploadStatus.value = '上传中...'
    try {
      const result = await uploadFile(file)
      if (result.status === 'indexed') {
        selectedCollection.value = result.filename
        uploadStatus.value = `上传成功: ${result.filename}（${result.chunk_count ?? 0} 块）`
        await refreshCollections()
      } else {
        uploadStatus.value = result.message || '上传失败'
      }
    } catch (err) {
      uploadStatus.value = `上传失败: ${err.message}`
    }
  }

  return {
    sessions,
    activeSessionId,
    activeSession,
    messages,
    models,
    collections,
    selectedModel,
    selectedCollection,
    maxLength,
    temperature,
    isStreaming,
    uploadStatus,
    pendingCollections,
    init,
    refreshCollections,
    newSession,
    switchSession,
    deleteSession,
    sendMessage,
    handleClear,
    handleUpload,
  }
}
