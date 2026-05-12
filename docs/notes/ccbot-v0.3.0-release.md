# ccbot v0.3.0 版本说明

> 发布日期：2026-05-09
> GitHub Release：https://github.com/decardlabs/basjoo/releases/tag/v0.3.0
> 线上地址：https://ai.decard.cc/

---

## 版本概述

ccbot（原 basjoo）多渠道 AI 智能体平台首个正式版本。定位为**企业级 RAG 智能客服解决方案**，支持多渠道接入（飞书/网页/公众号）。

### 核心能力

- ✅ 纯文本 RAG 问答
- ✅ 知识库管理（文字/图片/视频索引）
- ✅ 多渠道接入
- ✅ Widget 嵌入式客服
- 🔄 图像理解版（阶段二）
- 🔄 多模态输出版（阶段三）

---

## 新增功能

### 部署工具
| 功能 | 说明 |
|------|------|
| `install-deploy.sh` | 一键生产环境安装部署脚本 |
| `deploy.sh` | Docker Compose 部署脚本，支持 `BASJOO_DOCKER_BIN` 环境变量 |
| Playwright E2E 测试 | smoke / prod-like / widget-cross-origin 三套测试项目 |

### 安全加固
| 功能 | 说明 |
|------|------|
| SSRF 防护 | URL  ingestion 时阻止 localhost、IP 字面量、私有 IP |
| API Key 加密 | Fernet AES-256 加密存储（`ENCRYPTION_KEY` / `ENCRYPTION_KEY_FILE`） |
| 生产密钥校验 | `REQUIRE_SECRET_KEY` 环境变量强制校验 |
| CORS 收紧 | 拒绝无 Origin 请求的通配符 CORS |
| Widget 安全 | 替换 Turnstile 为基于 Agent 的 Origin 白名单 |

### 功能增强
- 管理员认证（路由级，URL/Q&A/索引重建端点）
- Jina Embedding 密钥轮换支持
- URL 归一化优化
- 聊天速率限制（分钟级滑动窗口）

---

## 修复的问题

| 问题 | 修复 |
|------|------|
| 内存泄漏 | 滑动窗口限流器增加过期 key 淘汰 |
| Widget XSS | 源码渲染安全修复 |
| Widget 重连 | 前端轮询稳定性改进 |
| 健康检查 | 行为统一化 |

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户渠道层                            │
│   飞书 Bot  │  网页 Widget  │  公众号  │  API              │
└─────────────┴───────────────┴──────────┴───────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Nginx 反向代理                          │
│              ai.decard.cc (HTTPS + SSL)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose (prod)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Frontend   │  │   Backend   │  │   Nginx     │        │
│  │  (Next.js)  │  │  (FastAPI)  │  │ (Internal)  │        │
│  │ :3008       │  │  :8000      │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐                         │
│  │    Redis    │  │   Qdrant    │                         │
│  │   Cache     │  │  Vector DB  │                         │
│  │  :6379      │  │  :6333      │                         │
│  └─────────────┘  └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 14 + TypeScript + TailwindCSS |
| 后端 | FastAPI + Python 3.11 + SQLAlchemy |
| 数据库 | SQLite (持久化) + Redis (缓存) |
| 向量库 | Qdrant v1.12.1 |
| 部署 | Docker Compose |
| 代理 | Nginx |

---

## 部署信息

### 服务器环境
- **SSH**: `root@43.165.186.252`
- **代码目录**: `/opt/basjoo`
- **容器前缀**: `ccbot-`

### Docker 容器
| 容器名 | 镜像 | 端口 | 状态 |
|--------|------|------|------|
| ccbot-frontend | basjoo-frontend-prod | 127.0.0.1:3008 | ✅ healthy |
| ccbot-backend | basjoo-backend-prod | 127.0.0.1:8000 | ✅ healthy |
| ccbot-redis | redis:7-alpine | 127.0.0.1:6379 | ✅ healthy |
| ccbot-qdrant | qdrant/qdrant:v1.12.1 | 127.0.0.1:6333 | ✅ healthy |
| ccbot-nginx | basjoo-nginx | (internal) | ✅ healthy |

### 部署命令
```bash
# SSH 到服务器
ssh root@43.165.186.252

# 进入项目目录
cd /opt/basjoo

# 拉取最新代码
git pull origin main

# 启动/重建容器
docker compose --profile prod up -d --build

# 查看状态
docker ps
```

### 端口映射
- **Backend**: `127.0.0.1:8000` → 代理到 `ai.decard.cc/api/`
- **Frontend**: `127.0.0.1:3008` → 代理到 `ai.decard.cc/`

---

## 访问信息

| 服务 | 地址 |
|------|------|
| 管理后台 | https://ai.decard.cc/ |
| API 文档 | https://ai.decard.cc/docs |
| 健康检查 | https://ai.decard.cc/health |

### 管理员账号
> ⚠️ **请及时修改默认密码**

- **邮箱**: `107105108@qq.com`
- **密码**: `12345678`

---

## 项目结构

```
basjoo/
├── backend/              # FastAPI 后端
│   ├── api/              # API 端点
│   ├── core/             # 核心模块（加密、工具）
│   ├── services/         # 服务层（认证、爬虫、存储）
│   ├── agent/            # Agent 引擎（ReAct 模式）
│   └── models.py         # SQLAlchemy 模型
├── frontend-nextjs/      # Next.js 管理后台
├── widget/               # 嵌入式 Widget
├── nginx/               # Nginx 配置
├── docs/                # 文档
├── openspec/             # 项目规划
│   ├── PHASED_ROADMAP.md    # 阶段路线图
│   └── EVAL_TEST_SET.md     # RAG 评估测试集
├── tests/                # E2E 测试
├── docker-compose.yml    # 容器编排
├── deploy.sh            # 部署脚本
└── install-deploy.sh    # 一键安装脚本
```

---

## 后续计划

### 阶段一 ✅ (v0.3.0)
- 纯文本 RAG 问答
- 文字问答准确率验证

### 阶段二 🔄
- 图像理解版
- 支持上传图片提问

### 阶段三 📋
- 多模态输出版
- 从知识库提取图片/视频返回

详见：[PHASED_ROADMAP.md](../openspec/PHASED_ROADMAP.md)

---

## 相关链接

- GitHub: https://github.com/decardlabs/basjoo
- Release: https://github.com/decardlabs/basjoo/releases/tag/v0.3.0
- API 网关: https://api.decard.cc (UniAPI)

---

*最后更新: 2026-05-09*
