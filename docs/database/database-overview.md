# Database Overview

## Engine

PostgreSQL 15+ is used as the primary database. SQLite is supported for local development and testing via `DATABASE_URL` override.

## Configuration Flow

```
.env ──→ app/config.py (Settings.database_url)
               │
               ▼
         app/database/connection.py (engine)
               │
               ▼
         app/database/session.py (SessionLocal, get_db)
               │
               ▼
         Services, Repositories, Routes
```

The `DATABASE_URL` environment variable controls which database is used:

| Value | Use case |
|---|---|
| `postgresql://user:pass@postgres:5432/db` | Docker Compose (container → container) |
| `postgresql://user:pass@localhost:5432/db` | Local development with system PostgreSQL |
| `sqlite:///./dev.db` | Local development without PostgreSQL |
| `sqlite:///:memory:` | Testing (via pytest conftest override) |

Pool settings (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, etc.) are also read from environment and passed to `create_engine`.

## Design Goals
- Store all predictions, results, and scores in a reproducible and auditable way
- Support re-computation of scores if rules change before finalization
- Separate raw inputs (predictions, actuals) from computed outputs (scores, leaderboard)
- Maintain a full audit trail of all scoring events

## Tables

| Table | Purpose |
|---|---|
| `users` | Registered user credentials and role classifications (`admin` / `team_leader`) |
| `teams` | Registered participating teams (tracks `is_csv_managed` status) |
| `team_members` | Roster of team members (associates names with corporate `employee_id`) |
| `matches` | Match schedule, status, deadlines |
| `predictions` | Team prediction submissions |
| `player_predictions` | Per-player prediction entries |
| `actual_results` | Actual match outcomes |
| `player_actuals` | Per-player actual statistics |
| `scores` | Computed match scores per team |
| `cumulative_phase_scores` | Aggregated phase scores |
| `technical_evaluations` | Phase 2 committee scores |
| `presentation_evaluations` | Phase 3 peer scores |
| `leaderboard` | Final ranked leaderboard |

## Key Principles
- UUIDs generated server-side; no client-provided IDs are trusted
- Predictions are immutable once the match freeze deadline passes
- Scores are recomputable from raw inputs (idempotent re-run)
- Leaderboard `is_final` flag marks the published version
- All records are permanent (no deletion)
- Score Reports are generated on-the-fly using calculated views and existing records. Do not create unnecessary duplicate tables for reporting unless export history is explicitly needed.
