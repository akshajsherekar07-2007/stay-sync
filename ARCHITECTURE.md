# ARCHITECTURE.md — StaySync

> **Version:** 1.0  
> **Last Updated:** 2026-05-30  
> **Status:** Active

---

## 1. System Overview

StaySync is a full-stack accommodation hold-management platform that connects **students** seeking PG/hostel/flat accommodations with **property owners** managing listings. The platform's core differentiator is a **real-time live status system** that manages temporary holds, waitlists, and occupancy states with atomic consistency.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT TIER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  React SPA   │  │  Mobile App  │  │  Admin Panel (Future)    │  │
│  │  (Vite+TS)   │  │  (Future)    │  │                          │  │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘  │
│         │                 │                        │                │
│         └─────────────────┼────────────────────────┘                │
│                           │                                        │
│                    HTTPS + WSS                                     │
└───────────────────────────┼────────────────────────────────────────┘
                            │
┌───────────────────────────┼────────────────────────────────────────┐
│                      API GATEWAY                                   │
│                   (Nginx / Render)                                  │
│              Rate Limiting · CORS · TLS                            │
└───────────────────────────┼────────────────────────────────────────┘
                            │
┌───────────────────────────┼────────────────────────────────────────┐
│                     APPLICATION TIER                                │
│  ┌────────────────────────┴─────────────────────────────────────┐  │
│  │                    FastAPI Application                        │  │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌───────────────┐  │  │
│  │  │  REST    │ │WebSocket │ │ Background│ │  Middleware    │  │  │
│  │  │  API     │ │  Server  │ │   Tasks   │ │  Pipeline     │  │  │
│  │  │ Routers  │ │ Handlers │ │  (Celery) │ │  Auth/CORS/   │  │  │
│  │  │          │ │          │ │           │ │  Logging       │  │  │
│  │  └────┬─────┘ └────┬─────┘ └─────┬─────┘ └───────────────┘  │  │
│  │       │             │             │                           │  │
│  │  ┌────┴─────────────┴─────────────┴──────────────────────┐   │  │
│  │  │              SERVICE LAYER                             │   │  │
│  │  │  AuthService · PropertyService · HoldService           │   │  │
│  │  │  NotificationService · WaitlistService · AnalyticsServ │   │  │
│  │  └────────────────────────┬───────────────────────────────┘   │  │
│  │                           │                                   │  │
│  │  ┌────────────────────────┴───────────────────────────────┐   │  │
│  │  │            REPOSITORY LAYER                             │   │  │
│  │  │  UserRepo · PropertyRepo · HoldRepo · BedRepo          │   │  │
│  │  │  NotificationRepo · WaitlistRepo · BookingRepo          │   │  │
│  │  └────────────────────────┬───────────────────────────────┘   │  │
│  └───────────────────────────┼───────────────────────────────────┘  │
└───────────────────────────────┼────────────────────────────────────┘
                                │
┌───────────────────────────────┼────────────────────────────────────┐
│                        DATA TIER                                   │
│  ┌─────────────┐  ┌──────────┴──┐  ┌──────────────┐               │
│  │  Supabase   │  │   Redis     │  │  Supabase    │               │
│  │  PostgreSQL │  │   Cache +   │  │  Storage     │               │
│  │  (Primary)  │  │   Queue     │  │  (Images)    │               │
│  └─────────────┘  └─────────────┘  └──────────────┘               │
└───────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Architecture

### 2.1 Frontend Architecture

