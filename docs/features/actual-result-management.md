# Actual Result Management

## Purpose
Allow organizers to input the ground-truth match result after a match concludes. The actual result serves as the reference data for all scoring computations.

## User / Actor
Organizer (submission, correction), System (automated validation)

## Input
Actual result JSON per match:
- `match_id`, `actual_winner`, `final_score` (home_team_goals, away_team_goals), `player_results` (player_id, player_name, actual_goals)

## Processing Workflow
1. Organizer submits actual result JSON via API
2. System validates against Pydantic schema
3. Service checks for existing result by match_id — rejects duplicates with 409
4. Validated result is stored for scoring reference

## Validation Rules
- `actual_winner` must be `home`, `away`, or `draw`
- `final_score` goals must be non-negative integers
- `player_results` must not be empty
- `match_id` must be non-empty

## Duplicate Handling
- A database-level unique constraint on `match_id` (`actual_results_match_id_key`) prevents entering two results for the same match.
- Submitting an existing result receives a clean **400 Bad Request** with error message `"Result already uploaded for this match"` to prevent 500 integrity crashes.
- This check is performed in the route layer (`result_routes.py`) prior to calling the database service.

## Output
- Success (new result): `{"status": "accepted", "match_id": "..."}` (200)
- Duplicate: 400 `Result already uploaded for this match`
- Validation failure: 422 `VALIDATION_ERROR`

## Related APIs
- `POST /api/v1/actual-results` — submit actual result

## Related Database Entities
- `actual_results` — stores match outcome
- `player_actuals` — stores per-player actual statistics
- `matches` — references match context
