# Feature 22: Exception Handling & Error Responses

## Feature Overview

Centralized exception handling system with custom exception hierarchy, global FastAPI exception handlers, and structured JSON error responses. All exceptions propagate to global handlers — no try/except blocks in route handlers.

## Purpose & Requirements

- Custom `ApplicationException` base class with message/detail/status_code
- Domain-specific exceptions (409 duplicates, 404 not found, 400 invalid state)
- SQLAlchemy IntegrityError mapping (UNIQUE→409, FK→400, NULL→400)
- Standard error envelope: `{success, error_code, message, details}`
- Global handlers for all exception types
- No try/except in route handlers (exceptions propagate)

## Related Specifications

- `architecture/error-handling-architecture.md` — Exception flow design (109 lines)
- `api/error-responses.md` — Error response format specification

## How the Feature Works Internally

### Exception Hierarchy
```
Exception
└── ApplicationException
    ├── message: str
    ├── detail: dict
    ├── status_code: int
    └── to_dict() → JSON-serializable

Business Exceptions (subclass ApplicationException):
├── DuplicateUserException (409)
├── DuplicateTeamException (409)
├── DuplicateMatchNumberException (409)
├── InvalidCredentialsException (401)
├── DataNotFoundException (404)
└── InvalidCompetitionStateException (400)
```

### Global Exception Handlers (`exception_handler.py`)
```python
# 1. Custom ApplicationException
@app.exception_handler(ApplicationException)
async def handle_app_exception(request, exc):
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

# 2. Pydantic Validation Error
@app.exception_handler(RequestValidationError)
async def handle_validation_error(request, exc):
    return JSONResponse(status_code=422, content={
        "success": False,
        "error_code": "VALIDATION_ERROR",
        "message": "Validation failed",
        "details": [{"field": e["loc"], "message": e["msg"]} for e in exc.errors()]
    })

# 3. SQLAlchemy IntegrityError
@app.exception_handler(IntegrityError)
async def handle_integrity_error(request, exc):
    # Parse error message for constraint type
    if "UNIQUE" in str(exc): → 409 DUPLICATE_ENTRY
    if "FOREIGN KEY" in str(exc): → 400 FOREIGN_KEY_VIOLATION
    if "NOT NULL" in str(exc): → 400 NULL_CONSTRAINT_VIOLATION
    else → 400 DATABASE_ERROR

# 4. Catch-all
@app.exception_handler(Exception)
async def handle_generic_error(request, exc):
    logger.error(traceback.format_exc())
    return JSONResponse(status_code=500, content={"error_code": "INTERNAL_SERVER_ERROR"})
```

### IntegrityError Parser (`database_exceptions.py`)
Uses regex patterns to parse both SQLite and PostgreSQL error messages:
```python
UNIQUE_PATTERNS = [r"UNIQUE constraint failed", r"duplicate key", r" UNIQUE "]
FK_PATTERNS = [r"FOREIGN KEY constraint failed", r"foreign key constraint"]
NULL_PATTERNS = [r"NOT NULL constraint failed", r"null value"]
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/exceptions/base_exception.py` | 22 | ApplicationException base class |
| `app/exceptions/business_exceptions.py` | 42 | Domain-specific exceptions |
| `app/exceptions/database_exceptions.py` | 70 | IntegrityError context manager |
| `app/exceptions/exception_handler.py` | 105 | Global FastAPI handlers |
| `app/exceptions/__init__.py` | 15 | Exception exports |

### Standard Error Envelope
```json
{
  "success": false,
  "error_code": "DUPLICATE_ENTRY",
  "message": "A record with this value already exists",
  "details": {}
}
```

### HTTP Status Code Mapping

| Error Code | HTTP Status |
|------------|-------------|
| DUPLICATE_ENTRY | 409 |
| FOREIGN_KEY_VIOLATION | 400 |
| NULL_CONSTRAINT_VIOLATION | 400 |
| RESOURCE_NOT_FOUND | 404 |
| VALIDATION_ERROR | 422 |
| INTERNAL_SERVER_ERROR | 500 |
| INVALID_COMPETITION_STATE | 400 |
| LEADERBOARD_ERROR | 400 |
| DATABASE_ERROR | 400 |

## Dependencies on Other Features

Used by ALL features — this is cross-cutting infrastructure.

## Step-by-Step Implementation Sequence

1. Create ApplicationException base class
2. Create business-specific exception subclasses
3. Create DBIntegrityErrorHandler context manager
4. Create global exception handlers
5. Register handlers on FastAPI app
6. Verify all exception paths work correctly
