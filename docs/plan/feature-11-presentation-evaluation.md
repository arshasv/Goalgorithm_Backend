# Feature 11: Presentation Evaluation

## Feature Overview

Phase 3 presentation scoring where judges submit scores across 3 criteria (ai_explanation 0-20, qa 0-15, delivery 0-15) per team per round. Supports multiple judges with score averaging, per-round ranking with grade multipliers, and normalization to 20 marks.

## Purpose & Requirements

- Judges submit presentation scores per team per round
- 3 criteria: ai_explanation (0-20), qa (0-15), delivery (0-15)
- Multiple judges supported with score averaging
- Per-round ranking: top=A(3x), mid=B(2x), low=C(1x)
- Two presentation rounds; weighted scores summed
- Final normalization: (total_weighted / denominator) * 20

## Related Specifications

- `features/presentation-evaluation.md` — Presentation scoring specification
- `api/evaluation-api.md` — Evaluation API cross-reference

## How the Feature Works Internally

### Presentation Score Calculation (`presentation_score.py`)

```python
def calculate_presentation_score(judges_scores, config):
    # 1. Average scores across judges per criteria
    avg_ai = mean([j.ai_explanation_score for j in judges])
    avg_qa = mean([j.qa_score for j in judges])
    avg_delivery = mean([j.delivery_score for j in judges])

    # 2. Raw total
    raw_total = avg_ai + avg_qa + avg_delivery  # max 50

    # 3. Rank teams in this round
    # Highest raw_total → Grade A (3x)
    # Middle → Grade B (2x)
    # Lowest → Grade C (1x)

    # 4. Weighted score
    weighted_score = raw_total * multiplier  # max 150

    return {
        "raw_total": raw_total,
        "rank": rank,
        "grade": grade,
        "multiplier": multiplier,
        "weighted_score": weighted_score,
    }

def calculate_final_presentation(rounds_weighted_scores, config):
    total_weighted = sum(r.weighted_score for r in rounds)
    dynamic_denominator = len(rounds) * 150
    final = (total_weighted / dynamic_denominator) * config.presentation_max_marks
    return round(final, 2)  # max 20.0
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/scoring_engine/presentation_score.py` | 109 | Multi-judge averaging, ranking, grading |
| `app/schemas/presentation_schema.py` | 12 | PresentationEvaluation schema |
| `app/schemas/presentation_round_schema.py` | 13 | Round create/response schemas |
| `app/models/evaluation.py` | 69 | PresentationEvaluationModel ORM |
| `app/models/judge.py` | 23 | JudgeModel ORM |
| `app/models/presentation_round.py` | 19 | PresentationRoundModel ORM |
| `app/api/judge_routes.py` | 37 | Judge CRUD endpoints |
| `app/services/presentation_round_service.py` | 22 | Round CRUD service |

### Key Functions

- `calculate_presentation_score(judges_scores, config)` → dict with raw/grade/multiplier/weighted
- `calculate_final_presentation(rounds, config)` → float (0-20)
- `PresentationRoundService.create_round(data)` → RoundModel
- `PresentationRoundService.get_rounds()` → List of rounds

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/presentation-evaluation` | ORGANIZER | Submit presentation scores |
| GET | `/api/v1/presentation-rounds` | ORGANIZER | List rounds |
| POST | `/api/v1/presentation-rounds` | ORGANIZER | Create round |
| GET | `/api/v1/judges` | ORGANIZER | List judges |
| POST | `/api/v1/judges` | ORGANIZER | Create judge |
| DELETE | `/api/v1/judges/{id}` | ORGANIZER | Delete judge |

## Database/Data Models Involved

### `presentation_evaluations` Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| team_id | UUID | FK → teams.id |
| round_id | UUID | FK → presentation_rounds.id |
| judge_scores | JSONB | not null |
| ai_explanation_score | Float | |
| qa_score | Float | |
| delivery_score | Float | |
| raw_total | Float | CHECK 0-50 |

### `judges` Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| name | String | not null |
| employee_id | String | nullable |

### `presentation_rounds` Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| name | String | not null |
| created_at | DateTime | server_default=now |

## Error Handling

| Scenario | HTTP Code |
|----------|-----------|
| Score exceeds max | 422 VALIDATION_ERROR |
| Non-organizer access | 403 FORBIDDEN |
| Judge not found | 404 NOT_FOUND |

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_presentation_score.py` | Single/multiple judges, ranking, grading (5 tests) |

## Dependencies on Other Features

- **Team Management** — team_id reference
- **Admin Scoring Config** — Configurable criteria weights
- **Leaderboard** — Presentation score feeds into final

## Step-by-Step Implementation Sequence

1. Create JudgeModel, PresentationRoundModel, PresentationEvaluationModel
2. Create Pydantic schemas
3. Create presentation_score.py calculator
4. Create judge CRUD routes
5. Create presentation round routes
6. Create presentation evaluation endpoint
7. Implement multi-judge averaging
8. Implement per-round ranking and grading
9. Implement final normalization
10. Run Alembic migrations
11. Write tests
