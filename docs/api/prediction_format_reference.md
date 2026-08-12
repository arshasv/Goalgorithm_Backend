# Prediction JSON Format Reference

This document outlines the exact JSON format expected by the GOALGORITHM Prediction API (`POST /api/v1/predictions`). Teams generating predictions via ML models should format their output to strictly match this schema.

## Complete Sample JSON

```json
{
  "team_id": "A",
  "match_id": "123e4567-e89b-12d3-a456-426614174000",
  "submission_id": "sub-9876",
  "match_prediction": {
    "predicted_winner": "home",
    "predicted_scoreline": {
      "home_team_goals": 2,
      "away_team_goals": 1
    },
    "probabilities": {
      "home_win_probability": 60.5,
      "draw_probability": 25.0,
      "away_win_probability": 14.5
    },
    "clean_sheet_probability": {
      "home_team": 30.0,
      "away_team": 15.5
    },
    "first_goal_team": "home",
    "both_teams_to_score_probability": 55.0,
    "total_goals_prediction": 3,
    "goal_scorers": {
      "home": [
        "Lionel Messi",
        "Kylian Mbappe"
      ],
      "away": [
        "Cristiano Ronaldo"
      ]
    }
  },
  "player_predictions": [
    {
      "player_id": "p123",
      "player_name": "Lionel Messi",
      "goal_probability": 45.5,
      "predicted_goals": 1,
      "assist_probability": 30.0
    }
  ]
}
```

## Schema Details

### Root Object
| Field | Type | Required | Validation Rules |
|---|---|---|---|
| `team_id` | string | **Yes** | Min length: 1 |
| `match_id` | string | **Yes** | Min length: 1. Must match an active scheduled match. |
| `submission_id` | string | **Yes** | Min length: 1. Used for tracking the submission event. |
| `match_prediction` | object | **Yes** | See `MatchPrediction` below. |
| `player_predictions` | array | **Yes** | Must contain at least 1 item. See `PlayerPrediction` below. |

### `MatchPrediction`
| Field | Type | Required | Validation Rules |
|---|---|---|---|
| `predicted_winner` | string | **Yes** | Must be exactly: `"home"`, `"away"`, or `"draw"`. Case-insensitive but normalized to lowercase. |
| `predicted_scoreline` | object | **Yes** | Must contain `home_team_goals` (int, ≥ 0) and `away_team_goals` (int, ≥ 0). |
| `probabilities` | object | **Yes** | Must contain `home_win_probability`, `draw_probability`, `away_win_probability` (floats, 0 to 100). |
| `clean_sheet_probability`| object | **Yes** | Must contain `home_team` and `away_team` (floats, 0 to 100). |
| `first_goal_team` | string | **Yes** | Must be exactly: `"home"`, `"away"`, or `"none"`. |
| `both_teams_to_score_probability` | float | **Yes** | Range: 0 to 100. |
| `total_goals_prediction` | int | **Yes** | Must be ≥ 0. |
| `goal_scorers` | object | No | Contains `home` and `away` arrays of strings (player names). **CRITICAL:** Length of `home` array MUST exactly equal `home_team_goals`. Length of `away` array MUST exactly equal `away_team_goals`. |

### `PlayerPrediction`
| Field | Type | Required | Validation Rules |
|---|---|---|---|
| `player_id` | string | **Yes** | Min length: 1 |
| `player_name` | string | **Yes** | Min length: 1 |
| `goal_probability` | float | **Yes** | Range: 0 to 100. |
| `predicted_goals` | int | **Yes** | Must be ≥ 0. |
| `assist_probability` | float | **Yes** | Range: 0 to 100. |
