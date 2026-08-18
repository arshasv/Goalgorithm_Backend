# Feature 01: Project Infrastructure & Foundation

## Feature Overview

The foundational layer of the GOALGORITHM backend providing project scaffolding, configuration management, database connectivity, dependency injection, and application entry point. This feature establishes the layered architecture pattern (API → Schema → Service → Scoring Engine → Repository → Database) that all other features build upon.

## Purpose & Requirements

- Establish a consistent layered architecture with clear separation of concerns
- Provide centralized configuration management from environment variables
- Set up SQLAlchemy database connection and session management
- Wire all components via FastAPI dependency injection
- Register global exception handlers for consistent error responses
- Define the FastAPI application factory with middleware and router registration

## Related Specifications

- `architecture/system-architecture.md` — Layer diagram, design principles, technology stack
- `architecture/database-architecture.md` — Database layer, connection, error handling
- `architecture/DEPLOYMENT.md` — Local setup, Docker build/run/compose
- `architecture/error-handling-architecture.md` — Exception flow, exception module
- `database/database-overview.md` — Engine, design goals, table list
- `database/postgres-implementation-plan.md` — PostgreSQL implementation phases

## User/Business Flow

```
Developer sets up .env → App starts → Alembic migrates DB → FastAPI serves API
                                                           ↓
Client sends request → Router validates auth → Service calls repository
     → Repository queries DB → Response returned → Global handler catches errors
```

## How the Feature is Created

The infrastructure is established through:
1. Project directory structure with package markers (`__init__.py`)
2. Configuration singleton loaded from `.env`
3. Database engine and session factory
4. Dependency injection container wiring repositories → services
5. Exception handler registration on app startup
6. Router registration under `/api/v1` prefix

## How the Feature Works Internally

### Application Entry Point (`app/main.py`)

```python
# Creates FastAPI app with:
# - CORS middleware (allows all origins)
# - Lifespan handler (startup/shutdown events)
# - All API routers registered under /api/v1
# - Global exception handlers registered
# - /health and /version endpoints
```

The `create_app()` factory function:
1. Creates `FastAPI` instance with title/version metadata
2. Adds `CORSMiddleware` with permissive origin policy
3. Defines `lifespan()` async context manager for startup/shutdown
4. Includes all route modules via `app.include_router()`
5. Registers exception handlers from `app/exceptions/exception_handler.py`
6. Mounts the API router at `/api/v1`

### Configuration (`app/config.py`)

Loads all settings from environment variables using `pydantic-settings`:

| Field | Source | Purpose |
|-------|--------|---------|
| `DATABASE_URL` | `.env` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | `.env` | JWT token signing secret |
| `JWT_ALGORITHM` | `.env` (default: HS256) | JWT algorithm |
| `JWT_EXPIRY_HOURS` | `.env` (default: 24) | Token lifetime |
| `AGENTMAIL_API_KEY` | `.env` | Email service API key |
| `AGENTMAIL_INBOX_ID` | `.env` | Email inbox identifier |
| `FOOTBALL_API_KEY` | `.env` | api-sports.io API key |
| `FOOTBALL_API_BASE_URL` | `.env` | Football API base URL |

Settings are loaded as a module-level singleton: `settings = Settings()`.

### Database Connection (`app/database/`)

```
connection.py → Creates SQLAlchemy engine from DATABASE_URL
session.py    → SessionLocal factory + get_db() generator
base.py       → DeclarativeBase for all ORM models
```

The `get_db()` generator yields sessions to FastAPI dependencies and ensures cleanup after each request.

### Dependency Injection (`app/dependencies/__init__.py`)

A centralized DI container that wires:

**17 Repository Providers:**
- `get_user_repository(db)` → `UserRepository`
- `get_team_repository(db)` → `TeamRepository`
- `get_match_repository(db)` → `MatchRepository`
- `get_prediction_repository(db)` → `PredictionRepository`
- `get_score_repository(db)` → `ScoreRepository`
- `get_scoring_config_repository(db)` → `ScoringConfigRepository`
- ... and 11 more

**12 Service Providers:**
- `get_auth_service(...)` → `AuthService`
- `get_team_service(...)` → `TeamService`
- `get_scoring_service(...)` → `ScoringService` (13 dependencies injected)
- ... and 9 more

Each provider is a FastAPI dependency function that creates the component with its required dependencies.

## Architecture & Components Involved

```
app/
├── main.py                    ← FastAPI app factory
├── config.py                  ← Pydantic Settings
├── database/
│   ├── base.py               ← SQLAlchemy DeclarativeBase
│   ├── connection.py         ← Engine creation
│   └── session.py            ← SessionLocal + get_db
├── dependencies/
│   └── __init__.py           ← DI container (17 repos + 12 services)
├── exceptions/
│   ├── base_exception.py     ← ApplicationException base
│   ├── business_exceptions.py ← Domain exceptions
│   ├── database_exceptions.py ← IntegrityError handler
│   └── exception_handler.py  ← Global FastAPI handlers
└── api/
    ├── __init__.py            ← API router aggregation
    └── deps.py               ← Auth dependency functions
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/main.py` | 59 | FastAPI app creation, middleware, router registration |
| `app/config.py` | 55 | Settings class with all env vars |
| `app/database/base.py` | 5 | SQLAlchemy DeclarativeBase |
| `app/database/connection.py` | 6 | Engine from DATABASE_URL |
| `app/database/session.py` | 16 | SessionLocal factory, get_db generator |
| `app/dependencies/__init__.py` | 208 | Full DI wiring |
| `app/exceptions/__init__.py` | 15 | Exception exports |
| `app/exceptions/base_exception.py` | 22 | ApplicationException |
| `app/exceptions/business_exceptions.py` | 42 | Domain-specific exceptions |
| `app/exceptions/database_exceptions.py` | 70 | DB IntegrityError handler |
| `app/exceptions/exception_handler.py` | 105 | Global handlers |

