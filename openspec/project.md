# Project Context

## Purpose

**Ccbot** is a RAG-based (Retrieval-Augmented Generation) intelligent system that enables businesses to deploy smart chatbots powered by their own knowledge bases. The system supports:

- **Q&A Knowledge Sources**: Curated question-answer pairs for precise responses
- **URL Knowledge Sources**: Automatic web content scraping and indexing
- **Web Widget**: Embeddable chat component for any website
- **Multi-LLM Support**: OpenAI, Anthropic (Claude), Google (Gemini), Azure OpenAI, and compatible APIs
- **Admin Dashboard**: Full management interface for knowledge, agents, and settings

**Status**: Production-ready repository with FastAPI backend, Next.js admin dashboard, embeddable widget, and Docker-based deployment.

## Tech Stack

### Backend (`backend/`)
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | 0.115.0 | Async web framework |
| SQLAlchemy | 2.0.35 | Async ORM with aiosqlite |
| Qdrant | Docker service | Vector similarity search |
| Jina embeddings / provider-specific embeddings | External API | Text embeddings |
| APScheduler | 3.10.4 | Background task scheduling |
| Pydantic | 2.10.1 | Request/response validation |
| OpenAI SDK | 1.54.0 | LLM API client |
| Anthropic SDK | 0.40.0 | Claude API client |
| google-generativeai | 0.8.3 | Gemini API client |

### Frontend (`frontend-nextjs/`)
| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 14.2.0 | App framework and routing |
| React | 18.3.1 | UI framework |
| TypeScript | ~5.6.2 | Type safety |
| i18next | 25.7.4 | Internationalization (zh-CN, en-US) |
| react-markdown | 10.1.0 | Markdown rendering |

### Widget (`widget/`)
| Technology | Version | Purpose |
|------------|---------|---------|
| TypeScript | 5.3.0 | Type safety |
| esbuild | 0.19.8 | Bundler (ESM + IIFE outputs) |

### Infrastructure
- **Docker + Docker Compose**: Container orchestration
- **Nginx**: Reverse proxy for frontend
- **SQLite**: Default application database
- **Redis**: Rate limiting, cache fallback, task coordination
- **Qdrant**: Vector storage and retrieval

### Deployment
- `install-deploy.sh`: One-command production installer for Ubuntu/Debian. Auto-installs Docker/Compose, clones/syncs repo, deploys via `deploy.sh`, and verifies health.
- `deploy.sh`: Low-level production deploy entrypoint. Prepares `.env` via `env_bootstrap.py` and runs `docker compose --profile prod up -d --build`.
- `bootstrap-env.sh`: Simple `.env` bootstrap helper.
- `docker-compose.yml`: Main orchestration with `prod` and `dev` profiles. Production uses `backend-prod`, `frontend-prod`, `nginx`, `redis`, `qdrant`.
- Persistent data is stored in Docker named volumes (`backend-data`, `redis-data`, `qdrant-data`). Do not use `docker compose down -v` unless intentionally resetting widget identity.

## Project Conventions

### Code Style

#### Python (Backend)
- **Imports**: stdlib → third-party → local
- **Naming**: `snake_case` (functions/vars), `PascalCase` (classes), `UPPER_SNAKE` (constants)
- **Type Hints**: Required for all function signatures
- **Validation**: Use Pydantic models for all request/response schemas
- **Async**: All DB operations and HTTP calls must be async
- **Error Handling**: Use `HTTPException` with proper status codes

```python
# Example
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from models import Agent

async def get_agent(agent_id: str, db: AsyncSession) -> Agent:
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
```

#### TypeScript (Frontend)
- **Imports**: React → libraries → components → types
- **Naming**: `PascalCase` (components, types), `camelCase` (vars/funcs), `useCamelCase` (hooks)
- **API Calls**: Always use typed `api` client from `services/api.ts`
- **i18n**: Use translation keys, never hardcoded strings

```typescript
// Example
import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import AdminLayout from '../components/AdminLayout'
import { api, Agent } from '../services/api'

const { t } = useTranslation('common')
```

### Architecture Patterns

#### API Design
- **Prefix**: `/api/v1/`
- **Resource Actions**: Use `:action` suffix (e.g., `/api/v1/qa:list`, `/api/v1/index:rebuild`)
- **Pagination**: `skip` and `limit` query parameters
- **Authentication**: JWT tokens via `Authorization: Bearer` header

