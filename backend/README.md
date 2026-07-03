# 企业级多租户知识库问答平台（后端）

基于 FastAPI + LangGraph 的企业级 RAG 后端，支持多租户隔离、RBAC 权限、混合检索、异步文档解析与审计日志。

## 技术栈

| 组件 | 用途 |
|------|------|
| FastAPI | HTTP API / SSE 流式输出 |
| MySQL + SQLAlchemy | 租户、用户、文件、会话、审计持久化 |
| Redis | JWT 缓存、会话、限流 |
| Qdrant | 稠密向量检索（按租户独立 Collection） |
| Elasticsearch | BM25 稀疏全文检索 |
| Celery | 大文件异步解析与向量化 |
| LangGraph | 轻量化 RAG 问答工作流 |

## 目录结构

```
backend/
├── config/          # 全局配置与业务常量
├── core/            # 通用底层工具（LLM 工厂、日志、安全、异常）
├── document/        # 全格式文档解析与分块
├── retrieval/       # 混合检索 + Rerank
├── agent/           # LangGraph RAG 问答 Agent
├── tenant/          # 多租户 + RBAC 权限
├── file_mgr/        # 文件与文件夹管理
├── chat/            # 会话与 SSE 流式输出
├── audit/           # 操作与问答审计
├── api/             # FastAPI 路由层
├── storage/         # MySQL / Redis / Qdrant / ES 封装
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

### 2. Docker Compose 一键部署

```bash
docker compose up -d
```

启动 MySQL、Redis、Qdrant、Elasticsearch、后端服务与 Celery Worker。

## 前端兼容接口

与现有 Vue 前端联调的路由：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/models` | 可用 LLM 模型列表 |
| GET | `/api/collections` | 知识库/集合列表 |
| POST | `/api/upload` | 文件上传 |
| POST | `/api/history/clear` | 清空会话历史 |
| POST | `/api/chat/stream` | SSE 流式问答 |

开发模式下可在 `.env` 设置 `AUTH_SKIP=true` 跳过 JWT 鉴权。

## 核心模块说明

### 多租户隔离（tenant/ + storage/）

- 每个租户拥有独立的 Qdrant Collection 与 ES Index 前缀
- 所有 DB 查询强制携带 `tenant_id` 过滤
- RBAC：超级管理员 / 企业管理员 / 普通员工

### RAG 检索链路（retrieval/ + agent/）

1. 混合召回：Qdrant 稠密向量 + ES BM25
2. Rerank 重排过滤噪声片段
3. LangGraph 线性流程：提问 → 检索 → 生成答案

### 文档解析（document/ + tasks/）

- 支持 PDF / docx / txt / csv / md / 图片
- 大文件通过 Celery 异步解析，不阻塞前端

## 面试讲解要点

1. **多租户数据隔离**：向量库按租户分 Collection + MySQL 行级 tenant_id + 文档权限校验三层防护
2. **混合检索**：稠密语义 + BM25 关键词互补，Rerank 提升精度
3. **异步架构**：Celery 解耦解析耗时操作，SSE 实现流式用户体验
4. **企业安全**：RBAC、操作审计、敏感词过滤、问答溯源
5. **可扩展性**：LLM/Embedding/Rerank 工厂模式，存储层抽象便于切换组件

## 测试

```bash
pytest tests/ -v
```

## License

Internal / Study Project
