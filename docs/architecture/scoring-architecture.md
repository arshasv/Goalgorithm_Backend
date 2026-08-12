# Scoring Architecture

## Data Flow
```
Client
    │
    │  POST /api/v1/calculate-match-score
    │  Body: {prediction, actual_result}
    │
    ▼
API Layer (scoring_routes.py)
    │  → validates with MatchScoreRequest schema
    │
    ▼
ScoringService.calculate_and_save_match_score()
    │  → calls calculate_base_score() (pure function)
    │  → persists score via ScoreModel
    │  → raises on IntegrityError (handled globally)
    │
    ▼
Scoring Engine
    │  calculate_base_score(prediction, actual_result, actual_probabilities)
    │  ├── calculate_winner_score      → 0 or 5
    │  ├── calculate_scoreline_score   → 0, 5, or 10
    │  ├── calculate_probability_score → 0 or 5
    │  └── calculate_player_score      → 0, 2, or 5
    │
    ▼
Response
    ├── Success: breakdown + base_score (200)
    ├── Duplicate score: 409 DUPLICATE_ENTRY
    └── Unexpected error: 500 INTERNAL_SERVER_ERROR
```

## Scoring Engine Design
- Pure functions only — no I/O, no database, no HTTP
- Deterministic: same inputs → same outputs
- Fully testable with no mocking required

## Error Scenarios

| Scenario | Error Code | HTTP |
|---|---|---|
| Duplicate score entry (team + match) | `DUPLICATE_ENTRY` | 409 |
| Foreign key violation | `FOREIGN_KEY_VIOLATION` | 400 |
| Schema violation | `VALIDATION_ERROR` | 422 |
| Unexpected server error | `INTERNAL_SERVER_ERROR` | 500 |

## Related Documentation
- [Feature: Base Scoring Engine](../features/base-scoring-engine.md)
- [Feature: Ranking & Multiplier](../features/ranking-multiplier.md)
- [Feature: Phase Normalization](../features/phase-normalization.md)
- [API: Scoring API](../api/scoring-api.md)
- [Error Handling Architecture](error-handling-architecture.md)
