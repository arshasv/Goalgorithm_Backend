# Base Scoring Engine

## Purpose
Compute each team's Base Score for a match by evaluating four prediction dimensions against the actual result. This is the core automated scoring logic.

## User / Actor
System (automated — triggered by scoring API call)

## Input
- Team prediction JSON (winner, scoreline, probabilities, player predictions)
- Actual result JSON (winner, scoreline, player actuals)
- Actual probabilities for comparison

## Processing Workflow

### Dimension 1 — Match Winner (max 5 pts)
- Compare `predicted_winner` vs `actual_winner`
- Correct = 5 pts, incorrect = 0 pts

### Dimension 2 — Scoreline Exactness (max 10 pts)
- Compare predicted scoreline vs actual scoreline
- Exact match = 10 pts
- Correct goal margin + correct direction = 5 pts
- Otherwise = 0 pts

### Dimension 3 — Probability Accuracy (max 5 pts)
- Compare 5 probability fields against actual values
- All within ±15% absolute threshold = 5 pts
- Any outside threshold = 0 pts

### Dimension 4 — Player Performance (max 5 pts)
- Compare predicted goals vs actual goals per player
- Exact match (diff=0) = 5 pts per player
- Close (diff=1) = 2 pts per player
- Wrong (diff≥2) = 0 pts per player
- Average across all predicted players → map to tier (≥4.0 = 5 pts, ≥2.0 = 2 pts, else 0 pts)

### Aggregation
- Base Score = winner + scoreline + probability + player scores
- Capped at max 25 per match

## Validation Rules
- (none — engine is pure computation, inputs pre-validated by schemas)

## Output
```json
{
  "team_id": "...",
  "match_id": "...",
  "breakdown": {
    "winner_score": 5,
    "scoreline_score": 10,
    "probability_score": 5,
    "player_score": 5
  },
  "base_score": 25
}
```

## Error States
| Scenario | Error Code | HTTP |
|---|---|---|
| Duplicate score entry (team + match) | `DUPLICATE_ENTRY` | 409 |
| Foreign key violation (missing prediction or result) | `FOREIGN_KEY_VIOLATION` | 400 |
| Schema violation | `VALIDATION_ERROR` | 422 |
| Unexpected error | `INTERNAL_SERVER_ERROR` | 500 |

## Related APIs
- `POST /api/v1/calculate-match-score`

## Related Database Entities
- `scores` — stores dimension points and base_score per team per match
