# Feature 07: Base Scoring Engine

## Feature Overview

Core automated scoring pipeline that evaluates team predictions against actual match results. Computes scores across 8 dimensions (winner, scoreline, probability, player, BTTS, total goals, first team to score, clean sheet) with a configurable maximum base score of 25 points per match. All scoring functions are **pure functions** — no I/O, no DB, no HTTP.

## Purpose & Requirements

- Score predictions across 8 independent dimensions
- All dimensions are pure mathematical functions (deterministic, stateless)
- Configurable point values via ScoringConfigModel
- Base score capped at configurable maximum (default 25)
- Support for tiered scoring (exact/close/wrong thresholds)

## Related Specifications

- `features/base-scoring-engine.md` — Scoring dimensions specification
- `architecture/scoring-architecture.md` — Scoring data flow
- `api/scoring-api.md` — Scoring API endpoints

## User/Business Flow

```
Organizer triggers scoring → POST /scoring/calculate {match_id}
    ↓
Load prediction + actual result for each team
    ↓
For each team:
    Calculate winner_score()
    Calculate scoreline_score()
    Calculate probability_score()
    Calculate player_score()
    Calculate btts_score()
    Calculate total_goals_score()
    Calculate first_team_to_score_score()
    Calculate clean_sheet_score()
    ↓
Sum all dimensions → base_score (capped at max)
    ↓
Save ScoreModel with breakdown
```

## How the Feature Works Internally

### Scoring Dimensions (8 Pure Functions)

#### 1. Winner Score (`winner_score.py`) — 0 to 5+ pts
```python
def calculate_winner_score(predicted_winner, actual_winner, config):
    if predicted_winner == actual_winner:
        return config.winner_points_correct  # default 5.0
    return config.winner_points_incorrect    # default 0.0
```

#### 2. Scoreline Score (`scoreline_score.py`) — 0 to 10 pts
```python
def calculate_scoreline_score(predicted, actual, config):
    if predicted_home == actual_home and predicted_away == actual_away:
        return config.scoreline_points_exact    # default 10.0
    if (predicted_home - predicted_away) == (actual_home - actual_away):
        return config.scoreline_points_margin   # default 5.0
    return config.scoreline_points_incorrect    # default 0.0
```

#### 3. Probability Score (`probability_score.py`) — 0 to 5 pts
```python
def calculate_probability_score(predicted_probs, actual_probs, config):
    # Compare 5 probability fields: home_win, draw, away_win, total_goals, btts
    # All within threshold (default 15%): config.probability_points_pass (5.0)
    # Any outside: config.probability_points_fail (0.0)
```

#### 4. Player Score (`player_score.py`) — 0 to 5 pts
```python
def calculate_player_score(predictions, actuals, config):
    # Per player: exact(diff=0)=5pts, close(diff=1)=2pts, wrong(diff>=2)=0pts
    # Average across players
    # >= config.player_avg_threshold_exact (4.0) → 5pts
    # >= config.player_avg_threshold_close (2.0) → 2pts
    # else → 0pts
```

#### 5. BTTS Score (`btts_score.py`) — 0 to 2 pts
```python
def calculate_btts_score(predicted_btts, actual_btts, config):
    if predicted_btts == actual_btts:
        return 2.0  # Correct prediction
    return 0.0
```

#### 6. Total Goals Score (`total_goals_score.py`) — 0 to 1 pt
```python
def calculate_total_goals_score(predicted, actual, config):
    if predicted == actual:
        return 1.0   # Exact match
    if abs(predicted - actual) <= 1:
        return 0.5   # Within 1 goal
    return 0.0
```

#### 7. First Team to Score (`first_team_to_score_score.py`) — 0 to 2 pts
```python
def calculate_first_team_to_score_score(predicted, actual, config):
    if predicted == actual:
        return 2.0
    return 0.0
```

#### 8. Clean Sheet Score (`clean_sheet_score.py`) — 0 to 4 pts
```python
def calculate_clean_sheet_score(predicted_home, predicted_away, actual_home_clean, actual_away_clean, config):
    score = 0.0
    if predicted_home == actual_home_clean:
        score += 2.0
    if predicted_away == actual_away_clean:
        score += 2.0
    return score
```

