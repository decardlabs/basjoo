# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo layout

- `frontend-nextjs/` is the active admin/dashboard frontend. Treat the older `frontend/` directory as legacy/reference only.
- `backend/` is a FastAPI app with SQLite persistence, Redis-backed rate limiting/cache fallbacks, and Qdrant-backed retrieval/indexing.
- `widget/` builds the embeddable chat widget SDK that talks to the backend streaming chat endpoints.
- `nginx/` contains the reverse-proxy config used in Docker deployments.
- `docker-compose.yml` is the primary local/dev/prod orchestration entrypoint.

## Common commands

### Docker compose

- Start development stack: `docker compose --profile dev up -d`
- Start production-style stack: `docker compose --profile prod up -d`
- Rebuild a service: `docker compose --profile dev up -d --build backend-dev frontend-dev`
- Follow logs: `docker compose logs -f backend-dev frontend-dev nginx`
- Dev watch mode (auto-reload on file changes): `docker compose --profile dev up --watch`

### One-command production install (Ubuntu/Debian)

- Blank server deploy: `curl -fsSL https://raw.githubusercontent.com/haoyiyin/ccbot/main/install-deploy.sh | sudo sh`
- Local repo deploy: `sudo sh install-deploy.sh`
- Supported systems: Ubuntu and Debian. The script auto-installs Docker/Compose, clones/syncs the repo, and deploys the production profile.
- Persistent volumes are preserved; `install-deploy.sh` does not remove `backend-data`, `redis-data`, or `qdrant-data`.

### Frontend (`frontend-nextjs/`)

- Install deps: `npm install`
- Start dev server: `npm run dev`
- Build: `npm run build`
- Start production build locally: `npm run start`
- Lint: `npm run lint`
- Type-check: `npm run typecheck`
- Run tests: `npm run test`

### Widget (`widget/`)

- Install deps: `npm install`
- Dev bundle/example server: `npm run dev`
- Build distributables: `npm run build`
- Type-check: `npm run typecheck`
- Run tests: `npm run test`

### Backend (`backend/`)

- Install deps: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- Run app locally: `python3 main.py`
- Run all tests: `pytest`
- Run one test file: `pytest tests/test_api.py`
- Run one test: `pytest tests/test_api.py::test_name`
- Test discovery is configured by `backend/pytest.ini` (`tests/`, `test_*.py`, `Test*`, `test_*`)
- Health check while developing locally: `curl http://localhost:8000/health`

### Root-level E2E tests (Playwright)

- Smoke tests (dev environment): `npm run test:e2e`
- All Playwright projects: `npm run test:e2e:all`
- Production-like E2E: `npm run test:e2e:prod`
- Widget cross-origin embed tests: `npm run test:e2e:widget`
- Sync widget bundle to backend: `npm run sync-widget`

## Architecture

### Backend request flow

- `backend/main.py` creates the FastAPI app, mounts auth plus `/api/v1` routers, configures CORS/i18n/rate limiting, and starts schedulers/Redis in non-test mode.
- CORS behavior is intentionally split between Starlette `CORSMiddleware` for normal requests and `apply_cors_headers()` from `backend/middleware/rate_limit.py` for early responses such as rate-limit/413 paths. Keep those in sync via the shared helper; do not add ad-hoc CORS header logic elsewhere.
- `Origin: null` is only allowed when `cors_allow_null_origin` is explicitly enabled in config; missing `Origin` headers should not receive wildcard CORS.
- `backend/config.py` centralizes settings. Secrets can come from env vars or on-disk key files; missing/insecure `SECRET_KEY` values are auto-generated and persisted. The default widget agent ID is also persisted to `/app/data/.agent_id`, and can be overridden with `DEFAULT_AGENT_ID`.
- If `ENCRYPTION_KEY` is not set, the backend auto-generates a Fernet key and persists it to `ENCRYPTION_KEY_FILE` (default `/app/data/.encryption_key`). Stored provider API keys are encrypted with this key.
- `REQUIRE_SECRET_KEY` should be set to `true` in production to reject auto-generated/insecure secret keys.
- `cors_allow_null_origin` (boolean, default `false`) controls whether `Origin: null` (e.g., `file://` widget preview) receives wildcard CORS headers.
- `backend/database.py` sets up the async SQLAlchemy engine/sessionmaker and initializes default workspace/agent data using the configured persistent default agent ID.
- `backend/models.py` is the system-of-record schema: workspace/agent config, URL and QA knowledge sources, document chunks, chat sessions/messages, quotas, index jobs, and admin users.

