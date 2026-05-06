# Decard 产品站接入 Basjoo 管理后台设计方案

**日期**: 2026-05-06
**状态**: 已批准
**方案**: 方案 A - 仅加入口链接 + Nginx 路径代理

---

## 1. 背景与目标

### 1.1 背景
- Decard 产品站（`decard-site`）是 Basjoo 的营销展示站点
- Basjoo 有独立的管理后台（`basjoo/frontend-nextjs`），目前运行在 `localhost:3000`
- 需要在产品站添加管理后台入口，实现统一访问

### 1.2 目标
1. 在 Decard 产品站导航栏添加「管理后台」入口
2. 通过 Nginx 代理实现 `decard.cc/admin/*` 路径转发到 Basjoo 前端
3. 通过 Nginx 代理实现 API 调用 `decard.cc/basjoo-api/*` 转发到 Basjoo 后端
4. 管理后台保持独立的登录认证系统

---

## 2. 技术架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   decard-site Nginx  │
              │   (端口 80/443)      │
              └──────────┬──────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
   ┌────────────┐ ┌────────────┐ ┌────────────┐
   │ 产品站前端  │ │ /admin/*   │ │ /basjoo-   │
   │ (Next.js)  │ │ 代理       │ │ api/* 代理 │
   └────────────┘ └─────┬──────┘ └─────┬──────┘
                         │              │
                         ▼              ▼
                  ┌────────────┐ ┌────────────┐
                  │ Basjoo     │ │ Basjoo     │
                  │ 前端:3000  │ │ 后端:8000  │
                  └────────────┘ └────────────┘
```

### 2.2 路径映射规则

| 外部路径 | 内部服务 | 说明 |
|----------|----------|------|
| `decard.cc/*` | decard-site 前端 | 产品站页面（原有规则） |
| `decard.cc/admin/*` | Basjoo 前端 `:3000/*` | 管理后台入口 |
| `decard.cc/basjoo-api/*` | Basjoo 后端 `:8000/*` | 管理后台 API 调用 |

---

## 3. 改动详情

### 3.1 文件清单

| 项目 | 文件路径 | 改动类型 |
|------|----------|----------|
| decard-site | `nginx/conf.d/basjoo-admin.conf` | **新增** - Nginx 代理配置 |
| decard-site | `frontend/app/page.tsx` | 修改 - 添加导航栏链接 |
| basjoo | `frontend-nextjs/.env.local` | **新增** - 开发环境 API 地址 |

### 3.2 Nginx 配置（新增）

**文件**: `decard-site/nginx/conf.d/basjoo-admin.conf`

```nginx
# Basjoo 管理后台代理配置

# 代理 Basjoo 前端（管理后台）
location /admin {
    # 移除 /admin 前缀，转发到 Basjoo 前端根路径
    rewrite ^/admin(/.*)? $1 break;
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # WebSocket 支持（Basjoo 可能使用）
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}

# 代理 Basjoo 后端 API
location /basjoo-api {
    # 移除 /basjoo-api 前缀
    rewrite ^/basjoo-api(/.*)? $1 break;
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 3.3 前端导航栏改动

**文件**: `decard-site/frontend/app/page.tsx`

在现有导航栏添加「管理后台」链接：

```tsx
<nav className="flex items-center gap-6">
  {/* 现有链接 */}
  <Link href="/" className="text-gray-600 hover:text-blue-600">
    首页
  </Link>

  {/* 新增：管理后台入口 */}
  <Link
    href="/admin"
    className="text-gray-600 hover:text-blue-600 flex items-center gap-1"
  >
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
    管理后台
  </Link>
</nav>
```

### 3.4 Basjoo 前端环境配置（开发环境）

**文件**: `basjoo/frontend-nextjs/.env.local`

```bash
# 开发环境：代理 API 调用到正确地址
NEXT_PUBLIC_API_BASE_URL=
BACKEND_PROXY_TARGET=http://localhost:8000
```

---

## 4. 用户流程

### 4.1 访问路径

```
1. 用户访问 decard.cc
2. 点击导航栏「管理后台」
3. 浏览器跳转到 decard.cc/admin
4. Nginx 代理到 localhost:3000/admin
5. Basjoo 前端检查登录状态
   ├─ 未登录 → 显示登录页
   └─ 已登录 → 显示管理后台
```

### 4.2 登录流程

```
1. 用户在 Basjoo 登录页输入邮箱密码
2. 请求发送至 /basjoo-api/api/admin/login
3. Nginx 代理到 localhost:8000/api/admin/login
4. Basjoo 后端验证并返回 JWT Token
5. 前端存储 Token，跳转到管理后台首页
```

---

## 5. 安全考虑

| 方面 | 措施 |
|------|------|
| CORS | Basjoo 后端已配置 `ALLOWED_ORIGINS=*`（开发环境） |
| 路径隔离 | `/admin` 和 `/basjoo-api` 独立路径，不影响产品站 |
| Cookie 安全 | Basjoo 前端使用 HttpOnly Cookie 存储 Token |
| 生产环境 | 需配置具体的 `ALLOWED_ORIGINS` 域名列表 |

---

## 6. 测试计划

| 测试项 | 验证方法 |
|--------|----------|
| 导航链接 | 点击「管理后台」能正确跳转 |
| 登录页加载 | `/admin` 路径正确显示 Basjoo 登录页 |
| 登录功能 | 能使用管理员账号登录 |
| 知识库功能 | 登录后能访问知识库页面 |
| API 代理 | 前端 API 调用能正确代理到后端 |

---

## 7. 部署步骤

### 阶段 1：开发环境验证
1. 配置 Basjoo 后端代理路径
2. 添加前端导航栏链接
3. 验证本地访问流程

### 阶段 2：生产环境部署
1. 更新 Decard 产品站 Nginx 配置
2. 重载 Nginx
3. 验证公网访问

---

## 8. 后续优化方向

- [ ] 统一登录体验（需给产品站加登录系统）
- [ ] 添加访问统计（哪些用户访问了管理后台）
- [ ] SSO 单点登录集成

---

## 9. 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-05-06 | v1.0 | 初始版本 |
