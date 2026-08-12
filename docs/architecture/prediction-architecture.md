# Prediction Architecture

## Data Flow
```
Team Client
    │
    │  POST /api/v1/predictions
    │  Body: PredictionSubmission JSON
    │
    ▼
API Layer (prediction_routes.py)
    │  → validates with PredictionSubmission schema
    │
    ▼
Schema Validation (Pydantic v2)
    │  → field validators: winner enum, first_goal enum, ranges, non-empty list
    │
    ▼
PredictionService.save_prediction()
    │  → checks for idempotency_key (returns 200 duplicate if matched)
    │  → checks for existing prediction (team_id + match_id unique)
    │  → overwrites existing prediction if new data is submitted
    │  → persists via PredictionRepository
    │
    ▼
Response
    ├── New prediction accepted: {"status": "accepted", ...} (200)
    ├── Duplicate idempotent key: {"status": "duplicate", ...} (200)
    ├── Schema invalid: 422 VALIDATION_ERROR
    └── Unexpected error: 500 INTERNAL_SERVER_ERROR
```

## Route Responsibility
- `prediction_routes.py`: receive → validate → call service → return response
- No scoring logic in routes
- No error handling in routes — exceptions propagate to global handlers

## Error Scenarios

| Scenario | Error Code | HTTP |
|---|---|---|
| Idempotent Duplicate | `{"status": "duplicate"}` | 200 |
| Schema violation | `VALIDATION_ERROR` | 422 |
| Missing team or match resource | `BAD_REQUEST` | 400 |
| Unexpected server error | `INTERNAL_SERVER_ERROR` | 500 |

## Related Documentation
- [Feature: Prediction Management](../features/prediction-management.md)
- [API: Prediction API](../api/prediction-api.md)
- [Error Handling Architecture](error-handling-architecture.md)