```
frontend/
├── public/                          # Static assets
├── src/
│   ├── app/
│   │   ├── App.tsx                  # Root component
│   │   ├── providers.tsx            # Context providers wrapper
│   │   └── router.tsx               # Route definitions
│   │
│   ├── components/                  # Shared UI components
│   │   ├── ui/                      # ShadCN primitives (Button, Input, etc.)
│   │   ├── common/                  # App-wide components
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── SkeletonCard.tsx
│   │   │   ├── StatusBadge.tsx
│   │   │   ├── ConfirmDialog.tsx
│   │   │   └── EmptyState.tsx
│   │   └── forms/                   # Reusable form components
│   │       ├── FormField.tsx
│   │       ├── ImageUpload.tsx
│   │       └── LocationPicker.tsx
│   │
│   ├── features/                    # Feature modules
│   │   ├── auth/
│   │   │   ├── components/          # Auth-specific components
│   │   │   ├── hooks/               # Auth hooks (useAuth, useLogin)
│   │   │   ├── schemas/             # Zod schemas for auth forms
│   │   │   └── types.ts             # Auth type definitions
│   │   │
│   │   ├── property/
│   │   │   ├── components/          # PropertyCard, PropertyForm, etc.
│   │   │   ├── hooks/               # useProperties, usePropertyDetail
│   │   │   ├── schemas/             # Property validation schemas
│   │   │   └── types.ts
│   │   │
│   │   ├── holds/                   # Phase 2
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── types.ts
│   │   │
│   │   └── notifications/           # Phase 2
│   │       ├── components/
│   │       ├── hooks/
│   │       └── types.ts
│   │
│   ├── hooks/                       # Global shared hooks
│   │   ├── useDebounce.ts
│   │   ├── useMediaQuery.ts
│   │   └── useWebSocket.ts
│   │
│   ├── layouts/                     # Layout wrappers
│   │   ├── RootLayout.tsx
│   │   ├── DashboardLayout.tsx
│   │   ├── AuthLayout.tsx
│   │   └── PublicLayout.tsx
│   │
│   ├── lib/                         # Utility libraries
│   │   ├── axios.ts                 # Configured Axios instance
│   │   ├── queryClient.ts           # TanStack Query config
│   │   ├── constants.ts             # App constants
│   │   └── utils.ts                 # General utilities
│   │
│   ├── pages/                       # Route-level page components
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   └── VerifyEmailPage.tsx
│   │   ├── owner/
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── AddPropertyPage.tsx
│   │   │   ├── ManagePropertiesPage.tsx
│   │   │   └── PropertyDetailPage.tsx
│   │   ├── student/
│   │   │   ├── BrowsePage.tsx
│   │   │   ├── PropertyViewPage.tsx
│   │   │   └── SavedPropertiesPage.tsx
│   │   └── common/
│   │       ├── HomePage.tsx
│   │       ├── NotFoundPage.tsx
│   │       └── ProfilePage.tsx
│   │
│   ├── services/                    # API service layer
│   │   ├── api.ts                   # Base API config
│   │   ├── authService.ts
│   │   ├── propertyService.ts
│   │   ├── holdService.ts           # Phase 2
│   │   └── notificationService.ts   # Phase 2
│   │
│   ├── stores/                      # Zustand stores
│   │   ├── authStore.ts
│   │   ├── uiStore.ts
│   │   └── notificationStore.ts     # Phase 2
│   │
│   ├── styles/                      # Global styles
│   │   ├── globals.css
│   │   └── themes.css
│   │
│   ├── types/                       # Shared type definitions
│   │   ├── api.ts                   # API response types
│   │   ├── models.ts                # Domain model types
│   │   └── enums.ts                 # Status enums
│   │
│   └── utils/                       # Pure utility functions
│       ├── formatters.ts
│       ├── validators.ts
│       └── dateUtils.ts
│
├── .env.example
├── .eslintrc.cjs
├── tailwind.config.ts
├── tsconfig.json
├── vite.config.ts
├── index.html
└── package.json
```

