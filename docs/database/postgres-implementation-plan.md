# PostgreSQL Implementation Plan

## Technology Stack

| Component | Technology |
|---|---|
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.0 (async) |
| Driver | asyncpg 0.29+ |
| Migrations | Alembic 1.13+ |
| Repository Pattern | SQLAlchemy repository classes |

---

## Implementation Order

### Phase 1 — Database Connection
- Configure async engine with `create_async_engine`
- Define session factory using `async_sessionmaker`
- Provide database URL via environment variable (`DATABASE_URL`)
- Implement connection lifecycle (startup / shutdown events)
- Add connection pool settings (pool_size, max_overflow)

### Phase 2 — ORM Models
- Define all models using `DeclarativeBase`
- Use `Mapped` / `mapped_column` for type-annotated column definitions
- Define relationships with `relationship()` and `ForeignKey`
- Configure composite indexes and unique constraints

### Phase 3 — Alembic Migrations
- Initialize Alembic with `alembic init`
- Configure `env.py` for async Alembic
- Generate initial migration with `alembic revision --autogenerate`
- Apply migrations with `alembic upgrade head`

### Phase 4 — Repository Layer
- Create abstract `BaseRepository` with common CRUD operations
- Implement feature-specific repositories per model
- Use SQLAlchemy async session for all operations
- Keep repositories stateless (session injected per operation)

### Phase 5 — Service Integration
- Wire repositories into existing service layer
- Replace in-memory stubs with database persistence
- Add unit-of-work pattern for transactional consistency
- Connect API routes to services with database-backed repositories

---

## Model Mapping

### TeamModel

| Property | Value |
|---|---|
| **Table name** | `teams` |
| **Columns** | `id` (UUID, PK), `name` (String, not null), `code` (String, unique, not null), `registered_at` (DateTime, not null), `is_active` (Boolean, default true) |
| **Relationships** | `predictions` (one-to-many), `scores` (one-to-many), `technical_evaluation` (one-to-one), `presentation_evaluation` (one-to-one), `leaderboard_entry` (one-to-one) |
| **Indexes** | `ix_teams_code` (unique) on `code` |
| **Constraints** | Unique constraint on `code` |

---

### MatchModel

| Property | Value |
|---|---|
| **Table name** | `matches` |
| **Columns** | `id` (UUID, PK), `match_number` (Integer, not null), `home_team_name` (String, not null), `away_team_name` (String, not null), `scheduled_at` (DateTime, not null), `freeze_deadline` (DateTime, not null), `status` (Enum: SCHEDULED, FROZEN, COMPLETED, RESULT_ENTERED, SCORED), `created_at` (DateTime) |
| **Relationships** | `predictions` (one-to-many), `actual_result` (one-to-one), `scores` (one-to-many) |
| **Indexes** | `ix_matches_match_number` (unique) on `match_number`; `ix_matches_status` on `status` |
| **Constraints** | Check constraint: `match_number BETWEEN 1 AND 32` |

---

### PredictionModel

| Property | Value |
|---|---|
| **Table name** | `predictions` |
| **Columns** | `id` (UUID, PK), `team_id` (UUID, FK→teams.id), `match_id` (UUID, FK→matches.id), `submission_id` (String, not null), `status` (Enum: PENDING_VALIDATION, VALIDATED, INVALID, LATE), `predicted_winner` (Enum: home, away, draw), `home_win_probability` (Float), `draw_probability` (Float), `away_win_probability` (Float), `predicted_home_goals` (Integer), `predicted_away_goals` (Integer), `home_clean_sheet_probability` (Float), `away_clean_sheet_probability` (Float), `first_goal_team` (Enum: home, away, none), `both_teams_to_score_probability` (Float), `total_goals_prediction` (Integer), `raw_payload` (JSON), `submitted_at` (DateTime) |
| **Relationships** | `team` (many-to-one), `match` (many-to-one), `player_predictions` (one-to-many) |
| **Indexes** | `ix_predictions_team_match` on `(team_id, match_id)` (unique); `ix_predictions_match_id` on `match_id`; `ix_predictions_team_id` on `team_id` |
| **Constraints** | Unique constraint on `(team_id, match_id)`; FK→teams.id ON DELETE RESTRICT; FK→matches.id ON DELETE RESTRICT |

---

### PlayerPredictionModel

| Property | Value |
|---|---|
| **Table name** | `player_predictions` |
| **Columns** | `id` (UUID, PK), `prediction_id` (UUID, FK→predictions.id), `player_id` (String), `player_name` (String), `goal_probability` (Float), `predicted_goals` (Integer), `assist_probability` (Float) |
| **Relationships** | `prediction` (many-to-one) |
| **Indexes** | `ix_player_predictions_prediction_id` on `prediction_id` |
| **Constraints** | FK→predictions.id ON DELETE CASCADE |

---

### ActualResultModel

| Property | Value |
|---|---|
| **Table name** | `actual_results` |
| **Columns** | `id` (UUID, PK), `match_id` (UUID, FK→matches.id, unique), `actual_winner` (Enum: home, away, draw), `actual_home_goals` (Integer), `actual_away_goals` (Integer), `entered_at` (DateTime) |
| **Relationships** | `match` (one-to-one), `player_actuals` (one-to-many) |
| **Indexes** | `ix_actual_results_match_id` (unique) on `match_id` |
| **Constraints** | FK→matches.id ON DELETE RESTRICT; Check constraint: `actual_home_goals >= 0 AND actual_away_goals >= 0` |

---

### PlayerActualModel

