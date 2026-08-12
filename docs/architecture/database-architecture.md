# Database Architecture

## Layer Stack

```
┌─────────────────────────────────────────────────┐
│                  FastAPI Routes                  │
│  (HTTP layer — request/response, validation)     │
└────────────────────┬────────────────────────────┘
                     │ calls
                     ▼
┌─────────────────────────────────────────────────┐
│               Service Layer                      │
│  (business logic, scoring engine, orchestration) │
└────────────────────┬────────────────────────────┘
                     │ calls
                     ▼
┌─────────────────────────────────────────────────┐
│              Repository Layer                    │
│  (data access abstraction, CRUD per entity)      │
└────────────────────┬────────────────────────────┘
                     │ queries via
                     ▼
┌─────────────────────────────────────────────────┐
│              SQLAlchemy ORM                      │
│  (model mapping, relationship loading, UoW)      │
└────────────────────┬────────────────────────────┘
                     │ connects via
                     ▼
┌─────────────────────────────────────────────────┐
│               PostgreSQL Driver                  │
│  (psycopg2 — sync wire protocol)                │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│               PostgreSQL 15+                     │
│  (relational database, constraints, indexes)     │
└─────────────────────────────────────────────────┘
```

## Error Handling

Database-level errors (constraint violations, connection failures) propagate up through SQLAlchemy as typed exceptions:

```
PostgreSQL constraint violation
    → psycopg2 raises exception
    → SQLAlchemy wraps as IntegrityError
    → Global IntegrityError handler in exception_handler.py
    → Structured JSON response (400/409)
```

| SQLAlchemy Error | Mapped To | HTTP |
|---|---|---|
| `IntegrityError` (UNIQUE) | `DUPLICATE_ENTRY` | 409 |
| `IntegrityError` (FOREIGN KEY) | `FOREIGN_KEY_VIOLATION` | 400 |
| `IntegrityError` (NOT NULL) | `NULL_CONSTRAINT_VIOLATION` | 400 |
| Other errors | `INTERNAL_SERVER_ERROR` | 500 (logged) |

Raw database error messages are never exposed in API responses.

## Data Flow

1. **FastAPI route** receives request → validates with Pydantic schema → calls service
2. **Service** executes business logic → invokes repository methods
3. **Repository** builds SQLAlchemy queries → commits or rolls back
4. **SQLAlchemy** translates ORM operations to SQL → executes via psycopg2
5. **psycopg2** sends/receives over connection pool to PostgreSQL
6. **PostgreSQL** stores, indexes, and enforces constraints → returns results

Response flows back up the same chain. If an error occurs at any layer, it propagates to the global exception handler.

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **Driver** | psycopg2-binary | Mature sync driver, minimal setup |
| **Session management** | `sessionmaker` | Sync session per request via `get_db` dependency |
| **Migrations** | Alembic with autogenerate | Schema-as-code, repeatable deployments |
| **IDs** | UUID (server-generated) | Uniqueness across distributed systems, no sequential leaks |
| **Deletes** | RESTRICT / CASCADE as specified | Protect audit trail; cascade only for child details |
| **Connection pooling** | 5–20 pool / 10 overflow | Tuned for FastAPI sync workers |

## Related Documentation

- [PostgreSQL Implementation Plan](../database/postgres-implementation-plan.md)
- [Database Overview](../database/database-overview.md)
- [Schema Design](../database/schema-design.md)
- [Feature-Database Mapping](../database/feature-database-mapping.md)
- [Error Handling Architecture](error-handling-architecture.md)
