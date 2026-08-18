# Feature 25: Docker & Deployment

## Feature Overview

Containerized deployment using Docker and Docker Compose. Includes Dockerfile for the FastAPI application, docker-compose.yml orchestrating API + PostgreSQL services, and comprehensive deployment documentation.

## Purpose & Requirements

- Dockerfile with python:3.12-slim base image
- Docker Compose with API + PostgreSQL services
- Environment variable injection via .env
- Health check endpoint for container monitoring
- Swagger UI accessible at /docs
- Nginx reverse proxy for frontend (optional)

## How the Feature Works Internally

### Dockerfile
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [db]
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: goalgorithm
      POSTGRES_USER: goalgorithm
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes: [pgdata:/var/lib/postgresql/data]

volumes:
  pgdata:
```

### Startup Flow
```
docker compose up -d --build
    ↓
PostgreSQL starts → accepts connections
    ↓
API starts → connects to DB
    ↓
Alembic runs migrations (if configured)
    ↓
FastAPI serves on port 8000
    ↓
Swagger UI at localhost:8000/docs
    ↓
Health check at localhost:8000/health
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `Dockerfile` | ~15 | Container build instructions |
| `docker-compose.yml` | ~30 | Multi-service orchestration |
| `.dockerignore` | ~10 | Exclude .venv, __pycache__, .git |
| `docs/architecture/DEPLOYMENT.md` | 112 | Deployment documentation |

## Configuration/Environment Variables

All configuration via `.env` file:
- `DATABASE_URL` — PostgreSQL connection string
- `JWT_SECRET_KEY` — JWT signing secret
- `AGENTMAIL_API_KEY` / `AGENTMAIL_INBOX_ID` — Email service
- `FOOTBALL_API_KEY` — External API

## Deployment Commands

```bash
# Build and start
docker compose up -d --build

# View logs
docker compose logs -f api

# Stop
docker compose down

# Reset database
docker compose down -v && docker compose up -d --build
```

## Edge Cases

- DB starts before API → depends_on handles ordering
- API crashes → restart: unless-stopped policy
- Volume persistence → pgdata survives container restarts

## Dependencies on Other Features

Requires ALL features to be implemented before deployment.

## Step-by-Step Implementation Sequence

1. Create Dockerfile with python:3.12-slim
2. Create .dockerignore
3. Create docker-compose.yml with API + PostgreSQL
4. Configure .env injection
5. Test docker compose build
6. Test docker compose up
7. Verify health endpoint returns 200
8. Verify Swagger UI accessible
9. Verify all API endpoints work in container
10. Test database persistence across restarts
