# Feature 09: Phase Normalization

## Feature Overview

Normalizes cumulative earned points across all 32 matches into a Phase 1 score on a 0-60 scale. Uses linear scaling where the highest-scoring team receives exactly 60.00 and others are proportionally scaled.

## Purpose & Requirements

- Sum all earned_points across 32 matches per team
- Linear normalize to phase1_max_marks (default 60)
- Highest scorer gets exactly 60.00
- Store in cumulative_phase_scores table
- Round to 2 decimal places

## Related Specifications

- `features/phase-normalization.md` — Normalization formula specification
- `database/schema-design.md` — cumulative_phase_scores table

## How the Feature Works Internally

### Normalization Formula (`phase1_normalizer.py`)
```python
def normalize_phase1(total_earned_points, max_earned_points, config):
    if max_earned_points == 0:
        return 0.0
    normalized = (total_earned_points / max_earned_points) * config.phase1_max_marks
    return round(normalized, 2)
```

### Calculation Flow
```
For each team:
    total_earned = sum(ScoreModel.earned_points for all matches)
    ↓
max_earned = max(total_earned across all teams)
    ↓
phase1_score = (team_total_earned / max_earned) * 60
    ↓
Store in CumulativePhaseScoreModel
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/scoring_engine/phase1_normalizer.py` | 52 | Linear normalization to /60 |
| `app/services/scores_service.py` | 296 | Cumulative score management |
| `app/repositories/score_repository.py` | 84 | Cumulative score queries |
| `app/models/cumulative_phase_score.py` | ~40 | CumulativePhaseScoreModel ORM |

### Key Functions

- `normalize_phase1(total_earned, max_earned, config)` → float (0-60)
- `ScoresService.calculate_cumulative_scores()` → Updates all teams
- `ScoreRepository.upsert_cumulative_score(team_id, data)` → Save/update

## Database/Data Models Involved

### `cumulative_phase_scores` Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| team_id | UUID | FK → teams.id, unique |
| total_earned_points | Float | CHECK >= 0 |
| phase1_score | Float | CHECK 0-60 |
| matches_played | Integer | |
| updated_at | DateTime | |

## Error Handling

| Scenario | Handling |
|----------|----------|
| All teams have 0 earned | All get 0.00 |
| Single team with all earned | Gets 60.00 |
| Empty input | Returns empty list |

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_normalization.py` | Phase1 normalization (8 tests) |

## Dependencies on Other Features

- **Base Scoring Engine** — Earned points source
- **Ranking & Multiplier** — Earned points after multiplier
- **Leaderboard** — Phase1 score feeds into final leaderboard

## Step-by-Step Implementation Sequence

1. Create phase1_normalizer.py with normalization function
2. Create CumulativePhaseScoreModel ORM
3. Create ScoresService for cumulative calculation
4. Create ScoreRepository for upsert operations
5. Integrate into scoring pipeline
6. Write unit tests for normalization edge cases
