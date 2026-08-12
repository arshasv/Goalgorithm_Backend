# Deployment Guide

## Prerequisites

- Python 3.12+
- Node.js 18+ (for local frontend development)
- Docker & Docker Compose (for containerised deployment)

---

## 1. Environment Configuration

Configuration follows a centralized flow:

```
.env
  ↓
python-dotenv → app/config.py (Settings singleton)
  ↓
FastAPI / SQLAlchemy / Alembic
```

All environment variables are loaded from `backend/.env` by `app/config.py` using `python-dotenv`. The `Settings` object is imported and reused across the application — no module reads `os.environ` directly.

| File | Purpose |
|---|---|
| `backend/.env` | Actual backend config values (git-ignored) |
| `backend/.env.example` | Template with placeholder secrets (committed) |
| `react-frontend/.env` | Optional Vite environment variables |

### Local vs Container

| Context | `DATABASE_URL` value |
|---|---|
| Local (no Docker) | `postgresql://user:pass@localhost:5432/db` |
| Docker Compose | `postgresql://user:pass@postgres:5432/db` |
| Testing | Override via `DATABASE_URL=sqlite:///...` |

---

## 2. Local Setup

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt

cp .env.example .env
# Edit .env: set DATABASE_URL to local PostgreSQL

python -m pytest
uvicorn app.main:app --reload
```

### Frontend (React + Vite)
```bash
cd react-frontend
npm install
npm run dev
```
The React dev server runs on `http://localhost:5173` and proxies `/api` calls to `http://localhost:8000`.

---

## 3. Docker Compose (Full Stack)

Both the API and PostgreSQL read from the same `backend/.env` file. The React frontend is built and served via an Nginx container.

Start all services:

```bash
docker compose up -d --build
```

Check service status:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f
```

Stop services:

```bash
docker compose down
```

---

## API Endpoints (Docker)

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/api/v1/auth/register` | POST | Register team leader |
| `/api/v1/auth/login` | POST | Login and receive JWT |
| `/api/v1/teams` | GET | List teams |
| `/api/v1/matches` | GET | List matches |
| `/api/v1/predictions` | POST | Submit team prediction |
| `/api/v1/actual-results` | POST | Submit actual match result |
| `/api/v1/calculate-match-score` | POST | Calculate match base score |
| `/api/v1/technical-score` | POST | Calculate technical score |
| `/api/v1/presentation-score` | POST | Calculate presentation score |
| `/api/v1/leaderboard/calculate` | POST | Generate final leaderboard |
| `/api/v1/team-leader/model` | POST | Upload team ML model |

Interactive Swagger UI is available at `http://localhost:8000/docs`.