### 2.2 Backend Architecture

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application factory
│   │
│   ├── api/                         # API routers
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py            # Aggregated v1 router
│   │   │   ├── auth.py              # Auth endpoints
│   │   │   ├── users.py             # User profile endpoints
│   │   │   ├── properties.py        # Property CRUD
│   │   │   ├── floors.py            # Floor management
│   │   │   ├── rooms.py             # Room management
│   │   │   ├── beds.py              # Bed management
│   │   │   ├── holds.py             # Hold requests (Phase 2)
│   │   │   ├── waitlists.py         # Waitlist management (Phase 2)
│   │   │   ├── notifications.py     # Notifications (Phase 2)
│   │   │   └── analytics.py         # Analytics (Phase 3)
│   │   └── deps.py                  # Shared dependencies
│   │
│   ├── core/                        # Application core
│   │   ├── __init__.py
│   │   ├── config.py                # Settings (pydantic-settings)
│   │   ├── security.py              # JWT, password hashing
│   │   ├── exceptions.py            # Custom exception classes
│   │   ├── constants.py             # Application constants
│   │   └── logging.py               # Structured logging config
│   │
│   ├── db/                          # Database
│   │   ├── __init__.py
│   │   ├── session.py               # Async engine + session factory
│   │   ├── base.py                  # Declarative base
│   │   └── init_db.py               # DB initialization
│   │
│   ├── models/                      # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── property.py
│   │   ├── floor.py
│   │   ├── room.py
│   │   ├── bed.py
│   │   ├── amenity.py
│   │   ├── image.py
│   │   ├── hold_request.py          # Phase 2
│   │   ├── waitlist.py              # Phase 2
│   │   ├── booking.py               # Phase 2
│   │   ├── notification.py          # Phase 2
│   │   └── review.py                # Phase 3
│   │
│   ├── schemas/                     # Pydantic DTOs
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── property.py
│   │   ├── floor.py
│   │   ├── room.py
│   │   ├── bed.py
│   │   ├── amenity.py
│   │   ├── image.py
│   │   ├── hold.py                  # Phase 2
│   │   ├── notification.py          # Phase 2
│   │   └── common.py                # Shared schemas (pagination, etc.)
│   │
│   ├── services/                    # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── property_service.py
│   │   ├── floor_service.py
│   │   ├── room_service.py
│   │   ├── bed_service.py
│   │   ├── image_service.py
│   │   ├── hold_service.py          # Phase 2
│   │   ├── waitlist_service.py      # Phase 2
│   │   ├── notification_service.py  # Phase 2
│   │   └── email_service.py         # Phase 2
│   │
│   ├── repositories/                # Data access
│   │   ├── __init__.py
│   │   ├── base.py                  # Generic CRUD repository
│   │   ├── user_repository.py
│   │   ├── property_repository.py
│   │   ├── floor_repository.py
│   │   ├── room_repository.py
│   │   ├── bed_repository.py
│   │   ├── hold_repository.py       # Phase 2
│   │   ├── waitlist_repository.py   # Phase 2
│   │   └── notification_repository.py  # Phase 2
│   │
│   ├── dependencies/                # FastAPI dependency injection
│   │   ├── __init__.py
│   │   ├── auth.py                  # get_current_user, require_role
│   │   ├── database.py              # get_db session
│   │   └── services.py              # Service factory dependencies
│   │
│   ├── middleware/                   # HTTP middleware
│   │   ├── __init__.py
│   │   ├── cors.py
│   │   ├── rate_limiter.py
│   │   ├── request_logging.py
│   │   └── error_handler.py
│   │
│   ├── websocket/                   # WebSocket handlers (Phase 2)
│   │   ├── __init__.py
│   │   ├── manager.py               # Connection manager
│   │   └── handlers.py              # Event handlers
│   │
│   ├── tasks/                       # Background tasks (Phase 2)
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   ├── hold_tasks.py            # Hold expiry tasks
│   │   └── email_tasks.py           # Email sending tasks
│   │
│   ├── integrations/                # External service integrations
│   │   ├── __init__.py
│   │   ├── supabase_client.py       # Supabase SDK wrapper
│   │   ├── supabase_storage.py      # File upload/download
│   │   ├── email_provider.py        # Resend/SendGrid abstraction
│   │   └── google_maps.py           # Google Maps API client
│   │
│   └── utils/                       # Pure utility functions
│       ├── __init__.py
│       ├── datetime_utils.py
│       ├── pagination.py
│       └── validators.py
│
├── alembic/                         # Database migrations
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
│
├── tests/
│   ├── conftest.py                  # Fixtures
│   ├── unit/
│   │   ├── test_auth_service.py
│   │   ├── test_property_service.py
│   │   └── test_hold_service.py
│   ├── integration/
│   │   ├── test_auth_api.py
│   │   ├── test_property_api.py
│   │   └── test_hold_api.py
│   └── factories/                   # Test data factories
│       └── model_factories.py
│
├── docker/
│   ├── Dockerfile
│   └── Dockerfile.dev
│
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
│
├── .env.example
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

## 3. Data Flow Architecture

### 3.1 Authentication Flow

