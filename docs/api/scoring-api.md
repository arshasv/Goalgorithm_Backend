# Scoring API

## Endpoint
`POST /api/v1/calculate-match-score`

## HTTP Method
POST

## Request JSON
```json
{
  "prediction": { ... },
  "actual_result": { ... }
}
```

## Response JSON
```json
{
  "team_id": "team-001",
  "match_id": "match-001",
  "breakdown": {
    "winner_score": 5,
    "scoreline_score": 10,
    "probability_score": 5,
    "player_score": 5
  },
  "base_score": 25
}
```

## Validation Rules
- `prediction` validated against `PredictionSubmission` schema
- `actual_result` validated against `ActualResultSubmission` schema

## Error Responses

| Status | Scenario | error_code |
|---|---|---|
| 200 | Score calculated and stored | — |
| 400 | Missing prediction or actual result | `INVALID_COMPETITION_STATE` |
| 409 | Duplicate score entry | `DUPLICATE_ENTRY` |
| 422 | Schema validation failure | `VALIDATION_ERROR` |
| 500 | Unexpected server error | `INTERNAL_SERVER_ERROR` |

See [Error Responses](error-responses.md) for the full format.

## Feature Mapping
- [Base Scoring Engine](../features/base-scoring-engine.md)
- [Ranking & Multiplier](../features/ranking-multiplier.md)

---

## Endpoint
`POST /api/v1/technical-score`

## HTTP Method
POST

## Request JSON
```json
{
  "team_id": "A",
  "code_quality": 5,
  "backend_quality": 5,
  "teamwork": 4,
  "ai_explanation": 5
}
```

## Response JSON
```json
{
  "team_id": "A",
  "breakdown": {
    "code_quality": 5,
    "backend_quality": 5,
    "teamwork": 4,
    "ai_explanation": 5
  },
  "technical_score": 19
}
```

## Validation Rules
- Each sub-score: integer, 0–5 inclusive

## Error Responses

| Status | Scenario | error_code |
|---|---|---|
| 200 | Technical score calculated | — |
| 422 | Schema validation failure | `VALIDATION_ERROR` |
| 500 | Unexpected server error | `INTERNAL_SERVER_ERROR` |

## Feature Mapping
- [Technical Evaluation](../features/technical-evaluation.md)

---

## Endpoint
`POST /api/v1/presentation-score`

## HTTP Method
POST

## Request JSON
```json
[
  {
    "team_id": "A",
    "ai_explanation_score": 19,
    "qa_score": 14,
    "delivery_score": 15
  }
]
```

## Response JSON
```json
[
  {
    "team_id": "A",
    "raw_score": 48,
    "rank": 1,
    "grade": "A",
    "multiplier": 3,
    "presentation_score": 19.2
  }
]
```

## Validation Rules
- `ai_explanation_score`: 0–20
- `qa_score`: 0–15
- `delivery_score`: 0–15

## Error Responses

| Status | Scenario | error_code |
|---|---|---|
| 200 | Presentation scores calculated and stored | — |
| 422 | Schema validation failure | `VALIDATION_ERROR` |
| 500 | Unexpected server error | `INTERNAL_SERVER_ERROR` |

## Feature Mapping
- [Presentation Evaluation](../features/presentation-evaluation.md)
