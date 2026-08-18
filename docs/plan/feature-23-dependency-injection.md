# Feature 23: Dependency Injection Container

## Feature Overview

Centralized FastAPI dependency injection container that wires repositories → services → API routes. Provides factory functions for creating properly initialized components with all their dependencies injected.

## Purpose & Requirements

- Single source of truth for component wiring
- 17 repository provider functions
- 12 service provider functions
- Proper dependency chain: DB session → Repository → Service → Route
- FastAPI `Depends()` integration

## How the Feature Works Internally

### Wiring Pattern
```python
# Repository providers (simple: just DB session)
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_team_repository(db: Session = Depends(get_db)) -> TeamRepository:
    return TeamRepository(db)

# Service providers (complex: multiple repository dependencies)
def get_scoring_service(
    scoring_config_repo = Depends(get_scoring_config_repository),
    score_repo = Depends(get_score_repository),
    cumulative_repo = Depends(get_cumulative_phase_score_repository),
    prediction_repo = Depends(get_prediction_repository),
    team_repo = Depends(get_team_repository),
    match_repo = Depends(get_match_repository),
    actual_result_repo = Depends(get_actual_result_repository),
    technical_eval_repo = Depends(get_technical_evaluation_repository),
    presentation_eval_repo = Depends(get_presentation_evaluation_repository),
    leaderboard_repo = Depends(get_leaderboard_repository),
    presentation_score_repo = Depends(get_presentation_score_repository),
    presentation_round_repo = Depends(get_presentation_round_repository),
    judge_repo = Depends(get_judge_repository),
) -> ScoringService:
    return ScoringService(
        scoring_config_repo, score_repo, cumulative_repo,
        prediction_repo, team_repo, match_repo, actual_result_repo,
        technical_eval_repo, presentation_eval_repo, leaderboard_repo,
        presentation_score_repo, presentation_round_repo, judge_repo,
    )
```

### Usage in Routes
```python
@router.post("/scoring/calculate")
async def calculate_score(
    match_id: str,
    scoring_service: ScoringService = Depends(get_scoring_service),
    current_user: UserModel = Depends(get_current_organizer),
):
    result = scoring_service.calculate_and_save_match_score(match_id)
    return result
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/dependencies/__init__.py` | 208 | Full DI container |
| `app/api/deps.py` | 55 | Auth dependency functions |

### Provider Count

| Type | Count | Examples |
|------|-------|---------|
| Repository Providers | 17 | get_user_repository, get_team_repository, get_match_repository |
| Service Providers | 12 | get_auth_service, get_scoring_service, get_analytics_service |

## Dependencies on Other Features

Used by ALL route files — this is cross-cutting infrastructure.

## Step-by-Step Implementation Sequence

1. Create repository provider functions (17)
2. Create service provider functions (12)
3. Wire into route handlers via `Depends()`
4. Verify dependency chain works end-to-end
