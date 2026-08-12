# API Layer

Handles HTTP request/response only.

**Responsibility:** Receive HTTP requests, validate input shape, serialize responses.

**Key principle:** Contains no business logic. Delegates immediately to the Service layer.

**Contents:**
- Route handlers / controllers for each API endpoint group
- Request validation middleware (schema enforcement)
- Authentication middleware (JWT verification)
- Response serializers (standardized JSON envelopes)
- Error handling middleware
