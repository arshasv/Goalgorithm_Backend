# Feature 10: Technical Evaluation

## Feature Overview

Phase 2 technical implementation scoring where the Architecture Committee evaluates each team across 4 sub-dimensions (code_quality, backend_quality, teamwork, ai_explanation), each scored 0-5. Total weighted score capped at 20 points.

## Purpose & Requirements

- Committee submits technical evaluation per team
- 4 sub-dimensions: code_quality, backend_quality, teamwork, ai_explanation (each 0-5)
- Weighted scoring: code*5 + backend*5 + teamwork*4 + ai*6, capped at 20
- One evaluation per team (no duplicates)
- Organizer-only access

## Related Specifications

- `features/technical-evaluation.md` — Technical scoring specification
- `api/evaluation-api.md` — Evaluation API cross-reference
- `api/scoring-api.md` — Technical score endpoint

## How the Feature Works Internally

### Scoring Formula (`technical_score.py`)
```python
def calculate_technical_score(code_quality, backend_quality, teamwork, ai_explanation, config):
    weighted = (
        code_quality * config.code_quality_weight +     # default 5
        backend_quality * config.backend_quality_weight + # default 5
        teamwork * config.teamwork_weight +               # default 4
        ai_explanation * config.ai_explanation_weight      # default 6
    )
    return min(weighted, config.technical_max_total)  # default 20.0
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/scoring_engine/technical_score.py` | 47 | Weighted scoring formula |
| `app/schemas/technical_evaluation_schema.py` | 9 | Bounded integer schema |
| `app/models/evaluation.py` | 69 | TechnicalEvaluationModel ORM |
| `app/api/scoring_routes.py` | 457 | Technical score endpoint |

### Key Functions

- `calculate_technical_score(scores, config)` → float (0-20)
- `ScoringService.save_technical_evaluation(team_id, scores)` → Save evaluation

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/technical-evaluation` | ORGANIZER | Submit technical scores |

## Database/Data Models Involved

### `technical_evaluations` Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| team_id | UUID | FK → teams.id, unique |
| code_quality | Integer | CHECK 0-5 |
| backend_quality | Integer | CHECK 0-5 |
| teamwork | Integer | CHECK 0-5 |
| ai_explanation | Integer | CHECK 0-5 |
| total_score | Float | CHECK 0-20 |

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_technical_score.py` | Weighted scoring, boundaries (7 tests) |

## Dependencies on Other Features

- **Team Management** — team_id reference
- **Admin Scoring Config** — Configurable weights and max
- **Leaderboard** — Technical score feeds into final

## Step-by-Step Implementation Sequence

1. Create TechnicalEvaluationModel ORM
2. Create TechnicalEvaluation schema with bounded integers
3. Create technical_score.py calculator
4. Create scoring route endpoint
5. Wire into scoring service
6. Run Alembic migration
7. Write tests