### Chat, RAG, and indexing

- Main chat APIs live in `backend/api/v1/endpoints.py`. They handle admin config APIs, public chat APIs, SSE streaming, session creation, quota checks, widget origin whitelist checks, and source normalization.
- URL and Q&A ingestion lives in `backend/api/v1/url_endpoints.py`. Those routers are admin-protected at the router level; URL creation queues async fetch jobs, and refetch/crawl/import operations feed the same knowledge-source tables.
- Full index rebuilds live in `backend/api/v1/index_endpoints.py`. Those routes are also admin-protected at the router level; rebuild jobs chunk URL/QA content, persist `DocumentChunk` rows, and replace the agent’s Qdrant collection.
- Retrieval/storage logic is split across `backend/services/qdrant_store.py`, `backend/services/rag_qdrant.py`, `backend/services/scraper.py`, `backend/services/crawler.py`, and `backend/services/llm_service.py`.
- `backend/services/websocket_service.py` manages admin WebSocket connections with Redis pub/sub for cross-worker broadcasting (session updates, new messages, human takeover).
- `backend/services/redis_service.py` provides Redis connection and cache fallback helpers.
- `backend/services/task_lock.py` provides a shared lock service that prevents conflicting operations (e.g., index rebuild vs. URL fetch) on the same agent.
- `backend/api/v1/schemas.py` defines all Pydantic request/response models with URL safety validation via `validate_url_safe`.
- `backend/api/v1/sse_utils.py` provides the shared `sse_event()` formatter used by streaming endpoints.
- URL safety/SSRF checks are centralized in `backend/services/url_safety.py` and reused by both schema validation and scraper fetch/discovery flows. If URL-ingestion policy changes, update the shared safety helper rather than reintroducing regex-only validation in multiple places.
- `backend/services/llm_service.py` is the provider abstraction layer. Provider selection is driven by `Agent.provider_type`; many providers are implemented via OpenAI-compatible base URLs, while OpenAI Native and Google have dedicated paths.

### Frontend structure

- The Next.js app uses the App Router under `frontend-nextjs/app/`, with route groups for auth pages and dashboard pages.
- Most page logic is delegated into `frontend-nextjs/src/views/`; shared UI/components live in `frontend-nextjs/src/components/`.
- `frontend-nextjs/src/context/AuthContext.tsx` stores admin auth state in `localStorage` and powers `RequireAuth`-guarded dashboard routes.
- `frontend-nextjs/src/services/api.ts` is the main frontend API client. It handles bearer auth, locale propagation, and SSE parsing for `/api/v1/chat/stream`.

### Widget structure

- `widget/src/CcbotWidget.tsx` is a self-contained embeddable widget implementation bundled with esbuild.
- The widget auto-detects `apiBase`, streams chat via SSE, persists visitor/session IDs in `localStorage`, and polls for human-takeover replies.
- Backend `/sdk.js`, `/ccbot-logo.png`, and widget demo routes are served directly from `backend/main.py`.

### Deployment notes

