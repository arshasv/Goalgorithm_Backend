# Error Handling Architecture

## Exception Flow

```
API Layer (routes)
    │
    ▼
Service Layer
    │  raises custom ApplicationException subclasses
    │  or lets SQLAlchemy exceptions propagate
    ▼
Repository / Database Layer
    │  IntegrityError, etc.
    │
    ▼  (unhandled exceptions bubble up)
Global Exception Handler (exception_handler.py)
    │  maps exception → structured JSON response
    ▼
Standard API Error Response
```

## Why Centralized

- **No try/except duplication** — handlers are registered once in `main.py` using `@app.exception_handler`. Routes and services remain clean.
- **Separation of concerns** — business logic raises exceptions with semantic meaning (e.g., `PredictionAlreadyExistsException`); the handler layer formats the wire response.
- **Consistent envelope** — every error returns `{"success": false, "error_code": "...", "message": "...", "details": {...}}` regardless of origin.

## Exceptions Module

```
app/exceptions/
├── __init__.py               # public API — re-exports all exception classes
├── base_exception.py         # ApplicationException base class
├── business_exceptions.py    # domain-specific exceptions
├── database_exceptions.py    # SQLAlchemy error mapping
└── exception_handler.py      # FastAPI exception handler registration
```

### base_exception.py

`ApplicationException` is the root for all application-level errors:

| Field | Type | Description |
|---|---|---|
| `error_code` | str | Machine-readable identifier (e.g., `PREDICTION_ALREADY_EXISTS`) |
| `message` | str | Human-readable explanation |
| `status_code` | int | HTTP status code |
| `details` | dict | Optional payload with additional context |

### business_exceptions.py

| Exception | HTTP | error_code | When raised |
|---|---|---|---|
| `PredictionAlreadyExistsException` | 409 | `PREDICTION_ALREADY_EXISTS` | Duplicate (team_id, match_id) |
| `ActualResultAlreadyExistsException` | 409 | `ACTUAL_RESULT_ALREADY_EXISTS` | Duplicate match_id |
| `ResourceNotFoundException` | 404 | `RESOURCE_NOT_FOUND` | Missing team, match, prediction |
| `InvalidCompetitionStateException` | 400 | `INVALID_COMPETITION_STATE` | Operation not allowed in current state |

### database_exceptions.py

Maps SQLAlchemy `IntegrityError` to structured `ApplicationException` responses:

| SQLAlchemy Error | HTTP | error_code |
|---|---|---|
| UNIQUE constraint violation | 409 | `DUPLICATE_ENTRY` |
| FOREIGN KEY constraint violation | 400 | `FOREIGN_KEY_VIOLATION` |
| NOT NULL constraint violation | 400 | `NULL_CONSTRAINT_VIOLATION` |
| Other integrity errors | 400 | `DATABASE_ERROR` |

Raw database errors are never exposed to the API consumer.

### exception_handler.py

Registered handlers (all in `main.py` via `register_exception_handlers`):

| Handler | Catches | Produces |
|---|---|---|
| `application_exception_handler` | `ApplicationException` | Custom status + error envelope |
| `validation_exception_handler` | `RequestValidationError` (FastAPI) | 422 with field-level details |
| `sqlalchemy_integrity_handler` | `IntegrityError` | 400/409 depending on constraint |
| `leaderboard_error_handler` | `LeaderboardError` | 400 with score range violations |
| `general_exception_handler` | `Exception` (catch-all) | 500, logs stack trace internally |

## Standard Error Response

```json
{
  "success": false,
  "error_code": "ERROR_CODE",
  "message": "Readable explanation",
  "details": {}
}
```

## HTTP Status Code Reference

| Status | Meaning | Example error_code |
|---|---|---|
| 400 | Bad request / business rule violation | `INVALID_COMPETITION_STATE`, `FOREIGN_KEY_VIOLATION` |
| 404 | Resource not found | `RESOURCE_NOT_FOUND` |
| 409 | Conflict / duplicate | `PREDICTION_ALREADY_EXISTS`, `DUPLICATE_ENTRY` |
| 422 | Validation failure | `VALIDATION_ERROR` |
| 500 | Unexpected server error | `INTERNAL_SERVER_ERROR` |

## Related Documentation

- [System Architecture](system-architecture.md)
- [API Error Responses](../api/error-responses.md)
