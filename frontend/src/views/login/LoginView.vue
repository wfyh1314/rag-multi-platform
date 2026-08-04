<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuth } from '@/composables/useAuth'

const route = useRoute()
const router = useRouter()
const { login } = useAuth()

const loading = ref(false)
const form = reactive({
  username: 'admin',
  password: 'admin@123',
})

async function handleSubmit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请填写完整登录信息')
    return
  }

  loading.value = true
  try {
    await login({
      username: form.username,
      password: form.password,
    })
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    router.replace(redirect || '/')
  } catch (err) {
    ElMessage.error(err.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="login-title">通用 RAG 知识库</h1>
      <p class="login-subtitle">请登录后使用系统</p>

      <el-form label-position="top" @submit.prevent="handleSubmit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
            autocomplete="current-password"
            @keyup.enter="handleSubmit"
          />
        </el-form-item>
        <el-button type="primary" class="login-btn" :loading="loading" @click="handleSubmit">
          登录
        </el-button>
        <p class="login-link-row">
          没有账号？
          <router-link to="/register">立即注册</router-link>
        </p>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4ebf5 100%);
  padding: 24px;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 12px 40px rgba(15, 23, 42, 0.08);
}

.login-title {
  margin: 0 0 8px;
  font-size: 24px;
  color: #1f2937;
}

.login-subtitle {
  margin: 0 0 24px;
  color: #6b7280;
  font-size: 14px;
}

.login-btn {
  width: 100%;
  margin-top: 8px;
}

.login-link-row {
  margin-top: 16px;
  text-align: center;
  font-size: 14px;
  color: #6b7280;
}
</style>
