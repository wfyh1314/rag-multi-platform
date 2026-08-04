<script setup>
import { ref, onMounted } from 'vue'
import { fetchOperationLogs, fetchChatAuditLogs } from '@/views/audit/api/audit'

const activeTab = ref('operations')
const loading = ref(false)

const opLogs = ref([])
const opTotal = ref(0)
const opPage = ref(1)
const opPageSize = ref(20)
const opAction = ref('')

const chatLogs = ref([])
const chatTotal = ref(0)
const chatPage = ref(1)
const chatPageSize = ref(20)
const chatSessionId = ref('')

function formatTime(iso) {
  if (!iso) return '-'
  try {
    return new Date(iso).toLocaleString('zh-CN')
  } catch {
    return iso
  }
}

async function loadOperationLogs() {
  loading.value = true
  try {
    const data = await fetchOperationLogs({
      page: opPage.value,
      page_size: opPageSize.value,
      action: opAction.value || undefined,
    })
    opLogs.value = data.items || []
    opTotal.value = data.total ?? 0
  } catch (err) {
    opLogs.value = []
    opTotal.value = 0
  } finally {
    loading.value = false
  }
}

async function loadChatLogs() {
  loading.value = true
  try {
    const data = await fetchChatAuditLogs({
      page: chatPage.value,
      page_size: chatPageSize.value,
      session_id: chatSessionId.value || undefined,
    })
    chatLogs.value = data.items || []
    chatTotal.value = data.total ?? 0
  } catch (err) {
    chatLogs.value = []
    chatTotal.value = 0
  } finally {
    loading.value = false
  }
}

function onTabChange(name) {
  activeTab.value = name
  if (name === 'operations') {
    loadOperationLogs()
  } else {
    loadChatLogs()
  }
}

function onOpSearch() {
  opPage.value = 1
  loadOperationLogs()
}

function onChatSearch() {
  chatPage.value = 1
  loadChatLogs()
}

function onOpPageChange(page) {
  opPage.value = page
  loadOperationLogs()
}

function onChatPageChange(page) {
  chatPage.value = page
  loadChatLogs()
}

onMounted(() => {
  loadOperationLogs()
})
</script>

<template>
  <div class="audit-page">
    <header class="page-header">
      <h1 class="page-header-title">审计日志</h1>
      <p class="page-header-subtitle">查看操作记录与问答审计，便于合规追溯</p>
    </header>

    <el-tabs v-model="activeTab" class="audit-tabs" @tab-change="onTabChange">
      <el-tab-pane label="操作审计" name="operations">
        <section class="page-card">
          <div class="filter-bar">
            <el-select
              v-model="opAction"
              clearable
              placeholder="全部操作"
              class="filter-item"
              @change="onOpSearch"
            >
              <el-option label="全部操作" value="" />
              <el-option label="文件上传" value="file.upload" />
              <el-option label="文件删除" value="file.delete" />
              <el-option label="用户注册" value="user.register" />
              <el-option label="会话删除" value="session.delete" />
            </el-select>
            <el-button :loading="loading" @click="onOpSearch">刷新</el-button>
          </div>

          <el-table v-loading="loading" :data="opLogs" stripe empty-text="暂无记录">
            <el-table-column prop="action" label="操作" width="140" />
            <el-table-column prop="resource_type" label="资源类型" width="100" />
            <el-table-column prop="resource_id" label="资源 ID" min-width="200" show-overflow-tooltip />
            <el-table-column label="详情" min-width="220">
              <template #default="{ row }">
                <span v-if="!row.detail">-</span>
                <code v-else class="audit-detail">{{ JSON.stringify(row.detail) }}</code>
              </template>
            </el-table-column>
            <el-table-column label="时间" width="170">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>

          <div class="audit-pagination">
            <el-pagination
              v-model:current-page="opPage"
              :page-size="opPageSize"
              :total="opTotal"
              layout="total, prev, pager, next"
              @current-change="onOpPageChange"
            />
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="问答审计" name="chats">
        <section class="page-card">
          <div class="filter-bar">
            <el-input
              v-model="chatSessionId"
              clearable
              placeholder="会话 ID 筛选"
              class="filter-item filter-search"
              @keyup.enter="onChatSearch"
              @clear="onChatSearch"
            />
            <el-button :loading="loading" @click="onChatSearch">查询</el-button>
          </div>

          <el-table v-loading="loading" :data="chatLogs" stripe empty-text="暂无记录">
            <el-table-column prop="session_id" label="会话 ID" min-width="180" show-overflow-tooltip />
            <el-table-column prop="query" label="问题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="answer" label="回答" min-width="240" show-overflow-tooltip />
            <el-table-column label="引用数" width="80" align="center">
              <template #default="{ row }">{{ row.sources?.length ?? 0 }}</template>
            </el-table-column>
            <el-table-column label="时间" width="170">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>

          <div class="audit-pagination">
            <el-pagination
              v-model:current-page="chatPage"
              :page-size="chatPageSize"
              :total="chatTotal"
              layout="total, prev, pager, next"
              @current-change="onChatPageChange"
            />
          </div>
        </section>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
