# decard.cc 网站设计规格文档

> 日期：2026-05-06
> 状态：已审核 ✓
> 对应项目：Basjoo 推广及开发进度说明网站

---

## 1. 背景与目标

decard.cc 是一个面向**开发者社区**和**企业用户**的独立产品网站，用于：

- 推广 Basjoo AI 客服平台产品能力
- 展示开发进度（Changelog / Roadmap / 博客）
- 提供 AI 辅助内容写作能力（基于 Basjoo 自身）
- **在首页直接嵌入 Basjoo Widget 做 Live Demo（dogfooding）**

网站与 Basjoo 平台解耦，独立部署，通过 API 调用 Basjoo 实现 AI 功能。

---

## 2. 目标受众

- **技术开发者 / 潜在贡献者**：关注架构设计、代码质量、开发进度、API 文档、如何参与贡献
- **企业用户 / 潜在客户**：关注产品功能、部署方式、使用案例、是否稳定可用

---

## 3. 整体架构

```
┌─────────────────────────────────────────────────────┐
│                     decard.cc                     │
│              （独立 Next.js 站点）                    │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ 产品主页  │  │ 开发进度  │  │ 管理后台     │   │
│  │+AI Live  │  │Changelog │  │(登录保护)    │   │
│  │Demo      │  │Roadmap    │  │              │   │
│  │          │  │博客      │  │              │   │
│  └────┬─────┘  └────┬─────┘  └──────┬───────┘   │
└───────┼───────────────┼─────────────────┼──────────┘
        │               │                 │
        ▼               ▼                 ▼
┌─────────────────────────────────────────────────────┐
│               decard-site-backend                   │
│           (FastAPI + SQLite)                       │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ 内容 API  │  │ 用户/鉴权 │  │ 反馈/统计    │   │
│  │CRUD       │  │JWT       │  │API           │   │
│  └──────────┘  └──────────┘  └──────────────┘   │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Basjoo API         │
              │  (AI 辅助写作 + Live Demo)│
              └──────────────────────┘
```

**技术选型：**

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 14（App Router）+ TypeScript + Tailwind CSS（独立品牌风格） |
| 后端 | FastAPI + SQLite |
| AI 能力 | 通过 HTTP 调用 Basjoo `/api/v1/chat/stream` |
| 部署 | Docker Compose，与 Basjoo 共享服务器及网络 |

---

## 4. 前端页面结构

### 公开页面（访客可见）

| 路由 | 页面 | 核心内容 |
|------|------|----------|
| `/` | 首页 | Basjoo 产品介绍、核心功能亮点、**嵌入式 AI 客服 Live Demo**、CTA |
| `/changelog` | 版本日志 | 按版本号倒序，每条含功能/修复/贡献者 |
| `/roadmap` | 路线图 | 三列看板：计划中 / 进行中 / 已完成 |
| `/blog` | 开发博客 | 文章列表，支持按标签筛选 |
| `/blog/[slug]` | 博客详情 | Markdown 渲染，底部评论区 |
| `/about` | 关于 | 项目背景、团队成员、开源协议 |

### 管理页面（需登录）

| 路由 | 页面 | 核心功能 |
|------|------|----------|
| `/admin/login` | 登录 | JWT 鉴权 |
| `/admin` | 管理首页 | 数据概览（文章数、访客数、反馈数） |
| `/admin/changelog` | 版本管理 | 新建/编辑/发布/草稿 |
| `/admin/roadmap` | 路线图管理 | 拖拽排序状态 |
| `/admin/blog` | 博客管理 | 列表 + **AI 辅助写作入口** |
| `/admin/feedback` | 反馈管理 | 查看/回复/归档访客反馈 |
| `/admin/analytics` | 数据分析 | 基础 PV/UV、来源渠道、热门文章 |

---

## 5. 首页 Live Demo — Basjoo Widget 集成

首页直接嵌入 Basjoo Widget，让访客**实时体验 AI 客服能力**，而非仅通过文字了解产品。这是典型的 dogfooding（自举示范）。

### 实现方式

在首页组件里引入 Basjoo Widget SDK，配置 `autoOpen={false}`（默认收起，点击按钮展开）：

```tsx
// pages/index.tsx
import { BasjooWidget } from '@/components/BasjooWidget'

export default function Home() {
  return (
    <>
      {/* 产品 Banner */}
      <Hero />

      {/* Live Demo 区 */}
      <section className="demo-section">
        <h2>亲自体验 AI 客服</h2>
        <p>问任何关于 Basjoo 的问题，看它如何回答</p>
        <BasjooWidget
          agentId={process.env.NEXT_PUBLIC_DEMO_AGENT_ID}
          autoOpen={false}
        />
        <a href="/docs/deploy">查看如何部署 →</a>
      </section>

      <Features />
    </>
  )
}
```

### 好处

| 角度 | 收益 |
|------|------|
| **产品力** | 访客立刻感受到 AI 能力，无需阅读文档 |
| **信任感** | "敢把自己产品跑在首页"，本身就是质量背书 |
| **转化** | 体验满意 → 直接引导到 GitHub 部署文档 |
| **需求挖掘** | 访客提问 = 真实用户需求 = Roadmap 素材 |

