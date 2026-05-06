# Decard 产品站接入 Basjoo 管理后台实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Decard 产品站添加「管理后台」入口链接，通过 Nginx 代理实现 Basjoo 管理后台的访问

**Architecture:** Decard 产品站导航栏添加「管理后台」链接，Nginx 配置 `/admin/*` 和 `/basjoo-api/*` 路径代理到本地 Basjoo 服务

**Tech Stack:** Next.js, Nginx, FastAPI

---

## 文件结构

| 操作 | 文件路径 | 职责 |
|------|----------|------|
| 创建 | `decard-site/nginx/conf.d/basjoo-admin.conf` | Nginx 路径代理配置 |
| 修改 | `decard-site/frontend/app/page.tsx` | 添加导航栏链接 |
| 创建 | `basjoo/frontend-nextjs/.env.local` | Basjoo 前端开发环境配置 |

---

## 实施任务

### Task 1: 创建 Nginx 代理配置

**Files:**
- 创建: `decard-site/nginx/conf.d/basjoo-admin.conf`

- [ ] **Step 1: 创建 Nginx 配置文件**

文件: `decard-site/nginx/conf.d/basjoo-admin.conf`

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

    # WebSocket 支持
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

- [ ] **Step 2: 提交配置**

```bash
cd /Users/sunm15/Documents/basjoo/decard-site
git add nginx/conf.d/basjoo-admin.conf
git commit -m "feat: add Nginx proxy config for Basjoo admin backend"
```

---

### Task 2: 添加前端导航栏链接

**Files:**
- 修改: `decard-site/frontend/app/page.tsx`

- [ ] **Step 1: 查看当前页面结构，找到导航栏位置**

运行: `cat /Users/sunm15/Documents/basjoo/decard-site/frontend/app/page.tsx`

找到导航栏 `<nav>` 或 `<header>` 组件的位置。

- [ ] **Step 2: 在导航栏中添加「管理后台」链接**

在现有导航链接附近添加：

```tsx
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
```

- [ ] **Step 3: 提交代码**

```bash
cd /Users/sunm15/Documents/basjoo/decard-site
git add frontend/app/page.tsx
git commit -m "feat: add admin backend navigation link"
```

---

### Task 3: 配置 Basjoo 前端环境变量

**Files:**
- 创建: `basjoo/frontend-nextjs/.env.local`

- [ ] **Step 1: 创建环境配置文件**

文件: `basjoo/frontend-nextjs/.env.local`

```bash
# 开发环境：代理 API 调用到正确地址
NEXT_PUBLIC_API_BASE_URL=
BACKEND_PROXY_TARGET=http://localhost:8000
```

- [ ] **Step 2: 提交配置**

```bash
cd /Users/sunm15/Documents/basjoo
git add basjoo/frontend-nextjs/.env.local
git commit -m "feat: add Basjoo frontend dev env config"
```

---

### Task 4: 验证与测试

**Files:**
- 无文件变更，纯测试验证

- [ ] **Step 1: 验证 Nginx 配置语法**

运行:
```bash
nginx -t -c /Users/sunm15/Documents/basjoo/decard-site/nginx/nginx.conf
```
预期: `syntax is ok`

- [ ] **Step 2: 重载 Nginx 配置**

运行:
```bash
sudo nginx -s reload
```
或重启 Nginx 服务。

- [ ] **Step 3: 验证页面访问**

1. 访问 `http://localhost/admin` 验证跳转到 Basjoo 登录页
2. 检查导航栏「管理后台」链接是否显示

- [ ] **Step 4: 验证登录功能**

1. 使用管理员账号登录
2. 验证能正常进入管理后台

---

## 验证检查清单

- [ ] `/admin` 路径正确代理到 Basjoo 前端
- [ ] 导航栏显示「管理后台」链接
- [ ] 点击链接能跳转到 Basjoo 登录页
- [ ] 能使用管理员账号登录
- [ ] 登录后能访问知识库页面
- [ ] API 调用正确代理到 Basjoo 后端

---

## 后续步骤

完成后可考虑：
- [ ] 公网服务器部署 Nginx 配置
- [ ] 配置 SSL 证书（生产环境）
