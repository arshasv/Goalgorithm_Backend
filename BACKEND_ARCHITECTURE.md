# Backend Architecture

> This document describes the backend architecture for the FIFA Challenge Scoring System. The folder structure has been created as a skeleton with package markers (`__init__.py`) and README stubs. No implementation code exists yet. This remains a design-first planning document.

---

## Architectural Style

The backend will follow a **layered architecture** pattern with clear separation of concerns. Each layer has a single responsibility and communicates only with its adjacent layers.

```
┌─────────────────────────────────────────────┐
│             API / Presentation Layer         │  ← HTTP endpoints, request/response handling
├─────────────────────────────────────────────┤
│              Service / Use Case Layer        │  ← Business logic, scoring rules
├─────────────────────────────────────────────┤
│              Domain / Core Layer             │  ← Entities, formulas, validation rules
├─────────────────────────────────────────────┤
│            Repository / Data Layer           │  ← Database access, queries
├─────────────────────────────────────────────┤
│              Infrastructure Layer            │  ← DB connection, config, external services
└─────────────────────────────────────────────┘
```

---

## Layer Descriptions

---

### Layer 1: API / Presentation Layer

**Responsibility:** Receive HTTP requests, validate input shape, serialize responses.

**Planned Components:**
- Route handlers / controllers for each API endpoint group
- Request validation middleware (schema enforcement against Input/Output Contracts)
- Authentication middleware (token/key verification)
- Response serializers (standardized JSON envelopes)
- Error handling middleware (standardized error format)

**Key Principle:** This layer contains **no business logic**. It delegates immediately to the Service layer.

---

### Layer 2: Service / Use Case Layer

**Responsibility:** Implement all business logic and orchestrate domain operations.

**Planned Service Modules:**

| Module | Responsibility |
|---|---|
| `PredictionService` | Handle prediction submission, deadline enforcement, validation orchestration |
| `ScoringService` | Compute Base Scores, apply multipliers, trigger normalization |
| `ResultService` | Store and validate actual match results |
| `RankingService` | Rank teams per match, assign grade tiers |
| `NormalizationService` | Normalize Phase 1 and Phase 3 scores to their respective mark ceilings |
| `TechnicalEvaluationService` | Accept and store Phase 2 committee scores |
| `PresentationEvaluationService` | Accept raw scores, rank teams, apply multiplier, normalize Phase 3 |
| `LeaderboardService` | Aggregate all phase scores and produce the final leaderboard |
| `TeamService` | Team registration and management |
| `MatchService` | Match lifecycle management (scheduling, freeze, completion) |

**Key Principle:** Services are the **only** layer allowed to contain scoring formulas and business rules. They are testable in isolation.

---

### Layer 3: Domain / Core Layer

**Responsibility:** Define the core entities, value objects, formulas, and validation rules that represent the problem domain.

**Planned Domain Objects:**

| Object | Description |
|---|---|
| `Team` | Core team entity |
| `Match` | Match entity with lifecycle states |
| `Prediction` | Team's prediction submission with validation logic |
| `ActualResult` | Ground truth result for a match |
| `MatchScore` | Computed per-match score for a team |
| `Leaderboard` | Final aggregated scoring structure |
| `ScoringFormula` | Pure functions: base score calculation, multiplier logic, normalization |
| `ValidationRules` | Prediction JSON validation rules, probability sum checks |

**Key Principle:** Domain objects are **framework-agnostic** — they have no dependency on the web framework, ORM, or database driver. They can be unit tested with zero infrastructure setup.

---

### Layer 4: Repository / Data Layer

**Responsibility:** Abstract all database interactions behind clean interfaces.

**Planned Repositories:**

| Repository | Responsibility |
|---|---|
| `TeamRepository` | CRUD operations for teams |
| `MatchRepository` | Match creation, status updates, queries |
| `PredictionRepository` | Store and retrieve predictions; enforce uniqueness per (team, match) |
| `ActualResultRepository` | Store actual results; enforce uniqueness per match |
| `ScoreRepository` | Store computed match scores and cumulative phase scores |
| `EvaluationRepository` | Store Phase 2 and Phase 3 evaluation records |
| `LeaderboardRepository` | Persist and retrieve leaderboard snapshots |

**Key Principle:** Repositories expose only the data access methods the service layer needs. Raw SQL or ORM queries are hidden behind repository interfaces.

---

### Layer 5: Infrastructure Layer

**Responsibility:** Manage all external dependencies and environment concerns.

**Planned Infrastructure Components:**