#### Database
- **ORM**: SQLAlchemy async with `AsyncSession`
- **ID Format**: Prefixed UUIDs (`agt_xxxx` for agents, `qa_xxxx` for Q&A, `url_xxxx` for URLs)
- **Timestamps**: Always use `timezone.utc`
- **Migrations**: Manual scripts in `backend/migrations/`

#### Frontend State
- **No Redux/Zustand**: React Context + local state only
- **Auth**: `useAuth()` hook from `AuthContext`
- **Protected Routes**: Wrap with `<RequireAuth>` component

#### Service Layer
- `llm_service.py`: LLM API abstraction (supports multiple providers and mock mode)
- `rag_qdrant.py`: RAG retrieval and response generation against Qdrant
- `qdrant_store.py`: Qdrant collection and vector management
- `scraper.py`: URL content extraction via Jina Reader API with direct fetch fallback
- `crawler.py`: Site-wide crawling built on top of `URLScraper`
- `scheduler.py`: Background tasks with APScheduler (URL fetch, history cleanup, session auto-close)
- `url_safety.py`: SSRF protection — validates URLs, blocks localhost/private IPs/DNS rebinding
- `task_lock.py`: Task concurrency control to prevent conflicting operations on the same agent
- `core/encryption.py`: Fernet-based API key encryption for stored provider credentials

### Testing Strategy

#### Backend Tests
- **Framework**: pytest + pytest-asyncio
- **Location**: `backend/tests/`
- **Coverage**: broad backend coverage across API, deployment, stress, edge-case, integration, observability, security, and service-layer scenarios
- **Categories**: Core API, Production, Stress, Edge Case, Integration, Observability, Extreme Stress, Security, Service Layer

