# Analytics API

The Analytics API provides read-only endpoints to power the Analytics visualizations on the frontend. It is powered by the `AnalyticsService` which queries `AnalyticsRepository`.

## Endpoints

### 1. `GET /api/v1/analytics/overview`
Returns high-level insights for the competition overview cards.

**Response**:
```json
{
  "total_teams": 5,
  "top_team": {
    "team_name": "Team A",
    "final_score": 85.5
  },
  "average_scores": {
    "phase1_average": 45.0,
    "technical_average": 15.0,
    "presentation_average": 12.0,
    "final_average": 72.0
  }
}
```

### 2. `GET /api/v1/analytics/models`
Returns performance and prediction accuracy for AI models.

**Response**:
```json
[
  {
    "team": "Team A",
    "model_information": {
      "model_name": "v1.model",
      "file_name": "v1.model",
      "upload_date": "2026-06-15T10:00:00Z",
      "is_active": true
    },
    "performance": {
      "matches_predicted": 5,
      "total_ai_score": 95.5,
      "average_match_score": 19.1,
      "accuracy_percentage": 80.0,
      "ranking_trend": [
        {"match_number": 1, "match_label": "A vs B", "rank": 1, "score": 22.0}
      ]
    }
  }
]
```

### 3. `GET /api/v1/analytics/presentation`
Returns analysis on presentation rounds and criteria evaluation.

**Response**:
```json
{
  "teams": [
    {
      "team": "Team A",
      "strongest": { "criterion": "Feature Engineering", "score": 14.5, "max_score": 15, "pct": 96.6 },
      "weakest": { "criterion": "Q&A", "score": 3.0, "max_score": 5, "pct": 60.0 },
      "criteria_averages": [
        { "criterion": "Problem Understanding", "avg_score": 9.0, "max_score": 10 }
      ]
    }
  ],
  "criteria_rankings": [
    {
      "criterion": "Feature Engineering",
      "rankings": [
        { "team": "Team A", "avg_score": 14.5, "max_score": 15 }
      ],
      "best_team": "Team A",
      "weakest_team": "Team B"
    }
  ]
}
```

### 4. `GET /api/v1/analytics/team/{team_id}`
Returns individual detailed analytics for a single team.

**Response**:
```json
{
  "team_name": "Team A",
  "scores_breakdown": {
    "total_predictions": 5,
    "correct_predictions": 4,
    "average_score": 19.1,
    "winner_accuracy_pct": 80.0
  },
  "leaderboard": {
    "rank": 1,
    "phase1_score": 55.0,
    "technical_score": 18.0,
    "presentation_score": 12.5,
    "final_score": 85.5
  },
  "strengths": [
    { "criterion": "Feature Engineering", "score": 14.5, "max_score": 15, "pct": 96.6 }
  ],
  "weaknesses": [
    { "criterion": "Q&A", "score": 3.0, "max_score": 5, "pct": 60.0 }
  ]
}
```

## Security
All endpoints verify granular visibility via the `LeaderboardVisibilityModel`. For Team Leaders, specific analytics flags (`show_model_analytics`, `show_prediction_analytics`, `show_presentation_analytics`, `show_technical_analytics`, `show_overall_comparison`) are respected. Oragnizers bypass these checks.
