# RAG 通用智能问答系统 - 前端

Vue 3 + Vite 6 构建的 RAG 聊天界面。

## 环境要求

- **Node.js 18.20+** 或 **20 LTS**（Vite 6 与 `@rollup/rollup-win32-x64-msvc` 原生依赖要求）
- 不推荐 Node 18.4 等过旧版本

## 启动

```bash
npm install
npm run dev
```

开发服务器运行在 http://localhost:5000，API 请求通过 Vite 代理转发到后端 `http://127.0.0.1:8000`。

## 依赖安装故障排查

若出现 `@rollup/rollup-win32-x64-msvc` 缺失：

```bash
rm -rf node_modules package-lock.json   # Windows: 手动删除
npm install
# 或单独安装
npm install @rollup/rollup-win32-x64-msvc --save-optional
```

## 目录结构

- `src/views/login/` — 登录页与 auth API
- `src/views/chat/` — 对话页、会话侧栏、ConfigSidebar（知识库 + 标签筛选）
- `src/views/tag/` — 打标签管理页
- `src/views/file/` — 文件管理页（含标签列）
- `src/composables/useAuth.js` — 全局认证

## 会话存储

会话与消息由**后端 MySQL 持久化**（`/api/sessions`）。首次加载时若检测到旧版 `localStorage` 键 `rag_sessions`，会自动调用 `/api/sessions/import` 迁移后清除。

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
- Element Plus
- Axios + Fetch SSE
- marked（Markdown 渲染）
