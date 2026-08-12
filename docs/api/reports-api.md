# Score Reports API

This document details the API endpoints supporting the **Score Reports & Normalization Analysis** feature.
These endpoints are restricted to the **Organizer** role by default.

## `GET /api/v1/reports/team-breakdown`

Returns the detailed scoring journey for every team, tracing from raw inputs to the final leaderboard score.

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "team_id": "team_a",
      "team_name": "Team A",
      "journey": {
        "phase_1_ai": {
          "raw_score": 45,
          "max_raw_score": 60,
          "normalized_score": 15,
          "max_normalized_score": 20
        },
        "phase_2_technical": {
          "raw_score": 42,
          "max_raw_score": 50,
          "normalized_score": 20,
          "max_normalized_score": 20
        },
        "phase_3_presentation": {
          "rounds": [
            {
              "round_name": "Round 1",
              "raw_average": 40.88,
              "grade": "A",
              "multiplier": 3,
              "weighted_score": 122.64
            }
          ],
          "combined_raw": 192.64,
          "combined_max": 300,
          "normalized_score": 12.84,
          "max_normalized_score": 20
        },
        "final_score": 47.84,
        "max_final_score": 100
      }
    }
  ]
}
```

## `GET /api/v1/reports/rank-impact`

Returns a before/after comparison of team rankings to show how multipliers and normalization impact final standings.

**Response:**
```json
{
  "status": "success",
  "data": {
    "before_multipliers": [
      { "team_name": "Team A", "score": 40.8, "rank": 1 },
      { "team_name": "Team D", "score": 35.1, "rank": 2 },
      { "team_name": "Team C", "score": 34.6, "rank": 3 }
    ],
    "after_multipliers": [
      { "team_name": "Team A", "score": 122.6, "rank": 1 },
      { "team_name": "Team D", "score": 70.2, "rank": 2 },
      { "team_name": "Team C", "score": 69.2, "rank": 3 }
    ],
    "rank_movements": [
      {
        "team_name": "Goal Jyolsyan",
        "raw_rank": 2,
        "final_rank": 1,
        "movement": 1
      }
    ]
  }
}
```

## `GET /api/v1/reports/phase-analysis`

Returns contribution data showing how each evaluation phase builds the final score. Useful for stacked bar charts.

**Response:**
```json
{
  "status": "success",
  "data": {
    "composition_weights": {
      "ai_prediction": 60,
      "technical": 20,
      "presentation": 20
    },
    "teams": [
      {
        "team_name": "Team A",
        "contributions": {
          "ai_prediction": 15,
          "technical": 20,
          "presentation": 12.84
        }
      }
    ]
  }
}
```

## `GET /api/v1/reports/multiplier-impact`

Highlights how grade-based multipliers alter team standings specifically for the presentation round.

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "team_name": "Team A",
      "grade": "A",
      "multiplier": 3,
      "raw_score": 40.88,
      "weighted_score": 122.64,
      "gain": 81.76
    }
  ]
}
```
