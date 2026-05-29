# PROJECT_RULES.md — StaySync

> **Version:** 1.0  
> **Last Updated:** 2026-05-30  
> **Status:** Active  
> **Maintained By:** Core Engineering Team

---

## 1. Project Identity

| Field            | Value                                                        |
| ---------------- | ------------------------------------------------------------ |
| **Project Name** | StaySync                                                     |
| **Tagline**      | Live Accommodation Hold-Management Platform                  |
| **Domain**       | Student Accommodation Marketplace (PGs, Hostels, Flats)      |
| **Target Users** | Students seeking accommodation · Property Owners/Managers    |
| **Scope**        | College-project grade with production-level architecture      |

---

## 2. Tech Stack (Locked)

### Frontend
| Technology       | Version / Notes                        |
| ---------------- | -------------------------------------- |
| React            | 18.x with TypeScript                   |
| Vite             | 5.x — build toolchain                  |
| TailwindCSS      | 3.x — utility-first CSS               |
| ShadCN UI        | Component library over Radix primitives |
| TanStack Query   | v5 — server state management           |
| Zustand          | Lightweight client state               |
| React Router     | v6 — routing                           |
| Framer Motion    | Animations & transitions               |
| Axios            | HTTP client                            |
| Zod              | Schema validation                      |
| React Hook Form  | Form management                        |

### Backend
| Technology       | Version / Notes                        |
| ---------------- | -------------------------------------- |
| FastAPI          | 0.110+ — async Python web framework    |
| Python           | 3.12+                                  |
| SQLAlchemy       | 2.0 — async ORM                        |
| Alembic          | Database migrations                    |
| Pydantic         | v2 — data validation                   |
| PostgreSQL       | Via Supabase                           |
| JWT              | Access + Refresh token authentication  |
| WebSockets       | FastAPI native WebSocket support        |
| Redis            | Caching + background job queues        |
| Celery           | Distributed task queue                 |

### Infrastructure
| Technology       | Purpose                                |
| ---------------- | -------------------------------------- |
| Supabase         | PostgreSQL database + Storage + Auth   |
| Docker           | Containerization                       |
| Docker Compose   | Multi-service orchestration            |
| Netlify          | Frontend deployment                    |
| Render           | Backend deployment                     |

---

## 3. Architecture Principles

### 3.1 Backend — Clean Architecture
```
Request → Router → Service → Repository → Database
                      ↕
               Domain Models / DTOs
```

- **Routers (API Layer):** HTTP endpoint definitions only. No business logic.
- **Services (Business Layer):** All business rules, validation, orchestration.
- **Repositories (Data Layer):** Database queries only. No business logic.
- **Schemas (DTOs):** Pydantic models for request/response serialization.
- **Models (Domain):** SQLAlchemy ORM models representing database tables.

### 3.2 Frontend — Feature-Based Architecture
```
src/
├── features/       ← Domain-specific modules (auth, property, holds)
├── components/     ← Shared reusable UI components
├── hooks/          ← Shared custom hooks
├── services/       ← API client layer
├── stores/         ← Global state (Zustand)
├── layouts/        ← Page layout wrappers
├── pages/          ← Route-level page components
└── lib/            ← Utility functions and config
```

### 3.3 Mandatory Patterns
- **Dependency Injection:** All services receive repositories via DI.
- **Repository Pattern:** All database access goes through repositories.
- **DTO Separation:** Never expose ORM models in API responses.
- **Error Boundaries:** React error boundaries on every route.
- **Optimistic Locking:** For all concurrent state mutations (holds, bookings).

---

## 4. Coding Standards

### 4.1 General Rules
- **DRY:** Do not repeat logic. Extract shared utilities.
- **KISS:** Prefer simple, readable solutions over clever abstractions.
- **SOLID:** Apply single-responsibility at function, class, and module levels.
- **Type Safety:** TypeScript `strict` mode on frontend. Pydantic models on backend.
- **No `any`:** TypeScript `any` is forbidden except in type guard utilities.
- **No Magic Numbers:** Use named constants or enums.
- **Max Function Length:** 40 lines (soft limit). Refactor if exceeded.
- **Max File Length:** 300 lines (soft limit). Split into modules if exceeded.

### 4.2 Naming Conventions

