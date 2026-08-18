# GOALGORITHM Backend

> Backend API for the **FIFA AI Match Prediction Challenge** — a competition where teams build AI/ML models that predict football match outcomes, scored across multiple phases with automated scoring, multi-judge evaluation, and a final leaderboard.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Scoring System](#scoring-system)
- [ML Model Execution](#ml-model-execution)
- [Testing](#testing)
- [Docker Deployment](#docker-deployment)
- [Database Migrations](#database-migrations)
- [Scripts](#scripts)
- [Documentation](#documentation)

---

## Overview

The GOALGORITHM backend is a **FastAPI** application that manages the full lifecycle of a FIFA prediction competition:

1. **Organizer** sets up teams, matches, and scoring configuration
2. **Team Leaders** submit match predictions (manual or via uploaded ML models)
3. **Organizer** enters actual match results
4. **Scoring Engine** automatically evaluates predictions across 8 dimensions
5. **Ranking** assigns grades (A/B/C) with multipliers (3x/2x/1x)
6. **Evaluation** — Committee scores technical implementation, judges score presentations
7. **Leaderboard** aggregates all phases into a final score (max 100 marks)
8. **Analytics** provide data-driven insights to organizers and team leaders

**Production URL:** `https://fifa-scoring.com`

---

## Architecture

The backend follows a **layered architecture** with strict separation of concerns:

```
┌─────────────────────────────────────────┐
│         API / Presentation Layer        │  Routes, request/response handling
├─────────────────────────────────────────┤
│       Schema Validation Layer           │  Pydantic v2 models
├─────────────────────────────────────────┤
│       Service / Use Case Layer          │  Business logic, orchestration
├─────────────────────────────────────────┤
│        Scoring Engine Layer             │  Pure math functions (no I/O)
├─────────────────────────────────────────┤
│        Repository / Data Layer          │  SQLAlchemy ORM queries
├─────────────────────────────────────────┤
│       Infrastructure Layer              │  PostgreSQL, Config, Auth
└─────────────────────────────────────────┘
```

**Key Design Rules:**
- Routes contain **no business logic** — they validate and delegate
- Services orchestrate workflows and decide **when** scoring happens
- Scoring engine contains **only pure functions** — no I/O, no DB, no HTTP
- All exceptions propagate to **global handlers** — no try/except in routes
- All configuration loaded from **environment variables** via Pydantic Settings

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.12+ |
| Framework | FastAPI | 0.111+ |
| Validation | Pydantic | 2.7+ |
| ORM | SQLAlchemy | 2.0+ |
| Database | PostgreSQL | 15+ |
| Migrations | Alembic | 1.13+ |
| Auth | python-jose + bcrypt | JWT (HS256) |
| ML Execution | scikit-learn, XGBoost, LightGBM | Latest |
| Email | AgentMail API | — |
| External Data | api-sports.io | v3 |
| Testing | pytest + httpx | 8.0+ |
| Container | Docker + Docker Compose | 24+ |

---

## Features

### Core Competition
- **Team Management** — 5 teams (A-E) with member rosters and CSV/Excel bulk import
- **Match Management** — 32 knockout matches with lifecycle states and external API import
- **Prediction Submission** — Dual format support (manual JSON + AI model output)
- **Actual Result Entry** — Organizer inputs ground-truth match results

### Scoring Engine (8 Dimensions)
- **Winner Score** (0-5 pts) — Correct prediction
- **Scoreline Score** (0-10 pts) — Exact match or correct margin
- **Probability Score** (0-5 pts) — Calibration accuracy
- **Player Score** (0-5 pts) — Goal prediction accuracy
- **BTTS Score** (0-2 pts) — Both Teams To Score accuracy
- **Total Goals Score** (0-1 pt) — Total goals accuracy
- **First Team to Score** (0-2 pts) — First scoring team
- **Clean Sheet Score** (0-4 pts) — Clean sheet prediction

### Multi-Phase Evaluation
- **Phase 1: AI Prediction** (0-60 marks) — Automated scoring + normalization
- **Phase 2: Technical** (0-20 marks) — Committee evaluation (4 categories)
- **Phase 3: Presentation** (0-20 marks) — Multi-judge scoring with ranking

### Additional Features
- **Dynamic Scoring Configuration** — 30+ adjustable parameters
- **Leaderboard** with visibility controls and historical snapshots
- **Analytics Dashboard** — 5 sections with granular visibility
- **Score Reports** — Team breakdown, multiplier impact, rank analysis
- **ML Model Execution** — Single and batch model execution pipeline
- **External Football API** — Fixture import and result sync
- **Email Service** — Welcome emails and password reset OTP

---

## Project Structure

```
Goalgorithm_Backend/
├── app/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Settings from environment variables
│   ├── api/                       # API routes (22 files)
│   │   ├── __init__.py            # Router aggregation
│   │   ├── deps.py                # Auth dependency injection
│   │   ├── auth_routes.py         # Registration, login, password reset
│   │   ├── admin_auth_routes.py   # Organizer auth
│   │   ├── team_routes.py         # Team CRUD + CSV upload
│   │   ├── match_routes.py        # Match CRUD
│   │   ├── prediction_routes.py   # Prediction submission
│   │   ├── result_routes.py       # Actual result entry
│   │   ├── scoring_routes.py      # Scoring calculation
│   │   ├── leaderboard_routes.py  # Leaderboard
│   │   ├── analytics_routes.py    # Analytics dashboards
│   │   └── ...                    # 12 more route files
│   ├── schemas/                   # Pydantic v2 validation (16 files)
│   ├── services/                  # Business logic (17 files)
│   ├── scoring_engine/            # Pure scoring functions (19 files)
│   │   ├── base_score/            # 8 scoring dimension modules
│   │   ├── multiplier/            # Grade assignment + multiplier
│   │   ├── normalization/         # Phase 1 normalization
│   │   ├── technical_evaluation/  # Phase 2 scoring
│   │   └── presentation_evaluation/ # Phase 3 scoring
│   ├── models/                    # SQLAlchemy ORM models (19 files)
│   ├── repositories/              # Database queries (12 files)
│   ├── auth/                      # JWT authentication (3 files)
│   ├── exceptions/                # Custom exception hierarchy (5 files)
│   ├── dependencies/              # DI container wiring
│   ├── database/                  # DB connection + session
│   ├── email/                     # AgentMail integration
│   ├── model_execution/           # ML model execution pipeline
│   └── utils/                     # Helpers (email validation, team names)
├── tests/                         # Test suite (20 files)
├── alembic/                       # Database migrations (31 versions)
├── scripts/                       # Utility scripts (7 files)
├── docs/                          # Documentation
│   ├── plan/                      # Feature-wise implementation plans (25 files)
│   ├── features/                  # Feature specifications (18 files)
│   ├── api/                       # API documentation (11 files)
│   ├── database/                  # Database design docs
│   └── architecture/              # Architecture documentation
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── alembic.ini
```

---

## Prerequisites

- **Python** 3.12+
- **PostgreSQL** 15+ (or Neon serverless)
- **Node.js** 18+ (for frontend, separate repo)
- **Docker** (optional, for containerized deployment)

---

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Goalgorithm_Backend
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials and API keys
```

### 5. Run Database Migrations

```bash
alembic upgrade head
```

### 6. Seed Initial Data (Optional)

```bash
python seed.py
```

### 7. Start the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 8. Verify

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

**Swagger UI:** http://localhost:8000/docs

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `SECRET_KEY` | Yes | `development_secret_key` | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | JWT token lifetime |
| `APP_NAME` | No | `FIFA Scoring System` | Application name |
| `APP_ENV` | No | `development` | Environment (development/production) |
| `DEBUG` | No | `false` | Debug mode |
| `HOST` | No | `0.0.0.0` | Server host |
| `PORT` | No | `8000` | Server port |
| `DB_POOL_SIZE` | No | `5` | Database pool size |
| `DB_MAX_OVERFLOW` | No | `10` | Database pool overflow |
| `FOOTBALL_API_KEY` | No | — | api-sports.io API key |
| `FOOTBALL_API_BASE_URL` | No | `https://v3.football.api-sports.io` | Football API URL |
| `AGENTMAIL_API_KEY` | No | — | AgentMail email service key |
| `AGENTMAIL_INBOX_ID` | No | — | AgentMail inbox identifier |

---

## API Endpoints

All endpoints are prefixed with `/api/v1`.

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/auth/register` | — | Team leader registration |
| `POST` | `/auth/login` | — | Team leader login |
| `POST` | `/auth/forgot-password` | — | Request password reset OTP |
| `POST` | `/auth/reset-password` | — | Reset password with OTP |
| `POST` | `/auth/change-password` | TEAM_LEADER | Change own password |
| `POST` | `/admin/auth/login` | — | Organizer login |
| `POST` | `/admin/auth/create-user` | ORGANIZER | Create team account |
| `GET` | `/admin/auth/users` | ORGANIZER | List all users |

### Teams

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/teams` | Any | List all teams |
| `GET` | `/teams/{id}` | Any | Get team details |
| `PUT` | `/teams/{id}` | ORGANIZER | Update team |
| `POST` | `/teams/{id}/members` | ORGANIZER | Add member |
| `PUT` | `/teams/{id}/members/{mid}` | ORGANIZER | Update member |
| `DELETE` | `/teams/{id}/members/{mid}` | ORGANIZER | Remove member |
| `POST` | `/teams/upload-members-csv` | ORGANIZER | Bulk CSV/Excel import |
| `GET` | `/teams/template/csv` | ORGANIZER | Download CSV template |
| `GET` | `/teams/template/xlsx` | ORGANIZER | Download XLSX template |

### Matches

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/matches` | ORGANIZER | Create match |
| `GET` | `/matches` | Any | List matches |
| `GET` | `/matches/{id}` | Any | Get match |
| `PUT` | `/matches/{id}` | ORGANIZER | Update match |
| `DELETE` | `/matches/{id}` | ORGANIZER | Delete match |
| `GET` | `/matches/upcoming` | Any | Upcoming matches |
| `POST` | `/external-matches/import` | ORGANIZER | Import from API |
| `POST` | `/external-matches/sync-results` | ORGANIZER | Sync results |

### Predictions

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/predictions` | TEAM_LEADER | Submit prediction |
| `GET` | `/predictions/team/{id}` | Any | Team predictions |
| `GET` | `/predictions/match/{id}` | ORGANIZER | Match predictions |

### Results & Scoring

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/results` | ORGANIZER | Submit actual result |
| `POST` | `/scoring/calculate` | ORGANIZER | Score a match |
| `POST` | `/scoring/recalculate-all` | ORGANIZER | Recalculate all |
| `POST` | `/scoring/batch` | ORGANIZER | Batch scoring |
| `GET` | `/scores/team/{id}` | Any | Team scores |
| `GET` | `/scores/overview` | Any | Score overview |

### Scoring Configuration

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/scoring-config/active` | Any | Active config |
| `GET` | `/scoring-config/guidelines` | Any | Config + guidelines |
| `POST` | `/scoring-config` | ORGANIZER | Create config |
| `PUT` | `/scoring-config/{id}` | ORGANIZER | Update config |
| `POST` | `/scoring-config/{id}/activate` | ORGANIZER | Activate config |
| `POST` | `/scoring-config/reset` | ORGANIZER | Reset to defaults |

### Evaluations

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/technical-evaluation` | ORGANIZER | Submit technical scores |
| `POST` | `/presentation-evaluation` | ORGANIZER | Submit presentation scores |
| `GET` | `/presentation-rounds` | ORGANIZER | List rounds |
| `POST` | `/presentation-rounds` | ORGANIZER | Create round |
| `GET` | `/judges` | ORGANIZER | List judges |
| `POST` | `/judges` | ORGANIZER | Create judge |

### Leaderboard

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/leaderboard` | Any | Get leaderboard |
| `POST` | `/leaderboard/recalculate` | ORGANIZER | Recalculate |
| `GET` | `/leaderboard/frozen` | Any | Frozen snapshot |
| `GET` | `/admin/leaderboard/settings` | ORGANIZER | Visibility settings |
| `PUT` | `/admin/leaderboard/settings` | ORGANIZER | Update visibility |

### Model Submission & Execution

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/model-submissions/upload` | TEAM_LEADER | Upload model |
| `GET` | `/model-submissions/team/{id}` | Any | Team submissions |
| `POST` | `/model-execution/upload` | ORGANIZER | Upload for execution |
| `POST` | `/model-execution/{id}/execute` | ORGANIZER | Execute model |
| `GET` | `/model-execution/{id}/status` | ORGANIZER | Execution status |
| `POST` | `/batch-executions/create` | ORGANIZER | Create batch |
| `POST` | `/batch-executions/{id}/execute` | ORGANIZER | Run batch |
| `GET` | `/batch-executions/{id}/progress` | ORGANIZER | Batch progress |

### Analytics & Reports

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/analytics/overview` | Visible* | Overview stats |
| `GET` | `/analytics/models` | Visible* | Model analytics |
| `GET` | `/analytics/presentation` | Visible* | Presentation analytics |
| `GET` | `/analytics/judges` | Visible* | Judge analytics |
| `GET` | `/analytics/team/{id}` | Any | Team analytics |
| `GET` | `/reports/team-breakdown` | ORGANIZER | Score journey |
| `GET` | `/reports/multiplier-impact` | ORGANIZER | Multiplier analysis |
| `GET` | `/reports/rank-analysis` | ORGANIZER | Rank movements |
| `GET` | `/reports/phase-contribution` | ORGANIZER | Phase composition |

\* Visibility checked against `LeaderboardVisibilityModel` for TEAM_LEADER role.

---

## Database Schema

### Core Tables

| Table | Purpose | Key Relationships |
|-------|---------|-------------------|
| `users` | Team leader + organizer accounts | → teams |
| `teams` | 5 competition teams (A-E) | ← users, → team_members |
| `team_members` | Team member roster | → teams |
| `matches` | 32 knockout matches | ← predictions, scores |
| `predictions` | Team predictions per match | → teams, matches |
| `player_predictions` | Player-level goal predictions | → predictions |
| `actual_results` | Actual match results | → matches |
| `player_actuals` | Actual player performance | → actual_results |
| `scores` | Per-match scoring breakdown | → teams, matches |
| `cumulative_phase_scores` | Phase 1 normalized scores | → teams |
| `technical_evaluations` | Phase 2 committee scores | → teams |
| `presentation_evaluations` | Phase 3 judge scores | → teams, rounds |
| `leaderboards` | Final leaderboard entries | → teams |
| `scoring_configs` | Dynamic scoring parameters | ← scores |
| `model_submissions` | Uploaded ML models | → teams |
| `model_evaluations` | Model performance metrics | → model_submissions |

### Entity Relationship

```
users ──→ teams ──→ team_members
                ├──→ predictions ──→ player_predictions
                ├──→ scores
                ├──→ cumulative_phase_scores
                ├──→ technical_evaluations
                ├──→ presentation_evaluations
                ├──→ model_submissions ──→ model_evaluations
                └──→ leaderboards

matches ──→ predictions
         ├──→ actual_results ──→ player_actuals
         └──→ scores
```

---

## Scoring System

### Phase 1: AI Prediction Scoring (0-60 marks)

**Base Score Calculation** (per match, max 25 pts):

| Dimension | Max Points | Logic |
|-----------|-----------|-------|
| Winner | 5+ | Correct prediction |
| Scoreline | 10 | Exact = 10, margin = 5, wrong = 0 |
| Probability | 5 | All 5 fields within ±15% threshold |
| Player | 5 | Average accuracy across predicted players |
| BTTS | 2 | Both Teams To Score accuracy |
| Total Goals | 1 | Exact total goals match |
| First Team to Score | 2 | Correct first scoring team |
| Clean Sheet | 4 | Home + away clean sheet accuracy |

**Multiplier & Grade:**

| Rank | Grade | Multiplier |
|------|-------|-----------|
| 1st (unique) | A | 3x |
| 2nd-4th | B | 2x |
| 5th (unique) | C | 1x |

**Normalization:** `(team_earned / max_earned) × 60`

### Phase 2: Technical Evaluation (0-20 marks)

| Category | Weight |
|----------|--------|
| Code Quality | ×5 |
| Backend Quality | ×5 |
| Teamwork | ×4 |
| AI Explanation | ×6 |

Total weighted sum, capped at 20.

### Phase 3: Presentation Evaluation (0-20 marks)

| Criteria | Max |
|----------|-----|
| AI Explanation | 20 |
| Q&A | 15 |
| Delivery | 15 |

Multi-judge averaging → per-round ranking → grade multiplier → normalization to 20 marks.

### Final Score

```
final_score = phase1_score + technical_score + presentation_score
```

Capped at 100.00 marks.

---

## ML Model Execution

### Single Execution

```
Upload .pkl → Execute (background) → Predict → Save as Prediction → Auto-score
```

### Batch Execution

```
Discover latest models per team → Create jobs (teams × matches) → Execute all → Track progress
```

### Supported Formats

`.pkl`, `.pickle`, `.pt`, `.pth`, `.h5`, `.joblib`, `.onnx`, `.sav`

### Safety

- Custom `CompatUnpickler` with restricted allowed classes
- Background task execution (non-blocking)
- Failed models never crash the backend

---

## Testing

### Run All Tests

```bash
pytest tests/
```

### Run Unit Tests Only

```bash
pytest tests/test_base_score.py tests/test_multiplier.py tests/test_normalization.py tests/test_technical_score.py tests/test_presentation_score.py tests/test_leaderboard.py
```

### Run Integration Tests Only

```bash
pytest tests/test_api.py tests/test_full_competition_flow.py tests/integration/
```

### Run with Coverage

```bash
pytest --cov=app tests/
```

### Test Structure

| Test File | Coverage | Tests |
|-----------|----------|-------|
| `test_base_score.py` | All 8 scoring dimensions | 14 |
| `test_multiplier.py` | Ranking, grades, tie-breaking | 17 |
| `test_normalization.py` | Phase 1 normalization | 8 |
| `test_technical_score.py` | Technical evaluation | 7 |
| `test_presentation_score.py` | Presentation scoring | 5 |
| `test_leaderboard.py` | Leaderboard generation | 17 |
| `test_schemas.py` | Pydantic validation | 18 |
| `test_api.py` | API integration | 30+ |
| `test_analytics.py` | Analytics endpoints | 9 |
| `test_scoring_config.py` | Config CRUD | 8 |
| `test_leaderboard_visibility.py` | Visibility settings | 8 |
| `test_full_competition_flow.py` | End-to-end flow | 3 |

**Total:** 127+ tests

---

## Docker Deployment

### Quick Start

```bash
docker compose up -d --build
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| `backend` | 8002:8000 | FastAPI application |

### Commands

```bash
# Build and start
docker compose up -d --build

# View logs
docker compose logs -f backend

# Stop
docker compose down

# Rebuild from scratch
docker compose down && docker compose up -d --build
```

### Verify

```bash
curl http://localhost:8002/health
# {"status": "ok"}

# Swagger UI
open http://localhost:8002/docs
```

---

## Database Migrations

### Generate Migration

```bash
alembic revision --autogenerate -m "description"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Rollback

```bash
alembic downgrade -1
```

### Current State

31 migration files covering full schema evolution.

---

## Scripts

| Script | Purpose |
|--------|---------|
| `seed.py` | Seed organizer admin account |
| `repair_teams.py` | Repair orphan team records |
| `repair_teams_v2.py` | Repair teams with gmail emails |
| `repair_teams_v3.py` | Comprehensive team repair |
| `cleanup_orphans.py` | Delete orphan predictions/scores |
| `clear_db.py` | Delete match-derived data |
| `wipe_data.py` | TRUNCATE all application tables |
| `hard_reset.py` | Full reset + reseed |
| `migrate_db.py` | SQLite migration utilities |
| `test_score.py` | Quick manual score test |

### Utility Scripts

| Script | Purpose |
|--------|---------|
| `scripts/evaluate_models.py` | Batch model evaluation pipeline |
| `scripts/generate_reports.py` | Generate MD/HTML/PDF reports |
| `scripts/generate_consolidated_prediction_report.py` | Cross-team PDF report |
| `scripts/clear_team_data.py` | Safe team data deletion |
| `scripts/clear_predictions.py` | Safe prediction deletion |
| `scripts/debug_models.py` | Debug model outputs |
| `scripts/reset_competition_data.py` | Full competition reset |

---

## Documentation

### Main Documentation

| Document | Description |
|----------|-------------|
| [Technical Documentation](docs/TECHNICAL_DOCUMENTATION.md) | Documentation index |
| [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) | SDD phase tracking |
| [Test Plan](docs/TEST_PLAN.md) | Testing strategy |

### Feature Specifications (`docs/features/`)

| Document | Feature |
|----------|---------|
| `prediction-management.md` | Prediction submission |
| `actual-result-management.md` | Result entry |
| `base-scoring-engine.md` | Scoring logic |
| `ranking-multiplier.md` | Grade/multiplier |
| `phase-normalization.md` | Score normalization |
| `technical-evaluation.md` | Phase 2 scoring |
| `presentation-evaluation.md` | Phase 3 scoring |
| `leaderboard.md` | Final leaderboard |
| `team-management.md` | Team/member CRUD |
| `match-management.md` | Match lifecycle |
| `excel-csv-upload.md` | Bulk import |
| `admin-scoring-config.md` | Dynamic config |
| `model-submission.md` | Model upload |
| `MODEL_EXECUTION_SYSTEM.md` | Model execution |
| `ANALYTICS_MODULE.md` | Analytics system |
| `score-reports-analysis.md` | Score reports |

### Implementation Plans (`docs/plan/`)

25 feature-wise implementation documents covering every module in the codebase. See [docs/plan/README.md](docs/plan/README.md) for the complete index.

### Architecture (`docs/architecture/`)

| Document | Description |
|----------|-------------|
| `system-architecture.md` | Layer diagram, tech stack |
| `database-architecture.md` | DB layer, error handling |
| `error-handling-architecture.md` | Exception hierarchy |
| `scoring-architecture.md` | Scoring data flow |
| `leaderboard-architecture.md` | Leaderboard generation |
| `prediction-architecture.md` | Prediction data flow |
| `external_football_api_integration.md` | API integration |
| `DEPLOYMENT.md` | Deployment guide |

---

## License

Private — GOALGORITHM Project
