<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getMe, updateProfile } from '@/views/login/api/auth'
import { useAuth } from '@/composables/useAuth'

const { user, initAuth } = useAuth()
const loading = ref(false)
const saving = ref(false)
const form = reactive({
  username: '',
  real_name: '',
  phone: '',
  email: '',
  department_id: '',
})

async function loadProfile() {
  loading.value = true
  try {
    await initAuth()
    const { data: profile } = await getMe()
    form.username = profile?.username || user.value?.username || ''
    form.real_name = profile?.real_name || ''
    form.phone = profile?.phone || ''
    form.email = profile?.email || ''
    form.department_id = profile?.department_id || ''
  } catch (err) {
    ElMessage.error(err.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (saving.value) return
  saving.value = true
  try {
    await updateProfile({
      real_name: form.real_name || null,
      phone: form.phone || null,
      email: form.email || null,
      department_id: form.department_id || null,
    })
    ElMessage.success('资料已保存')
    await initAuth()
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadProfile)
</script>

<template>
  <div class="profile-page">
    <header class="page-header">
      <h1 class="page-header-title">个人资料</h1>
      <p class="page-header-subtitle">更新您的姓名、部门、手机与邮箱</p>
    </header>

    <section v-loading="loading" class="page-card profile-card">
      <el-form label-width="88px" @submit.prevent="handleSave">
        <el-form-item label="用户名">
          <el-input v-model="form.username" disabled />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.real_name" placeholder="真实姓名" />
        </el-form-item>
        <el-form-item label="部门 ID">
          <el-input v-model="form.department_id" placeholder="同部门用户可访问部门文档" />
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="form.phone" placeholder="手机号" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="邮箱地址" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
        </el-form-item>
      </el-form>
    </section>
  </div>
</template>

<style scoped>
.profile-page {
  flex: 1;
  padding: 24px 28px;
  overflow: auto;
}

.profile-card {
  max-width: 520px;
}
</style>
