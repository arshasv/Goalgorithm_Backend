# Feature 08: Ranking & Multiplier

## Feature Overview

Ranks teams per match by their base score and assigns grade-based multipliers (A=3x, B=2x, C=1x). The multiplier transforms raw base scores into earned points, creating separation between top and bottom performers. Includes deterministic tie-breaking logic.

## Purpose & Requirements

- Rank 5 teams by base score per match (descending)
- Grade A (unique top) = 3x multiplier
- Grade B (middle) = 2x multiplier
- Grade C (unique bottom) = 1x multiplier
- Tie rules: tie at top = all B, tie at bottom = all C, all tied = all B
- Earned points = base_score * multiplier

## Related Specifications

- `features/ranking-multiplier.md` — Ranking and multiplier specification
- `api/scoring-api.md` — Scoring API endpoints

## User/Business Flow

```
After base scores calculated for all 5 teams in a match:
    ↓
Sort teams by base_score descending
    ↓
Assign ranks (with tie handling)
    ↓
Assign grades based on rank position
    ↓
Apply multiplier to base_score → earned_points
```

## How the Feature Works Internally

### Ranking Algorithm (`ranking_engine.py`)
```python
def rank_teams(scores: list[dict]) -> list[dict]:
    # Sort by base_score descending
    # Assign ranks: unique scores get unique ranks
    # Tied teams share the same rank
```

### Multiplier Assignment (`multiplier_calculator.py`)
```python
def assign_grade_and_multiplier(teams_ranked, config):
    for team in teams_ranked:
        if team is unique top (rank 1 alone):
            team.grade = "A"
            team.multiplier = config.multiplier_a  # default 3.0
        elif team is unique bottom (rank 5 alone):
            team.grade = "C"
            team.multiplier = config.multiplier_c  # default 1.0
        else:
            team.grade = "B"
            team.multiplier = config.multiplier_b  # default 2.0

    # Tie rules:
    # Tie at top → all get B (2x)
    # Tie at bottom → all get C (1x)
    # All tied → all get B (2x)

    # Calculate earned points
    for team in teams_ranked:
        team.earned_points = team.base_score * team.multiplier
```

### Tie-Breaking Logic
| Scenario | Result |
|----------|--------|
| 1 team unique top | Grade A (3x) |
| 2+ teams tied for top | All get Grade B (2x) |
| 1 team unique bottom | Grade C (1x) |
| 2+ teams tied for bottom | All get Grade C (1x) |
| All 5 teams same score | All get Grade B (2x) |

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/scoring_engine/ranking_engine.py` | 21 | Sort teams by score, assign ranks |
| `app/scoring_engine/multiplier_calculator.py` | 47 | Grade assignment + multiplier calculation |
| `app/services/scoring_service.py` | 367 | Pipeline: score → rank → multiply → save |

### Key Functions

- `rank_teams(scores)` → Ranked list with rank numbers
- `assign_grade_and_multiplier(teams, config)` → Teams with grades and earned_points
- `calculate_earned_points(base_score, multiplier)` → earned_points

## APIs/Endpoints Involved

Ranking/multiplier is triggered as part of:
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/scoring/calculate` | ORGANIZER | Score + rank + multiply |
| POST | `/api/v1/scoring/recalculate-all` | ORGANIZER | Full re-scoring |

## Database/Data Models Involved

Stored in `scores` table:
- `match_rank` — Rank position per match
- `grade` — Enum(A, B, C)
- `multiplier` — Numeric multiplier value
- `earned_points` — base_score * multiplier

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_multiplier.py` | Ranking, grade assignment, tie handling (17 tests) |

## Dependencies on Other Features

- **Base Scoring Engine** — Base scores are ranking inputs
- **Phase Normalization** — Earned points feed into normalization

## Step-by-Step Implementation Sequence

1. Create ranking_engine.py with sort + rank assignment
2. Create multiplier_calculator.py with grade logic
3. Implement tie-breaking rules
4. Integrate into scoring pipeline
5. Persist rank, grade, multiplier, earned_points to ScoreModel
6. Write unit tests for all tie scenarios