```bash
# Run all tests
cd backend && pytest

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

#### Frontend
- **Type Checking**: `npx tsc --noEmit`
- **Linting**: `npm run lint` (ESLint)
- **Build Verification**: `npm run build`

### Git Workflow

- **Branching**: Feature branches from `main`
- **Naming**: `feature/`, `fix/`, `refactor/` prefixes
- **Commits**: Conventional commits preferred
- **PRs**: Required for all changes to `main`

## Domain Context

### Core Entities
| Entity | ID Format | Description |
|--------|-----------|-------------|
| Workspace | Integer | Container for one user's resources |
| Agent | `agt_xxxx` | AI assistant configuration (LLM, prompts, settings) |
| QAItem | `qa_xxxx` | Question-answer knowledge pair |
| URLSource | `url_xxxx` | Web page knowledge source |
| ChatSession | `sess_xxxx` | Multi-turn conversation session |

### RAG Flow
1. User sends message → `/api/v1/chat`
2. System retrieves relevant contexts from the agent's Qdrant collection (Q&A + URL content)
3. Contexts are injected into LLM prompt with system prompt
4. LLM generates response with source citations
5. Response includes `sources` array for transparency

### Quota System
- Daily message limits per agent
- Automatic reset at midnight (agent's timezone)
- Tracked in `WorkspaceQuota` model

## Important Constraints

### Anti-Patterns (NEVER do these)
| Don't | Do Instead |
|-------|------------|
| `as any` or `@ts-ignore` | Fix the type properly |
| Hardcoded UI strings | Use i18n translation keys |
| `console.log` in production | Use proper logging |
| Empty catch blocks | Log or handle the error |
| Synchronous DB calls | Use async/await |

### Security Requirements
- SQL injection protection (via SQLAlchemy ORM)
- XSS attack prevention
- Input validation on all endpoints
- Rate limiting (Redis-first with in-memory fallback)
- CORS with shared helper for early responses; `Origin: null` only when explicitly enabled
- SSRF protection for URL ingestion: blocks localhost, direct IPs, private/resolved-private IPs
- Widget embed origin whitelist enforcement per agent
- API key encryption at rest via Fernet key (`core/encryption.py`)
- Secret key auto-generation and persistence with `REQUIRE_SECRET_KEY` enforcement in production

### Frontend Design & Interaction Constraints

Use these constraints as the single source of truth for UI consistency across `frontend-nextjs/` and `widget/` surfaces.

#### Design Goals (Modern, Unified, Professional)
- Modern: clean, low-noise, information-first interfaces with restrained decoration
- Unified: consistent visual language across pages/components; no ad-hoc local styles
- Professional: high readability, trustworthy hierarchy, enterprise-grade maintainability

#### Core Design Keywords
- Order, restraint, information-first, precision, consistency, readability, accessibility, scalability

#### Design Token Rules (Mandatory)
- All colors, spacing, typography, radius, shadows, and motion values must come from shared design tokens.
- Do not hardcode one-off hex values, arbitrary spacing, or ad-hoc shadow values in feature code.
- Token layering:
    - Primitive tokens: raw values (color scales, spacing steps)
    - Semantic tokens: purpose-driven values (`action-primary`, `text-secondary`, `state-error`)
    - Component tokens: component-level aliases mapped from semantic tokens

#### Color System Constraints
- Keep neutral colors as the dominant visual base (background, borders, body text).
- Reserve brand/primary color for key CTAs, active states, and focus emphasis.
- Semantic colors (success/warning/error/info) are for state meaning only, not decoration.
- Do not rely on color alone to convey critical status; pair with icon/text.
- Light and dark modes must preserve semantic meaning (same intent, adapted contrast), not re-interpret states.

#### Typography Constraints
- Use a defined type scale; avoid arbitrary font sizes.
- Default body text should prioritize readability (recommended minimum: 14px equivalent).
- Limit visual hierarchy depth per view (avoid too many competing heading/body sizes).
- Chinese/English font stacks must be explicitly defined and consistently applied.

#### Spacing & Layout Constraints
- Use a fixed spacing scale (8pt system; 4pt only for fine adjustments).
- Page/layout spacing must align to grid and scale steps; avoid random margins/paddings.
- Recommended structure:
    - 12-column grid on desktop
    - Mobile-first breakpoints
    - Stable navigation hierarchy (top-level nav + section nav + content area)
- Keep alignment mathematically consistent; avoid "almost aligned" placements.

#### Shape, Border, Elevation Constraints
- Radius must use a limited tier set (for example: control/card/dialog tiers), not custom per component.
- Border usage should be subtle and consistent; avoid stacking heavy borders and shadows together.
- Elevation (shadow) is for layering and interaction feedback, not decoration.

#### Component Consistency Constraints
- Every interactive component must define complete states:
    - default, hover, active/pressed, focus-visible, disabled, loading (where applicable)
- Buttons:
    - Primary for one main action per context
    - Secondary/ghost for lower-priority actions
    - Danger only for destructive actions
- Forms:
    - Labels cannot be replaced by placeholder-only design
    - Validation errors must be field-local, explicit, and actionable
- Data display (table/tag/badge/notice/empty/skeleton) must follow shared patterns and avoid per-page reinterpretation.

#### Motion Constraints
- Motion should clarify state/structure changes, not add visual noise.
- Recommended duration bands:
    - 100-160ms: micro interactions (hover/press)
    - 180-240ms: component enter/exit
    - 240-320ms: page-level transitions
- Avoid animating many properties at once; prefer opacity/transform.
- High-frequency data updates should minimize animation to preserve readability.

#### Responsive Constraints
- Mobile-first implementation is required.
- Suggested breakpoints:
    - xs: 0-575
    - sm: 576-767
    - md: 768-1023
    - lg: 1024-1279
    - xl: 1280-1535
    - 2xl: 1536+
- On small screens:
    - prioritize single-column flows
    - keep touch targets at usable sizes (recommended minimum 44x44)
    - convert dense tables to card/key-field views when necessary

#### Accessibility Constraints (Non-Negotiable)
- Meet WCAG contrast guidance (normal text at least 4.5:1, large text at least 3:1).
- All interactive elements must have visible focus states.
- Keyboard navigation order must match visual reading order.
- Use semantic HTML and ARIA only where needed to extend semantics.
- Respect reduced-motion user preferences.

#### Engineering Implementation Constraints
- Centralize tokens and component primitives in shared frontend layers; avoid duplicate style sources.
- New UI patterns must be added to shared components before broad reuse.
- Style changes affecting shared components require regression checks (visual and interaction states).
- Pull requests with UI changes should include a consistency check against:
    - token usage
    - state completeness
    - responsive behavior
    - accessibility requirements

#### Token Naming Convention (Recommended)
- Use purpose-first names, not raw color names.
- Keep naming stable across themes and map light/dark by token value, not by token key.
- Suggested token groups:
    - `color-bg-*`: background layers
    - `color-text-*`: text hierarchy
    - `color-border-*`: border hierarchy
    - `color-action-*`: interactive/action tokens
    - `color-state-*`: semantic status tokens
    - `space-*`: spacing scale
    - `radius-*`: corner radius tiers
    - `shadow-*`: elevation tiers
    - `motion-duration-*`, `motion-easing-*`: animation system
- Example naming set:
    - `color-bg-base`, `color-bg-subtle`, `color-bg-elevated`
    - `color-text-primary`, `color-text-secondary`, `color-text-muted`
    - `color-border-default`, `color-border-strong`
    - `color-action-primary`, `color-action-primary-hover`, `color-action-primary-active`
    - `color-state-success`, `color-state-warning`, `color-state-error`, `color-state-info`
    - `space-1` to `space-10` (mapped to scale values)
    - `radius-sm`, `radius-md`, `radius-lg`
    - `shadow-1`, `shadow-2`, `shadow-3`

#### UI Pull Request Checklist (Required for UI Changes)
- Token usage
    - No hardcoded color/spacing/radius/shadow values in feature UI code
    - New visual values are added through token definitions first
- Component state completeness
    - Interactive components implement default/hover/active/focus-visible/disabled
    - Async actions include loading behavior without layout shift
- Responsive behavior
    - Mobile-first layout validated at key breakpoints
    - Dense content remains readable on small screens
- Accessibility
    - Contrast meets WCAG guidance
    - Keyboard-only navigation works end-to-end
    - Focus-visible is clearly perceivable
    - Status and errors are not color-only
- Consistency and regression
    - Reused existing shared component where possible
    - New pattern documented before repeated usage
    - Visual/interaction regression checks completed for modified shared components

### Performance Targets
| Metric | Target | Achieved |
|--------|--------|----------|
| Response time | <100ms | 4.0ms |
| Throughput | >50 req/s | 384.7 req/s |
| Concurrent users | >100 | 1000+ |
| Success rate | >99% | 100% (normal load) |

## External Dependencies

### Required Services
| Service | Purpose | Required |
|---------|---------|----------|
| LLM API | Text generation | Yes (or use Mock mode) |
| Jina Reader API | URL content extraction | Optional |

### Supported LLM Providers
| Provider | Environment Variable | Notes |
|----------|---------------------|-------|
| OpenAI / Compatible | `OPENAI_API_KEY` | Default, works with DeepSeek |
| Anthropic | `ANTHROPIC_API_KEY` | Claude models |
| Google | `GOOGLE_API_KEY` | Gemini models |
| Azure OpenAI | `AZURE_OPENAI_API_KEY` | Enterprise deployments |

### Key Configuration
```bash
# Required or zero-config persisted on first startup
SECRET_KEY=
DEFAULT_AGENT_ID=
REQUIRE_SECRET_KEY=false          # set true in production

# LLM (choose provider-specific keys as needed)
DEEPSEEK_API_KEY=
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
GOOGLE_API_KEY=xxx
AZURE_OPENAI_API_KEY=xxx

# Optional
JINA_API_KEY=xxx
DATABASE_URL=sqlite:////app/data/ccbot.db
ALLOWED_ORIGINS=http://localhost:3000
SECRET_KEY_FILE=/app/data/.secret_key
ENCRYPTION_KEY_FILE=/app/data/.encryption_key
cors_allow_null_origin=false       # enable for file:// widget preview in dev only
```

## File Locations Quick Reference

| Task | Location |
|------|----------|
| Add API endpoint | `backend/api/v1/endpoints.py` or `url_endpoints.py` |
| Add Pydantic schema | `backend/api/v1/schemas.py` |
| Modify DB models | `backend/models.py` |
| Add frontend page | `frontend-nextjs/src/views/` + route entry in `app/(dashboard)/` |
| Modify API client | `frontend-nextjs/src/services/api.ts` |
| Add translations | `frontend-nextjs/src/locales/{lang}/common.json` |
| Backend tests | `backend/tests/` |
| Widget source | `widget/src/CcbotWidget.tsx` |