```
┌──────────┐     POST /auth/register      ┌───────────┐
│  Client   │ ─────────────────────────▶   │  FastAPI   │
│  (React)  │                              │  Router    │
└──────────┘                               └─────┬─────┘
     ▲                                           │
     │                                     ┌─────▼─────┐
     │                                     │  Auth      │
     │                                     │  Service   │
     │                                     └─────┬─────┘
     │                                           │
     │         ┌─────────────────────────────────┤
     │         │                                 │
     │   ┌─────▼─────┐                    ┌─────▼─────┐
     │   │  User      │                    │  Security  │
     │   │  Repository│                    │  Module    │
     │   └─────┬─────┘                    │  (hash pw) │
     │         │                           └───────────┘
     │   ┌─────▼─────┐
     │   │  Supabase  │
     │   │  PostgreSQL│
     │   └───────────┘
     │
     │    { access_token, refresh_token }
     └──────────────────────────────────
```

### 3.2 Property Creation Flow

```
Owner UI → PropertyForm → propertyService.create()
  → POST /api/v1/properties
    → AuthMiddleware (verify JWT + role=OWNER)
      → PropertyRouter
        → PropertyService.create_property()
          → PropertyRepository.create()
            → PostgreSQL INSERT
          → ImageService.upload()
            → Supabase Storage
        → Return PropertyResponse DTO
```

### 3.3 Hold Request Flow (Phase 2)

```
Student UI → holdService.requestHold()
  → POST /api/v1/holds
    → AuthMiddleware (verify JWT + role=STUDENT)
      → HoldRouter
        → HoldService.create_hold()
          ├── Check: Student hold limit (max 3)
          ├── Check: Cooldown period (30 min)
          ├── Check: Bed status == VACANT
          │     ├── YES → BedRepository.update_status(HELD)
          │     │        → HoldRepository.create()
          │     │        → WebSocket broadcast (bed_status_changed)
          │     │        → Celery: schedule_hold_expiry(hold_id, duration)
          │     │        → Email: send_hold_confirmation()
          │     │        → Return HoldResponse
          │     └── NO (HELD) → WaitlistService.add_to_queue()
          │                    → Return WaitlistResponse
          └── TRANSACTION COMMIT (atomic)
```

### 3.4 Hold Expiry Flow (Phase 2)

```
Celery Beat (periodic) → check_expired_holds()
  → HoldRepository.find_expired()
    → For each expired hold:
      ├── HoldRepository.update_status(EXPIRED)
      ├── BedRepository.update_status(VACANT)
      ├── WaitlistService.notify_next_in_queue()
      │     └── Email + In-App Notification
      ├── WebSocket broadcast (bed_status_changed)
      └── TRANSACTION COMMIT
```

---

## 4. Real-Time Architecture (Phase 2)

```
┌────────────────┐         WSS          ┌─────────────────────┐
│   React App    │ ◄──────────────────▶  │  FastAPI WebSocket  │
│                │                       │  Manager            │
│  useWebSocket()│                       │                     │
│  hook          │                       │  Rooms:             │
│                │                       │  - property:{id}    │
│  Updates:      │                       │  - user:{id}        │
│  - Bed status  │                       │  - global           │
│  - Hold status │                       │                     │
│  - Notifications│                      └──────────┬──────────┘
└────────────────┘                                  │
                                                    │ Publish
                                           ┌────────▼────────┐
                                           │  Redis Pub/Sub   │
                                           │  (Event Bus)     │
                                           └────────┬────────┘
                                                    │
                           ┌────────────────────────┼──────────────┐
                           │                        │              │
                    ┌──────▼──────┐         ┌───────▼─────┐  ┌────▼────┐
                    │ HoldService  │         │ BedService   │  │ Celery  │
                    │ (status      │         │ (occupancy   │  │ Workers │
                    │  changes)    │         │  updates)    │  │         │
                    └─────────────┘         └─────────────┘  └─────────┘
```

### WebSocket Message Schema
```json
{
  "event": "bed_status_changed",
  "data": {
    "bed_id": "uuid",
    "property_id": "uuid",
    "old_status": "VACANT",
    "new_status": "HELD",
    "hold_expires_at": "2026-06-01T12:00:00Z",
    "waitlist_count": 2
  },
  "timestamp": "2026-05-30T10:30:00Z"
}
```

