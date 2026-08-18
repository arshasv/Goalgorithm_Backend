# Feature 05: Prediction Management

## Feature Overview

Accept, validate, and store team prediction JSON files for football matches. Supports both manual (human-entered) and AI model-generated prediction formats. Idempotent submission — same team+match overwrites existing. Freeze deadline enforcement prevents late submissions.

## Purpose & Requirements

- Teams submit predictions before match freeze deadline
- Support dual format: Legacy/Manual and AI Model output
- Automatic normalization of AI format to internal schema
- Idempotent: same team+match overwrites previous prediction
- Store raw_payload preserving original JSON
- Auto-trigger scoring on prediction submission

## Related Specifications

- `features/prediction-management.md` — Prediction submission specification
- `api/prediction-api.md` — Prediction API endpoints
- `api/prediction_format_reference.md` — Exact JSON schema reference (82 lines)
- `architecture/prediction-architecture.md` — Prediction data flow

## User/Business Flow

### Team Leader Submits Prediction
```
Team Leader → POST /predictions → {team_id, match_id, match_prediction, player_predictions}
    ↓
Validate freeze deadline not passed
    ↓
Validate schema (Pydantic v2 validators)
    ↓
Check idempotency (same team+match → overwrite)
    ↓
Save PredictionModel + PlayerPredictionModels
    ↓
Auto-trigger scoring if actual result exists
    ↓
Return prediction
```

### AI Model Prediction
```
AI Model Output → ModelSerializer.serialize_output()
    ↓
Transform to PredictionSubmission format
    ↓
Auto-calculate winner from probabilities
    ↓
Auto-calculate total goals from scoreline
    ↓
Validate goal scorer counts match scoreline
    ↓
Save via PredictionService.save_prediction()
```

## How the Feature Works Internally

### Prediction Schema (Dual Format)

**Legacy Format:**
```json
{
  "team_id": "A", "match_id": "...",
  "match_prediction": {
    "predicted_winner": "home",
    "predicted_scoreline": {"home_team_goals": 2, "away_team_goals": 1},
    "probabilities": {"home_win_probability": 60, "draw_probability": 25, "away_win_probability": 15},
    "clean_sheet_probability": {"home_team": 40, "away_team": 20},
    "first_goal_team": "home",
    "both_teams_to_score_probability": 70,
    "goal_scorers": {"home": ["Player A"], "away": []}
  },
  "player_predictions": [
    {"player_id": "1", "player_name": "Player A", "goal_probability": 80, "predicted_goals": 1, "assist_probability": 30}
  ]
}
```

**AI Model Format (auto-normalized):**
```json
{
  "win_probabilities": {"home_team": {"probability": 60}, "draw": {"probability": 25}, "away_team": {"probability": 15}},
  "predicted_scoreline": {"home_goals": 2, "away_goals": 1},
  "both_teams_to_score": {"prediction": true, "probability": 70},
  "first_team_to_score": {"team": "home", "probability": 55},
  "clean_sheet_predictions": [{"goalkeeper": "GK Name", "prediction": true, "probability": 40}]
}
```

### Pydantic Validators Auto-Normalize
- AI format fields mapped to legacy flat fields
- Winner auto-calculated from highest probability
- Total goals auto-calculated from scoreline
- Goal scorer array lengths validated against scoreline

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/schemas/prediction_schema.py` | 249 | PredictionSubmission with AI format support |
| `app/services/prediction_service.py` | 456 | Prediction save, retrieval, AI normalization |
| `app/repositories/prediction_repository.py` | 136 | Prediction queries, cumulative scores |
| `app/api/prediction_routes.py` | 361 | Prediction endpoints |
| `app/models/prediction.py` | 285 | PredictionModel + PlayerPredictionModel ORM |

### Key Classes & Functions

- `PredictionService.save_prediction(data)` → Save/overwrite prediction
- `PredictionService.get_predictions_by_team(team_id)` → Team predictions
- `PredictionService.get_predictions_by_match(match_id)` → Match predictions
- `PredictionSubmission` (Pydantic) — Validates and normalizes both formats
- `MatchPrediction` (Pydantic) — Nested prediction schema
- `PlayerPrediction` (Pydantic) — Player-level predictions

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/predictions` | TEAM_LEADER | Submit prediction |
| GET | `/api/v1/predictions/team/{team_id}` | Any | Team predictions |
| GET | `/api/v1/predictions/match/{match_id}` | ORGANIZER | Match predictions |
| GET | `/api/v1/predictions/{id}` | Any | Single prediction |

## Database/Data Models Involved

### `predictions` Table (`PredictionModel`)
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| team_id | UUID | FK → teams.id |
| match_id | UUID | FK → matches.id |
| submission_id | String | nullable |
| status | Enum(PredictionStatus) | default PENDING |
| predicted_winner | Enum(Winner) | nullable |
| home_win_probability, draw_probability, away_win_probability | Float | nullable |
| predicted_home_goals, predicted_away_goals | Integer | nullable |
| clean_sheet_prob_home, clean_sheet_prob_away | Float | nullable |
| first_goal_team | Enum(FirstGoalTeam) | nullable |
| btts_probability | Float | nullable |
| total_goals_prediction | Integer | nullable |
| raw_payload | JSON | nullable |
| submitted_at | DateTime | server_default=now |
| UNIQUE | (team_id, match_id) | |

### `player_predictions` Table (`PlayerPredictionModel`)
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| prediction_id | UUID | FK → predictions.id, CASCADE |
| player_name | String | not null |
| team_side | String | nullable |
| position | String | nullable |
| goal_scoring_probability | Float | nullable |
| predicted_goals | Integer | nullable |
| assist_probability | Float | nullable |

## Error Handling

| Scenario | HTTP Code |
|----------|-----------|
| Prediction after freeze | 423 LOCKED |
| Match not found | 404 NOT_FOUND |
| Team not found | 404 NOT_FOUND |
| Schema validation failure | 422 VALIDATION_ERROR |
| Goal scorer count mismatch | 422 VALIDATION_ERROR |

## External Dependencies/Integrations

- Pydantic v2 custom validators for AI format normalization
- Scoring engine triggered automatically on prediction save

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_schemas.py` | Prediction schema validation (18 tests) |
| `tests/test_api.py` | Prediction submission API |
| `tests/test_full_competition_flow.py` | End-to-end prediction flow |

## Dependencies on Other Features

- **Team Management** — team_id references
- **Match Management** — match_id references, freeze deadline
- **Scoring Engine** — Auto-triggered on prediction save
- **Model Execution** — AI models generate predictions

## Step-by-Step Implementation Sequence

1. Create PredictionModel + PlayerPredictionModel ORM
2. Create PredictionSubmission schema with dual format support
3. Create Pydantic validators for AI format normalization
4. Create PredictionRepository with CRUD and queries
5. Create PredictionService with save/retrieve logic
6. Create Prediction routes with all endpoints
7. Implement freeze deadline check
8. Implement idempotent overwrite logic
9. Integrate auto-scoring trigger
10. Run Alembic migration
11. Write schema and API tests