### 环境配置

```env
# .env.local / Docker 环境变量
NEXT_PUBLIC_DEMO_AGENT_ID=agt_xxxxxxxxxxxx
NEXT_PUBLIC_BASJOO_API_BASE=https://api.decard.cc
```

> **注意**：`BasjooWidget` 组件可以直接复用 Basjoo 项目 `widget/` 目录下的代码，无需重新开发。

---

## 6. AI 辅助写作集成

### 工作流程

```
管理后台点击「AI 辅助写作」
        │
        ▼
弹出对话框 → 输入写作提示
        │
        ▼
后端调用 Basjoo API (/api/v1/chat/stream)
        │
        ▼
SSE 流式返回 → 前端实时渲染生成的内容
        │
        ▼
用户编辑/润色 → 保存为草稿或直接发布
```

### 集成细节

| 项目 | 说明 |
|------|------|
| 调用方式 | 后端作为代理，转发请求到 Basjoo `/api/v1/chat/stream` |
| 认证 | 使用 Basjoo 配置的 API Key，存于 decard-site 后端环境变量 `BASJOO_API_KEY` |
| 提示词模板 | 后端预制模板，如"你是一位技术博客作者，请基于以下要点写一篇博客文章：\n{user_input}" |
| 流式渲染 | 前端使用 `ReadableStream` 处理 SSE，逐字显示生成内容 |
| 错误处理 | Basjoo 不可用时降级为纯手动编辑模式 |

### 管理后台操作界面

在 `/admin/blog` 页面新增按钮 **「AI 生成草稿」**：

1. 点击后弹出 Modal，输入写作要求
2. 实时显示 AI 生成过程（打字机效果）
3. 生成完毕后，内容自动填入 Markdown 编辑器
4. 用户可继续手动编辑，然后保存

---

## 7. 数据模型设计（SQLite）

### `admin_users` — 管理员账号

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| username | TEXT UNIQUE | |
| password_hash | TEXT | |
| created_at | DATETIME | |

### `changelogs` — 版本发布日志

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| version | TEXT | 语义版本号 |
| release_date | DATE | |
| title_zh | TEXT | |
| title_en | TEXT | |
| content_zh | TEXT | Markdown |
| content_en | TEXT | Markdown |
| is_published | BOOLEAN | |
| created_at | DATETIME | |

### `roadmap_items` — 路线图条目

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| title_zh | TEXT | |
| title_en | TEXT | |
| description_zh | TEXT | |
| description_en | TEXT | |
| status | TEXT | planned / in_progress / done |
| sort_order | INTEGER | |
| created_at | DATETIME | |

### `blog_posts` — 博客文章

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| slug | TEXT UNIQUE | |
| title_zh | TEXT | |
| title_en | TEXT | |
| content_zh | TEXT | Markdown |
| content_en | TEXT | Markdown |
| tags | TEXT | JSON 数组 |
| is_published | BOOLEAN | |
| view_count | INTEGER | |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### `comments` — 访客评论/反馈

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| post_id | INTEGER NULLABLE | 为 NULL 时表示独立反馈 |
| author_name | TEXT | |
| content | TEXT | |
| is_approved | BOOLEAN | |
| created_at | DATETIME | |

### `analytics` — 访问统计（按日聚合）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| date | DATE | |
| page_path | TEXT | |
| pv | INTEGER | |
| uv | INTEGER | |

---

## 8. 部署方案

### Docker Compose 结构

decard-site 作为独立项目，与 Basjoo 共享 `basjoo-network` Docker 网络，直接互通。

```yaml
services:
  decard-backend:
    build: ./backend
    ports: ["127.0.0.1:8001:8000"]
    environment:
      - BASJOO_API_KEY=${BASJOO_API_KEY}
      - BASJOO_API_URL=http://basjoo-backend:8000
    volumes: ["decard-data:/app/data"]
    networks: [basjoo-network]

  decard-frontend:
    build: ./frontend
    ports: ["127.0.0.1:3001:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://decard-backend:8000
    networks: [basjoo-network]

networks:
  basjoo-network:
    external: true
```

### Nginx 路由

在已有 Basjoo nginx 里新增 `decard.cc` server block：

```nginx
server {
    server_name www.decard.cc;
    location / {
        proxy_pass http://decard-frontend:3000;
    }
    location /api/ {
        proxy_pass http://decard-backend:8000;
    }
}
```

### 部署步骤

1. 在服务器上 clone `decard-site` 项目
2. 配置 `.env`（Basjoo API Key、JWT Secret）
3. `docker compose up -d --build`
4. Nginx 新增 `decard.cc` server block，reload
5. 初始化管理员账号（`python init_admin.py`）

---

## 9. 待确认事项

- [ ] 设计文档审核通过
- [ ] 独立品牌视觉风格具体设计（颜色、字体、布局）
- [ ] Basjoo API 调用鉴权细节确认
- [ ] 多语言（中英文）切换交互方式确认

---

*本文档由 brainstorming 技能生成，待用户审核后进入实施计划阶段。*
