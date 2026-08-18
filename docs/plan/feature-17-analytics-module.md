# Feature 17: Analytics Module

## Feature Overview

Read-only analytics dashboard providing data-driven insights to organizers and team leaders. Covers 5 analytics sections: overview, model performance, presentation, technical, and judge analytics. Visibility-controlled per team leader role. Never modifies scoring or competition data.

## Purpose & Requirements

- Read-only: analytics NEVER modify scoring/leaderboard data
- Sections: overview, models, presentation, judges, team-specific
- Granular visibility per section (via LeaderboardVisibilityModel)
- Anonymous mode for team leaders (optional)
- Aggregation from existing scoring/leaderboard data
- Source of truth: Phase 1 from scoring engine, Phase 2 from technical_evaluations, Phase 3 from presentation_scores

## Related Specifications

- `features/ANALYTICS_MODULE.md` — Complete analytics spec (862 lines)
- `features/ANALYTICS.md` — Analytics architecture (430 lines)
- `api/analytics-api.md` — Analytics API endpoints

## How the Feature Works Internally

### Analytics Pipeline
```
READ existing data (scores, evaluations, leaderboard)
    ↓
PROCESS (aggregate, calculate averages, rank)
    ↓
VISUALIZE (return structured JSON for frontend charts)
    ↓
NEVER: READ → MODIFY → SAVE SCORES
```

### Analytics Sections

#### 1. Overview
```python
def get_overview():
    return {
        "total_teams": count(TeamModel),
        "top_team": get_rank_1_from_leaderboard(),
        "average_phase1": avg(leaderboard.phase1_score),
        "average_technical": avg(leaderboard.technical_score),
        "average_presentation": avg(leaderboard.presentation_score),
        "average_final": avg(leaderboard.final_score),
    }
```

#### 2. Model Analytics
```python
def get_model_analytics():
    for team in teams:
        submissions = get_submissions(team.id)
        evaluation = get_evaluation(team.id)
        yield {
            "team_id": team.id,
            "model_name": submissions.latest.model_name,
            "accuracy": evaluation.overall_accuracy,
            "total_ai_score": evaluation.final_ai_score,
        }
```

#### 3. Presentation Analytics
```python
def get_presentation_analytics():
    for team in teams:
        scores = get_presentation_scores(team.id)
        yield {
            "team_id": team.id,
            "criteria_averages": {
                "ai_explanation": avg(scores.ai),
                "qa": avg(scores.qa),
                "delivery": avg(scores.delivery),
            },
            "strongest": max_criteria,
            "weakest": min_criteria,
        }
```

#### 4. Judge Analytics
```python
def get_judge_analytics():
    for judge in judges:
        scores = get_judge_scores(judge.id)
        yield {
            "judge_name": judge.name,
            "total_evaluations": len(scores),
            "average_scores": avg_per_criteria,
        }
```

#### 5. Team-Specific Analytics
```python
def get_team_analytics(team_id):
    return {
        "scores_breakdown": get_all_scores(team_id),
        "leaderboard_entry": get_leaderboard(team_id),
        "strengths": analyze_strengths(team_id),
        "weaknesses": analyze_weaknesses(team_id),
    }
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/services/analytics_service.py` | 452 | All analytics aggregation logic |
| `app/repositories/analytics_repository.py` | 58 | Analytics data queries |
| `app/schemas/analytics_schema.py` | 89 | Response schemas |
| `app/api/analytics_routes.py` | 122 | Analytics endpoints with visibility checks |

### Key Functions

- `AnalyticsService.get_overview()` → OverviewResponse
- `AnalyticsService.get_model_analytics()` → list[ModelAnalytics]
- `AnalyticsService.get_presentation_analytics()` → PresentationResponse
- `AnalyticsService.get_judge_analytics()` → list[JudgeAnalytics]
- `AnalyticsService.get_team_analytics(team_id)` → TeamAnalytics
- `check_analytics_visibility(section, db, user)` → Raise 403 if hidden

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/analytics/overview` | Visible* | Overview stats |
| GET | `/api/v1/analytics/models` | Visible* | Model analytics |
| GET | `/api/v1/analytics/presentation` | Visible* | Presentation analytics |
| GET | `/api/v1/analytics/judges` | Visible* | Judge analytics |
| GET | `/api/v1/analytics/team/{team_id}` | Any | Team-specific analytics |

*Visibility checked against LeaderboardVisibilityModel for TEAM_LEADER role.

## Database/Data Models Involved

Reads from (never writes to):
- `leaderboards` — Final scores
- `scores` — Per-match scores
- `technical_evaluations` — Phase 2 data
- `presentation_evaluations` — Phase 3 data
- `model_submissions` — Model info
- `model_evaluations` — Model performance
- `judges` — Judge info

## Error Handling

| Scenario | HTTP Code |
|----------|-----------|
| Analytics hidden for team leader | 403 FORBIDDEN |
| Analytics master toggle off | 403 ANALYTICS_DISABLED |
| Team not found | 404 NOT_FOUND |

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_analytics.py` | All analytics endpoints (9 tests) |

## Dependencies on Other Features

- **Leaderboard** — Final score data
- **Scoring Engine** — Per-match scores
- **Technical Evaluation** — Phase 2 data
- **Presentation Evaluation** — Phase 3 data
- **Model Submission** — Model info
- **Model Evaluation** — Performance metrics
- **Leaderboard Visibility** — Section access control

## Step-by-Step Implementation Sequence

1. Create AnalyticsRepository with data queries
2. Create Pydantic response schemas
3. Create AnalyticsService with all aggregation functions
4. Create Analytics routes with visibility checks
5. Implement visibility enforcement
6. Implement each analytics section
7. Write tests