| Context                  | Convention          | Example                         |
| ------------------------ | ------------------- | ------------------------------- |
| Python files             | `snake_case`        | `hold_service.py`               |
| Python classes           | `PascalCase`        | `HoldRequest`                   |
| Python functions/vars    | `snake_case`        | `create_hold_request()`         |
| Python constants         | `UPPER_SNAKE_CASE`  | `MAX_ACTIVE_HOLDS`              |
| TypeScript files         | `camelCase`         | `holdService.ts`                |
| React components         | `PascalCase`        | `PropertyCard.tsx`              |
| React hooks              | `camelCase`         | `useHoldStatus.ts`              |
| CSS/style files          | `camelCase`         | `propertyCard.module.css`       |
| Database tables          | `snake_case`        | `hold_requests`                 |
| Database columns         | `snake_case`        | `created_at`                    |
| API endpoints            | `kebab-case`        | `/api/v1/hold-requests`         |
| Environment variables    | `UPPER_SNAKE_CASE`  | `DATABASE_URL`                  |

### 4.3 Python-Specific Rules
- Use `async/await` for all I/O-bound operations.
- Use `Annotated` types with `Depends()` for FastAPI dependency injection.
- All Pydantic models must use `model_config = ConfigDict(from_attributes=True)`.
- Use `Enum` classes for fixed value sets (roles, statuses).
- Docstrings on all public service methods (Google style).
- No bare `except:` clauses. Always catch specific exceptions.

### 4.4 TypeScript/React-Specific Rules
- Functional components only. No class components.
- Props must be typed with explicit interfaces (not inline).
- Use `const` by default. `let` only when mutation is required.
- Custom hooks must start with `use` prefix.
- Memoize expensive computations with `useMemo` / `useCallback`.
- API calls must go through the `services/` layer, never directly in components.

### 4.5 Import Order (Both Languages)
```
1. Standard library / Node built-ins
2. Third-party packages
3. Internal absolute imports (aliases)
4. Relative imports
--- blank line between groups ---
```

---

## 5. API Design Standards

### 5.1 URL Structure
```
/api/v1/{resource}              → Collection
/api/v1/{resource}/{id}         → Single resource
/api/v1/{resource}/{id}/{sub}   → Sub-resource
```

### 5.2 HTTP Methods
| Method   | Usage                          |
| -------- | ------------------------------ |
| `GET`    | Read (idempotent)              |
| `POST`   | Create                         |
| `PUT`    | Full replace                   |
| `PATCH`  | Partial update                 |
| `DELETE` | Soft delete (set `deleted_at`) |

### 5.3 Response Envelope
```json
{
  "success": true,
  "data": { ... },
  "message": "Property created successfully",
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 150
  }
}
```

### 5.4 Error Response
```json
{
  "success": false,
  "error": {
    "code": "HOLD_ALREADY_ACTIVE",
    "message": "An active hold already exists for this bed.",
    "details": { "bed_id": "uuid", "expires_at": "ISO-8601" }
  }
}
```

### 5.5 Status Codes
| Code  | Usage                                        |
| ----- | -------------------------------------------- |
| `200` | Success                                      |
| `201` | Created                                      |
| `204` | No Content (successful delete)               |
| `400` | Validation error / bad request               |
| `401` | Unauthenticated                              |
| `403` | Forbidden (insufficient role)                |
| `404` | Resource not found                           |
| `409` | Conflict (double booking, race condition)    |
| `422` | Unprocessable entity                         |
| `429` | Rate limited                                 |
| `500` | Internal server error                        |

---

## 6. Security Rules

- **Passwords:** Hash with `bcrypt` (min 12 rounds).
- **JWT Access Tokens:** 15-minute expiry. Signed with RS256 or HS256.
- **JWT Refresh Tokens:** 7-day expiry. Rotate on every use.
- **CORS:** Whitelist only known frontend origins.
- **Rate Limiting:** Max 100 requests/minute per IP for public endpoints.
- **Input Validation:** All inputs validated via Pydantic (backend) and Zod (frontend).
- **SQL Injection:** Use parameterized queries only (SQLAlchemy ORM handles this).
- **XSS:** Sanitize all user-generated content before rendering.
- **CSRF:** Use SameSite cookie attributes + custom headers.
- **Secrets:** Never commit `.env` files. Use `.env.example` templates.
- **File Uploads:** Validate MIME type + file size. Max 5MB per image.
- **Role Guards:** Every API endpoint must validate user role server-side.

---

## 7. Database Rules

- **Soft Deletes:** All tables use `deleted_at` timestamp. Never hard delete.
- **Timestamps:** Every table has `created_at` and `updated_at`.
- **UUIDs:** Use UUID v4 for all primary keys.
- **Indexes:** Add indexes on all foreign keys and frequently queried columns.
- **Constraints:** Use database-level constraints (NOT NULL, UNIQUE, CHECK).
- **Migrations:** All schema changes go through Alembic. No manual DDL.
- **Naming:** Tables are plural `snake_case`. Columns are singular `snake_case`.
- **Enums:** Store as PostgreSQL `VARCHAR` with application-level validation.

---

## 8. Git & Version Control

