# Feature 24: Database & Migrations

## Feature Overview

SQLAlchemy 2.0 ORM with PostgreSQL (Neon serverless), Alembic migration system with 31 migration files, and a complete data model covering 24+ tables with relationships, constraints, and indexes.

## Purpose & Requirements

- SQLAlchemy 2.0 mapped_column style ORM
- PostgreSQL 15+ in production (Neon serverless)
- SQLite for development/testing
- Alembic for version-controlled schema migrations
- UUID primary keys for all tables
- Foreign key relationships with RESTRICT/CASCADE
- Check constraints for score ranges
- Unique constraints for data integrity

## How the Feature Works Internally

### Database Connection
```python
# connection.py
engine = create_engine(settings.DATABASE_URL, pool_size=5, max_overflow=10)

# session.py
SessionLocal = sessionmaker(bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Migration Management
```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### 31 Migration Files Covering:
1. Initial schema (users, teams, matches, predictions, scores)
2. Player predictions and actuals
3. Cumulative phase scores
4. Technical and presentation evaluations
5. Leaderboard with visibility
6. Scoring configuration
7. Model submissions and evaluations
8. Upload windows
9. Password reset OTPs
10. Judges and presentation rounds
11. External API fields
12. AI prediction format support
13. Analytics visibility flags

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/database/base.py` | 5 | SQLAlchemy DeclarativeBase |
| `app/database/connection.py` | 6 | Engine creation |
| `app/database/session.py` | 16 | SessionLocal + get_db |
| `alembic/env.py` | 54 | Migration environment |
| `alembic/versions/` | 31 files | Migration scripts |

### Table Summary

| Table | Model | Key Relationships |
|-------|-------|-------------------|
| users | UserModel | → teams (user_id) |
| teams | TeamModel | ← users, → team_members |
| team_members | TeamMemberModel | → teams |
| matches | MatchModel | ← predictions, actual_results, scores |
| predictions | PredictionModel | → teams, matches, → player_predictions |
| player_predictions | PlayerPredictionModel | → predictions |
| actual_results | ActualResultModel | → matches, → player_actuals |
| player_actuals | PlayerActualModel | → actual_results |
| scores | ScoreModel | → teams, matches, scoring_configs |
| cumulative_phase_scores | CumulativePhaseScoreModel | → teams |
| technical_evaluations | TechnicalEvaluationModel | → teams |
| presentation_evaluations | PresentationEvaluationModel | → teams, rounds |
| presentation_scores | PresentationScoreModel | → teams, rounds |
| leaderboards | LeaderboardModel | → teams |
| leaderboard_visibility | LeaderboardVisibilityModel | Singleton |
| scoring_configs | ScoringConfigModel | ← scores |
| model_submissions | ModelSubmissionModel | → teams |
| model_evaluations | ModelEvaluationModel | → model_submissions, teams |
| upload_windows | UploadWindowModel | Singleton |
| password_reset_otps | PasswordResetOtpModel | → users |
| judges | JudgeModel | |
| presentation_rounds | PresentationRoundModel | ← presentation_evaluations |
| model_uploads | ModelUploadModel | → teams, matches |
| model_executions | ModelExecutionModel | → model_uploads |
| batch_executions | BatchExecutionModel | → batch_jobs |
| batch_jobs | BatchJobModel | → batch_executions |

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_database_connection.py` | DB settings, engine, session (7 tests) |

## Dependencies on Other Features

Foundation for ALL features — provides data persistence.

## Step-by-Step Implementation Sequence

1. Create database/base.py with DeclarativeBase
2. Create database/connection.py with engine
3. Create database/session.py with SessionLocal + get_db
4. Initialize Alembic with async env.py
5. Create all ORM models
6. Generate initial migration
7. Create 30+ incremental migrations
8. Verify all migrations apply cleanly