### Base Score Aggregation
```python
def calculate_base_score(match_data, actual_data, config):
    total = (winner_score + scoreline_score + probability_score + player_score)
    # Additional tracked (but not in base total):
    # btts_score, total_goals_score, first_team_to_score_score, clean_sheet_score
    return min(total, config.max_base_score)  # default 25.0
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/scoring_engine/base_score_calculator.py` | 35 | Orchestrator summing all categories |
| `app/scoring_engine/winner_score.py` | 36 | Winner prediction scoring |
| `app/scoring_engine/scoreline_score.py` | 55 | Scoreline prediction scoring |
| `app/scoring_engine/probability_score.py` | 76 | Probability accuracy scoring |
| `app/scoring_engine/player_score.py` | 88 | Player goal prediction scoring |
| `app/scoring_engine/btts_score.py` | 22 | Both Teams To Score scoring |
| `app/scoring_engine/total_goals_score.py` | 14 | Total goals scoring |
| `app/scoring_engine/first_team_to_score_score.py` | 20 | First team to score scoring |
| `app/scoring_engine/clean_sheet_score.py` | 52 | Clean sheet prediction scoring |
| `app/services/scoring_service.py` | 367 | Scoring pipeline orchestration |

### Key Functions

- `calculate_base_score(prediction, actual_result, config)` → dict with all scores + total
- `calculate_winner_score(predicted, actual, config)` → float
- `calculate_scoreline_score(predicted, actual, config)` → float
- `calculate_probability_score(predicted, actual, config)` → float
- `calculate_player_score(predictions, actuals, config)` → float
- `calculate_btts_score(predicted, actual, config)` → float
- `calculate_total_goals_score(predicted, actual, config)` → float
- `calculate_first_team_to_score_score(predicted, actual, config)` → float
- `calculate_clean_sheet_score(predicted, actual, config)` → float
- `ScoringService.calculate_and_save_match_score(match_id)` → ScoreModel

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/scoring/calculate` | ORGANIZER | Score a single match |
| POST | `/api/v1/scoring/recalculate-all` | ORGANIZER | Recalculate all matches |
| POST | `/api/v1/scoring/batch` | ORGANIZER | Batch scoring |
| GET | `/api/v1/scoring/status` | ORGANIZER | Scoring status |

## Database/Data Models Involved

### `scores` Table (`ScoreModel`)
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| team_id | UUID | FK → teams.id |
| match_id | UUID | FK → matches.id |
| config_id | UUID | FK → scoring_configs.id |
| winner_score | Float | |
| scoreline_score | Float | |
| probability_score | Float | |
| player_score | Float | |
| btts_score | Float | |
| total_goals_score | Float | |
| first_team_to_score_score | Float | |
| clean_sheet_score | Float | |
| total_base_score | Float | CHECK 0-25 |
| match_rank | Integer | |
| grade | Enum(Grade) | |
| multiplier | Float | |
| earned_points | Float | |
| normalized_score | Float | |
| UNIQUE | (team_id, match_id) | |

## Configuration/Environment Variables

All scoring parameters come from `ScoringConfigModel` (DB-driven, not env vars):
- `winner_points_correct` (5.0), `winner_points_incorrect` (0.0)
- `scoreline_points_exact` (10.0), `scoreline_points_margin` (5.0)
- `probability_threshold` (15.0), `probability_points_pass` (5.0)
- `player_points_exact` (5.0), `player_points_close` (2.0)
- `player_avg_threshold_exact` (4.0), `player_avg_threshold_close` (2.0)
- `max_base_score` (25.0)

## Error Handling

| Scenario | HTTP Code |
|----------|-----------|
| Prediction missing for team | Skipped (no score) |
| Actual result missing | 400 INVALID_STATE |
| Duplicate score entry | 409 DUPLICATE_ENTRY |
| Config not found | 400 NO_ACTIVE_CONFIG |

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_base_score.py` | All 8 scoring dimensions (14 tests) |
| `tests/test_full_competition_flow.py` | End-to-end scoring flow |

## Known Limitations/Technical Debt

- Some scoring functions have extended logic beyond the spec (confidence bonuses)
- Base score cap is configurable but default is 25

## Dependencies on Other Features

- **Prediction Management** — Predictions are scoring inputs
- **Actual Result Management** — Results are scoring reference
- **Admin Scoring Config** — Configurable point values
- **Ranking & Multiplier** — Score outputs feed into ranking

## Step-by-Step Implementation Sequence

1. Create each scoring function as pure function module
2. Create base_score_calculator.py orchestrator
3. Create scoring_service.py for orchestration + persistence
4. Create scoring_routes.py for API endpoints
5. Wire with ScoringConfigModel for configurable values
6. Implement ScoreModel persistence
7. Write unit tests for each pure function
8. Write integration tests for scoring pipeline
