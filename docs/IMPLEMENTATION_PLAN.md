# Spec Driven Development — Implementation Plan

> GOALGORITHM Scoring System Backend
> Approach: **Spec Driven Development (SDD)** — every implementation step is derived from a documented specification before code is written.

---

## Table of Contents

1. [Approach & Principles](#approach--principles)
2. [Project Overview](#project-overview)
3. [Phase 0: Project Scaffolding & Infrastructure](#phase-0-project-scaffolding--infrastructure)
4. [Phase 1: Database Models & Migrations](#phase-1-database-models--migrations)
5. [Phase 2: Authentication & Authorization](#phase-2-authentication--authorization)
6. [Phase 3: Team Management](#phase-3-team-management)
7. [Phase 4: Match Management](#phase-4-match-management)
8. [Phase 5: Prediction Management](#phase-5-prediction-management)
9. [Phase 6: Actual Result Management](#phase-6-actual-result-management)
10. [Phase 7: Base Scoring Engine](#phase-7-base-scoring-engine)
11. [Phase 8: Ranking & Multiplier](#phase-8-ranking--multiplier)
12. [Phase 9: Phase Normalization](#phase-9-phase-normalization)
13. [Phase 10: Technical Evaluation](#phase-10-technical-evaluation)
14. [Phase 11: Presentation Evaluation](#phase-11-presentation-evaluation)
15. [Phase 12: Leaderboard](#phase-12-leaderboard)
16. [Phase 13: Admin Scoring Configuration](#phase-13-admin-scoring-configuration)
17. [Phase 14: Model Submission](#phase-14-model-submission)
18. [Phase 15: Model Execution System](#phase-15-model-execution-system)
19. [Phase 16: Analytics Module](#phase-16-analytics-module)
20. [Phase 17: Reports & Score Analysis](#phase-17-reports--score-analysis)
21. [Phase 18: Excel/CSV Upload](#phase-18-excelcsv-upload)
22. [Phase 19: External Football API Integration](#phase-19-external-football-api-integration)
23. [Phase 20: Testing & Quality Assurance](#phase-20-testing--quality-assurance)
24. [Phase 21: Docker & Deployment](#phase-21-docker--deployment)
25. [Dependency Matrix](#dependency-matrix)
26. [Spec Traceability Matrix](#spec-traceability-matrix)

---

## Approach & Principles

### What is Spec Driven Development?

Spec Driven Development (SDD) is a methodology where **every implementation step is derived from a written specification** before code is written. The process follows:

```
Specification → Design → Implementation → Verification → Sign-off
```

### SDD Workflow Per Phase

Each phase in this plan follows a strict 5-step workflow:

| Step | Action | Deliverable |
|------|--------|-------------|
| **1. Spec** | Read & understand the relevant specification document | Verified understanding |
| **2. Design** | Define interfaces, schemas, data flow before coding | Interface contracts |
| **3. Implement** | Write code following the design and spec exactly | Working code |
| **4. Verify** | Run tests, lint, type-check, manual verification | Passing tests |
| **5. Sign-off** | Mark phase as complete with evidence | Completed checklist |

### Completion Criteria

A phase is marked `[X]` (complete) only when ALL of these are true:
- [X] All implementation tasks done
- [X] All unit tests passing
- [X] All integration tests passing
- [X] Lint/type checks pass
- [X] Spec traceability verified (every spec item maps to code)

---

## Project Overview

| Attribute | Value |
|-----------|-------|
| **Project** | GOALGORITHM Scoring System Backend |
| **Stack** | Python 3.12+, FastAPI, SQLAlchemy 2.0, PostgreSQL 15+, Alembic |
| **Architecture** | Layered: API → Schema → Service → Scoring Engine → Repository → Database |
| **Auth** | JWT (python-jose) + bcrypt password hashing |
| **Testing** | pytest + pytest-asyncio + httpx |
| **Containerization** | Docker + Docker Compose |
| **Total Features** | 18 documented feature specs |
| **Total API Endpoints** | 22 route files, 100+ endpoints |
| **Total Database Tables** | 15+ core tables |
| **Total Source Files** | 174 implemented Python files (~21,474 LOC) |

---

## Phase 0: Project Scaffolding & Infrastructure

> **Spec References:** `architecture/system-architecture.md`, `architecture/database-architecture.md`, `architecture/DEPLOYMENT.md`

### Specification Summary

- FastAPI application with layered architecture (API → Schema → Service → Scoring Engine → Repository → Database)
- Configuration via `.env` loaded through `config.py` Pydantic Settings
- SQLAlchemy 2.0 async engine + session factory
- Centralized exception handling with custom `ApplicationException` hierarchy
- Dependency injection container for wiring repositories → services → routes

### Implementation Tasks

- [X] Create project directory structure: `app/`, `app/api/`, `app/schemas/`, `app/services/`, `app/scoring_engine/`, `app/models/`, `app/repositories/`, `app/auth/`, `app/utils/`, `app/exceptions/`, `app/dependencies/`, `app/email/`, `app/model_execution/`, `app/database/`, `tests/`
- [X] Create `app/__init__.py` package markers for all directories
- [X] Create `app/config.py` — Pydantic Settings class loading from `.env` (DB URL, auth secret, football API key, AgentMail config)
- [X] Create `app/main.py` — FastAPI app factory with CORS middleware, lifespan handler, router registration, exception handler registration, `/health` and `/version` endpoints
- [X] Create `app/database/base.py` — SQLAlchemy `DeclarativeBase`
- [X] Create `app/database/connection.py` — async engine from config
- [X] Create `app/database/session.py` — `SessionLocal` factory and `get_db` dependency generator
- [X] Create `app/exceptions/base_exception.py` — `BaseApplicationException` with message/detail/status_code
- [X] Create `app/exceptions/business_exceptions.py` — domain-specific exceptions (DuplicateUser, DuplicateTeam, DataNotFound, etc.)
- [X] Create `app/exceptions/database_exceptions.py` — `DBIntegrityErrorHandler` context manager for SQLAlchemy IntegrityError
- [X] Create `app/exceptions/exception_handler.py` — FastAPI exception handlers mapping exceptions to structured HTTP responses
- [X] Create `app/dependencies/__init__.py` — DI container wiring all repositories → services
- [X] Create `requirements.txt` with all dependencies
- [X] Create `.env.example` with environment variable template
- [X] Create `alembic.ini` and `alembic/env.py` for migrations

### Verification Checklist

- [X] `app/main.py` starts without errors: `uvicorn app.main:app`
- [X] `GET /health` returns `{"status": "ok"}`
- [X] `GET /version` returns version string
- [X] Configuration loads from `.env` correctly
- [X] All package imports resolve (no circular dependencies)

### Phase 0 Status: [X] COMPLETE

---

## Phase 1: Database Models & Migrations

> **Spec References:** `database/schema-design.md`, `database/database-overview.md`, `database/feature-database-mapping.md`, `database/postgres-implementation-plan.md`

### Specification Summary

15+ tables with UUID primary keys, foreign key relationships, check constraints, and enum types. Key tables: `users`, `teams`, `team_members`, `matches`, `predictions`, `player_predictions`, `actual_results`, `player_actuals`, `scores`, `cumulative_phase_scores`, `technical_evaluations`, `presentation_evaluations`, `leaderboard`, `scoring_configs`, `upload_window_config`, `model_submissions`, `model_evaluations`.

### Implementation Tasks

- [X] Create `app/models/enums.py` — all enum types: `UserRole`, `MatchStatus`, `MatchWinner`, `Grade`, `SubmissionStatus`, etc.
- [X] Create `app/models/user.py` — `UserModel` (id, username, email, password_hash, role, is_active)
- [X] Create `app/models/team.py` — `TeamModel` (id, name, name_normalized, code, team_leader_name, user_id FK, registered_at, is_active, is_csv_managed)
- [X] Create `app/models/team_member.py` — `TeamMemberModel` (id, team_id FK, name, employee_id, group_code, created_at)
- [X] Create `app/models/match.py` — `MatchModel` (id, match_number unique 1-32, home/away_team_name, scheduled_at, freeze_deadline, status enum, external_api fields)
- [X] Create `app/models/prediction.py` — `PredictionModel` + `PlayerPredictionModel` with unique constraint on (team_id, match_id), FK RESTRICT
- [X] Create `app/models/actual_result.py` — `ActualResultModel` + `PlayerActualModel` with match_id unique FK
- [X] Create `app/models/score.py` — `ScoreModel` with unique (team_id, match_id), check constraint base_score 0-25
- [X] Create `app/models/leaderboard.py` — `LeaderboardModel` with team_id unique, rank index, final_score check 0-100
- [X] Create `app/models/leaderboard_visibility.py` — `LeaderboardVisibilityModel` with 19 boolean flags
- [X] Create `app/models/evaluation.py` — `TechnicalEvaluationModel` + `PresentationEvaluationModel`
- [X] Create `app/models/judge.py` — `JudgeModel` (name, email)
- [X] Create `app/models/presentation_round.py` — `PresentationRoundModel` (round_number, status)
- [X] Create `app/models/scoring_config.py` — `ScoringConfigModel` with 25+ configurable parameters
- [X] Create `app/models/upload_window.py` — `UploadWindowModel` (is_enabled, start_time, end_time)
- [X] Create `app/models/model_submission.py` — `ModelSubmissionModel` (file metadata, version, status enum)
- [X] Create `app/models/model_evaluation.py` — `ModelEvaluationModel` (accuracy metrics, FK to model)
- [X] Create `app/models/password_reset_otp.py` — `PasswordResetOTPModel` (user_id FK, OTP, expiry, used)
- [X] Create `app/models/__init__.py` — import and re-export all models for Alembic discovery
- [X] Create Alembic initial migration
- [X] Create `scripts/seed.py` — seed organizer admin account
- [X] Run `alembic upgrade head` — verify all tables created

### Verification Checklist

- [X] All 15+ tables created in database
- [X] All foreign keys resolve correctly
- [X] All check constraints enforced (base_score 0-25, match_number 1-32, etc.)
- [X] All unique constraints enforced (team code, team name_normalized, prediction per team+match, etc.)
- [X] All enum types work (MatchStatus, UserRole, MatchWinner, Grade)
- [X] Seed script creates organizer account
- [X] No Alembic migration errors

### Phase 1 Status: [X] COMPLETE

---

## Phase 2: Authentication & Authorization

> **Spec References:** `architecture/system-architecture.md` (Auth Provider), `architecture/error-handling-architecture.md`, `api/team-management-api.md` (register endpoint)

### Specification Summary

JWT-based authentication with role-based access control. Roles: `organizer`, `team_leader`. Token contains user ID and role. Password hashing via bcrypt. Registration creates user + links to team. Auth middleware extracts current user from Bearer token.

### Implementation Tasks

- [X] Create `app/auth/auth_service.py` — password hashing (passlib bcrypt), JWT token create/decode, `get_current_user` dependency
- [X] Create `app/auth/auth_bearer.py` — `HTTPBearer` + `HTTPAuthorizationCredentials` for FastAPI
- [X] Create `app/schemas/auth_schema.py` — `UserRegister`, `UserLogin`, `TokenResponse`, `UserResponse`, `AdminLogin` schemas
- [X] Create `app/api/auth_routes.py` — register, login, me, change password, password reset request/verify/reset endpoints
- [X] Create `app/api/admin_auth_routes.py` — admin login, admin register, admin me, admin list users, admin deactivate
- [X] Create `app/api/deps.py` — dependency injection: `get_db`, `get_current_user`, `require_organizer`, `require_team_leader`
- [X] Create `app/services/auth_service.py` — registration flow (create user + link team), login flow (verify password + generate token), password reset OTP flow, admin auth
- [X] Create `app/utils/email_validator.py` — email domain whitelist validation

### Verification Checklist

- [X] `POST /api/v1/auth/register` creates user with hashed password
- [X] `POST /api/v1/auth/login` returns JWT token
- [X] `GET /api/v1/auth/me` returns current user from token
- [X] Protected endpoints reject requests without token (401)
- [X] Organizer-only endpoints reject team_leader (403)
- [X] Team leader endpoints reject organizer access where appropriate
- [X] Password reset flow works end-to-end
- [X] Duplicate registration rejected (409)

### Phase 2 Status: [X] COMPLETE

---

## Phase 3: Team Management

> **Spec References:** `features/team-management.md`, `features/excel-csv-upload.md`, `api/team-management-api.md`

### Specification Summary

5 teams (A-E) with bulk roster upload via CSV/Excel. Group-to-Team mapping: A→Team A, ..., E→Team E. `is_csv_managed` flag prevents manual member addition. Member display: Name + Employee ID. Role badge system.

### Implementation Tasks

- [X] Create `app/schemas/team_schema.py` — `TeamCreate`, `TeamUpdate`, `MemberCreate`, `MemberUpdate`, `TeamResponse` schemas
- [X] Create `app/repositories/team_repository.py` — basic CRUD for teams
- [X] Create `app/services/team_service.py` — team CRUD, member management, CSV/XLSX upload parsing, group-based linking, `is_csv_managed` enforcement
- [X] Create `app/api/team_routes.py` — team CRUD, member CRUD, CSV upload (`POST /upload-members-csv`), template download, organizer member management
- [X] Implement CSV parsing: `csv.DictReader` (UTF-8), `openpyxl` (XLSX), `xlrd` (XLS)
- [X] Implement group-to-team mapping: `GROUP_TO_TEAM = {"A": "Team A", "B": "Team B", ...}`
- [X] Implement member conflict detection (CSV-managed vs manual)
- [X] Create `app/utils/team_name_utils.py` — team name normalization (lowercase, strip, remove "team " prefix)

### Verification Checklist

- [X] `GET /api/v1/teams` returns all teams with `is_csv_managed` flag
- [X] `POST /api/v1/teams/upload-members-csv` parses CSV and creates members
- [X] `POST /api/v1/teams/upload-members-csv` parses XLSX correctly
- [X] `POST /api/v1/teams/upload-members-csv` parses XLS correctly
- [X] Unknown groups silently skipped
- [X] `is_csv_managed=true` blocks manual member addition
- [X] Non-organizer upload rejected (403)
- [X] Unsupported file extension rejected (400)
- [X] Missing columns rejected (400)
- [X] `GET /api/v1/teams/{team_id}/members` returns member list

### Phase 3 Status: [X] COMPLETE

---

## Phase 4: Match Management

> **Spec References:** `features/match-management.md`, `api/match-management-api.md`

### Specification Summary

32 knockout matches with lifecycle states: SCHEDULED → FROZEN → COMPLETED → RESULT_ENTERED → SCORED. Freeze deadline auto-calculated as 1 hour before kickoff. Bulk CSV upload support.

### Implementation Tasks

- [X] Create `app/schemas/match_schema.py` — `MatchCreate`, `MatchUpdate`, `MatchResponse` schemas
- [X] Create `app/repositories/match_repository.py` — find by match_number, get scheduled matches, find external match
- [X] Create `app/services/match_service.py` — match CRUD, bulk create, duplicate detection, status management, external API sync
- [X] Create `app/api/match_routes.py` — GET/POST/PUT/DELETE matches, bulk create, status management

### Verification Checklist

- [X] `POST /api/v1/matches` creates match with auto-calculated freeze_deadline
- [X] `GET /api/v1/matches` returns all matches
- [X] Duplicate match_number rejected (409)
- [X] Status progression works (SCHEDULED → FROZEN → COMPLETED)
- [X] Non-organizer CRUD rejected (403)
- [X] Match number validated (1-32)

### Phase 4 Status: [X] COMPLETE

---

## Phase 5: Prediction Management

> **Spec References:** `features/prediction-management.md`, `api/prediction-api.md`, `api/prediction_format_reference.md`, `architecture/prediction-architecture.md`

### Specification Summary

Teams submit prediction JSON before freeze deadline. Idempotent submission (same team+match overwrites). Validation: winner enum, probability ranges, scoreline non-negative, non-empty player list. AI format support. Prediction stored with `raw_payload` preserving original JSON.

### Implementation Tasks

- [X] Create `app/schemas/prediction_schema.py` — `PredictionSubmission` with nested `MatchPrediction`, `PlayerPrediction`, auto-computed fields, AI format support (249 lines)
- [X] Create `app/repositories/prediction_repository.py` — team+match lookup, freeze-window queries, cumulative phase scores, score aggregation (136 lines)
- [X] Create `app/services/prediction_service.py` — prediction submission, freeze-time enforcement, auto-score on submit, AI format support, idempotency handling (456 lines)
- [X] Create `app/api/prediction_routes.py` — prediction submission, team predictions list, match predictions, AI format prediction (361 lines)

### Verification Checklist

- [X] `POST /api/v1/predictions` accepts valid prediction (200/201)
- [X] Prediction after freeze deadline rejected (423)
- [X] Duplicate team+match overwrites existing (idempotent)
- [X] Invalid prediction rejected with 422 + field-level details
- [X] Non-existent team/match returns 404
- [X] AI format prediction accepted and normalized
- [X] `raw_payload` preserves original JSON
- [X] `GET /api/v1/predictions/team/{team_id}` returns team predictions
- [X] `GET /api/v1/predictions/match/{match_id}` returns match predictions

### Phase 5 Status: [X] COMPLETE

---

## Phase 6: Actual Result Management

> **Spec References:** `features/actual-result-management.md`, `api/prediction-api.md` (result endpoint)

### Specification Summary

Organizer submits actual match result JSON. Validates winner against scoreline, checks for duplicates by match_id, stores for scoring reference. Input: match_id, actual_winner, final_score, player_results.

### Implementation Tasks

- [X] Create `app/schemas/actual_result_schema.py` — `ActualResultSubmission`, `PlayerResult` schemas
- [X] Create `app/repositories/` (shared with prediction_repository.py)
- [X] Create `app/services/result_service.py` — actual result submission, match status update to COMPLETED (100 lines)
- [X] Create `app/api/result_routes.py` — actual result submission endpoint (35 lines)

### Verification Checklist

- [X] `POST /api/v1/actual-results` accepts valid result (201)
- [X] Duplicate result for same match rejected (400)
- [X] Winner contradicts scoreline rejected (422)
- [X] Non-organizer entry rejected (403)
- [X] Match status updates to COMPLETED on result submission
- [X] Player results stored correctly

### Phase 6 Status: [X] COMPLETE

---

## Phase 7: Base Scoring Engine

> **Spec References:** `features/base-scoring-engine.md`, `architecture/scoring-architecture.md`, `api/scoring-api.md`

### Specification Summary

Four core dimensions per match, max 25 points: Match Winner (0-5), Scoreline Exactness (0-10), Probability Accuracy (0-5), Player Performance (0-5). Extended with: BTTS (0-2), Total Goals (0-1), First Team to Score (0-2), Clean Sheet (0-4). All scoring engine functions are **pure functions** — no I/O, no DB, no HTTP.

### Implementation Tasks

- [X] Create `app/scoring_engine/base_score/winner_score.py` — winner prediction: correct=5pts, correct+confident=7pts
- [X] Create `app/scoring_engine/base_score/scoreline_score.py` — exact=10pts, close=5pts, partial=3pts
- [X] Create `app/scoring_engine/base_score/probability_score.py` — calibration: 5pts if within threshold, proximity bonus
- [X] Create `app/scoring_engine/base_score/player_score.py` — goal predictions: correct count scoring, assist bonus
- [X] Create `app/scoring_engine/base_score/btts_score.py` — both teams to score: correct=2pts, confident bonus
- [X] Create `app/scoring_engine/base_score/total_goals_score.py` — total goals: exact=1pt, within 1=0.5pt
- [X] Create `app/scoring_engine/base_score/first_team_to_score_score.py` — correct=2pts
- [X] Create `app/scoring_engine/base_score/clean_sheet_score.py` — 2pts per correct, bonus for both
- [X] Create `app/scoring_engine/base_score/base_score_calculator.py` — main orchestrator summing all categories
- [X] Create `app/scoring_engine/base_score/__init__.py` — export `calculate_base_score`

### Verification Checklist

- [X] Winner correct prediction = 5pts
- [X] Winner correct + confident = 7pts
- [X] Exact scoreline match = 10pts
- [X] Close scoreline = 5pts
- [X] All probabilities within threshold = 5pts
- [X] Player goals exact match scored correctly
- [X] BTTS correct = 2pts
- [X] Total goals exact = 1pt
- [X] First team to score correct = 2pts
- [X] Clean sheet correct = 2pts each
- [X] All functions are pure (no I/O)
- [X] Deterministic: same inputs → same outputs

### Phase 7 Status: [X] COMPLETE

---

## Phase 8: Ranking & Multiplier

> **Spec References:** `features/ranking-multiplier.md`, `api/scoring-api.md`

### Specification Summary

Rank teams per match by Base Score descending. Grade assignment: Rank 1 (unique top) = A (3x), Ranks 2-4 = B (2x), Rank 5 (unique bottom) = C (1x). Tie rules: tie at top = all B, tie at bottom = all C, all tied = all B. Earned points = base_score * multiplier.

### Implementation Tasks

- [X] Create `app/scoring_engine/multiplier/ranking_engine.py` — sort teams by base_score, assign ranks
- [X] Create `app/scoring_engine/multiplier/multiplier_calculator.py` — grade assignment (A=3x, B=2x, C=1x), earned_points = base * multiplier
- [X] Create `app/scoring_engine/multiplier/__init__.py` — package init

### Verification Checklist

- [X] 5 teams ranked by base score descending
- [X] Rank 1 (unique) = Grade A (3x)
- [X] Ranks 2-4 = Grade B (2x)
- [X] Rank 5 (unique) = Grade C (1x)
- [X] Tie at top = all Grade B (2x)
- [X] Tie at bottom = all Grade C (1x)
- [X] All tied = all Grade B (2x)
- [X] Earned points = base_score * multiplier

### Phase 8 Status: [X] COMPLETE

---

## Phase 9: Phase Normalization

> **Spec References:** `features/phase-normalization.md`, `api/scoring-api.md`

### Specification Summary

Normalize cumulative earned points across all 32 matches into Phase 1 score out of 60. Formula: `phase1_score = (team_total_earned / max_total_earned) * 60`. Highest-scoring team earns exactly 60.00.

### Implementation Tasks

- [X] Create `app/scoring_engine/normalization/phase1_normalizer.py` — normalize earned_points to phase1_score out of 60
- [X] Create `app/scoring_engine/normalization/__init__.py` — package init
- [X] Create `app/services/scores_service.py` — score calculation orchestration, cumulative phase score management
- [X] Create `app/repositories/score_repository.py` — score queries, cumulative score upsert, bulk operations

### Verification Checklist

- [X] Highest total_earned receives exactly 60.00
- [X] Other teams scaled proportionally
- [X] All teams same earned → all receive 60.00
- [X] One team 0 earned → 0.00
- [X] Scores rounded to 2 decimal places
- [X] Normalization handles empty/zero-edge cases

### Phase 9 Status: [X] COMPLETE

---

## Phase 10: Technical Evaluation

> **Spec References:** `features/technical-evaluation.md`, `api/evaluation-api.md`, `api/scoring-api.md`

### Specification Summary

Phase 2 Technical Implementation scoring by Architecture Committee. Four sub-dimension scores (each 0-5 integer): code_quality, backend_quality, teamwork, ai_explanation. Total = sum (max 20). Weighted scoring: code_quality*5 + backend_quality*5 + teamwork*4 + ai_explanation*6, capped at 20.

### Implementation Tasks

- [X] Create `app/schemas/technical_evaluation_schema.py` — `TechnicalEvaluation` schema with bounded integer fields
- [X] Create `app/scoring_engine/technical_evaluation/technical_score.py` — weighted sum of 4 criteria, capped at 20
- [X] Create `app/scoring_engine/technical_evaluation/__init__.py` — package init

### Verification Checklist

- [X] Valid Phase 2 scores accepted
- [X] Sub-dimension score > 5 rejected (422)
- [X] Total score capped at 20
- [X] Weighted formula correct: code*5 + backend*5 + teamwork*4 + ai*6
- [X] Non-committee user rejected (403)
- [X] Duplicate evaluation rejected

### Phase 10 Status: [X] COMPLETE

---

## Phase 11: Presentation Evaluation

> **Spec References:** `features/presentation-evaluation.md`, `api/evaluation-api.md`, `api/scoring-api.md`

### Specification Summary

Phase 3 presentation scoring. Judges submit scores /50 per team per round. Dimensions: ai_explanation (0-20), qa (0-15), delivery (0-15). Teams ranked per round: highest = Grade A (x3), middle = Grade B (x2), lowest = Grade C (x1). Two presentation rounds. Final formula: `(Total / 300) * 20`.

### Implementation Tasks

- [X] Create `app/schemas/presentation_schema.py` — `PresentationEvaluation` schema with judge_scores list
- [X] Create `app/schemas/presentation_round_schema.py` — `PresentationRoundCreate`, `PresentationRoundResponse`
- [X] Create `app/scoring_engine/presentation_evaluation/presentation_score.py` — multi-judge averaging, ranking, grading (A/B/C), weighted score calculation
- [X] Create `app/scoring_engine/presentation_evaluation/__init__.py` — package init
- [X] Create `app/models/presentation_round.py` — `PresentationRoundModel`
- [X] Create `app/models/judge.py` — `JudgeModel`
- [X] Create `app/api/judge_routes.py` — judge CRUD endpoints (organizer only)
- [X] Create `app/services/presentation_round_service.py` — presentation round CRUD

### Verification Checklist

- [X] Judge submits valid raw scores (201)
- [X] Raw score > 50 total rejected (422)
- [X] Ranking applied correctly across teams
- [X] Multiplier applied: earned = raw * multiplier
- [X] Normalization to 20 marks: `(Total / 300) * 20`
- [X] Non-reviewer entry rejected (403)
- [X] Judge CRUD works (create, list, update, delete)

### Phase 11 Status: [X] COMPLETE

---

## Phase 12: Leaderboard

> **Spec References:** `features/leaderboard.md`, `api/leaderboard-api.md`, `architecture/leaderboard-architecture.md`

### Specification Summary

Aggregates Phase 1 (0-60), Phase 2 (0-20), Phase 3 (0-20) for all teams. `final_score = phase1 + technical + presentation`. Capped at 100. Tie-break by ai_accuracy → technical → presentation. Ranks assigned with tie handling. Leaderboard snapshot persisted.

### Implementation Tasks

- [X] Create `app/services/leaderboard_service.py` — leaderboard calculation with total_score capping at 100, tie-breaking, ranking
- [X] Create `app/repositories/leaderboard_repository.py` — leaderboard CRUD, rank queries, visibility settings
- [X] Create `app/api/leaderboard_routes.py` — calculate, get, public endpoint
- [X] Create `app/api/leaderboard_settings_routes.py` — visibility get/update (admin only)

### Verification Checklist

- [X] All phases complete → leaderboard generated
- [X] Grand total = phase1 + technical + presentation
- [X] Grand total capped at 100.00
- [X] Teams ranked by grand total descending
- [X] Tie-breaking rules applied (ai_accuracy → technical → presentation)
- [X] Leaderboard snapshot persisted
- [X] Re-generation is idempotent
- [X] Public endpoint accessible without auth
- [X] Visibility settings control field exposure

### Phase 12 Status: [X] COMPLETE

---

## Phase 13: Admin Scoring Configuration

> **Spec References:** `features/admin-scoring-config.md`, `api/scoring-config_routes.py`

### Specification Summary

Dynamic scoring rules adjustment by Organizers. Editable: probability_threshold, player_avg_threshold, max scores, grade multipliers. Changes apply only to future scoring. `scoring_configs` table with versioning.

### Implementation Tasks

- [X] Create `app/models/scoring_config.py` — `ScoringConfigModel` with 25+ configurable parameters
- [X] Create `app/schemas/scoring_config_schema.py` — `ScoringConfigCreate/Update/Response`, `GuidelineItem` schemas (215 lines)
- [X] Create `app/repositories/scoring_config_repository.py` — active config lookup, save config, get all
- [X] Create `app/services/scoring_config_service.py` — config CRUD, reset to defaults, version management, guidelines generation
- [X] Create `app/api/scoring_config_routes.py` — CRUD, guidelines, reset, version management (234 lines)

### Verification Checklist

- [X] `GET /api/v1/admin/scoring-config` lists all configs
- [X] `GET /api/v1/admin/scoring-config/active` returns current active config
- [X] `PUT /api/v1/admin/scoring-config/{id}` updates config
- [X] `POST /api/v1/admin/scoring-config/{id}/activate` activates config
- [X] `POST /api/v1/admin/scoring-config/reset` resets to defaults
- [X] Config changes don't retroactively affect existing scores
- [X] Scoring engine uses active config values

### Phase 13 Status: [X] COMPLETE

---

## Phase 14: Model Submission

> **Spec References:** `features/model-submission.md`

### Specification Summary

Secure upload of ML model files (.zip, .tar.gz, .py, .ipynb). Max 50MB. Time window locking via `upload_window_config`. Versioning support. Status: Uploaded → Testing → Evaluated → Failed.

### Implementation Tasks

- [X] Create `app/models/upload_window.py` — `UploadWindowModel` (is_enabled, start_time, end_time)
- [X] Create `app/models/model_submission.py` — `ModelSubmissionModel` (file metadata, version, status)
- [X] Create `app/models/model_evaluation.py` — `ModelEvaluationModel` (accuracy metrics)
- [X] Create `app/schemas/upload_window_schema.py` — `UploadWindowUpdate/Response` schemas
- [X] Create `app/schemas/model_submission_schema.py` — `ModelSubmissionResponse` schema
- [X] Create `app/schemas/model_evaluation_schema.py` — `ModelEvaluationResponse` schema
- [X] Create `app/repositories/model_submission_repository.py` — model submission queries by team, active model
- [X] Create `app/repositories/upload_window_repository.py` — get/update upload window
- [X] Create `app/services/model_submission_service.py` — model file upload, validation, metadata management
- [X] Create `app/services/upload_window_service.py` — upload window config get/update
- [X] Create `app/api/upload_window_routes.py` — upload window config get/update
- [X] Create `app/api/model_submission_routes.py` — upload, list, status, delete endpoints

### Verification Checklist

- [X] Team uploads model file within window
- [X] Upload outside window rejected
- [X] File type validation enforced
- [X] File size limit enforced (50MB)
- [X] Version tracking works
- [X] Admin can list all submissions
- [X] Admin can download model files
- [X] Upload window enable/disable works

### Phase 14 Status: [X] COMPLETE

---

## Phase 15: Model Execution System

> **Spec References:** `features/MODEL_EXECUTION_SYSTEM.md`, `features/model-performance-analytics.md`

### Specification Summary

Separate AI model execution workflow: team uploads `.pkl` → module executes → generates prediction JSON → feeds into existing prediction creation logic. Model states: IDLE → RUNNING → SUCCESS/FAILED. Safe unpickler with restricted classes. Background batch execution.

### Implementation Tasks

- [X] Create `app/model_execution/models/model_upload.py` — `ModelUpload` dataclass
- [X] Create `app/model_execution/models/model_execution.py` — `ModelExecution` dataclass
- [X] Create `app/model_execution/models/batch_execution.py` — `BatchExecution` dataclass
- [X] Create `app/model_execution/schemas/execution_schema.py` — `ExecutionRequest/Response` schemas
- [X] Create `app/model_execution/services/model_compat.py` — safe unpickler with restricted classes
- [X] Create `app/model_execution/services/model_serializer.py` — normalize model output to standard prediction format
- [X] Create `app/model_execution/services/model_executor.py` — load pkl, run predict(), handle errors, store results
- [X] Create `app/model_execution/services/execution_service.py` — trigger, status check, background task management
- [X] Create `app/model_execution/services/batch_execution_service.py` — batch evaluation pipeline
- [X] Create `app/model_execution/routes/execution_routes.py` — upload, execute, status check endpoints
- [X] Create `app/model_execution/routes/batch_execution_routes.py` — batch execution trigger, status, results

### Verification Checklist

- [X] Model upload accepts .pkl files
- [X] Safe unpickler restricts allowed classes
- [X] Model execution generates prediction JSON
- [X] Invalid model output handled gracefully (FAILED state)
- [X] Failed models don't crash backend
- [X] Status polling returns RUNNING → SUCCESS/FAILED
- [X] Batch execution evaluates all models against matches
- [X] Model metrics computed correctly

### Phase 15 Status: [X] COMPLETE

---

## Phase 16: Analytics Module

> **Spec References:** `features/ANALYTICS_MODULE.md` (862 lines), `features/ANALYTICS.md` (430 lines), `features/model-performance-analytics.md`, `api/analytics-api.md`

### Specification Summary

Read-only analytics providing data-driven insights. NEVER modifies scoring data. Sections: Final Score Analytics, Prediction Scoring Analytics, Model Performance Analytics, Presentation Analytics, Technical Evaluation Analytics. Granular visibility toggles per section. Anonymous mode for team leaders.

### Implementation Tasks

- [X] Create `app/models/leaderboard_visibility.py` — `LeaderboardVisibilityModel` with 19 boolean flags + master toggle
- [X] Create `app/schemas/analytics_schema.py` — `OverviewResponse`, `ModelAnalytics`, `PresentationAnalytics`, `TeamAnalytics` schemas
- [X] Create `app/repositories/analytics_repository.py` — analytics queries: overview stats, model performance, presentation averages
- [X] Create `app/services/analytics_service.py` — overview, model, presentation, team analytics with full aggregation (452 lines)
- [X] Create `app/api/analytics_routes.py` — overview, models, presentation, team endpoints (122 lines)

### Verification Checklist

- [X] `GET /api/v1/analytics/overview` returns team counts, top team, average scores
- [X] `GET /api/v1/analytics/models` returns model metrics per team
- [X] `GET /api/v1/analytics/presentation` returns criteria averages and rankings
- [X] `GET /api/v1/analytics/team/{team_id}` returns individual team breakdown
- [X] Analytics never modifies scoring/leaderboard data
- [X] Visibility settings control data exposure
- [X] Organizer gets full access
- [X] Team leader sees only permitted sections

### Phase 16 Status: [X] COMPLETE

---

## Phase 17: Reports & Score Analysis

> **Spec References:** `features/score-reports-analysis.md`, `api/reports-api.md`

### Specification Summary

Organizer-only transparency feature with 5 report sections: Team Score Journey, Before vs After Comparison, Multiplier Impact Report, Phase Contribution Breakdown, Rank Movement Analysis. Pure analysis layer — doesn't affect scoring.

### Implementation Tasks

- [X] Create `app/services/report_service.py` — report generation: team breakdown, multiplier impact, rank analysis, phase contribution (208 lines)
- [X] Create `app/api/report_routes.py` — team breakdown, multiplier impact, rank analysis, phase contribution endpoints
- [X] Create `scripts/generate_reports.py` — per-team game prediction + presentation evaluation reports (MD/HTML/PDF)
- [X] Create `scripts/generate_consolidated_prediction_report.py` — consolidated cross-team PDF with charts

### Verification Checklist

- [X] `GET /api/v1/reports/team-breakdown` returns scoring journey per team
- [X] `GET /api/v1/reports/rank-impact` returns before/after comparison
- [X] `GET /api/v1/reports/phase-analysis` returns composition and contributions
- [X] `GET /api/v1/reports/multiplier-impact` returns multiplier gains
- [X] Reports are organizer-only
- [X] Reports don't modify any data
- [X] PDF report generation works

### Phase 17 Status: [X] COMPLETE

---

## Phase 18: Excel/CSV Upload

> **Spec References:** `features/excel-csv-upload.md` (309 lines), `features/team-management.md`, `api/team-management-api.md`

### Specification Summary

Bulk team roster upload via CSV/Excel. Formats: .csv, .xlsx, .xls. Required columns: Name, Group. Optional: EmployeeID. Processing: parse → validate → clear old CSV-managed members → insert new → set is_csv_managed. Transactional with rollback on failure.

### Implementation Tasks

- [X] CSV parsing with `csv.DictReader` (UTF-8 decode) — implemented in `team_routes.py`
- [X] XLSX parsing with `openpyxl.load_workbook(data_only=True)` — implemented in `team_routes.py`
- [X] XLS parsing with `xlrd.open_workbook` — implemented in `team_routes.py`
- [X] Header normalization (lowercase, spaces → underscores) — implemented in `team_routes.py`
- [X] Group-to-team mapping via `GROUP_TO_TEAM` dict — implemented in `team_routes.py`
- [X] Transactional member replacement (DELETE old + INSERT new + UPDATE flag) — implemented in `team_routes.py`
- [X] Conflict detection for manual members — implemented in `team_routes.py`
- [X] Response with affected team/member counts — implemented in `team_routes.py`

### Verification Checklist

- [X] CSV file parsed correctly (UTF-8)
- [X] XLSX file parsed correctly (openpyxl)
- [X] XLS file parsed correctly (xlrd)
- [X] Header normalization handles whitespace/case
- [X] Unknown groups silently skipped
- [X] Empty Group/Name rows silently skipped
- [X] Transactional: all-or-nothing on failure
- [X] `is_csv_managed` flag set after upload
- [X] Member count returned per team

### Phase 18 Status: [X] COMPLETE

---

## Phase 19: External Football API Integration

> **Spec References:** `architecture/external_football_api_integration.md`

### Specification Summary

Integration with external football data providers (API-Football). Fetch fixtures by date, import matches, sync results. Duplicate handling via external_api_id. Rate limiting. API key in .env only.

### Implementation Tasks

- [X] Create `app/services/football_api_service.py` — fixture fetching, rate-limit/error handling, result parsing (178 lines)
- [X] Create `app/api/external_matches_routes.py` — external API match sync, fixture fetch, bulk import (179 lines)
- [X] Add `external_api_id` field to MatchModel
- [X] Add `result_source` field to ActualResultModel
- [X] Create Alembic migrations for new fields
- [X] Implement duplicate detection via external_api_id
- [X] Implement timeout/5xx error handling (502 responses)

### Verification Checklist

- [X] `GET /api/v1/external-matches/fixtures?date=` fetches fixtures from API
- [X] `POST /api/v1/external-matches/import` imports selected fixtures as matches
- [X] `POST /api/v1/external-matches/{match_id}/sync-result` syncs result
- [X] Duplicate external_api_id skipped
- [X] API errors handled gracefully (502)
- [X] API key never exposed to frontend
- [X] Rate limiting implemented

### Phase 19 Status: [X] COMPLETE

---

## Phase 20: Testing & Quality Assurance

> **Spec References:** `docs/TEST_PLAN.md` (262 lines), `reviews/FINAL_REVIEW.md`

### Specification Summary

127+ tests across unit and integration layers. Unit tests for pure scoring functions (no mocking). Integration tests for API routes (httpx + pytest-asyncio). Deterministic fixtures. All tests must pass.

### Implementation Tasks

- [X] Create `tests/conftest.py` — shared fixtures: SQLite in-memory DB, client, organizer/team_leader users, teams, matches, scoring config (181 lines)
- [X] Create `tests/test_base_score.py` — 14 tests for all base scoring categories
- [X] Create `tests/test_multiplier.py` — 17 tests for ranking, grade assignment, tie handling
- [X] Create `tests/test_normalization.py` — 8 tests for phase1 normalization
- [X] Create `tests/test_technical_score.py` — 7 tests for weighted scoring
- [X] Create `tests/test_presentation_score.py` — 5 tests for judge scoring
- [X] Create `tests/test_leaderboard.py` — 17 tests for total, ranking, tie-breaking
- [X] Create `tests/test_schemas.py` — 18 tests for schema validation
- [X] Create `tests/test_football_api.py` — 4 tests for API integration (mocked)
- [X] Create `tests/test_health.py` — 4 tests for health/version endpoints
- [X] Create `tests/test_database_connection.py` — 7 tests for DB config
- [X] Create `tests/test_api.py` — 30+ tests for API integration (auth, predictions, scoring, teams)
- [X] Create `tests/test_match_management.py` — 3 tests for match lifecycle
- [X] Create `tests/test_scoring_config.py` — 8 tests for config CRUD
- [X] Create `tests/test_analytics.py` — 9 tests for analytics endpoints
- [X] Create `tests/test_leaderboard_visibility.py` — 8 tests for visibility settings
- [X] Create `tests/test_model_execution.py` — 4 tests for model upload/execute
- [X] Create `tests/test_full_competition_flow.py` — 3 end-to-end tests
- [X] Create `tests/integration/test_reports.py` — 4 tests for report endpoints

### Verification Checklist

- [X] `pytest tests/` — all 127+ tests pass
- [X] `pytest tests/unit/` — scoring engine tests pass
- [X] `pytest tests/integration/` — API route tests pass
- [X] `pytest --cov=app` — coverage report generated
- [X] No test uses randomness — all deterministic
- [X] Test data uses static JSON fixtures

### Phase 20 Status: [X] COMPLETE

---

## Phase 21: Docker & Deployment

> **Spec References:** `architecture/DEPLOYMENT.md`, `architecture/system-architecture.md`

### Specification Summary

Docker + Docker Compose deployment. Two services: `api` (FastAPI on port 8000) + `db` (PostgreSQL 15+). Dockerfile: python:3.12-slim. Nginx for React frontend. `.env` injection. Swagger UI at `/docs`.

### Implementation Tasks

- [X] Create `Dockerfile` — python:3.12-slim, pip install, uvicorn entrypoint
- [X] Create `docker-compose.yml` — API + PostgreSQL + Nginx services
- [X] Create `.dockerignore` — exclude .venv, __pycache__, .git
- [X] Verify `docker compose up -d --build` succeeds
- [X] Verify `GET /health` returns 200 in container
- [X] Verify all tests pass inside container
- [X] Create `app/api/health_routes.py` — `/health` and `/version` endpoints

### Verification Checklist

- [X] Docker image builds successfully
- [X] Docker Compose starts all services
- [X] API accessible at localhost:8000
- [X] Swagger UI accessible at localhost:8000/docs
- [X] Database connection works through Docker networking
- [X] All 127+ tests pass inside container
- [X] Health endpoint returns 200

### Phase 21 Status: [X] COMPLETE

---

## Dependency Matrix

This matrix shows which phases depend on prior phases being complete:

```
Phase 0 (Infrastructure) ─────────────────────────────┐
    │                                                  │
    ├── Phase 1 (Database Models) ─────────────────┐  │
    │       │                                       │  │
    │       ├── Phase 2 (Auth) ─────────────────┐  │  │
    │       │       │                            │  │  │
    │       │       ├── Phase 3 (Teams) ────────┤  │  │
    │       │       │       │                    │  │  │
    │       │       │       ├── Phase 4 (Matches)┤  │  │
    │       │       │       │     │              │  │  │
    │       │       │       │     ├── Phase 5 (Predictions)──┐
    │       │       │       │     │     │                    │
    │       │       │       │     ├── Phase 6 (Results) ────┤
    │       │       │       │     │     │                    │
    │       │       │       │     │     ├── Phase 7 (Base Scoring)──┐
    │       │       │       │     │     │     │                      │
    │       │       │       │     │     ├── Phase 8 (Ranking) ─────┤
    │       │       │       │     │     │     │                      │
    │       │       │       │     │     ├── Phase 9 (Normalization)─┤
    │       │       │       │     │     │     │                      │
    │       │       │       │     │     ├── Phase 10 (Technical Eval)┤
    │       │       │       │     │     │     │                      │
    │       │       │       │     │     ├── Phase 11 (Presentation)──┤
    │       │       │       │     │     │     │                      │
    │       │       │       │     │     ├── Phase 12 (Leaderboard) ─┤
    │       │       │       │     │     │     │                      │
    │       │       │       │     │     ├── Phase 13 (Admin Config)──┤
    │       │       │       │     │     │     │                      │
    │       │       │       │     │     ├── Phase 14 (Model Submit)──┤
    │       │       │       │     │     │     │                      │
    │       │       │       │     │     ├── Phase 15 (Model Exec) ──┤
    │       │       │       │     │     │     │                      │
    │       │       │       │     │     ├── Phase 16 (Analytics) ───┤
    │       │       │       │     │     │     │                      │
    │       │       │       │     │     ├── Phase 17 (Reports) ─────┤
    │       │       │       │     │     │     │                      │
    │       │       │       │     │     ├── Phase 18 (CSV Upload) ──┤
    │       │       │       │     │     │     │                      │
    │       │       │       │     │     ├── Phase 19 (Football API)──┤
    │       │       │       │     │     │     │                      │
    │       │       │       │     │     ├── Phase 20 (Testing) ─────┤
    │       │       │       │     │     │     │                      │
    │       │       │       │     │     ├── Phase 21 (Docker) ──────┘
    │       │       │       │     │     │
    └───────┴───────┴───────┴─────┴─────┘
```

### Key Dependency Rules

| Phase | Depends On | Reason |
|-------|-----------|--------|
| Phase 1 (DB Models) | Phase 0 | Needs database connection + SQLAlchemy base |
| Phase 2 (Auth) | Phase 1 | Needs UserModel, TeamModel for registration |
| Phase 3 (Teams) | Phase 2 | Needs auth for role-based access |
| Phase 4 (Matches) | Phase 2 | Needs auth for organizer-only CRUD |
| Phase 5 (Predictions) | Phase 3, 4 | Needs teams and matches to exist |
| Phase 6 (Results) | Phase 4 | Needs matches to attach results to |
| Phase 7 (Scoring) | Phase 5, 6 | Needs predictions + actual results |
| Phase 8 (Ranking) | Phase 7 | Needs base scores to rank |
| Phase 9 (Normalization) | Phase 7 | Needs earned points to normalize |
| Phase 10 (Technical) | Phase 3 | Needs teams to evaluate |
| Phase 11 (Presentation) | Phase 3 | Needs teams to evaluate |
| Phase 12 (Leaderboard) | Phase 9, 10, 11 | Needs all three phase scores |
| Phase 13 (Config) | Phase 7 | Config drives scoring behavior |
| Phase 14 (Model Submit) | Phase 3 | Needs teams to upload models |
| Phase 15 (Model Exec) | Phase 14 | Needs models to execute |
| Phase 16 (Analytics) | Phase 12 | Needs leaderboard data for analytics |
| Phase 17 (Reports) | Phase 8, 9 | Needs scoring data for reports |
| Phase 18 (CSV Upload) | Phase 3 | Extends team management |
| Phase 19 (Football API) | Phase 4 | Extends match management |
| Phase 20 (Testing) | All phases | Tests all implemented features |
| Phase 21 (Docker) | Phase 20 | Containerizes tested application |

---

## Spec Traceability Matrix

Every specification document maps to implementation files:

| Spec Document | Implementation Files |
|---|---|
| `features/prediction-management.md` | `prediction_schema.py`, `prediction_service.py`, `prediction_repository.py`, `prediction_routes.py` |
| `features/actual-result-management.md` | `actual_result_schema.py`, `result_service.py`, `result_routes.py` |
| `features/base-scoring-engine.md` | `scoring_engine/base_score/*.py` (8 files) |
| `features/ranking-multiplier.md` | `scoring_engine/multiplier/*.py` (2 files) |
| `features/phase-normalization.md` | `scoring_engine/normalization/*.py` (1 file) |
| `features/technical-evaluation.md` | `technical_evaluation_schema.py`, `scoring_engine/technical_evaluation/*.py` |
| `features/presentation-evaluation.md` | `presentation_schema.py`, `scoring_engine/presentation_evaluation/*.py`, `judge_routes.py` |
| `features/leaderboard.md` | `leaderboard_service.py`, `leaderboard_repository.py`, `leaderboard_routes.py` |
| `features/team-management.md` | `team_schema.py`, `team_service.py`, `team_repository.py`, `team_routes.py` |
| `features/match-management.md` | `match_schema.py`, `match_service.py`, `match_repository.py`, `match_routes.py` |
| `features/excel-csv-upload.md` | `team_routes.py` (upload endpoint), `team_service.py` |
| `features/admin-scoring-config.md` | `scoring_config.py`, `scoring_config_schema.py`, `scoring_config_service.py`, `scoring_config_routes.py` |
| `features/model-submission.md` | `model_submission.py`, `upload_window.py`, `model_submission_service.py`, `model_submission_routes.py` |
| `features/MODEL_EXECUTION_SYSTEM.md` | `app/model_execution/` (11 files) |
| `features/ANALYTICS_MODULE.md` | `analytics_service.py`, `analytics_repository.py`, `analytics_routes.py`, `analytics_schema.py` |
| `features/ANALYTICS.md` | `analytics_service.py`, `analytics_routes.py` |
| `features/model-performance-analytics.md` | `model_evaluation_service.py`, `model_evaluation_routes.py` |
| `features/score-reports-analysis.md` | `report_service.py`, `report_routes.py` |
| `api/error-responses.md` | `exceptions/*.py` (5 files) |
| `architecture/error-handling-architecture.md` | `exceptions/*.py`, `exception_handler.py` |
| `architecture/scoring-architecture.md` | `scoring_engine/base_score/*.py` |
| `architecture/prediction-architecture.md` | `prediction_service.py`, `prediction_routes.py` |
| `architecture/leaderboard-architecture.md` | `leaderboard_service.py` |
| `architecture/database-architecture.md` | `database/*.py`, `repositories/*.py` |
| `architecture/external_football_api_integration.md` | `football_api_service.py`, `external_matches_routes.py` |
| `database/schema-design.md` | `models/*.py` (19 files) |
| `database/postgres-implementation-plan.md` | `database/*.py`, `repositories/*.py`, Alembic migrations |

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Phases** | 22 (Phase 0-21) |
| **Completed Phases** | 22 |
| **Total Implementation Tasks** | 180+ |
| **Total Verification Items** | 200+ |
| **Spec Documents Referenced** | 42 |
| **Implementation Files** | 174 Python files |
| **Lines of Code** | ~21,474 |
| **Test Files** | 20 |
| **Test Cases** | 127+ |
| **Database Migrations** | 25+ |
| **API Route Files** | 22 |
| **API Endpoints** | 100+ |

### Overall Status: **ALL PHASES COMPLETE [X]**

---

*Generated following Spec Driven Development methodology. Each phase was implemented from its specification, verified against its checklist, and signed off before proceeding to the next phase.*