| Component | Description |
|---|---|
| **Database Connection** | Connection pool management; configuration from environment variables |
| **Configuration Loader** | Load settings (DB URL, secrets, scoring constants) from environment |
| **Auth Provider** | JWT token verification or API key validation |
| **Logging** | Structured logging for all requests and scoring events |
| **Audit Logger** | Immutable log of all scoring computations for traceability |
| **Scheduler (Optional)** | Trigger freeze deadline enforcement and result reminders |

---

## Folder-to-Layer Mapping

The folder structure under `backend/app/` maps directly to the following architecture layers, each with a single, well-defined responsibility:

```
┌─────────────────────────────────────┐
│          api/                       │  ← Handles HTTP request/response only
├─────────────────────────────────────┤
│          schemas/                   │  ← Validates incoming JSON
├─────────────────────────────────────┤
│          services/                  │  ← Controls workflows, decides WHEN scoring happens
├─────────────────────────────────────┤
│          scoring_engine/            │  ← Pure math, decides HOW scoring happens
├─────────────────────────────────────┤
│          database/                  │  ← Stores and retrieves information
└─────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Responsibility | Key Principle |
|---|---|---|
| **api/** | Only handles HTTP request/response | Contains **no business logic**. Delegates immediately to services. |
| **schemas/** | Validates incoming JSON payloads | Defines the contract boundary. Rejects malformed data before any logic runs. |
| **services/** | Controls workflows and orchestrates domain operations | Decides **WHEN** scoring happens. Orchestrates calls to the scoring engine. |
| **scoring_engine/** | Contains pure mathematical calculations only | Decides **HOW** scoring happens. No I/O, no DB, no HTTP. Fully testable in isolation. |
| **database/** | Stores information | No business logic. Storage mechanics only. |
| **utils/** | Reusable helpers | Stateless, side-effect-free utility functions. |

### Services vs. Scoring Engine — The Critical Distinction

| Aspect | Services | Scoring Engine |
|---|---|---|
| Role | Orchestrator | Calculator |
| Decides | **WHEN** scoring happens | **HOW** scoring happens |
| I/O | Yes — calls DB, calls other services | No — pure functions only |
| State | Aware of workflow state (match status, deadlines) | Stateless — receives inputs, returns outputs |
| Composability | Can call multiple engines, combine results | Single focused calculation per function |

---

## Confirmed Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Language | **Python** | 3.11+ |
| API Framework | **FastAPI** | 0.111+ |
| Database | **PostgreSQL** | 15+ |
| ORM | **SQLAlchemy 2.0** (async) | 2.0+ |
| DB Driver | **asyncpg** | 0.29+ |
| Migrations | **Alembic** | 1.13+ |
| Schema Validation | **Pydantic v2** | 2.7+ |
| Authentication | **PyJWT** | 2.8+ |
| Password Hashing | **passlib + bcrypt** | — |
| Testing | **pytest + pytest-asyncio + httpx** | — |
| Containerization | **Docker + Docker Compose** | Docker 24+ |

---

## Planned Folder Structure

> This structure is confirmed for Python/FastAPI. The folder skeleton exists with `__init__.py` package markers and README stubs. Implementation files listed below are planned but not yet created.

```
backend/
│
├── api/                        ← FastAPI routers, middleware, response schemas
│   ├── __init__.py
│   ├── routes/                 ← One router file per feature group
│   │   ├── __init__.py
│   │   ├── teams.py
│   │   ├── matches.py
│   │   ├── predictions.py
│   │   ├── results.py
│   │   ├── scoring.py
│   │   ├── evaluations.py
│   │   └── leaderboard.py
│   ├── middleware/             ← Auth middleware, request logging
│   │   ├── __init__.py
│   │   ├── auth_middleware.py  ← JWT verification, role injection
│   │   └── logging_middleware.py ← Request/response structured logging
│   └── dependencies.py        ← FastAPI dependency injection (DB session, auth)
│
├── schemas/                   ← Pydantic v2 request/response models
│   ├── __init__.py
│   ├── prediction.py
│   ├── result.py
│   ├── evaluation.py
│   ├── score.py
│   └── leaderboard.py
│
├── services/                  ← Business logic and orchestration
│   ├── __init__.py
│   ├── prediction_service.py
│   ├── result_service.py
│   ├── scoring_service.py
│   ├── ranking_service.py
│   ├── normalization_service.py
│   ├── evaluation_service.py
│   ├── leaderboard_service.py
│   ├── team_service.py
│   └── match_service.py
│
├── scoring_engine/            ← Pure scoring functions (no I/O, no DB)
│   ├── __init__.py
│   ├── winner_evaluator.py
│   ├── scoreline_evaluator.py
│   ├── probability_evaluator.py
│   ├── player_evaluator.py
│   ├── base_score_calculator.py
│   ├── ranking_engine.py
│   ├── multiplier_engine.py
│   └── normalization_engine.py
│
├── models/                    ← SQLAlchemy ORM models (database tables)
│   ├── __init__.py            ← Import all models here so Alembic detects them
│   ├── base.py                ← SQLAlchemy DeclarativeBase definition
│   ├── team.py
│   ├── match.py
│   ├── prediction.py
│   ├── player_prediction.py
│   ├── actual_result.py
│   ├── player_actual.py
│   ├── match_score.py
│   ├── cumulative_score.py
│   ├── technical_evaluation.py
│   ├── presentation_evaluation.py
│   └── leaderboard.py
│
├── repositories/              ← Data access layer (one file per entity)
│   ├── __init__.py
│   ├── team_repository.py
│   ├── match_repository.py
│   ├── prediction_repository.py
│   ├── result_repository.py
│   ├── score_repository.py
│   ├── evaluation_repository.py
│   └── leaderboard_repository.py
│
├── infrastructure/            ← DB session, config, auth, logging
│   ├── __init__.py
│   ├── database.py            ← SQLAlchemy async engine + session factory
│   ├── config.py              ← Pydantic Settings (reads .env)
│   ├── auth.py                ← PyJWT token creation and verification
│   └── logging.py             ← Structured logging setup
│
├── migrations/                ← Alembic migration scripts (not a Python package)
│   ├── env.py                 ← Alembic environment config (imports all models)
│   ├── script.py.mako         ← Migration file template
│   └── versions/              ← Auto-generated migration files live here
│
├── tests/                     ← pytest test suite
│   ├── __init__.py
│   ├── conftest.py            ← Shared fixtures (test DB session, async test client)
│   ├── unit/                  ← Pure function tests (no DB, no HTTP)
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_winner_evaluator.py
│   │   ├── test_scoreline_evaluator.py
│   │   ├── test_probability_evaluator.py
│   │   ├── test_player_evaluator.py
│   │   ├── test_base_score_calculator.py
│   │   ├── test_ranking_engine.py
│   │   ├── test_multiplier_engine.py
│   │   └── test_normalization_engine.py
│   └── integration/           ← API route tests (httpx + pytest-asyncio)
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_teams.py
│       ├── test_matches.py
│       ├── test_predictions.py
│       ├── test_results.py
│       ├── test_scoring.py
│       ├── test_evaluations.py
│       └── test_leaderboard.py
│
├── main.py                    ← FastAPI app entry point (creates app, registers routers)
├── alembic.ini                ← Alembic configuration file
├── pyproject.toml             ← Python dependencies and project metadata
└── .env.example               ← Environment variable template
```

---

## Confirmed Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Language | **Python 3.11+** | Team preference; strong ecosystem for data-processing backends |
| API Framework | **FastAPI** | Native async, Pydantic validation built-in, auto-generates OpenAPI docs |
| Database | **PostgreSQL 15+** | ACID compliance, relational integrity for scoring entities, UUID support |
| ORM | **SQLAlchemy 2.0 async** | Async-native, mature repository pattern, pairs with Alembic for migrations |
| DB Driver | **asyncpg** | Fastest async PostgreSQL driver; required by SQLAlchemy async engine |
| Schema Validation | **Pydantic v2** | Bundled with FastAPI; JSON contracts map directly to Pydantic model classes |
| Auth approach | **JWT via PyJWT** | Stateless; role claims (organizer/committee/reviewer/team) encoded in token |
| Scoring trigger | **On-demand (POST API call)** | Organizer-controlled; simpler than event-driven for this scale |
| Score re-computation | **Allowed before `is_final = true`** | Supports ActualResult correction pre-finalization |
| Containerization | **Docker + Docker Compose** | Two services: `api` (FastAPI) + `db` (PostgreSQL) |
| Migrations | **Alembic** | Version-controlled schema changes; integrates with SQLAlchemy |

---

## Scoring Computation Guarantees

The backend architecture must enforce the following guarantees:

1. **Idempotency:** Re-running a scoring computation for the same match produces the same result if inputs are unchanged
2. **Auditability:** Every score computation is logged with a timestamp, inputs used, and outputs produced
3. **Isolation:** Phase 1 scoring, Phase 2 input, and Phase 3 scoring operate independently and do not block each other
4. **Immutability of Predictions:** No prediction can be modified after the freeze deadline; the system enforces this at the repository layer
5. **Single Source of Truth:** Scores are always derived from stored Predictions and ActualResults — they are never directly editable by users
