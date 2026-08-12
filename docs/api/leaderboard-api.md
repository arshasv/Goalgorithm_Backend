# Leaderboard API

## Endpoint
`POST /api/v1/leaderboard/calculate`

## HTTP Method
POST

## Request JSON
```json
[
  {
    "team_id": "A",
    "phase1_score": 60.0,
    "technical_score": 19,
    "presentation_score": 19.2
  },
  {
    "team_id": "B",
    "phase1_score": 16.0,
    "technical_score": 17,
    "presentation_score": 11.47
  }
]
```

## Response JSON
```json
[
  {
    "rank": 1,
    "team_id": "A",
    "scores": {
      "ai_accuracy": 60.0,
      "technical": 19,
      "presentation": 19.2
    },
    "final_score": 98.2
  },
  {
    "rank": 2,
    "team_id": "B",
    "scores": {
      "ai_accuracy": 16.0,
      "technical": 17,
      "presentation": 11.47
    },
    "final_score": 44.47
  }
]
```

## Validation Rules
- `phase1_score`: float, 0–60
- `technical_score`: float, 0–20
- `presentation_score`: float, 0–20

## Error Responses

| Status | Scenario | error_code |
|---|---|---|
| 200 | Leaderboard calculated and stored | — |
| 400 | Score out of range | `LEADERBOARD_ERROR` |
| 422 | Schema validation failure | `VALIDATION_ERROR` |
| 500 | Unexpected server error | `INTERNAL_SERVER_ERROR` |

See [Error Responses](error-responses.md) for the full format.

## Feature Mapping
- [Leaderboard](../features/leaderboard.md)
