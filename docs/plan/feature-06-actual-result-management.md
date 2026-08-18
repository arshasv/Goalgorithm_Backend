# Feature 06: Actual Result Management

## Feature Overview

Organizer-only submission of actual match results. Stores ground-truth data used as reference for scoring predictions. Validates winner against scoreline, prevents duplicate results, and updates match status.

## Purpose & Requirements

- Organizer enters actual result after match concludes
- Validate winner field against final score
- One result per match (prevent duplicates)
- Store player-level actual performance data
- Update match status to COMPLETED on result entry

## Related Specifications

- `features/actual-result-management.md` — Result input specification
- `api/scoring-api.md` — Result-related endpoints

## User/Business Flow

```
Organizer → POST /results → {match_id, actual_winner, final_score, player_results}
    ↓
Validate match exists and not already has result
    ↓
Validate winner matches scoreline
    ↓
Save ActualResultModel + PlayerActualModels
    ↓
Update match.status = COMPLETED
    ↓
Return result
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/models/actual_result.py` | 65 | ActualResultModel + PlayerActualModel ORM |
| `app/services/result_service.py` | 100 | Result submission, status update |
| `app/api/result_routes.py` | 35 | Result endpoints |
| `app/schemas/actual_result_schema.py` | 68 | ActualResultSubmission schema |

### Key Classes & Functions

- `ResultService.submit_result(data)` → Save result + update match status
- `ResultService.get_result_by_match(match_id)` → Get result for match
- `ActualResultSubmission` (Pydantic) — Validates result payload
- `PlayerResult` (Pydantic) — Player actual performance

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/results` | ORGANIZER | Submit actual result |
| GET | `/api/v1/results/match/{match_id}` | Any | Get match result |
| GET | `/api/v1/results` | ORGANIZER | List all results |

## Database/Data Models Involved

### `actual_results` Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| match_id | UUID | FK → matches.id, unique |
| actual_winner | Enum(Winner) | not null |
| actual_home_goals, actual_away_goals | Integer | not null, CHECK >= 0 |
| total_goals | Integer | not null |
| home_clean_sheet | Boolean | default False |
| btts | Boolean | default False |
| first_team_to_score | Enum(FirstGoalTeam) | nullable |
| result_source | String | default MANUAL |

### `player_actuals` Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| actual_result_id | UUID | FK → actual_results.id, CASCADE |
| player_name | String | not null |
| actual_goals | Integer | CHECK >= 0 |
| actual_assists | Integer | default 0 |

## Error Handling

| Scenario | HTTP Code |
|----------|-----------|
| Duplicate result for match | 400 ALREADY_EXISTS |
| Winner contradicts scoreline | 422 VALIDATION_ERROR |
| Match not found | 404 NOT_FOUND |
| Non-organizer access | 403 FORBIDDEN |

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_full_competition_flow.py` | Result submission in flow |

## Dependencies on Other Features

- **Match Management** — match_id reference, status update
- **Scoring Engine** — Results used as scoring reference

## Step-by-Step Implementation Sequence

1. Create ActualResultModel + PlayerActualModel ORM
2. Create ActualResultSubmission schema with validation
3. Create ResultService with submission logic
4. Create Result routes
5. Implement winner vs scoreline validation
6. Implement duplicate prevention
7. Implement match status update
8. Run Alembic migration
9. Write tests