### Supported Events
| Event                    | Trigger                          | Audience          |
| ------------------------ | -------------------------------- | ----------------- |
| `bed_status_changed`     | Hold created/expired/overridden  | Property room     |
| `hold_accepted`          | Owner accepts hold               | Requesting student|
| `hold_rejected`          | Owner rejects hold               | Requesting student|
| `hold_expiring_soon`     | 1 hour before expiry             | Hold student      |
| `waitlist_position_updated`| Queue position change          | Waitlisted student|
| `notification_received`  | Any notification                 | Target user       |

---

## 5. Security Architecture

```
┌─────────────────────────────────────────────┐
│              SECURITY LAYERS                 │
├─────────────────────────────────────────────┤
│                                             │
│  Layer 1: Network                           │
│  ├── TLS/HTTPS enforcement                  │
│  ├── CORS whitelist                         │
│  └── Rate limiting (100 req/min/IP)         │
│                                             │
│  Layer 2: Authentication                    │
│  ├── JWT access tokens (15 min)             │
│  ├── Refresh token rotation (7 days)        │
│  ├── bcrypt password hashing (12 rounds)    │
│  └── Email verification required            │
│                                             │
│  Layer 3: Authorization                     │
│  ├── Role-based access control (RBAC)       │
│  ├── Resource ownership validation          │
│  └── Route-level permission guards          │
│                                             │
│  Layer 4: Input Validation                  │
│  ├── Pydantic v2 schema validation          │
│  ├── Zod frontend validation                │
│  ├── File type + size validation            │
│  └── SQL injection prevention (ORM)         │
│                                             │
│  Layer 5: Data Protection                   │
│  ├── Soft deletes (audit trail)             │
│  ├── Parameterized queries                  │
│  ├── Secrets in environment variables       │
│  └── No sensitive data in logs              │
│                                             │
└─────────────────────────────────────────────┘
```

### Role-Based Access Control Matrix

| Endpoint                    | Student | Owner | Admin |
| --------------------------- | ------- | ----- | ----- |
| Browse properties           | ✅      | ✅    | ✅    |
| View property detail        | ✅      | ✅    | ✅    |
| Create property             | ❌      | ✅    | ✅    |
| Edit own property           | ❌      | ✅    | ✅    |
| Delete own property         | ❌      | ✅    | ✅    |
| Request hold                | ✅      | ❌    | ❌    |
| Accept/reject hold          | ❌      | ✅    | ✅    |
| View own holds              | ✅      | ✅    | ✅    |
| Override hold (occupy)      | ❌      | ✅    | ✅    |
| View all users              | ❌      | ❌    | ✅    |
| Verify property listing     | ❌      | ❌    | ✅    |

---

## 6. Deployment Architecture

### Development Environment
```
docker-compose up
  ├── backend:     FastAPI (uvicorn, port 8000)
  ├── frontend:    React dev server (Vite, port 5173)
  ├── redis:       Redis 7 (port 6379)
  ├── celery:      Celery worker
  └── db:          PostgreSQL 16 (port 5432) — or Supabase remote
```

### Production Environment
```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Netlify    │         │    Render     │         │  Supabase   │
│   (CDN)      │  HTTPS  │   (Backend)  │   TCP   │  (Database) │
│              │ ───────▶│              │ ───────▶│             │
│  React SPA   │         │  FastAPI     │         │  PostgreSQL │
│  Static      │         │  + Celery    │         │  + Storage  │
│  Assets      │         │  + Redis     │         │             │
└─────────────┘         └──────────────┘         └─────────────┘
```

### Environment Strategy
| Environment   | Database       | Redis    | Email    | Purpose              |
| ------------- | -------------- | -------- | -------- | -------------------- |
| `development` | Local PG / Supa| Local    | Console  | Local dev            |
| `staging`     | Supabase (stg) | Render   | Sandbox  | Pre-production tests |
| `production`  | Supabase (prod)| Render   | Live     | Production           |

---

## 7. Scalability Considerations

### Current Architecture Supports

| Dimension              | Strategy                                           |
| ---------------------- | -------------------------------------------------- |
| **Horizontal scaling** | Stateless FastAPI → multiple Render instances       |
| **Database scaling**   | Supabase managed PG with connection pooling         |
| **Cache scaling**      | Redis for hot data (bed statuses, session cache)    |
| **Background jobs**    | Celery workers independently scalable               |
| **Frontend CDN**       | Netlify global CDN for static assets               |
| **WebSocket scaling**  | Redis Pub/Sub for cross-instance message broadcast  |
| **Multi-city**         | City/locality fields in property model              |
| **API versioning**     | `/api/v1/` prefix for backward compatibility        |

