# Database Layer

Stores and retrieves information.

**Responsibility:** Manage database connections, sessions, and queries. Abstract all data access behind clean interfaces.

**Key principle:** No business logic lives here. This layer handles storage mechanics only.

**Contents:**
- Database connection pool management
- Session factory and dependency injection
- Repository implementations for data access
- Alembic migration configuration
