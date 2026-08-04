import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  fetchModels,
  fetchCollections,
  fetchSessions,
  createSession as apiCreateSession,
  importSessions,
  deleteSessionApi,
  archiveSessionApi,
  fetchSessionHistory,
  clearHistory,
  streamChat,
  streamAgentChat,
  updateSession,
} from '@/views/chat/api/chat'
import { fetchTagCategories } from '@/views/tag/api/tag'

const LEGACY_STORAGE_KEY = 'rag_sessions'

function createMessage(role, content = '', id, sources = []) {
  return {
    id: id || `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    role,
    content,
    sources,
  }
}

function mapSessionFromApi(item) {
  return {
    id: item.id,
    title: item.title || '新对话',
    messages: [],
    createdAt: item.created_at ? new Date(item.created_at).getTime() : Date.now(),
    isArchived: !!item.is_archived,
  }
}

function mapMessageFromApi(item) {
  return createMessage(item.role, item.content || '', item.id, item.sources || [])
}

export function normalizeCollection(item) {
  if (typeof item === 'string') {
    return { file_id: item, filename: item, visibility: 'private' }
  }
  return {
    file_id: item.file_id || item.id || '',
    filename: item.filename || item.name || '未命名文件',
    visibility: item.visibility || 'private',
  }
}

async function migrateLegacySessions() {
  try {
    const raw = localStorage.getItem(LEGACY_STORAGE_KEY)
    if (!raw) return false
    const data = JSON.parse(raw)
    if (!Array.isArray(data.sessions) || !data.sessions.length) {
      localStorage.removeItem(LEGACY_STORAGE_KEY)
      return false
    }
    await importSessions(data.sessions)
    localStorage.removeItem(LEGACY_STORAGE_KEY)
    return true
  } catch (err) {
    console.warn('localStorage 会话迁移失败:', err)
    return false
  }
}

export function useChat() {
  const sessions = ref([])
  const activeSessionId = ref('')
  const models = ref([])
  const collections = ref([])
  const tagCategories = ref([])
  const selectedModel = ref('qwen-max')
  const selectedCollection = ref('')
  const selectedTagIds = ref([])
  const maxLength = ref(4000)
  const temperature = ref(0.7)
  const chatMode = ref('stream')
  const showArchived = ref(false)
  const isStreaming = ref(false)
  const pendingCollections = ref([])
  const isLoading = ref(false)

  const activeSession = computed(() =>
    sessions.value.find((s) => s.id === activeSessionId.value),
  )

  const messages = computed(() => activeSession.value?.messages ?? [])

  function applyCollectionsData(data) {
    const raw = data?.collections || []
    collections.value = raw.map(normalizeCollection).filter((item) => item.file_id)
    pendingCollections.value = data?.pending || []
    if (
      selectedCollection.value
      && !collections.value.some((item) => item.file_id === selectedCollection.value)
    ) {
      selectedCollection.value = ''
    }
  }

  async function loadSessionMessages(sessionId) {
    const history = await fetchSessionHistory(sessionId)
    const session = sessions.value.find((s) => s.id === sessionId)
    if (session) {
      session.messages = history.map(mapMessageFromApi)
    }
  }

  async function reloadSessions() {
    const serverSessions = await fetchSessions(showArchived.value)
    sessions.value = serverSessions.map(mapSessionFromApi)
    if (!sessions.value.length) {
      await newSession()
      return
    }
    if (!sessions.value.some((s) => s.id === activeSessionId.value)) {
      activeSessionId.value = sessions.value[0].id
      await loadSessionMessages(activeSessionId.value)
    }
  }

  async function init() {
    isLoading.value = true
    try {
      const [modelList, collectionData, tagData] = await Promise.all([
        fetchModels(),
        fetchCollections(),
        fetchTagCategories().catch(() => ({ categories: [] })),
      ])
      models.value = modelList
      applyCollectionsData(collectionData)
      tagCategories.value = tagData?.categories || []

      let serverSessions = await fetchSessions()
      if (!serverSessions.length) {
        const migrated = await migrateLegacySessions()
        if (migrated) {
          serverSessions = await fetchSessions()
        }
      }

      if (serverSessions.length) {
        sessions.value = serverSessions.map(mapSessionFromApi)
        activeSessionId.value = sessions.value[0].id
        await loadSessionMessages(activeSessionId.value)
      } else {
        const created = await apiCreateSession()
        const session = mapSessionFromApi(created)
        sessions.value = [session]
        activeSessionId.value = session.id
      }

      if (modelList.length && !modelList.find((m) => m.id === selectedModel.value)) {
        selectedModel.value = modelList[0].id
      }
    } catch (err) {
      console.error('初始化失败:', err)
    } finally {
      isLoading.value = false
    }
  }

  async function newSession() {
    const created = await apiCreateSession()
    const session = mapSessionFromApi(created)
    sessions.value.unshift(session)
    activeSessionId.value = session.id
  }

  async function switchSession(id) {
    activeSessionId.value = id
    await loadSessionMessages(id)
  }

  async function archiveSession(id) {
    try {
      await archiveSessionApi(id)
      ElMessage.success('会话已归档')
    } catch (err) {
      ElMessage.error(err.message || '归档失败')
      return
    }
    const idx = sessions.value.findIndex((s) => s.id === id)
    if (idx !== -1) sessions.value.splice(idx, 1)
    if (!showArchived.value) {
      if (sessions.value.length === 0) {
        await newSession()
      } else if (activeSessionId.value === id) {
        activeSessionId.value = sessions.value[0].id
        await loadSessionMessages(activeSessionId.value)
      }
    } else {
      await reloadSessions()
    }
  }

  async function toggleShowArchived() {
    showArchived.value = !showArchived.value
    await reloadSessions()
  }

  function setAssistantSources(sources) {
    const sessionId = activeSessionId.value
    const session = sessions.value.find((s) => s.id === sessionId)
    if (!session) return
    const last = session.messages[session.messages.length - 1]
    if (last?.role === 'assistant') {
      last.sources = sources || []
    }
  }

  async function deleteSession(id) {
    try {
      await deleteSessionApi(id)
    } catch (err) {
      console.error('删除会话失败:', err)
    }
    const idx = sessions.value.findIndex((s) => s.id === id)
    if (idx === -1) return
    sessions.value.splice(idx, 1)
    if (sessions.value.length === 0) {
      await newSession()
    } else if (activeSessionId.value === id) {
      activeSessionId.value = sessions.value[0].id
      await loadSessionMessages(activeSessionId.value)
    }
  }

  function updateSessionTitle(sessionId, text) {
    const session = sessions.value.find((s) => s.id === sessionId)
    if (session && session.title === '新对话') {
      const title = text.slice(0, 20) + (text.length > 20 ? '...' : '')
      session.title = title
      updateSession(sessionId, title).catch(() => {})
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

    if (chatMode.value === 'agent') {
      try {
        await streamAgentChat(
          {
            query: question,
            session_id: sessionId,
            collection: selectedCollection.value || undefined,
            tag_ids: selectedTagIds.value,
          },
          appendAssistantChunk,
          async () => {
            isStreaming.value = false
            await loadSessionMessages(sessionId)
          },
          (error) => {
            setAssistantContent(`错误: ${error}`)
            isStreaming.value = false
          },
          (warning) => {
            ElMessage.warning(warning)
          },
          (sources) => {
            setAssistantSources(sources)
          },
        )
      } catch (err) {
        setAssistantContent(`错误: ${err.message}`)
        isStreaming.value = false
      }
      return
    }

    try {
      await streamChat(
        {
          query: question,
          history,
          collection: selectedCollection.value || undefined,
          tag_ids: selectedTagIds.value,
          model: selectedModel.value,
          max_length: maxLength.value,
          temperature: temperature.value,
          session_id: sessionId,
        },
        appendAssistantChunk,
        async () => {
          isStreaming.value = false
          await loadSessionMessages(sessionId)
        },
        (error) => {
          setAssistantContent(`错误: ${error}`)
          isStreaming.value = false
        },
        (warning) => {
          console.warn('会话持久化警告:', warning)
          ElMessage.warning(warning)
        },
        (sources) => {
          setAssistantSources(sources)
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

  return {
    sessions,
    activeSessionId,
    activeSession,
    messages,
    models,
    collections,
    tagCategories,
    selectedModel,
    selectedCollection,
    selectedTagIds,
    maxLength,
    temperature,
    chatMode,
    showArchived,
    isStreaming,
    pendingCollections,
    isLoading,
    init,
    newSession,
    switchSession,
    deleteSession,
    archiveSession,
    toggleShowArchived,
    sendMessage,
    handleClear,
  }
}
