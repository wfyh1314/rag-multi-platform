# 多租户 RAG 知识库问答平台

企业级多租户 RAG（检索增强生成）全栈项目：支持文档上传、解析向量化、Qdrant 混合检索、SSE 流式问答与文件管理。

## 项目简介

本仓库包含 **Vue 3 前端** 与 **FastAPI 后端**，面向「上传文档 → 入库检索 → 基于知识库对话」的完整链路。

**已实现能力：**

- 多格式文档上传（PDF / Word / TXT / MD / CSV 等）与同步解析入库
- 文档流水线：加载 → 清洗 → 分块 → 通义 Embedding 稠密向量化 + jieba 稀疏向量
- Qdrant 混合检索（dense + sparse，RRF 融合）
- 选中知识库时的 RAG 流式问答（SSE）
- 文件管理：列表、搜索、上传、删除（含本地文件与向量索引清理）
- 开发模式 JWT 免鉴权（`AUTH_SKIP=true`）

**规划中 / 占位：** MySQL 持久化、会话 API、Celery 异步解析、Rerank、LangGraph Agent 等。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3、Vue Router、Element Plus、Vite、Axios |
| 后端 | FastAPI、Uvicorn、Pydantic Settings |
| LLM / Embedding | 阿里通义 DashScope（OpenAI 兼容接口） |
| 向量库 | Qdrant（按租户独立 Collection，dense + sparse） |
| 文档解析 | pypdf、python-docx、jieba 等 |
| 基础设施（可选） | MySQL、Redis、Docker Compose |

## 目录结构

```
rag-multi-platform/
├── backend/                 # FastAPI 后端
│   ├── api/                 # HTTP 路由
│   ├── chat/                # SSE 流式问答、RAG 上下文
│   ├── config/              # 配置与常量
│   ├── core/                # LLM/Embedding 工厂、稀疏编码、安全
│   ├── document/            # 文档加载、清洗、分块、入库流水线
│   ├── file_mgr/            # 文件上传、存储、删除
│   ├── retrieval/           # 混合检索
│   ├── storage/             # Qdrant、Redis、MySQL 封装
│   ├── tests/               # 单元测试
│   ├── .env.example         # 环境变量模板
│   └── docker-compose.yml   # 基础设施编排
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── views/           # 对话页、文件管理页
│   │   ├── components/      # 导航、侧边栏、聊天面板
│   │   ├── composables/     # useChat、useFileList
│   │   └── api/             # 后端 API 封装
│   └── vite.config.js       # 开发代理 /api → 8000
└── README.md
```

## 环境要求

- **Python** 3.11+
- **Node.js** 18+（前端）
- **Qdrant**（上传与 RAG 必需，默认 `localhost:6333`）
- **DashScope API Key**（对话与向量化必需）

MySQL / Redis 当前核心流程可不启动；Celery 异步任务仍为占位。

## 快速开始

### 1. 启动 Qdrant（推荐 Docker）

```bash
cd backend
docker compose up -d qdrant
```

或使用已有 Qdrant 服务，在 `.env` 中配置 `QDRANT_HOST` / `QDRANT_PORT`。

### 2. 后端

```bash
cd backend

# 创建并激活虚拟环境
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux / macOS
# source .venv/bin/activate

pip install -r requirements.txt

# 复制并编辑环境变量（至少填写 DASHSCOPE_API_KEY）
copy .env.example .env   # Windows
# cp .env.example .env   # Linux / macOS

# 启动 API 服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

验证：

- 健康检查：<http://localhost:8000/health>
- API 文档：<http://localhost:8000/docs>

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器访问：<http://localhost:5000>

Vite 已将 `/api` 代理到 `http://127.0.0.1:8000`。若后端部署在远程服务器，需修改 [`frontend/vite.config.js`](frontend/vite.config.js) 中的 `proxy.target`。

### 4. Docker Compose（完整基础设施）

在 `backend/` 目录下可一键启动 MySQL、Redis、Qdrant 及后端容器：

```bash
cd backend
docker compose up -d
```

## 环境变量说明（后端）

复制 [`backend/.env.example`](backend/.env.example) 为 `backend/.env`，重点配置：

| 变量 | 说明 |
|------|------|
| `DASHSCOPE_API_KEY` | 通义 API 密钥（LLM + Embedding） |
| `QDRANT_HOST` / `QDRANT_PORT` | Qdrant 地址（host 不要带 `http://`） |
| `AUTH_SKIP` | 开发环境设为 `true` 跳过 JWT |
| `CORS_ORIGINS` | 允许的前端源，需包含 `http://localhost:5000` |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 文档分块参数 |
| `UPLOAD_DIR` | 上传文件本地目录，默认 `tmp/uploads` |

## 核心数据流

**文档入库：** 上传 → 本地磁盘 → 解析/清洗/分块 → 通义 Embedding + 稀疏向量 → Qdrant

**RAG 问答：** 用户提问（选中知识库）→ 混合检索 Qdrant → 检索片段注入 Prompt → 通义 LLM SSE 流式回答

关键文件：

- 入库流水线：[`backend/document/pipeline.py`](backend/document/pipeline.py)
- 向量化：[`backend/core/llm_factory.py`](backend/core/llm_factory.py)、[`backend/core/sparse_encoder.py`](backend/core/sparse_encoder.py)
- 向量库：[`backend/storage/vector_store.py`](backend/storage/vector_store.py)
- 混合检索：[`backend/retrieval/hybrid_search.py`](backend/retrieval/hybrid_search.py)
- RAG 对话：[`backend/chat/rag_service.py`](backend/chat/rag_service.py)

## 主要 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/models` | LLM 模型列表 |
| GET | `/api/collections` | 知识库（已索引文件）列表 |
| GET | `/api/files` | 文件管理列表（支持 keyword 搜索） |
| POST | `/api/upload` | 上传并索引文档 |
| DELETE | `/api/files/{file_id}` | 删除文件及向量 |
| POST | `/api/chat/stream` | SSE 流式问答（带 `collection` 时走 RAG） |
| POST | `/api/history/clear` | 清空当前会话历史（前端 localStorage 为主） |

## 测试

```bash
cd backend
.venv\Scripts\pytest tests/ -v
```

## 常见问题

**Qdrant 连接失败 / 上传报 502**  
确认 Qdrant 已启动且 `QDRANT_HOST`、`QDRANT_PORT` 正确。云服务器上 host 用 IP 或 `127.0.0.1`，不要写成 `http://...`。

**缺少 jieba 模块**  
在 backend 虚拟环境中执行：`pip install -r requirements.txt`

**浏览器无法打开 `http://0.0.0.0:8000`**  
`0.0.0.0` 是监听地址，访问时请用 `http://127.0.0.1:8000` 或服务器公网 IP。

**旧版 Qdrant 数据不兼容**  
升级双向量 schema 后，需删除旧 collection（如 `tenant_dev-tenant`）并重新上传文档。

## License

Internal / Study Project
