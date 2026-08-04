# 企业级知识库问答平台（后端）

基于 FastAPI 的企业级 RAG 后端，支持私有/公共知识库权限、混合检索、文档解析与 SSE 流式问答。

## 技术栈

| 组件 | 用途 |
|------|------|
| FastAPI | HTTP API / SSE 流式输出 |
| MySQL + SQLAlchemy | 用户、文件元数据持久化 |
| Redis | 缓存、限流（可选） |
| Qdrant | 稠密 + 稀疏混合向量检索（单 collection） |
| Celery | 大文件异步解析与向量化（占位） |
| LangGraph | 轻量化 RAG 问答工作流（占位） |

## 目录结构

```
backend/
├── config/          # 全局配置与业务常量
├── core/            # 通用底层工具（LLM 工厂、日志、安全、文档权限）
├── document/        # 全格式文档解析与分块
├── retrieval/       # 混合检索 + Rerank 精排
├── agent/           # LangGraph RAG 问答 Agent（占位）
├── user/            # 用户账户服务
├── file_mgr/        # 文件与文件夹管理
├── chat/            # 会话与 SSE 流式输出
├── audit/           # 操作与问答审计（占位）
├── api/             # FastAPI 路由层
├── storage/         # MySQL / Redis / Qdrant 封装
├── tasks/           # Celery 异步任务
├── tests/           # 单元测试
├── logs/            # 运行日志（git 忽略）
└── tmp/             # 临时上传缓存（git 忽略）
```

## 快速启动

### 1. 本地开发

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # 按需修改密钥与连接信息

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问：
- 健康检查：http://localhost:8000/health
- API 文档：http://localhost:8000/docs

默认 MySQL 库名：`rag_multi_platform`（见 `.env.example`）

### 2. Docker Compose 一键部署

```bash
docker compose up -d
```

启动 MySQL、Redis、Qdrant、后端服务与 Celery Worker。

## 前端兼容接口

与现有 Vue 前端联调的路由：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/users/me` | 当前用户信息 |
| GET | `/api/models` | 可用 LLM 模型列表 |
| GET | `/api/collections` | 知识库/集合列表 |
| POST | `/api/upload` | 文件上传 |
| POST | `/api/history/clear` | 清空会话历史 |
| POST | `/api/chat/stream` | SSE 流式问答 |

开发模式下可在 `.env` 设置 `AUTH_SKIP=true` 跳过 JWT 鉴权。

## 核心模块说明

### 文档权限（core/doc_permission + file_mgr）

- 私有文档仅上传者可见，公共文档全员可见
- 删除操作仅文档 owner 可执行
- RAG 检索前校验用户对目标 `file_id` 的访问权限

### RAG 检索链路（retrieval/ + chat/）

1. 混合召回：Qdrant 稠密向量 + jieba 稀疏向量（RRF 融合，召回 20 条）
2. Rerank 精排：DashScope gte-rerank-v2 重排至 top 5
3. 检索片段注入 Prompt → LLM 流式生成

### 文档解析（document/ + tasks/）

- 支持 PDF / docx / txt / csv / md / 图片
- 大文件通过 Celery 异步解析（占位）

## 测试

```bash
pytest tests/ -v
```

## License

Internal / Study Project