### Key Classes & Functions

- `create_app() -> FastAPI` — Application factory
- `Settings(BaseSettings)` — Configuration singleton
- `get_db() -> Generator[Session]` — Database session dependency
- `Base` — SQLAlchemy declarative base class
- `ApplicationException(Exception)` — Base exception with message/detail/status_code
- All exception handler functions in `exception_handler.py`

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Health check endpoint |
| GET | `/version` | None | Version info endpoint |

## Database/Data Models Involved

No domain models in this feature — only the database connection infrastructure.

## Configuration/Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Yes | — | JWT signing secret |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm |
| `JWT_EXPIRY_HOURS` | No | `24` | Token lifetime |
| `AGENTMAIL_API_KEY` | No | — | Email service key |
| `AGENTMAIL_INBOX_ID` | No | — | Email inbox ID |
| `FOOTBALL_API_KEY` | No | — | Football API key |

## Authentication/Authorization Requirements

The infrastructure provides the auth middleware that all other features use:
- `get_current_user()` — Extracts JWT from Bearer token, returns `UserModel`
- `get_current_organizer()` — Requires `ORGANIZER` role
- `get_current_team_leader()` — Requires `TEAM_LEADER` role

## Important Classes, Functions, Services, Modules

### `ApplicationException` (`app/exceptions/base_exception.py`)
Base class for all business exceptions. Fields: `message`, `detail`, `status_code`. Provides `to_dict()` for JSON serialization.

### `DBIntegrityErrorHandler` (`app/exceptions/database_exceptions.py`)
Context manager that catches SQLAlchemy `IntegrityError` and maps to structured responses:
- `UNIQUE` violation → 409 `DUPLICATE_ENTRY`
- `FOREIGN KEY` violation → 400 `FOREIGN_KEY_VIOLATION`
- `NOT NULL` violation → 400 `NULL_CONSTRAINT_VIOLATION`

### Global Exception Handlers (`app/exceptions/exception_handler.py`)
Registered on the FastAPI app:
- `ApplicationException` → Custom status + JSON envelope
- `RequestValidationError` → 422 with field-level details
- `IntegrityError` → 400/409 based on constraint type
- `Exception` (catch-all) → 500 with logged stack trace

## Request/Response Flow

```
HTTP Request
    ↓
FastAPI Router (API Layer)
    ↓ validates auth via deps.py
Service Layer
    ↓ calls business logic
Repository Layer
    ↓ queries database
SQLAlchemy ORM → PostgreSQL
    ↓
Response (or Exception)
    ↓
Global Exception Handler (if error)
    ↓
Structured JSON Response
```

## Error Handling

- All exceptions propagate to global handlers — no try/except in routes
- Database constraint violations caught by `DBIntegrityErrorHandler`
- Unknown errors logged with full stack trace and returned as 500

## Validation

- Pydantic v2 schemas validate all request/response payloads
- Settings validated at import time (missing env vars cause startup failure)

## External Dependencies/Integrations

- `fastapi` — Web framework
- `sqlalchemy` — ORM
- `pydantic-settings` — Configuration management
- `python-jose` — JWT tokens
- `passlib` + `bcrypt` — Password hashing
- `uvicorn` — ASGI server

## Deployment/Runtime Considerations

- App runs on port 8000 (configurable via `PORT` env var)
- Docker: `python:3.12-slim` base image
- Database: PostgreSQL 15+ (Neon serverless in production)
- Pool settings: 5-20 connections, 10 overflow

## Edge Cases

- Missing `.env` variables cause `ValidationError` at import time
- Database connection failures return 500 on health check
- Circular dependency imports prevented by careful module ordering

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_health.py` | Health/version endpoints (4 tests) |
| `tests/test_database_connection.py` | DB settings, engine, session, SQLite integration (7 tests) |

## Known Limitations/Technical Debt

- CORS allows all origins (`*`) — should be restricted in production
- No rate limiting middleware
- No request logging middleware (planned in `architecture/`)
- No audit logging for scoring computations

## Dependencies on Other Features

None — this is the foundational feature that all others depend on.

## Step-by-Step Implementation Sequence

1. Create project directory structure with `__init__.py` markers
2. Create `app/config.py` with Pydantic Settings
3. Create `app/database/base.py` with DeclarativeBase
4. Create `app/database/connection.py` with engine creation
5. Create `app/database/session.py` with SessionLocal and get_db
6. Create `app/exceptions/` module with base exception, business exceptions, DB handler
7. Create `app/exceptions/exception_handler.py` with global handlers
8. Create `app/api/deps.py` with auth dependencies
9. Create `app/dependencies/__init__.py` with DI container
10. Create `app/main.py` with app factory, middleware, router registration
11. Create `app/api/__init__.py` aggregating all sub-routers
12. Verify health endpoint returns 200
13. Verify all exception handlers registered correctly
