# Feature 14: Admin Scoring Configuration

## Feature Overview

Dynamic, database-driven scoring configuration allowing organizers to adjust all scoring parameters (point values, thresholds, multipliers, normalization targets) without code changes. Changes apply only to future scoring operations — existing scores are never retroactively recalculated.

## Purpose & Requirements

- 30+ configurable scoring parameters stored in DB
- Only one config active at a time (is_active flag)
- Version management with creation timestamps
- Reset to defaults functionality
- Config-driven scoring engine (reads from active config at runtime)
- Guidelines endpoint for frontend display of current settings

## Related Specifications

- `features/admin-scoring-config.md` — Dynamic scoring configuration
- `database/schema-design.md` — scoring_configs table

## How the Feature Works Internally

### Config Model (`ScoringConfigModel`)
30+ columns including:

| Category | Parameters |
|----------|-----------|
| Winner | winner_points_correct, winner_points_incorrect |
| Scoreline | scoreline_points_exact, scoreline_points_margin, scoreline_points_incorrect |
| Probability | probability_threshold, probability_medium_threshold, probability_points_pass/fail |
| Player | player_points_exact/close/wrong, player_avg_threshold_exact/close |
| Base Score | max_base_score |
| Technical | technical_max_per_category, technical_max_total |
| Presentation | presentation_max_ai, presentation_max_qa, presentation_max_delivery, presentation_denominator, presentation_max_marks |
| Multiplier | multiplier_a, multiplier_b, multiplier_c |
| Normalization | phase1_max_marks |

### `to_dict()` Method
Returns all parameters as a dictionary for the scoring engine to consume.

### Activation Flow
```
POST /scoring-config/{id}/activate
    ↓
Set current active config.is_active = False
    ↓
Set new config.is_active = True
    ↓
Future scoring operations use new config
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/models/scoring_config.py` | 130 | ScoringConfigModel with 30+ params |
| `app/schemas/scoring_config_schema.py` | 215 | Create/Update/Response + GuidelineItem |
| `app/repositories/scoring_config_repository.py` | 41 | Config CRUD queries |
| `app/services/scoring_config_service.py` | 166 | Config management + defaults |
| `app/api/scoring_config_routes.py` | 234 | Config CRUD endpoints |

### Key Functions

- `ScoringConfigService.get_active_config()` → Current active config
- `ScoringConfigService.create_config(data)` → New config version
- `ScoringConfigService.activate_config(config_id)` → Set as active
- `ScoringConfigService.reset_to_defaults()` → Create default config
- `ScoringConfigService.get_guidelines()` → Config + descriptions
- `ScoringConfigModel.to_dict()` → All params as dict

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/scoring-config/active` | Any | Get active config |
| GET | `/api/v1/scoring-config/guidelines` | Any | Config + guideline descriptions |
| GET | `/api/v1/scoring-config` | ORGANIZER | List all configs |
| POST | `/api/v1/scoring-config` | ORGANIZER | Create new config |
| PUT | `/api/v1/scoring-config/{id}` | ORGANIZER | Update config |
| POST | `/api/v1/scoring-config/{id}/activate` | ORGANIZER | Activate config |
| POST | `/api/v1/scoring-config/reset` | ORGANIZER | Reset to defaults |

## Database/Data Models Involved

### `scoring_configs` Table
All 30+ scoring parameter columns with Float type, plus:
- `id` (UUID PK), `name` (String), `is_active` (Boolean), `version` (Integer), `created_at`, `updated_at`

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_scoring_config.py` | CRUD, permissions, reset, config effect (8 tests) |

## Dependencies on Other Features

- **Base Scoring Engine** — Reads config at runtime
- **Ranking & Multiplier** — Multiplier values from config
- **Phase Normalization** — max_marks from config
- **Presentation Evaluation** — Criteria weights from config

## Step-by-Step Implementation Sequence

1. Create ScoringConfigModel with all columns + to_dict()
2. Create Pydantic schemas with GUIDELINE_DESCRIPTIONS
3. Create repository with active config query
4. Create service with CRUD + activate + reset logic
5. Create API routes
6. Wire scoring engine to read from active config
7. Create default config with standard values
8. Run Alembic migration
9. Write tests
