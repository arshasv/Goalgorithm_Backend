# Feature 20: External Football API Integration

## Feature Overview

Integration with api-sports.io external football data provider. Allows organizers to import match fixtures by date and sync match results automatically. Tracks external API IDs for deduplication and sync status.

## Purpose & Requirements

- Import match fixtures from external API by date
- Sync match results (actual scores) from external API
- Store external_api_id for deduplication
- Track external_sync_status per match
- Rate limiting and error handling for API calls
- API key stored in .env, never exposed to frontend

## Related Specifications

- `architecture/external_football_api_integration.md` — External API integration design (120 lines)

## How the Feature Works Internally

### API Client (`FootballAPIService`)
```python
class FootballAPIService:
    def __init__(self):
        self.api_key = settings.FOOTBALL_API_KEY
        self.base_url = settings.FOOTBALL_API_BASE_URL
        self.headers = {"x-apisports-key": self.api_key}

    async def get_fixtures(self, date: str) -> list[dict]:
        # GET /fixtures?date={date}
        # Returns list of fixture dictionaries

    async def get_fixture_result(self, fixture_id: int) -> dict:
        # GET /fixtures?id={fixture_id}
        # Returns match result with scores
```

### Import Flow
```
Organizer → POST /external-matches/import {date: "2026-07-15"}
    ↓
FootballAPIService.get_fixtures(date)
    ↓
Map external fixtures to internal MatchModel format
    ↓
Check external_api_id for duplicates (skip if exists)
    ↓
Save matches with external_api_id + external_sync_status=PENDING
```

### Sync Results Flow
```
Organizer → POST /external-matches/sync-results {match_ids: [...]}
    ↓
For each match:
    FootballAPIService.get_fixture_result(match.external_api_id)
    ↓
Map external result to ActualResultModel format
    ↓
Save actual result
    ↓
Update external_sync_status = SYNCED
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/services/football_api_service.py` | 178 | API client with rate limiting |
| `app/api/external_matches_routes.py` | 179 | Import/sync endpoints |

### Key Functions

- `FootballAPIService.get_fixtures(date)` → list of fixtures
- `FootballAPIService.get_fixture_result(fixture_id)` → result dict
- `FootballAPIService._make_request(method, endpoint)` → Rate-limited HTTP

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/external-matches/import` | ORGANIZER | Import fixtures by date |
| POST | `/api/v1/external-matches/sync-results` | ORGANIZER | Sync match results |

## Database/Data Models Involved

Adds to `matches` table:
- `external_api_id` — External fixture ID (nullable, indexed)
- `external_sync_status` — Enum(PENDING, SYNCED, FAILED)

Adds to `actual_results` table:
- `result_source` — String (default "MANUAL")

## Configuration/Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FOOTBALL_API_KEY` | Yes | api-sports.io API key |
| `FOOTBALL_API_BASE_URL` | Yes | API base URL |

## Error Handling

| Scenario | HTTP Code |
|----------|-----------|
| API timeout | 502 BAD_GATEWAY |
| API key invalid | 502 BAD_GATEWAY |
| Duplicate external_api_id | Silently skipped |

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_football_api.py` | Fixture fetch, errors (4 tests, mocked) |

## Dependencies on Other Features

- **Match Management** — Imports create MatchModel records
- **Actual Result Management** — Synced results create ActualResultModel

## Step-by-Step Implementation Sequence

1. Create FootballAPIService with httpx client
2. Implement fixture fetching with rate limiting
3. Implement result syncing
4. Add external_api_id and external_sync_status to MatchModel
5. Create import/sync routes
6. Implement deduplication
7. Run Alembic migration
8. Write tests with mocked API responses
