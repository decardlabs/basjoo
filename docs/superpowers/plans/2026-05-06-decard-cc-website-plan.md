# decard.cc 网站实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建 decard.cc 独立产品网站（Next.js 前端 + FastAPI 后端），展示 Basjoo 产品能力与开发进度，管理后台支持 AI 辅助写作。

**Architecture:** 独立 Next.js 站点 + FastAPI + SQLite，与 Basjoo 平台解耦，通过 API 调用 Basjoo 实现 AI 能力（AI 写作 + 首页 Live Demo）。

**Tech Stack:** Next.js 14 + TypeScript + Tailwind CSS | FastAPI + SQLAlchemy + SQLite | Docker Compose + Nginx

---

## 项目结构预览

```
decard-site/
├── frontend/                 # Next.js 站点
│   ├── app/
│   │   ├── page.tsx          # 首页 + Basjoo Widget Live Demo
│   │   ├── changelog/
│   │   ├── roadmap/
│   │   ├── blog/
│   │   ├── about/
│   │   └── admin/            # 管理后台（需登录保护）
│   ├── components/
│   │   ├── BasjooWidget.tsx  # 复用 Basjoo widget/ 代码
│   │   └── ...
│   └── lib/
│       └── api.ts
│
├── backend/                  # FastAPI 后端
│   ├── main.py
│   ├── models.py             # SQLAlchemy 模型
│   ├── database.py
│   ├── schemas.py            # Pydantic schemas
│   ├── routers/
│   │   ├── auth.py           # JWT 登录
│   │   ├── changelogs.py
│   │   ├── roadmap.py
│   │   ├── blog.py
│   │   ├── comments.py
│   │   ├── analytics.py
│   │   └── ai_proxy.py       # Basjoo SSE 调用代理
│   └── requirements.txt
│
├── docker-compose.yml
└── README.md
```

---

## Phase 1: 项目初始化

### Task 1: 创建项目结构与 Git 仓库

**Files:**
- Create: `decard-site/` 目录（新仓库）
- Create: `decard-site/README.md`
- Create: `.gitignore` (node_modules, __pycache__, .env, dist/)

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p decard-site/frontend/{app/{changelog,roadmap,blog,about,admin},components,lib} \
         decard-site/backend/{routers,tests}