| Property | Value |
|---|---|
| **Table name** | `player_actuals` |
| **Columns** | `id` (UUID, PK), `actual_result_id` (UUID, FK→actual_results.id), `player_id` (String), `player_name` (String), `actual_goals` (Integer) |
| **Relationships** | `actual_result` (many-to-one) |
| **Indexes** | `ix_player_actuals_actual_result_id` on `actual_result_id` |
| **Constraints** | FK→actual_results.id ON DELETE CASCADE; Check constraint: `actual_goals >= 0` |

---

### ScoreModel

| Property | Value |
|---|---|
| **Table name** | `scores` |
| **Columns** | `id` (UUID, PK), `team_id` (UUID, FK→teams.id), `match_id` (UUID, FK→matches.id), `winner_points` (Integer), `scoreline_points` (Integer), `probability_points` (Integer), `player_points` (Integer), `base_score` (Float), `match_rank` (Integer), `grade` (Enum: A, B, C), `multiplier` (Integer), `earned_points` (Float), `computed_at` (DateTime) |
| **Relationships** | `team` (many-to-one), `match` (many-to-one) |
| **Indexes** | `ix_scores_team_match` on `(team_id, match_id)` (unique); `ix_scores_match_id` on `match_id` |
| **Constraints** | Unique constraint on `(team_id, match_id)`; FK→teams.id ON DELETE RESTRICT; FK→matches.id ON DELETE RESTRICT; Check constraint: `base_score BETWEEN 0 AND 25` |

---

### CumulativePhaseScoreModel

| Property | Value |
|---|---|
| **Table name** | `cumulative_phase_scores` |
| **Columns** | `id` (UUID, PK), `team_id` (UUID, FK→teams.id, unique), `total_earned_points` (Float), `matches_played` (Integer), `phase1_score` (Float), `technical_score` (Float), `presentation_score` (Float) |
| **Relationships** | `team` (one-to-one) |
| **Indexes** | `ix_cumulative_phase_scores_team_id` (unique) on `team_id` |
| **Constraints** | FK→teams.id ON DELETE RESTRICT; Check constraint: `phase1_score BETWEEN 0 AND 60` |

---

### TechnicalEvaluationModel

| Property | Value |
|---|---|
| **Table name** | `technical_evaluations` |
| **Columns** | `id` (UUID, PK), `team_id` (UUID, FK→teams.id, unique), `code_quality` (Integer), `backend_quality` (Integer), `teamwork` (Integer), `ai_explanation` (Integer), `total_score` (Integer), `submitted_at` (DateTime) |
| **Relationships** | `team` (one-to-one) |
| **Indexes** | `ix_technical_evaluations_team_id` (unique) on `team_id` |
| **Constraints** | FK→teams.id ON DELETE RESTRICT; Check constraint: `code_quality BETWEEN 0 AND 5 AND backend_quality BETWEEN 0 AND 5 AND teamwork BETWEEN 0 AND 5 AND ai_explanation BETWEEN 0 AND 5` |

---

### PresentationEvaluationModel

| Property | Value |
|---|---|
| **Table name** | `presentation_evaluations` |
| **Columns** | `id` (UUID, PK), `team_id` (UUID, FK→teams.id, unique), `ai_explanation_score` (Integer), `qa_score` (Integer), `delivery_score` (Integer), `raw_total` (Integer), `presentation_score` (Float), `rank` (Integer), `grade` (Enum: A, B, C), `multiplier` (Integer), `submitted_at` (DateTime) |
| **Relationships** | `team` (one-to-one) |
| **Indexes** | `ix_presentation_evaluations_team_id` (unique) on `team_id` |
| **Constraints** | FK→teams.id ON DELETE RESTRICT; Check constraint: `ai_explanation_score BETWEEN 0 AND 20 AND qa_score BETWEEN 0 AND 15 AND delivery_score BETWEEN 0 AND 15` |

---

### LeaderboardModel

| Property | Value |
|---|---|
| **Table name** | `leaderboard` |
| **Columns** | `id` (UUID, PK), `team_id` (UUID, FK→teams.id, unique), `rank` (Integer), `phase1_score` (Float), `technical_score` (Float), `presentation_score` (Float), `final_score` (Float), `is_final` (Boolean, default false), `generated_at` (DateTime) |
| **Relationships** | `team` (one-to-one) |
| **Indexes** | `ix_leaderboard_team_id` (unique) on `team_id`; `ix_leaderboard_rank` on `rank` |
| **Constraints** | FK→teams.id ON DELETE RESTRICT; Check constraint: `final_score BETWEEN 0 AND 100` |

---

## Entity Relationship Diagram (Text)

```
teams ──────────────────────────────────────────┐
  │                                              │
  ├── predictions (1:N) ← team_id                │
  │     └── player_predictions (1:N)              │
  ├── scores (1:N) ← team_id                     │
  ├── cumulative_phase_scores (1:1) ← team_id    │
  ├── technical_evaluations (1:1) ← team_id      │
  ├── presentation_evaluations (1:1) ← team_id   │
  └── leaderboard (1:1) ← team_id                │
                                                  │
matches ─────────────────────────────────────────┘
  │
  ├── predictions (1:N) ← match_id
  ├── actual_results (1:1) ← match_id
  │     └── player_actuals (1:N)
  └── scores (1:N) ← match_id
```

---

## Migration Strategy

| Step | Command |
|---|---|
| Initialize Alembic | `alembic init alembic` |
| Configure async driver | Update `env.py` for async Alembic |
| Generate migration | `alembic revision --autogenerate -m "initial schema"` |
| Apply migration | `alembic upgrade head` |
| Rollback | `alembic downgrade -1` |

All migrations will be stored in an `alembic/versions/` directory within the backend.