### 8.1 Branch Strategy
```
main            ← Production-ready code
├── develop     ← Integration branch
│   ├── feature/auth-system
│   ├── feature/property-crud
│   ├── feature/hold-management
│   └── fix/hold-expiry-race-condition
```

### 8.2 Commit Messages
Follow **Conventional Commits:**
```
feat(auth): add JWT refresh token rotation
fix(holds): prevent race condition in concurrent hold requests
docs(schema): update database schema for waitlist table
refactor(api): extract property service from router
chore(docker): update Python base image to 3.12-slim
test(holds): add unit tests for hold expiry logic
```

### 8.3 Rules
- No direct commits to `main` or `develop`.
- Feature branches must be rebased before merge.
- Every PR must pass linting + type checks + tests.
- Squash merge feature branches into `develop`.

---

## 9. Testing Standards

| Layer              | Tool                    | Minimum Coverage |
| ------------------ | ----------------------- | ---------------- |
| Backend unit tests | Pytest + pytest-asyncio | 70%              |
| Backend API tests  | Pytest + httpx          | All endpoints    |
| Frontend unit      | Vitest + RTL            | Critical paths   |
| Frontend E2E       | Playwright (optional)   | Happy paths      |

### Rules
- Test files live adjacent to source files or in a `tests/` directory.
- Mock external services (Supabase, Redis, email) in unit tests.
- Integration tests use a test database (separate from dev).
- No test should depend on execution order.

---

## 10. Environment Configuration

### Required `.env` Variables
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx

# Authentication
JWT_SECRET_KEY=xxx
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_PROVIDER=resend
EMAIL_API_KEY=xxx
EMAIL_FROM_ADDRESS=noreply@staysync.app

# Google Maps
GOOGLE_MAPS_API_KEY=xxx

# Application
ENVIRONMENT=development
DEBUG=true
ALLOWED_ORIGINS=http://localhost:5173
API_V1_PREFIX=/api/v1
```

---

## 11. Development Phase Rules

### Phase Isolation
- Each phase must be independently deployable and runnable.
- Phase N+1 must not break Phase N functionality.
- No forward references to unimplemented phase features.

### Phase Boundaries
| Phase | Scope                                            | Status    |
| ----- | ------------------------------------------------ | --------- |
| 1     | Foundation + Auth + Property CRUD                | 🔜 Next   |
| 2     | Hold System + Realtime + Notifications           | ⏳ Queued |
| 3     | Optimization + Analytics + Security Hardening    | ⏳ Queued |

### Inter-Phase Rules
- Database schema must be forward-compatible. Plan for Phase 2/3 columns.
- API versioning (`/api/v1/`) ensures backward compatibility.
- Feature flags for phase-gated functionality.
- Stub interfaces for services that will be implemented in future phases.

---

## 12. Documentation Requirements

- Every module must have a `README.md` if it contains non-obvious setup.
- API endpoints are auto-documented via FastAPI OpenAPI (`/docs`).
- Database changes must update `DATABASE_SCHEMA.md`.
- Architecture changes must update `ARCHITECTURE.md`.
- Phase completions must update `PHASE_STATUS.md` and `SESSION_SUMMARY.md`.

---

## 13. Performance Budgets

| Metric                    | Target                |
| ------------------------- | --------------------- |
| API response time (p95)   | < 200ms               |
| Frontend First Paint      | < 1.5s                |
| Frontend Bundle Size      | < 500KB (gzipped)     |
| Database query time (p95) | < 50ms                |
| WebSocket latency         | < 100ms               |
| Image upload size limit   | 5MB per file          |
| Max active holds/student  | 3                     |
| Hold request cooldown     | 30 minutes per bed    |

---

## 14. Prohibited Patterns

| ❌ Do NOT                                    | ✅ Instead                                    |
| -------------------------------------------- | --------------------------------------------- |
| Put business logic in routers                | Use service layer                             |
| Return ORM models from API                   | Use Pydantic response schemas                 |
| Use `any` in TypeScript                      | Define proper types/interfaces                |
| Hardcode configuration values               | Use environment variables                     |
| Trust frontend state for bookings           | Always validate server-side                   |
| Use `SELECT *` in queries                    | Select only needed columns                    |
| Skip error handling                          | Use centralized exception handlers            |
| Commit secrets or `.env` files               | Use `.env.example` templates                  |
| Write monolithic components (500+ lines)     | Split into smaller, focused components        |
| Implement payment/billing features           | Out of scope for this project                 |

---

## 15. No-Payment Scope Boundary

This project explicitly **excludes**:
- Online payments / payment gateways
- Subscription billing
- Transaction systems / wallets
- Refund systems

The architecture must remain **extensible** for future payment integration, but no payment code should be written.

---

*This document is the single source of truth for all development decisions on StaySync.*