### Future Migration Path
```
Current (Monolith)          →          Future (Microservices)
┌─────────────────┐         ┌────────────┐ ┌────────────┐
│  FastAPI         │         │ Auth       │ │ Property   │
│  (all services)  │   →→→   │ Service    │ │ Service    │
│                  │         └────────────┘ └────────────┘
│                  │         ┌────────────┐ ┌────────────┐
│                  │         │ Hold       │ │ Notification│
└─────────────────┘         │ Service    │ │ Service     │
                            └────────────┘ └────────────┘
```

The modular architecture (services + repositories) makes this migration straightforward — each service module can be extracted into an independent microservice with its own database.

---

## 8. Key Technical Decisions

| Decision                        | Choice               | Rationale                                                  |
| ------------------------------- | -------------------- | ---------------------------------------------------------- |
| State management                | Zustand              | Lightweight, TypeScript-native, no boilerplate vs Redux    |
| Server state                    | TanStack Query       | Built-in caching, refetching, optimistic updates           |
| ORM                             | SQLAlchemy 2.0 async | Mature, full-featured, native async support                |
| Background tasks                | Celery + Redis       | Production-proven, supports schedules, retries, monitoring |
| WebSocket transport             | FastAPI native WS    | No extra dependency, integrates with auth middleware        |
| Image storage                   | Supabase Storage     | Co-located with database, built-in CDN, signed URLs        |
| Password hashing                | bcrypt               | Industry standard, timing-attack resistant                 |
| Token format                    | JWT (HS256)          | Stateless auth, easy to verify, widely supported           |
| API documentation               | OpenAPI (Swagger)    | Auto-generated by FastAPI, zero maintenance                |
| Database IDs                    | UUID v4              | No sequential guessing, merge-friendly, globally unique    |

---

## 9. Observability Strategy (Phase 3)

```
Application Logs (structlog)
  → stdout → Render Log Drain
    → Log aggregation (future: Datadog/Grafana)

Health Checks:
  GET /health          → Application health
  GET /health/db       → Database connectivity
  GET /health/redis    → Redis connectivity

Metrics (future):
  - Request latency (p50, p95, p99)
  - Active WebSocket connections
  - Hold request throughput
  - Background job queue depth
  - Error rates by endpoint
```

---

## 10. Bed Status State Machine

This is the **most critical** business logic in the system:

```
                    ┌──────────────────┐
                    │                  │
            ┌───── │    🟢 VACANT      │ ◄────────────────────┐
            │      │                  │                      │
            │      └──────┬───────────┘                      │
            │             │                                  │
            │    Student requests hold                       │
            │             │                                  │
            │      ┌──────▼───────────┐              ┌───────┴──────┐
            │      │                  │   Expires/   │              │
            │      │    🟡 HELD       │──Rejected──▶ │  Auto-release │
            │      │                  │              │              │
            │      └──────┬───────────┘              └──────────────┘
            │             │
            │    Owner accepts / overrides
            │             │
            │      ┌──────▼───────────┐
            │      │                  │
            │      │    🔴 OCCUPIED    │
            │      │                  │
            │      └──────┬───────────┘
            │             │
            │    Owner marks vacated
            │             │
            └─────────────┘

  🔵 WAITLIST: Overlay state — students in queue while bed is HELD/OCCUPIED
```

### State Transition Rules
| From       | To         | Triggered By              | Side Effects                          |
| ---------- | ---------- | ------------------------- | ------------------------------------- |
| VACANT     | HELD       | Student hold request      | Create hold record, schedule expiry   |
| HELD       | OCCUPIED   | Owner accepts/overrides   | Cancel expiry, notify student         |
| HELD       | VACANT     | Hold expires/rejected     | Notify waitlist, auto-promote next    |
| OCCUPIED   | VACANT     | Owner marks vacated       | Notify waitlisted students            |
| Any        | WAITLIST   | Student requests held bed | Add to queue, show position           |

---

*This architecture document is the blueprint for all StaySync development. All implementation must conform to the patterns and decisions documented here.*