- `docker-compose.yml` defines shared Redis/Qdrant plus separate dev/prod backend/frontend services.
- `install-deploy.sh` is the one-command production installer for Ubuntu/Debian. It wraps `deploy.sh` and handles Docker/Compose installation, repo clone/sync, and post-deploy health checks.
- The active frontend container is `frontend-nextjs`; compose and nginx configs route traffic to that app, not the legacy frontend.
- Nginx should allow bodies larger than the backend guard: `nginx/conf.d/default.conf` sets `client_max_body_size 12m` so oversized requests reach FastAPI and return JSON 413 responses.
- Optional HTTPS is enabled by `nginx/docker-entrypoint.sh` only when readable cert/key files exist in `./ssl`; otherwise the stack stays in HTTP-only mode.
- When HTTPS is enabled, nginx redirects HTTP requests to HTTPS automatically.
- `SERVER_DOMAIN` can be passed to nginx to enforce a canonical host: matching hostnames are served, direct IP/other-host access is dropped with nginx 444, and `/health` stays available for probes.

## Testing notes

- Backend tests use `backend/tests/conftest.py` to force `BASJOO_TEST_MODE=1`, create isolated SQLite DBs under `backend/.pytest_dbs/`, and monkeypatch Qdrant/Jina/LLM integrations for most API tests.
- Use the existing `client` fixture for authenticated admin API tests and `public_client` for unauthenticated/public-route coverage instead of building ad-hoc `AsyncClient` fixtures in individual test files.
- If a test depends on real Redis/Qdrant hostnames, the fixtures auto-fallback between container hostnames and localhost.

## Phased Roadmap & Current Stage

The project follows a three-phase MVP approach defined in `openspec/PHASED_ROADMAP.md`:

### Phase 1: MVP Text QA (CURRENT)
- **Goal**: Pure text Q&A, validate RAG accuracy
- **Tech stack**: FastAPI + LlamaIndex + Qdrant
- **Key files**:
  - `backend/services/rag_qdrant.py` — RAG retrieval logic
  - `backend/services/qdrant_store.py` — Vector store abstraction
  - `openspec/EVAL_TEST_SET.md` — RAG evaluation test set (~140 cases target)
- **Phase 1 File Format Support** (defined in PHASED_ROADMAP.md T1.1-T1.6):
  | Format | Priority | Status |
  |--------|----------|--------|
  | TXT | 🔴 High | TODO |
  | HTML | 🔴 High | TODO |
  | Markdown | 🔴 High | TODO |
  | PDF | 🔴 High | TODO |
  | Word (DOCX) | 🟡 Medium | TODO |
  | Excel (XLSX) | 🟡 Medium | TODO |
  | Image | 🟢 Low | TODO |
- **Acceptance**: RAG text accuracy validated via EVAL_TEST_SET.md before moving to Phase 2
- **Note**: PDF embedded images must be extracted and indexed as first-class citizens

### Phase 1 Tech Stack Details (已确认)

#### Embedding 模型
- **当前**：硅基流动（Silicon Flow），`bge-large-zh-v1.5`（1024维，余弦距离）
- **后续**：接入 UniAPI 后统一走 UniAPI 调用
- **向量维度**：1024
- **距离算法**：Cosine（余弦）

#### Qdrant Collection 设计（⚠️ 已修正：单 Collection + Payload 过滤）

> **设计变更（2026-05-10）**：原方案按 `agent_id` 分 Collection，经 RAG 专家评审指出存在资源浪费和运维灾难风险。已修正为单 Collection + Payload 过滤方案。

- **Collection 名称**：`ccbot_docs`（单一集合）
- **逻辑隔离**：通过 `payload.agent_id` 字段区分不同 agent 的数据
- **Payload 索引**：对 `agent_id` 建 keyword 索引，查询性能几乎无损
- **扩展优势**：调整向量维度或距离算法只需操作一个 Collection

```python
# 对 agent_id 建 Payload 索引（加速过滤查询）
client.create_payload_index(
    collection_name="ccbot_docs",
    field_name="agent_id",
    field_schema="keyword",
)

# 查询时按 agent_id 过滤
client.search(
    collection_name="ccbot_docs",
    query_vector=query_embedding,
    query_filter={"must": [{"key": "agent_id", "match": {"value": agent_id}}]},
    limit=5,
)
```

