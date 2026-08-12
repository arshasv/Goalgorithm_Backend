# Phase Normalization

## Purpose
Normalize cumulative earned points across all 32 matches into a Phase 1 score out of 60 marks.

## User / Actor
System (automated)

## Input
Per-team cumulative match data: `[{team_id, matches: [{match_id, earned_points}]}]`

## Processing Workflow
1. Sum `earned_points` across all matches per team → `total_earned`
2. Find the maximum `total_earned` among all teams
3. Compute: `phase1_score = (team_total_earned / max_total_earned) × 60`
4. Round to 2 decimal places
5. Team with highest total earns exactly 60.00

## Validation Rules
- `earned_points` must be non-negative per match
- Total must not exceed `matches_played × 75` (max possible)
- Raises `NormalizationError` on invalid data

## Output
```json
{
  "team_id": "...",
  "total_earned_points": 1800,
  "matches_played": 32,
  "phase1_score": 60.0
}
```

## Related APIs
- Primarily called internally; related to match scoring pipeline

## Related Database Entities
- `cumulative_phase_scores` — stores normalized phase1_score
