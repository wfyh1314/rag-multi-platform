# RAG 通用智能问答系统 - 前端

Vue 3 + Vite 构建的 RAG 聊天界面。

## 启动

```bash
npm install
npm run dev
```

开发服务器运行在 http://localhost:5000，API 请求通过 Vite 代理转发到后端 `http://127.0.0.1:8000`。

## 目录结构

前端按业务模块组织：

- `src/views/login/` — 登录页与 auth API
- `src/views/chat/` — 对话页、组件、composables、chat API
- `src/views/file/` — 文件管理页、composables、file API
- `src/composables/useAuth.js` — 全局认证（AppNav 使用）
- `src/api/index.js` — 全局 axios 实例

## 生产部署

```bash
npm run build
```

构建产物在 `dist/` 目录。部署时在 `public/config.js` 中配置后端地址：

```js
window.baseUrl = 'http://your-backend-host:8000'
```

## 技术栈

- Vue 3 Composition API
- Axios + Fetch SSE
- marked（Markdown 渲染）
