# Feature-to-Database Mapping

## Prediction Management
**Writes:** predictions, player_predictions
**Reads:** teams, matches

## Actual Result Management
**Writes:** actual_results, player_actuals
**Reads:** matches

## Base Scoring Engine
**Writes:** scores
**Reads:** predictions, actual_results, player_predictions, player_actuals

## Ranking & Multiplier
**Writes:** scores (grade, multiplier, earned_points)
**Reads:** scores

## Phase Normalization
**Writes:** cumulative_phase_scores (phase1_score)
**Reads:** scores

## Technical Evaluation
**Writes:** technical_evaluations
**Reads:** teams

## Presentation Evaluation
**Writes:** presentation_evaluations
**Reads:** teams

## Leaderboard
**Writes:** leaderboard
**Reads:** cumulative_phase_scores, technical_evaluations, presentation_evaluations

## Team Management
**Writes:** teams (is_csv_managed), team_members
**Reads:** teams, team_members, users

## Admin Scoring Configuration
**Writes:** scoring_configs
**Reads:** scoring_configs

## Model Submission
**Writes:** model_submissions, upload_window_config
**Reads:** teams, upload_window_config, model_submissions