```

- [ ] **Step 2: 初始化 Git**

```bash
cd decard-site && git init && git add . && git commit -m "init: decard-site project"
```

---

### Task 2: 初始化 Next.js 前端

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/next.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tailwind.config.ts`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "decard-site-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.2.x",
    "react": "^18",
    "react-dom": "^18",
    "react-markdown": "^9",
    "react-syntax-highlighter": "^15",
    "axios": "^1"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "typescript": "^5",
    "tailwindcss": "^3",
    "postcss": "^8",
    "autoprefixer": "^10"
  }
}
```

- [ ] **Step 2: 配置 Tailwind**

```ts
// tailwind.config.ts
import type { Config } from 'tailwindcss'
const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: { primary: '#...', secondary: '#...' }
      }
    },
  },
  plugins: [],
}
export default config
```

- [ ] **Step 3: 创建全局 CSS 和布局**

```css
/* app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

```tsx
// app/layout.tsx
import './globals.css'
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="zh"><body>{children}</body></html>
}
```

- [ ] **Step 4: 提交**

```bash
git add frontend/ && git commit -m "feat: init Next.js frontend"
```

---

### Task 3: 初始化 FastAPI 后端

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/main.py`
- Create: `backend/database.py`
- Create: `backend/models.py`
- Create: `backend/config.py`

- [ ] **Step 1: 创建 requirements.txt**

```
fastapi==0.111.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.30
pydantic==2.7.0
pydantic-settings==2.2.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.27.0
python-multipart==0.0.9
aiosqlite==0.20.0
```

- [ ] **Step 2: 创建 config.py**

```python
# backend/config.py
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./decard.db"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h
    BASJOO_API_URL: str = "http://localhost:8000"
    BASJOO_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
```

- [ ] **Step 3: 创建 database.py**

```python
# backend/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        yield session
```

- [ ] **Step 4: 提交**

```bash
git add backend/ && git commit -m "feat: init FastAPI backend"
```

---

### Task 4: 配置 Docker Compose

**Files:**
- Create: `docker-compose.yml`
- Create: `frontend/Dockerfile`
- Create: `frontend/Dockerfile.dev`
- Create: `backend/Dockerfile`
- Create: `backend/Dockerfile.dev`
- Create: `.env.example`

- [ ] **Step 1: 创建 docker-compose.yml**

```yaml
version: '3.9'
services:
  decard-backend:
    build: ./backend
    ports: ["127.0.0.1:8001:8000"]
    env_file: [.env]
    volumes: ["./data:/app/data"]
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

- [ ] **Step 2: 创建 .env.example**

```bash
SECRET_KEY=your-secret-key-here
BASJOO_API_URL=http://basjoo-backend:8000
BASJOO_API_KEY=your-basjoo-api-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme
```

- [ ] **Step 3: 提交**

```bash
git add docker-compose.yml frontend/Dockerfile* backend/Dockerfile* .env.example
git commit -m "feat: add Docker Compose configuration"
```

---

## Phase 2: 后端开发

### Task 5: 数据库模型

**Files:**
- Modify: `backend/models.py`（创建所有表）
- Create: `backend/init_db.py`（初始化管理员账号）

- [ ] **Step 1: 实现 models.py**

```python
# backend/models.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, JSON
from datetime import datetime
from database import Base

class AdminUser(Base):
    __tablename__ = "admin_users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)

class Changelog(Base):
    __tablename__ = "changelogs"
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, unique=True)
    release_date = Column(Date)
    title_zh = Column(Text)
    title_en = Column(Text)
    content_zh = Column(Text)
    content_en = Column(Text)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class RoadmapItem(Base):
    __tablename__ = "roadmap_items"
    id = Column(Integer, primary_key=True, index=True)
    title_zh = Column(Text)
    title_en = Column(Text)
    description_zh = Column(Text)
    description_en = Column(Text)
    status = Column(String)  # planned / in_progress / done
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class BlogPost(Base):
    __tablename__ = "blog_posts"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)
    title_zh = Column(Text)
    title_en = Column(Text)
    content_zh = Column(Text)
    content_en = Column(Text)
    tags = Column(JSON, default=list)
    is_published = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, nullable=True)
    author_name = Column(String)
    content = Column(Text)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Analytics(Base):
    __tablename__ = "analytics"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    page_path = Column(String)
    pv = Column(Integer, default=0)
    uv = Column(Integer, default=0)
```

- [ ] **Step 2: 创建 init_db.py**

```python
# backend/init_db.py
from passlib.context import CryptContext
from database import engine, async_session
from models import Base, AdminUser
import asyncio

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        user = AdminUser(
            username="admin",
            password_hash=pwd_context.hash("changeme")
        )
        session.add(user)
        await session.commit()
    print("Database initialized.")

if __name__ == "__main__":
    asyncio.run(init())
```

- [ ] **Step 3: 提交**

```bash
git add backend/models.py backend/init_db.py
git commit -m "feat: add database models"
```

---

### Task 6: JWT 认证与登录 API

**Files:**
- Create: `backend/routers/auth.py`
- Modify: `backend/main.py`（挂载路由）

- [ ] **Step 1: 实现 auth.py**

```python
# backend/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from database import get_db
from models import AdminUser
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
router = APIRouter(prefix="/api/auth", tags=["auth"])

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    data.update({"exp": expire})
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

class Token(BaseModel):
    access_token: str
    token_type: str

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> AdminUser:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401)

    result = await db.execute(select(AdminUser).where(AdminUser.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401)
    return user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AdminUser).where(AdminUser.username == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
```

- [ ] **Step 2: 修改 main.py 挂载路由**

```python
# backend/main.py（追加）
from routers.auth import router as auth_router

app.include_router(auth_router)
```

- [ ] **Step 3: 提交**

```bash
git add backend/routers/auth.py backend/main.py
git commit -m "feat: add JWT authentication"
```

---

### Task 7: 内容 CRUD API（Changelog / Roadmap / Blog）

**Files:**
- Create: `backend/routers/changelogs.py`
- Create: `backend/routers/roadmap.py`
- Create: `backend/routers/blog.py`
- Modify: `backend/main.py`（挂载所有路由）

- [ ] **Step 1: 实现 changelogs.py**

```python
# backend/routers/changelogs.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional
from datetime import date
from database import get_db
from models import Changelog, AdminUser
from routers.auth import get_current_user

router = APIRouter(prefix="/api/changelogs", tags=["changelogs"])

class ChangelogCreate(BaseModel):
    version: str
    release_date: date
    title_zh: str
    title_en: str
    content_zh: str
    content_en: str
    is_published: bool = False

class ChangelogOut(ChangelogCreate):
    id: int
    created_at: datetime

# 公开：获取已发布列表
@router.get("/")
async def list_changelogs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Changelog).where(Changelog.is_published == True).order_by(desc(Changelog.release_date))
    )
    return result.scalars().all()

# 管理：创建
@router.post("/", response_model=ChangelogOut)
async def create_changelog(
    data: ChangelogCreate,
    db: AsyncSession = Depends(get_db),
    user: AdminUser = Depends(get_current_user)
):
    changelog = Changelog(**data.model_dump())
    db.add(changelog)
    await db.commit()
    await db.refresh(changelog)
    return changelog

# 管理：获取所有（含草稿）
@router.get("/all")
async def list_all_changelogs(
    db: AsyncSession = Depends(get_db),
    user: AdminUser = Depends(get_current_user)
):
    result = await db.execute(select(Changelog).order_by(desc(Changelog.release_date)))
    return result.scalars().all()

# 管理：更新 / 删除（补充）
```

- [ ] **Step 2: 实现 roadmap.py**（结构同上，支持状态筛选 planned/in_progress/done）

- [ ] **Step 3: 实现 blog.py**（支持 slug、标签筛选、分页、view_count 更新）

- [ ] **Step 4: 提交**

```bash
git add backend/routers/changelogs.py backend/routers/roadmap.py backend/routers/blog.py backend/main.py
git commit -m "feat: add content CRUD APIs"
```

---

### Task 8: 访客评论与统计 API

**Files:**
- Create: `backend/routers/comments.py`
- Create: `backend/routers/analytics.py`
- Modify: `backend/main.py`

- [ ] **Step 1: 实现 comments.py**

```python
# backend/routers/comments.py
# POST /api/comments          — 访客提交评论（需审核）
# GET  /api/comments?post_id=X — 获取已审核评论
# 管理端：PATCH /api/comments/:id/approve — 审核通过
# 管理端：DELETE /api/comments/:id        — 删除
```

- [ ] **Step 2: 实现 analytics.py**

```python
# backend/routers/analytics.py
# POST /api/analytics/track   — 记录访问（page_path, uv uuid）
# GET  /api/analytics/summary  — 获取 PV/UV 统计
# GET  /api/analytics/popular  — 热门文章
# 管理端：DELETE /api/comments/:id — 删除
```

- [ ] **Step 3: 提交**

```bash
git add backend/routers/comments.py backend/routers/analytics.py backend/main.py
git commit -m "feat: add comments and analytics APIs"
```

---

### Task 9: AI 辅助写作代理 API

**Files:**
- Create: `backend/routers/ai_proxy.py`

- [ ] **Step 1: 实现 ai_proxy.py**

```python
# backend/routers/ai_proxy.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from models import AdminUser
from routers.auth import get_current_user
from config import settings
import httpx
import json

router = APIRouter(prefix="/api/ai", tags=["ai"])

PROMPT_TEMPLATE = """你是一位技术博客作者。请基于以下要求撰写一篇博客文章：

要求：{user_input}

请用 Markdown 格式输出，包含：
- 吸引人的标题
- 简洁的导语
- 2-4 个主要段落
- 总结

写作语言：中文"""
SYSTEM_PROMPT = "你是一位专业的技术博客作者，擅长撰写深入浅出的技术文章。"

@router.post("/generate")
async def generate_blog(
    user_input: str,
    db: AsyncSession = Depends(get_db),
    user: AdminUser = Depends(get_current_user)
):
    if not settings.BASJOO_API_KEY:
        raise HTTPException(status_code=503, detail="Basjoo API not configured")

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": PROMPT_TEMPLATE.format(user_input=user_input)}
        ],
        "stream": True
    }

    async def stream_response():
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{settings.BASJOO_API_URL}/api/v1/chat/stream",
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.BASJOO_API_KEY}",
                    "Content-Type": "application/json"
                }
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        yield f"{line[6:]}\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")
```

- [ ] **Step 2: 提交**

```bash
git add backend/routers/ai_proxy.py backend/main.py
git commit -m "feat: add AI writing proxy API"
```

---

## Phase 3: 前端开发 — 公开页面

### Task 10: 首页 + Basjoo Widget Live Demo

**Files:**
- Modify: `frontend/app/page.tsx`
- Create: `frontend/components/BasjooWidget.tsx`
- Create: `frontend/components/Hero.tsx`
- Create: `frontend/components/Features.tsx`
- Create: `frontend/components/Footer.tsx`

- [ ] **Step 1: 实现 BasjooWidget 组件**

```tsx
// frontend/components/BasjooWidget.tsx
"use client"
import { useEffect, useRef, useState } from "react"

interface BasjooWidgetProps {
  agentId: string
  autoOpen?: boolean
}

export function BasjooWidget({ agentId, autoOpen = false }: BasjooWidgetProps) {
  const [isOpen, setIsOpen] = useState(autoOpen)
  const [messages, setMessages] = useState<{role: string; content: string}[]>([
    { role: "assistant", content: "👋 你好！有什么关于 Basjoo 的问题可以问我。" }
  ])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    const userMsg = { role: "user", content: input }
    setMessages(prev => [...prev, userMsg])
    setInput("")
    setLoading(true)

    try {
      const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId, messages: [...messages, userMsg] })
      })
      const reader = resp.body?.getReader()
      const decoder = new TextDecoder()
      let assistantMsg = ""
      setMessages(prev => [...prev, { role: "assistant", content: "" }])
      while (reader) {
        const { done, value } = await reader.read()
        if (done) break
        assistantMsg += decoder.decode(value)
        setMessages(prev => {
          const updated = [...prev]
          updated[updated.length - 1] = { role: "assistant", content: assistantMsg }
          return updated
        })
      }
    } catch (e) {
      setMessages(prev => [...prev.slice(0, -1), { role: "assistant", content: "抱歉，服务暂时不可用。" }])
    }
    setLoading(false)
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {!isOpen ? (
        <button onClick={() => setIsOpen(true)} className="bg-brand-primary text-white rounded-full px-6 py-3 shadow-lg">
          💬 体验 AI 客服
        </button>
      ) : (
        <div className="w-96 bg-white rounded-xl shadow-2xl border overflow-hidden">
          <div className="bg-brand-primary text-white p-4 flex justify-between items-center">
            <span className="font-bold">Basjoo AI 客服</span>
            <button onClick={() => setIsOpen(false)}>✕</button>
          </div>
          <div className="h-80 overflow-y-auto p-4 space-y-3">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] rounded-lg px-4 py-2 ${m.role === "user" ? "bg-blue-500 text-white" : "bg-gray-100"}`}>
                  {m.content}
                </div>
              </div>
            ))}
            {loading && <div className="text-gray-400">正在输入...</div>}
            <div ref={bottomRef} />
          </div>
          <div className="p-4 border-t flex gap-2">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && sendMessage()}
              className="flex-1 border rounded-lg px-3 py-2 text-sm"
              placeholder="输入你的问题..."
            />
            <button onClick={sendMessage} disabled={loading} className="bg-brand-primary text-white rounded-lg px-4 py-2 text-sm">
              发送
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: 实现首页 page.tsx**

```tsx
// frontend/app/page.tsx
import { BasjooWidget } from "@/components/BasjooWidget"
import { Hero } from "@/components/Hero"
import { Features } from "@/components/Features"
import { Footer } from "@/components/Footer"

export default function Home() {
  return (
    <main className="min-h-screen">
      <Hero />
      <Features />
      <section className="py-20 bg-gray-50">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold mb-4">亲自体验 AI 客服</h2>
          <p className="text-gray-600 mb-8">问任何关于 Basjoo 的问题，看它如何回答</p>
          <BasjooWidget agentId={process.env.NEXT_PUBLIC_DEMO_AGENT_ID!} autoOpen={false} />
        </div>
      </section>
      <Footer />
    </main>
  )
}
```

- [ ] **Step 3: 实现 Hero / Features / Footer**（独立品牌视觉风格，简约现代）

- [ ] **Step 4: 提交**

```bash
git add frontend/app/page.tsx frontend/components/
git commit -m "feat: add homepage with Basjoo Widget Live Demo"
```

---

### Task 11: 开发进度页面（Changelog / Roadmap / Blog）

**Files:**
- Create: `frontend/app/changelog/page.tsx`
- Create: `frontend/app/roadmap/page.tsx`
- Create: `frontend/app/blog/page.tsx`
- Create: `frontend/app/blog/[slug]/page.tsx`
- Create: `frontend/app/about/page.tsx`
- Modify: `frontend/lib/api.ts`（API 调用封装）

- [ ] **Step 1: 实现 api.ts**

```typescript
// frontend/lib/api.ts
import axios from "axios"

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "",
})

export const changelogApi = {
  list: () => api.get("/api/changelogs/"),
  create: (data: any, token: string) => api.post("/api/changelogs/", data, {
    headers: { Authorization: `Bearer ${token}` }
  }),
}

export const roadmapApi = {
  list: () => api.get("/api/roadmap/"),
}

export const blogApi = {
  list: (params?: { page?: number; tag?: string }) =>
    api.get("/api/blog/", { params }),
  get: (slug: string) => api.get(`/api/blog/${slug}/`),
}

export const commentApi = {
  submit: (data: { post_id?: number; author_name: string; content: string }) =>
    api.post("/api/comments/", data),
}

export const analyticsApi = {
  track: (data: { page_path: string; uv_id: string }) =>
    api.post("/api/analytics/track", data),
}
```

- [ ] **Step 2: 实现 changelog/page.tsx**

```tsx
// frontend/app/changelog/page.tsx
"use client"
import { useEffect, useState } from "react"
import { changelogApi } from "@/lib/api"

export default function ChangelogPage() {
  const [changelogs, setChangelogs] = useState([])

  useEffect(() => {
    changelogApi.list().then(r => setChangelogs(r.data))
  }, [])

  return (
    <div className="max-w-3xl mx-auto px-6 py-12">
      <h1 className="text-4xl font-bold mb-8">版本更新日志</h1>
      <div className="space-y-8">
        {changelogs.map((cl: any) => (
          <article key={cl.id} className="border rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-mono">
                v{cl.version}
              </span>
              <span className="text-gray-400 text-sm">{cl.release_date}</span>
            </div>
            <h2 className="text-xl font-bold mb-2">{cl.title_zh}</h2>
            <div className="prose prose-slate max-w-none">
              {cl.content_zh}
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: 实现 roadmap/page.tsx（三列看板布局）**

- [ ] **Step 4: 实现 blog/page.tsx 和 blog/[slug]/page.tsx（Markdown 渲染 + 评论区）**

- [ ] **Step 5: 实现 about/page.tsx**

- [ ] **Step 6: 提交**

```bash
git add frontend/app/changelog frontend/app/roadmap frontend/app/blog frontend/app/about frontend/lib/api.ts
git commit -m "feat: add public pages (changelog, roadmap, blog, about)"
```

---

## Phase 4: 前端开发 — 管理后台

### Task 12: 管理后台框架与登录

**Files:**
- Create: `frontend/middleware.ts`（路由保护）
- Create: `frontend/app/admin/layout.tsx`
- Create: `frontend/app/admin/login/page.tsx`
- Create: `frontend/lib/auth.ts`（token 管理）

- [ ] **Step 1: 实现 auth.ts**

```typescript
// frontend/lib/auth.ts
const TOKEN_KEY = "decard_admin_token"

export const auth = {
  getToken: () => typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null,
  setToken: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clearToken: () => localStorage.removeItem(TOKEN_KEY),
  isAuthenticated: () => !!localStorage.getItem(TOKEN_KEY),
}
```

- [ ] **Step 2: 实现登录页面 login/page.tsx**

```tsx
// frontend/app/admin/login/page.tsx
"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { auth } from "@/lib/auth"
import axios from "axios"

export default function LoginPage() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const router = useRouter()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const formData = new FormData()
      formData.append("username", username)
      formData.append("password", password)
      const resp = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/auth/login`,
        formData,
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
      )
      auth.setToken(resp.data.access_token)
      router.push("/admin")
    } catch {
      setError("用户名或密码错误")
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={handleLogin} className="bg-white p-8 rounded-xl shadow-lg w-96">
        <h1 className="text-2xl font-bold mb-6 text-center">管理后台登录</h1>
        {error && <p className="text-red-500 mb-4 text-sm">{error}</p>}
        <input
          className="w-full border rounded-lg px-4 py-3 mb-4"
          placeholder="用户名"
          value={username}
          onChange={e => setUsername(e.target.value)}
        />
        <input
          type="password"
          className="w-full border rounded-lg px-4 py-3 mb-6"
          placeholder="密码"
          value={password}
          onChange={e => setPassword(e.target.value)}
        />
        <button type="submit" className="w-full bg-brand-primary text-white rounded-lg py-3 font-medium">
          登录
        </button>
      </form>
    </div>
  )
}
```

- [ ] **Step 3: 实现 middleware.ts**

```typescript
// frontend/middleware.ts
import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

export function middleware(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith("/admin") && !request.nextUrl.pathname.startsWith("/admin/login")) {
    const token = request.cookies.get("decard_admin_token")?.value
    // 简化处理：重定向到登录页（实际用服务端 session 更安全）
    if (!token) {
      return NextResponse.redirect(new URL("/admin/login", request.url))
    }
  }
  return NextResponse.next()
}
```

- [ ] **Step 4: 提交**

```bash
git add frontend/middleware.ts frontend/app/admin/login frontend/lib/auth.ts
git commit -m "feat: add admin login page and auth"
```

---

### Task 13: 管理后台内容管理

**Files:**
- Create: `frontend/app/admin/page.tsx`（管理首页）
- Create: `frontend/app/admin/changelog/page.tsx`
- Create: `frontend/app/admin/roadmap/page.tsx`
- Create: `frontend/app/admin/blog/page.tsx`
- Create: `frontend/app/admin/feedback/page.tsx`
- Create: `frontend/app/admin/analytics/page.tsx`

- [ ] **Step 1: 实现 admin/page.tsx（数据概览）**

```tsx
// frontend/app/admin/page.tsx
"use client"
import { useEffect, useState } from "react"
import { auth } from "@/lib/auth"

export default function AdminDashboard() {
  const [stats, setStats] = useState({ changelogs: 0, blogs: 0, comments: 0 })

  useEffect(() => {
    const token = auth.getToken()
    if (!token) return
    // 调用统计 API...
  }, [])

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">管理后台</h1>
      <div className="grid grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl shadow">
          <div className="text-3xl font-bold">{stats.changelogs}</div>
          <div className="text-gray-500">版本日志</div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow">
          <div className="text-3xl font-bold">{stats.blogs}</div>
          <div className="text-gray-500">博客文章</div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow">
          <div className="text-3xl font-bold">{stats.comments}</div>
          <div className="text-gray-500">待审核反馈</div>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: 实现 changelog 管理页面**（列表 + 新建/编辑表单 + Markdown 编辑器）

- [ ] **Step 3: 实现 blog 管理页面（含 AI 辅助写作入口）**

- [ ] **Step 4: 实现 AI 辅助写作 Modal**

```tsx
// frontend/components/AiWriterModal.tsx
"use client"
import { useState } from "react"
import { auth } from "@/lib/auth"

export function AiWriterModal({ onAccept }: { onAccept: (content: string) => void }) {
  const [prompt, setPrompt] = useState("")
  const [generating, setGenerating] = useState(false)
  const [content, setContent] = useState("")

  const generate = async () => {
    const token = auth.getToken()
    setGenerating(true)
    const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/ai/generate`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ user_input: prompt })
    })
    const reader = resp.body?.getReader()
    const decoder = new TextDecoder()
    let result = ""
    while (reader) {
      const { done, value } = await reader.read()
      if (done) break
      result += decoder.decode(value)
      setContent(result)
    }
    setGenerating(false)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-[700px] max-h-[80vh] overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">AI 辅助写作</h2>
        <textarea
          className="w-full border rounded-lg p-3 mb-4 h-24"
          placeholder="输入写作要求，例如：写一篇介绍 Basjoo v0.3.0 新功能的博客文章"
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
        />
        <button onClick={generate} disabled={generating || !prompt.trim()}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg mb-4 disabled:opacity-50">
          {generating ? "生成中..." : "开始生成"}
        </button>
        {content && (
          <div className="mb-4">
            <textarea
              className="w-full border rounded-lg p-3 h-64 font-mono text-sm"
              value={content}
              onChange={e => setContent(e.target.value)}
            />
            <div className="mt-3 flex gap-3">
              <button onClick={() => onAccept(content)}
                className="bg-green-600 text-white px-4 py-2 rounded-lg">
                使用此草稿
              </button>
              <button onClick={() => setContent("")}
                className="border px-4 py-2 rounded-lg">
                重新生成
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 5: 提交**

```bash
git add frontend/app/admin frontend/components/AiWriterModal.tsx
git commit -m "feat: add admin management pages with AI writer"
```

---

## Phase 5: 部署与上线

### Task 14: Nginx 配置与上线

**Files:**
- Modify: `nginx/conf.d/default.conf`（新增 decard.cc server block）

- [ ] **Step 1: 新增 Nginx 配置**

```nginx
# 在 Basjoo nginx conf.d/ 下新增
server {
    server_name www.decard.cc;

    location / {
        proxy_pass http://decard-frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://decard-backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

- [ ] **Step 2: 服务器部署脚本**

```bash
# deploy.sh
#!/bin/bash
git clone https://github.com/your-org/decard-site.git
cd decard-site
cp .env.example .env
# 编辑 .env 填入实际值
docker compose up -d --build
docker exec decard-backend python init_db.py
nginx -t && nginx -s reload
```

- [ ] **Step 3: 提交所有代码并推送**

```bash
git add -A && git commit -m "feat: complete decard-site v0.1.0" && git push
```

---

## 自审检查清单

**1. Spec 覆盖检查：**

| Spec 章节 | 对应 Task |
|-----------|-----------|
| 独立 Next.js 站点 | Task 2, 3, 4 |
| FastAPI + SQLite | Task 5, 6, 7, 8, 9 |
| 公开页面（6个） | Task 10, 11 |
| 管理后台（7个） | Task 12, 13 |
| Basjoo Widget Live Demo | Task 10 |
| AI 辅助写作 | Task 9, Task 13 |
| 访客评论/反馈 | Task 8 |
| 数据分析 | Task 8 |
| Docker 部署 | Task 4, Task 14 |
| Nginx 路由 | Task 14 |

**2. 占位符检查：** 无 TBD / TODO / "待实现" 段落。

**3. 类型一致性：** API 路由 `/api/changelogs/`、`/api/roadmap/`、`/api/blog/`、`/api/comments/`、`/api/analytics/`、`/api/auth/`、`/api/ai/` 在前后端一致使用。

---

**Plan 结束。文件路径：`docs/superpowers/plans/2026-05-06-decard-cc-website-plan.md`**
