# 企业级知识库问答平台

企业级 RAG（检索增强生成）全栈项目：支持文档上传、解析向量化、Qdrant 混合检索、标签管理、SSE 流式问答、后端会话持久化与文件管理。

## 项目简介

本仓库包含 **Vue 3 前端** 与 **FastAPI 后端**，面向「上传文档 → 入库检索 → 基于知识库对话」的完整链路。

**已实现能力：**

- 多格式文档上传（PDF / Word / TXT / MD / CSV / 图片等）与同步/异步解析入库
- 文档流水线：加载 → 清洗 → 固定/语义分块 → 通义 Embedding 稠密向量化 + jieba 稀疏向量
- Qdrant 混合检索（dense + sparse，RRF 融合），单 collection `knowledge_base`
- **gte-rerank-v2 重排序**精筛检索结果
- **标签系统**：标签字典、关键词自动打标、手动打标、文件列表标签列、RAG 按标签筛选
- 标签同步至 Qdrant chunk payload（`tag_ids`）
- 私有/公共/部门知识库权限控制
- 选中知识库或标签时的 RAG 流式问答（SSE）
- **后端会话持久化**（MySQL `chat_sessions` / `chat_messages`）
- 文件夹管理、文件预览、用户注册、操作/问答审计
- **Celery 异步解析**大文件（超过阈值自动入队）
- **LangGraph Agent** 问答（`POST /api/chat/agent`、流式 `POST /api/chat/agent/stream`）
- 多模态检索（文本 + 图片 chunk）
- 文件夹树管理、文件预览、会话归档
- 用户注册 / 个人资料、操作/问答审计前端
- API 限流（Redis，不可用时自动跳过）
- **Alembic** 数据库迁移（`alembic upgrade head`）
- 输入敏感词过滤（默认词库，问答/Agent 入口拦截）

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3、Vue Router、Element Plus、Vite 6、Axios |
| 后端 | FastAPI、Uvicorn、Pydantic Settings、Celery |
| LLM / Embedding / Rerank | 阿里通义 DashScope |
| 向量库 | Qdrant（单 collection，dense + sparse） |
| 持久化 | MySQL（用户、文件、会话、标签、审计） |
| Agent | LangGraph |
| 文档解析 | pypdf、python-docx、jieba、PIL 等 |
| 基础设施 | Redis（Celery）、Docker Compose |

## 环境要求

- **Python** 3.11+
- **Node.js** 18.20+ 或 **20 LTS**（Vite 6 需要；推荐 20 LTS）
- **MySQL** 8.0+（默认库名 `rag_multi_platform`）
- **Qdrant**（默认 `localhost:6333`）
- **Redis**（Celery 异步解析与可选缓存）
- **DashScope API Key**

## 快速开始

### 1. 基础设施

```bash
cd backend
docker compose up -d mysql qdrant redis
```

### 2. 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env   # 填写 DASHSCOPE_API_KEY

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Celery Worker（大文件异步解析）

```bash
cd backend
celery -A tasks.celery_app worker --loglevel=info
```

或使用 Docker Compose 中的 `celery-worker` 服务。

### 4. 前端

```bash
cd frontend
npm install
npm run dev
```

访问：<http://localhost:5000>

## 环境变量（重点）

| 变量 | 说明 |
|------|------|
| `DASHSCOPE_API_KEY` | 通义 API 密钥 |
| `CHUNK_STRATEGY` | `fixed`（默认）或 `semantic` |
| `ASYNC_UPLOAD_THRESHOLD_MB` | 超过此大小走 Celery，默认 5 |
| `CELERY_BROKER_URL` | Redis broker |
| `AUTH_SKIP` | 开发环境跳过 JWT |

## 核心数据流

**文档入库：** 上传 → 本地磁盘 + MySQL → 解析/分块 → Embedding + 稀疏向量 → Qdrant → 自动打标 → 同步 `tag_ids` 到 Qdrant

**RAG 问答：** 提问（可选 `collection` + `tag_ids`）→ 混合检索 → Rerank → Prompt 注入 → SSE 流式回答 → 消息落库

**会话：** 前端调用 Session API → MySQL 持久化；旧版 localStorage 数据可通过 `/api/sessions/import` 一次性迁移

## 主要 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/register` | 注册 |
| PUT | `/api/users/me` | 更新个人信息 |
| GET/POST/PUT/DELETE | `/api/sessions` | 会话 CRUD |
| POST | `/api/sessions/{id}/archive` | 归档会话 |
| POST | `/api/sessions/import` | 批量导入 localStorage 会话 |
| GET | `/api/sessions/{id}/history` | 会话历史 |
| POST | `/api/chat/stream` | SSE 流式问答（支持 `collection`、`tag_ids`） |
| POST | `/api/chat/agent` | LangGraph Agent 问答（JSON） |
| POST | `/api/chat/agent/stream` | LangGraph Agent 流式问答（SSE） |
| GET/POST | `/api/tag-categories` | 标签分类 |
| GET | `/api/files/with-tags` | 带标签文件列表 |
| PUT | `/api/files/{id}/tags` | 手动打标 |
| POST | `/api/files/tags/rerun` | 重跑自动标签 |
| POST | `/api/folders` | 创建文件夹 |
| GET | `/api/folders` | 文件夹树 |
| PUT | `/api/folders/{id}` | 重命名文件夹 |
| PUT | `/api/folders/{id}/move` | 移动文件夹 |
| DELETE | `/api/folders/{id}` | 删除空文件夹 |
| PUT | `/api/files/{id}/move` | 移动文件到文件夹 |
| GET | `/api/files/{id}/preview` | 文件预览 |
| GET | `/api/audit/operations` | 操作审计 |
| GET | `/api/audit/chats` | 问答审计 |
| POST | `/api/upload` | 上传并索引 |
| DELETE | `/api/files/{file_id}` | 删除文件及向量 |

## 标签回填（已有索引）

```bash
cd backend
python scripts/backfill_tag_payload.py
```

## 测试

```bash
cd backend
pytest tests/ -v
```

## 常见问题

**Rollup 原生模块缺失（Windows）**  
删除 `frontend/node_modules` 与 `package-lock.json` 后重新 `npm install`；Node 升级到 18.20+ 或 20 LTS。

**MySQL 旧库缺列**  
重启后端触发 `ensure_schema()`；或使用 `alembic upgrade head` 执行迁移。库名使用 `rag_multi_platform`。

**数据库迁移（Alembic）**

```bash
cd backend
pip install alembic   # 已含于 requirements.txt
alembic upgrade head  # 应用 002_department 等迁移
```

已有通过 `create_all()` 建库的部署，可先 `alembic stamp 001_baseline` 再 `alembic upgrade head`。

## License

Internal / Study Project