**图片/文件存储路径**：

| 阶段 | 存储方式 | 路径/位置 |
|------|-----------|------------|
| 阶段一 | 本地文件系统 | `/opt/ccbot/storage/` |
| 阶段二 | MinIO（S3 兼容） | `s3://ccbot-docs/` |

- Qdrant 只存向量 + 元数据（文件路径/URL），**不存原始二进制文件**
- 图片元数据存入 payload：`{"content_type": "image", "file_path": "/opt/ccbot/storage/images/xxx.jpg"}`

#### AI 辅助任务模型分配
| 任务 | 模型 | 说明 |
|------|------|------|
| TXT AI 分段/提取标题 | DeepSeek-chat | 便宜，结构化输出 |
| 表格理解（Excel/Word → MD） | DeepSeek-chat | 需要一定推理 |
| PDF 图片描述生成 | — | **阶段一只存图片，描述留阶段二** |
| Text Embedding | bge-large-zh-v1.5（硅基流动） | 中文效果好 |
| RAG 回答生成 | MiniMax（主力）/ DeepSeek（兜底） | 已确认 |

#### 文本归一化
| 规则 | 处理方式 |
|------|---------|
| 繁体→简体 | 用 `opencc` 转换 |
| 全角→半角 | 英文/数字全角转半角 |
| 标点归一化 | 保留原文，不强制转换 |
| 代码块 | 保留原文，标记 `content_type: code` |

### Phase 2: Image Understanding
- **Goal**: Accept image input from users, understand and answer with text
- **Key files**: TBD (to be scaffolded after Phase 1 complete)
- **Note**: Image understanding, not image output

### Phase 3: Multimodal Output
- **Goal**: Agent replies with existing images/videos from knowledge base (not real-time generation)
- **Key constraint**: Images/videos are first-class citizens in the knowledge base (see Core Constraints below)

**Current focus**: Phase 1. Do not start Phase 2/3 work until Phase 1 RAG accuracy is validated.

## Core Constraints

### Knowledge Base: Images/Videos as First-Class Citizens

**CRITICAL — do not violate this constraint:**

- Images and videos uploaded to the knowledge base MUST be indexed as **first-class citizens**, not merely extracted for text.
- The knowledge base index MUST support retrieving image/video content directly, not just text chunks derived from them.
- When the agent replies, it MUST be able to return **existing images/videos** from the knowledge base to the user, not generate new ones.
- **NO real-time image/video generation** — all visual content comes from pre-uploaded knowledge base material.
- During RAG retrieval, image/video relevance scoring must be treated on par with text relevance.

### Model Provider Convention

- Primary model channel: **MiniMax** (via UniAPI at `api.decard.cc`)
- Secondary channel: **DeepSeek** (fallback)
- UniAPI endpoint: configured in `backend/config.py` or env vars
- Local xray proxy (for dev): `HTTP 1081` (MacBook Air M5)

### Evaluation-Driven Development

- RAG evaluation test set: `openspec/EVAL_TEST_SET.md`
- Before any Phase 1 completion claim, run the eval test set and document accuracy
- Target: ~140 test cases for Phase 1
- Format: each case has `question`, `expected_source_type`, `expected_keywords`

## Evaluation (EVAL_TEST_SET.md)

`openspec/EVAL_TEST_SET.md` is the RAG evaluation test set for Phase 1:

- **Purpose**: Validate text Q&A accuracy of the RAG pipeline
- **Usage**: Run evaluations against the current RAG implementation; record pass/fail per case
- **Target size**: ~140 test cases
- **Do NOT** modify the expected answers without explicit user approval
- **When evaluating**: Compare RAG-retrieved context and generated answer against `expected_keywords` and `expected_source_type`
