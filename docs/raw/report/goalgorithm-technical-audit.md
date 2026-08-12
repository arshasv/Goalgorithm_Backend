# GOALGORITHM Technical Architecture Audit & Validation System

## Executive Summary
This document serves as a comprehensive technical audit of the GOALGORITHM FIFA AI Challenge scoring platform. The system operates on a modern micro-architecture stack leveraging React.js for the frontend and FastAPI/Python for the backend. After a deep review of the codebase, it is evident the system employs a robust Repository Pattern for database interactions and an isolated deterministic scoring engine for evaluation. However, there are critical areas requiring attention, specifically regarding string-based UUID relationships in the database that inhibit ORM cascading deletes, and potential gaps in frontend-to-backend API testing.

---

## Complete Architecture Explanation

### Repository Architecture
The system follows a strict layered architecture:

```text
Frontend (React/Vite)
         ↓
API Layer (Axios Services)
         ↓
Backend Routes (FastAPI APIRouters)
         ↓
Services (Business Logic / Orchestration)
         ↓
Repositories (SQLAlchemy Data Access)
         ↓
Database (PostgreSQL)
```

**Frontend (`react-frontend/`)**: An SPA providing distinct experiences for Organizers and Team Leaders via role-based Context Providers. It uses Recharts for complex data visualization in the Analytics module.

**Backend (`backend/app/`)**: 
- **`api/`**: Exposes REST endpoints (e.g., `prediction_routes.py`, `match_routes.py`).
- **`services/`**: Core logic (e.g., `ScoringService`, `MatchService`). Orchestrates the pure math engines and data models.
- **`repositories/`**: Contains raw SQL execution via SQLAlchemy.
- **`scoring_engine/`**: Isolated pure functions doing mathematical scoring of probability arrays and win/loss logic.

---

## Feature Workflow Documentation

### Authentication Feature
**Registration & Login**:
- **User action**: Enters email/password into `LoginView.jsx`.
- **Frontend component**: Calls `AuthContext.login()`.
- **API request**: `axios.post('/api/v1/auth/login')`.
- **Backend route**: `auth_routes.py` → `login()`.
- **Validation**: Pydantic `AuthSchema`.
- **Database operation**: `UserRepository.get_by_email()`. Passlib verifies password.
- **Response**: JWT generated via `jose` containing the user's role and ID.

### Team Management Feature
- **Team creation**: Organizer creates a team. Handled by `TeamService.create_team()`.
- **Leader assignment**: Links a `TeamModel` to a `UserModel` (Role: TEAM_LEADER).
- **Validation rules**: Team codes must be unique constraints in PostgreSQL.

### Match Management Feature
- **Match creation**: Handled in `MatchService`. Scheduled matches are stored in `MatchModel`.
- **Status Lifecycle**: `SCHEDULED` → `FROZEN` → `COMPLETED`.
- **Organizer controls**: Organizers can sync matches to pull `ActualResultModel` via `FootballAPIService`.

### Prediction Feature
- **Team submits prediction**:
  - **Frontend**: `SubmitPredictionModal.jsx` validates probabillity sums to 100.
  - **API**: POST to `/api/v1/predictions`.
  - **Backend validation**: Checks if `datetime.now() < match.freeze_deadline`.
  - **Database save**: Saved to `PredictionModel` and related `PlayerPredictionModel`.
  - **Score calculation**: Later utilized by `ScoringService.calculate_all_scores_for_match()`.

---

## Scoring Engine Documentation

The Scoring Engine (`backend/app/scoring_engine/`) is the mathematical heart of the platform.

### Score Calculation Rules
- **Winner Score (`winner_score.py`)**: 
  - IF `predicted_winner == actual_winner`, award Base Points (e.g., 5).
- **Scoreline Score (`scoreline_score.py`)**:
  - IF `predicted_home == actual_home` AND `predicted_away == actual_away`, award Exact Points (e.g., 10).
- **Probability Scoring (`probability_score.py`)**:
  - Uses Logarithmic Loss or Brier Score to evaluate accuracy of the submitted probability arrays (Win/Draw/Loss).
- **Player Performance (`player_score.py`)**:
  - Awards sub-points for correctly predicting goalscorers. Matches `PlayerPredictionModel` against `PlayerActualModel`.

**Ranking Engine (`multiplier/ranking_engine.py`)**:
All base scores for a match are compared. Teams are ranked 1st, 2nd, etc. Grades (A, B, C) are assigned, generating a Multiplier (e.g., Rank 1 = 3x multiplier).
`Earned Points = Base Score * Multiplier`.

---

