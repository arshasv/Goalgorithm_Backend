# External Football API Integration Architecture

## 1. Current System Flow
The current system operates via a manual match management process and pipeline:
1. **Manual Match Creation**: Organizers manually create upcoming matches or upload an Excel schedule in the Organizer Dashboard.
2. **Predictions**: Team Leaders submit their predictions manually or via JSON against the generated internal `match_id`s before the freeze deadline.
3. **Actual Result Upload**: After the match finishes, Organizers manually input the final score, winner, and goal scorers into the match management dashboard.
4. **Scoring Engine**: The Organizer triggers the Scoring Engine, which compares the actual results to the submitted predictions across winner, scoreline, probability, and player metrics.
5. **Leaderboard**: The normalized base points are saved to the database, and the leaderboard automatically recalculates to reflect the updated standings.

## 2. New Proposed API Flow
The integration of an external football data provider will automate the match creation and result input pipeline:
1. **Organizer Selects Date**: Organizer selects a date or date range in the Match Management UI.
2. **Backend Fetches Fixtures**: The backend calls the external Football API (e.g., API-Football, Sportmonks) to fetch scheduled fixtures for that date.
3. **Matches Saved to Database**: Valid fixtures are stored in the PostgreSQL database with an external API mapping ID alongside the internal `match_id`.
4. **Teams Submit Predictions**: Teams predict exactly as they do today, unaware of the external source.
5. **Completed Results Synced Automatically**: A manual "Sync Results" button (or cron job) pulls the completed match data (scorelines, goalscorers) from the Football API and writes it to the `actual_results` table.
6. **Scoring Engine Runs**: Organizers trigger the match scores calculation against predictions.
7. **Leaderboard Updates**: Ranks and points reflect the newly scored matches automatically.

## 3. Backend Architecture

### Football API Service Layer
A new integration service `app/services/football_api_service.py` will be created to encapsulate external API communication.
- **Client**: HTTP wrapper (e.g., `httpx` or `requests`) to communicate with the external API.
- **Rate Limiting**: Add safeguards to avoid exceeding API quotas.

### Required Endpoints
- `GET /api/v1/external-matches/fixtures?date=YYYY-MM-DD`: Fetches external fixtures and maps them to the internal schema format for preview.
- `POST /api/v1/external-matches/import`: Accepts selected fixtures from the frontend and creates internal `MatchModel` records.
- `POST /api/v1/external-matches/{match_id}/sync-result`: Fetches the live/completed result for a single match and generates an `ActualResultModel`.

### Request/Response Flow
1. **Importing**: The frontend requests fixtures for a specific date. The backend fetches raw external JSON, standardizes it, and returns a preview list. The organizer selects specific matches and posts them to the import endpoint.
2. **Syncing**: The backend uses the stored external match ID to request the specific fixture's result, maps home/away goals and goalscorers, and inserts them into the database.

### Duplicate Handling
- The backend will check if an external match ID already exists in the database before importing.
- Attempting to import an existing match will gracefully return a skipped status.

### Error Handling
- Timeout and 5xx errors from the external provider will return standard 502 Bad Gateway errors to the frontend.
- API Key invalidation will be logged and explicitly messaged to the Organizer.

## 4. Frontend Architecture

### Match Management Changes
- Add an "Import from API" tab or modal to the Match Management view.
- Introduce a DatePicker workflow to allow the Organizer to query external fixtures by date.

### Fetch Matches UI
- A table listing fetched external fixtures with checkboxes to select which ones to import into the GOALGORITHM system.
- Display teams, competition names, and scheduled times fetched from the API.

### Sync Results Workflow
- Add a "Sync Result" action button next to API-imported matches in the Matches table.
- A "Sync All Pending" button to automate fetching results for all matches whose scheduled time has passed.

### Loading/Error States
- Skeletons and spinners during API calls to external providers.
- Distinct error toasts if the external API is unreachable or rate-limited.

## 5. Database Architecture

The following schema updates are required in PostgreSQL:

**`matches` table updates (`MatchModel`)**
- `external_api_id` (String, Optional, Indexed): The unique ID provided by the external API.
- `competition_name` (String, Optional): To store the league or cup name.
- `external_sync_status` (Enum: `PENDING`, `SYNCED`, `FAILED`): Tracks result sync state.

**`actual_results` table updates (`ActualResultModel`)**
- `result_source` (String, default `MANUAL`): Track if the result was inputted manually or pulled via the API.
- `last_synced_at` (DateTime, Optional): Timestamp of the last successful pull from the external provider.

## 6. Security

### API Key Storage
- The external Football API requires authentication (typically via header `x-api-key` or similar).
- This key must **never** be exposed to the frontend React application.

### Environment Variables
- `FOOTBALL_API_KEY`: Stored securely in the `.env` file and Docker environment blocks.
- `FOOTBALL_API_BASE_URL`: Configurable base URL to easily swap between sandbox and production environments.
- `FOOTBALL_ALLOWED_LEAGUES`: Comma-separated list of API-FOOTBALL league IDs to filter fetched fixtures (e.g., `1,15` for World Cup and Club World Cup). This ensures only relevant configured competitions are presented for import.

## 7. Migration

### Existing Manual Matches vs New API Matches
- Existing manual matches will have `external_api_id = NULL` and `result_source = MANUAL`.
- The frontend will display the standard "Enter Result" manual button for these matches.
- New imported matches will display the "Sync Result" button instead.
- Both manual and API-driven matches funnel into the exact same `MatchModel` and `ActualResultModel` formats. This means the Scoring Engine and Leaderboard require **zero changes** and will treat all matches identically regardless of their origin.

## 8. Phase-wise Implementation Roadmap

### Phase 1: Backend API Service
- Define the external API client.
- Add environment variables to config.
- Write data mapping functions (External JSON -> Internal Schemas).

### Phase 2: Match Import
- Update the database schemas (`MatchModel` and `ActualResultModel`) with new fields.
- Create the `/external-matches/fixtures` and `/external-matches/import` endpoints.

### Phase 3: Frontend Connection
- Build the "Import Matches" UI in the Organizer dashboard.
- Connect the date picker to the new backend preview endpoints.

### Phase 4: Result Sync
- Build the `/sync-result` endpoint.
- Add "Sync Result" buttons to the frontend match cards.

### Phase 5: Scoring Integration
- Ensure synced results seamlessly trigger or can be used by the existing Scoring Engine.
- Implement fuzzy matching logic if external goalscorer names differ slightly from internal prediction spellings.

### Phase 6: Testing
- Unit testing for the API client using mocked external JSON responses.
- End-to-End testing of the full flow: Import -> Predict -> Sync -> Score.
