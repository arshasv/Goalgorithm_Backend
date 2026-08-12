# System Architecture

## Layers

```
┌─────────────────────────────────────────┐
│         Frontend (React SPA)              │
│   (pages/, components/, api/)            │
├─────────────────────────────────────────┤
│         API / Presentation Layer          │
│   (main.py, api/routes, health_routes)   │
├─────────────────────────────────────────┤
│         Schema Validation Layer           │
│   (Pydantic v2 schemas)                  │
├─────────────────────────────────────────┤
│         Service / Use Case Layer          │
│   (prediction_service, result_service,   │
│    scoring_service, leaderboard_service,  │
│    analytics_service, model_eval_service, │
│    report_service)                       │
├─────────────────────────────────────────┤
│         Domain / Core Layer               │
│   (scoring_engine/ — pure functions)     │
├─────────────────────────────────────────┤
│         Repository / Data Layer           │
│   (SQLAlchemy ORM repositories)          │
├─────────────────────────────────────────┤
│         Infrastructure Layer              │
│   (PostgreSQL, Config, Docker)           │
└─────────────────────────────────────────┘
```

## Error Handling Flow

```
Route → Service → Exception raised → Global Handler → JSON error response
                        │
                   ┌────┴────┐
                   │         │
            Application    SQLAlchemy
            Exception      IntegrityError
                   │         │
                   ▼         ▼
              exception_handler.py → consistent error envelope
```

All errors converge through `app/exceptions/exception_handler.py` registered in `main.py`. Routes never contain try/except blocks — they remain clean dispatch points.

## Exceptions Module

```
app/exceptions/
├── base_exception.py         # ApplicationException — error_code, message, status_code, details
├── business_exceptions.py    # PredictionAlreadyExists, ActualResultAlreadyExists, ResourceNotFound, InvalidState
├── database_exceptions.py    # IntegrityError → structured ApplicationException mapping
└── exception_handler.py      # Global FastAPI exception handlers
```

See [Error Handling Architecture](error-handling-architecture.md) for full details.

## Config Flow

```
.env
  ↓  python-dotenv
app/config.py  (Settings singleton)
  ↓
  ├── FastAPI (app_name, api_prefix, host, port)
  ├── SQLAlchemy (database_url, pool settings)
  ├── Alembic (migration target URL)
  └── Application code (debug, security)
```

## Architecture Rules
- Routes receive request → validate using schemas → call services → return response
- Services orchestrate business logic, call scoring engine, and persist via repositories
- Scoring engine contains pure mathematical calculations only (no I/O, no DB, no HTTP)
- Database layer handles storage mechanics via SQLAlchemy ORM
- All configuration originates from `.env` → `app/config.py` → consumed by all layers
- Errors are raised as typed exceptions in services/repos; formatting happens in global handlers only

## Key Design Principles
- Automated Scoring — Phase 1 scoring is fully formula-driven
- Immutable Predictions — No updates after freeze deadline
- Reproducibility — Every score computation is traceable and re-runnable
- Separation of Concerns — Evaluation logic decoupled from participant model code
- Strict Input Contracts — Schema violations result in rejection

## Technology Stack
| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, React Router DOM, Axios |
| Framework | Python 3.12+, FastAPI |
| Validation | Pydantic v2 |
| API Server | Uvicorn |
| Testing | pytest, httpx (TestClient) |
| Database | PostgreSQL 16+ / SQLite (dev/test) |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Config | python-dotenv |
| Exception Handling | Custom exceptions + FastAPI global handlers |
| Containerization | Docker + Docker Compose |
