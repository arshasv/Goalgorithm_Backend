# Leaderboard Architecture

## Data Flow
```
Client
    │
    │  POST /api/v1/leaderboard/calculate
    │  Body: [{team_id, phase1_score, technical_score, presentation_score}]
    │
    ▼
API Layer (leaderboard_routes.py)
    │  → validates with LeaderboardEntry schema
    │
    ▼
ScoringService.compute_and_save_leaderboard()
    │  → calls calculate_leaderboard() (pure function)
    │  → persists results via LeaderboardModel
    │
    ▼
Leaderboard Service
    │  calculate_leaderboard(scores)
    │  ├── Validates score ranges (0–60, 0–20, 0–20)
    │  │   → raises LeaderboardError if out of range
    │  ├── Computes final_score = sum of phases
    │  ├── Sorts by final_score descending
    │  ├── Applies tie-breaking (ai_accuracy → technical → presentation)
    │  └── Assigns ranks with tie handling
    │
    ▼
Response
    ├── Success: ranked leaderboard array (200)
    ├── Score out of range: 400 LEADERBOARD_ERROR
    └── Schema invalid: 422 VALIDATION_ERROR
```

## Error Scenarios

| Scenario | Error Code | HTTP |
|---|---|---|
| Score out of valid range | `LEADERBOARD_ERROR` | 400 |
| Schema violation | `VALIDATION_ERROR` | 422 |
| Unexpected server error | `INTERNAL_SERVER_ERROR` | 500 |

## Related Documentation
- [Feature: Leaderboard](../features/leaderboard.md)
- [API: Leaderboard API](../api/leaderboard-api.md)
- [Error Handling Architecture](error-handling-architecture.md)
