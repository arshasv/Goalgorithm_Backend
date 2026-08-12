# Prediction API

## Endpoint
`POST /api/v1/predictions`

## HTTP Method
POST

## Request JSON
```json
{
  "team_id": "team-001",
  "match_id": "match-045",
  "submission_id": "sub-a-01",
  "match_prediction": {
    "predicted_winner": "home",
    "predicted_scoreline": {
      "home_team_goals": 2,
      "away_team_goals": 0
    },
    "probabilities": {
      "home_win_probability": 65.0,
      "draw_probability": 22.0,
      "away_win_probability": 13.0
    },
    "clean_sheet_probability": {
      "home_team": 55.0,
      "away_team": 10.0
    },
    "first_goal_team": "home",
    "both_teams_to_score_probability": 35.0,
    "total_goals_prediction": 2
  },
  "player_predictions": [
    {
      "player_id": "p-arg-1",
      "player_name": "Lionel Messi",
      "goal_probability": 55.0,
      "predicted_goals": 1,
      "assist_probability": 30.0
    }
  ]
}
```

## Response JSON
```json
{
  "status": "accepted",
  "team_id": "team-001",
  "match_id": "match-045"
}
```

## Validation Rules
- `predicted_winner`: enum — `home`, `away`, `draw`
- `first_goal_team`: enum — `home`, `away`, `none`
- All probabilities: float, 0–100
- Scoreline goals: integer, ≥ 0
- `player_predictions`: non-empty array
- All ID fields: non-empty strings

## Error Responses

| Status | Scenario | error_code |
|---|---|---|
| 200 | Prediction accepted and stored (or duplicate idempotency) | — |
| 400 | Bad Request (e.g., Team not found) | `BAD_REQUEST` |
| 422 | Schema validation failure | `VALIDATION_ERROR` |
| 500 | Unexpected server error | `INTERNAL_SERVER_ERROR` |

See [Error Responses](error-responses.md) for the full format.

## Feature Mapping
- [Prediction Management](../features/prediction-management.md)
- [Error Responses](error-responses.md)
