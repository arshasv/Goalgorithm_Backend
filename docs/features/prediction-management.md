# Prediction Management

## Purpose
Accept, validate, and store team prediction JSON files submitted before each match freeze deadline. Enforce schema compliance, deadline cutoffs, and duplicate prevention.

## User / Actor
Participant Team (submission), Organizer (view history), System (automated validation)

## Input
Prediction JSON per team per match:
- `team_id`, `match_id`, `submission_id`
- `match_prediction`: predicted_winner, predicted_scoreline, probabilities, clean_sheet_probability, first_goal_team, both_teams_to_score_probability, total_goals_prediction
- `player_predictions`: list of per-player predictions (player_id, player_name, goal_probability, predicted_goals, assist_probability)

## Processing Workflow
1. Team submits prediction JSON via API
2. System validates against Pydantic schema
3. Schema checks: required fields, data types, value ranges, enum values, non-empty player list
4. Service checks for existing prediction by (team_id, match_id) — rejects duplicates with 409
5. Valid payload → stored; invalid → rejected with appropriate error

## Validation Rules
- `predicted_winner` must be `home`, `away`, or `draw`
- `first_goal_team` must be `home`, `away`, or `none`
- Probability fields: 0–100
- Scoreline goals: non-negative integers
- `goal_scorers` array lengths must exactly match the `predicted_scoreline` goals
- `player_predictions` must not be empty
- `team_id`, `match_id`, `submission_id` must be non-empty strings

> **Format Reference**: For an exact JSON schema, required field rules, and a full JSON example, see the [Prediction Format Reference](../api/prediction_format_reference.md) and the root `sample_prediction.json` file.

## Duplicate Handling & Updates
- **Idempotency Key**: Duplicate submissions with the same `idempotency_key` (or `submission_id`) will safely return a 200 OK duplicate status without reprocessing.
- **Overwrites (Edits)**: If a team submits a new prediction for the same match (same `team_id`, same `match_id`), the existing prediction and associated player predictions are gracefully deleted and replaced with the new submission. This allows Team Leaders to edit their predictions seamlessly up until the match is frozen.

## Output
- Success (new/updated prediction): `{"status": "accepted", "team_id": "...", "match_id": "..."}` (200)
- Duplicate (idempotent): `{"status": "duplicate", "message": "Prediction already submitted", "team_id": "...", "match_id": "..."}` (200)
- Validation failure: 422 `VALIDATION_ERROR`
- Bad Request (Missing Team): 400 `Team not found`

## Related APIs
- `POST /api/v1/predictions` — submit prediction

## Related Database Entities
- `predictions` — stores submitted prediction data
- `player_predictions` — stores per-player prediction entries
- `teams` — references team identity
- `matches` — references match context