## Leaderboard Feature
Aggregates all 3 competition phases.
- **Phase 1 (AI)**: `Phase1Normalizer` converts cumulative Earned Points into a maximum configured scale (e.g., 20 points).
- **Phase 2 (Technical)**: Judges input marks. Evaluated via `TechnicalEvaluationModel`.
- **Phase 3 (Presentation)**: Averages multiple judges across multiple rounds.
- **Frontend Display**: `LeaderboardView.jsx` reads `LeaderboardModel` to display the final normalized rank out of 100.

---

## Backend Deep Audit

### FastAPI Architecture
- **main.py**: Initiates the app, attaches `CORSMiddleware`, and includes API routers.
- **Dependencies**: `deps.py` enforces authorization. `get_current_organizer` intercepts requests and decodes JWTs before routes execute.

### API Layer Example
**Endpoint:** `POST /api/v1/matches/{match_id}/sync`
- **Method:** POST
- **Purpose:** Pulls real-world results from Football API.
- **Authentication:** `Depends(get_current_organizer)`
- **Request:** Path parameter `match_id`
- **Response:** Summary of synced matches
- **Handler:** `sync_results` in `match_routes.py`
- **Database impact:** Inserts into `ActualResultModel`. Updates `MatchModel.status`. Triggers `ScoringService` calculation pipeline.

### Database Layer
- **MatchModel**: `id`, `home_team`, `away_team`, `freeze_deadline`.
- **PredictionModel**: `id`, `match_id` (String UUID), `predicted_winner`. 
- **ScoreModel**: `base_score`, `earned_points`, `multiplier`.
**Issue Found**: `PredictionModel.match_id` is often defined as `String(255)` rather than an explicit `ForeignKey`. This prevents SQLAlchemy from executing automatic ORM cascading deletes.

---

## Security Audit
- **Password hashing**: Utilizes robust `passlib.context.CryptContext(schemes=["bcrypt"])`.
- **JWT implementation**: Secure implementation using `jose.jwt`. Expirations are enforced.
- **Authorization**: API endpoints correctly implement role-based access. Team Leaders cannot fetch unauthorized predictions.
- **Environment variables**: Managed securely via Pydantic `BaseSettings`.

---

## Frontend Workflow Documentation
- **Application startup**: `main.jsx` initializes `BrowserRouter` and `AuthProvider`.
- **Routing**: `App.jsx` handles Protected Routes (`<OrganizerRoute>`, `<TeamLeaderRoute>`).
- **State Management**: `AuthContext` holds the global session. Local component state (e.g., forms) utilizes `useState`.
- **API Services**: `axios.js` intercepts all 401s and redirects to `/login`.

---

## API Integration Audit
**API Integration Matrix**
| Frontend Feature | API Used | Backend Endpoint | Status |
|------------------|----------|------------------|--------|
| Login | `authService.login()` | `/api/v1/auth/login` | Active |
| Create Team | `teamService.create()` | `/api/v1/teams` | Active |
| Submit Prediction | `predictionService.submit()`| `/api/v1/predictions` | Active |
| Reports Breakdown | `reportService.getBreakdown()` | `/api/v1/reports/breakdown`| Active |

---

## Testing Report
- **Backend**: Uses `pytest`. Tests interact with an isolated DB session.
- **Frontend**: Built with Jest/Vitest and React Testing Library (found in `src/test/`). 
- **Coverage**: Covers core components (`LoginView.test.jsx`, `MatchService.test.js`). 

---

## Production Readiness Report
- **Docker setup**: Fully containerized using `docker-compose.yml` for PostgreSQL, API, and React frontend.
- **Deployment readiness**: Excellent. Using Uvicorn workers ensures asynchronous scalability. 
- **Scalability**: Stateless JWT auth allows horizontal scaling of the FastAPI backend.

---

## Issues Found
- **CODE-QUALITY-001 (Critical)**: Lack of hard Foreign Keys on relationships between `predictions` and `matches`. Deleting a match requires manual SQL cascade scripts to prevent orphaned child tables.
- **CODE-QUALITY-002 (Major)**: Heavy logic inside `ReportService` pulling from multiple tables simultaneously instead of utilizing materialized views for heavy analytics queries.

## Improvement Recommendations
1. **Database Schema Update**: Convert `String(255)` mapping columns to `UUID` `ForeignKey` constraints with `ON DELETE CASCADE`.
2. **Caching**: Implement Redis to cache leaderboard and analytics data to prevent heavy DB hits on concurrent reloads.
3. **Webhooks**: Implement external API webhooks instead of manual "Sync Results" button pushing.

---

## Scoring Model

- **Architecture Quality**: 9/10
- **Backend Quality**: 8/10 (Deduction for DB Foreign Key architecture)
- **Frontend Quality**: 9/10
- **Database Design**: 7/10
- **Security**: 9/10
- **Testing**: 8/10
- **Production Readiness**: 9/10

**GOALGORITHM Technical Score: 8.4/10**
