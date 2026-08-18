# Feature 04: Match Management

## Feature Overview

CRUD management of 32 knockout football matches with lifecycle state tracking (UPCOMING, LIVE, COMPLETED, CANCELLED, POSTPONED). Supports manual creation, external API import from api-sports.io, and cascade deletion of related data.

## Purpose & Requirements

- Create, read, update, delete matches
- Each match: match_number (1-32), home/away team names, scheduled time, freeze deadline, status
- Freeze deadline auto-calculated as 1 hour before kickoff
- External API integration for importing fixtures
- Cascade deletion removes related predictions, scores, results
- Match status drives prediction freeze and scoring triggers

## Related Specifications

- `features/match-management.md` — Match lifecycle specification
- `api/match-management-api.md` — Match management API endpoints
- `architecture/external_football_api_integration.md` — External API integration

## User/Business Flow

```
Organizer creates match → status=UPCOMING
    ↓
Freeze deadline passes → predictions locked
    ↓
Match played → Organizer enters result → status=COMPLETED
    ↓
Scores calculated → status=SCORED
```

## How the Feature Works Internally

### Freeze Deadline Calculation
```python
freeze_deadline = scheduled_at - timedelta(hours=1)
```

### External API Integration (`FootballAPIService`)
- `get_fixtures(date)` → Fetches fixtures from api-sports.io
- `get_fixture_result(fixture_id)` → Fetches match result
- Stores `external_api_id` for deduplication

### Match Lifecycle States
```
UPCOMING → LIVE → COMPLETED → RESULT_ENTERED → SCORED
                     ↓
               CANCELLED / POSTPONED
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/models/match.py` | 37 | MatchModel ORM with status enum |
| `app/repositories/match_repository.py` | 43 | Match queries, find by number, scheduled |
| `app/services/match_service.py` | 366 | Match CRUD, external sync, cascade delete |
| `app/services/football_api_service.py` | 178 | External API client (api-sports.io) |
| `app/api/match_routes.py` | 353 | Match CRUD endpoints |
| `app/api/external_matches_routes.py` | 179 | External API import/sync endpoints |
| `app/schemas/match_schema.py` | 49 | MatchCreate/Update/Response schemas |

### Key Classes & Functions

- `MatchService.create_match(data)` → Creates match with auto freeze_deadline
- `MatchService.get_all_matches(filters)` → List with status/date filters
- `MatchService.get_match_by_id(match_id)` → Single match
- `MatchService.update_match(match_id, data)` → Update match
- `MatchService.delete_match(match_id)` → Delete with cascade
- `MatchService.get_upcoming_matches()` → UPCOMING status matches
- `FootballAPIService.get_fixtures(date)` → External fixtures
- `FootballAPIService.sync_result(match_id)` → Sync external result

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/matches` | ORGANIZER | Create match |
| GET | `/api/v1/matches` | Any | List matches |
| GET | `/api/v1/matches/{id}` | Any | Get match |
| PUT | `/api/v1/matches/{id}` | ORGANIZER | Update match |
| DELETE | `/api/v1/matches/{id}` | ORGANIZER | Delete match |
| GET | `/api/v1/matches/upcoming` | Any | Upcoming matches |
| POST | `/api/v1/external-matches/import` | ORGANIZER | Import from API |
| POST | `/api/v1/external-matches/sync-results` | ORGANIZER | Sync results |

## Database/Data Models Involved

### `matches` Table (`MatchModel`)
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| match_number | Integer | unique, CHECK 1-32 |
| home_team_name | String | not null |
| away_team_name | String | not null |
| scheduled_at | DateTime | not null |
| freeze_deadline | DateTime | not null |
| status | Enum(MatchStatus) | default UPCOMING |
| round | String | nullable |
| external_api_id | String | nullable, indexed |
| external_sync_status | Enum | default PENDING |

## Error Handling

| Scenario | HTTP Code |
|----------|-----------|
| Duplicate match_number | 409 DUPLICATE_MATCH |
| Match not found | 404 NOT_FOUND |
| Non-organizer access | 403 FORBIDDEN |
| External API timeout | 502 BAD_GATEWAY |

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_match_management.py` | Duplicate number, status update, scoring (3 tests) |
| `tests/test_football_api.py` | External API fetch, errors (4 tests) |

## Dependencies on Other Features

- **Team Management** — Teams referenced as home/away
- **Prediction Management** — Freeze deadline controls prediction window
- **Scoring Engine** — Match completion triggers scoring
- **Result Management** — Results attached to matches

## Step-by-Step Implementation Sequence

1. Create MatchModel with status enum and constraints
2. Create MatchRepository with CRUD queries
3. Create MatchService with business logic
4. Create Match routes with all endpoints
5. Implement freeze deadline auto-calculation
6. Implement cascade deletion
7. Create FootballAPIService for external API
8. Create external matches routes
9. Run Alembic migration
10. Write tests
