# Leaderboard

## Purpose
Aggregate Phase 1, Phase 2, and Phase 3 scores for all teams, compute grand totals, rank teams, and produce the final leaderboard.

## User / Actor
Organizer (generation), All roles (view)

## Input
List of per-team score entries:
- `team_id`
- `phase1_score` (0–60)
- `technical_score` (0–20)
- `presentation_score` (0–20)

## Processing Workflow
1. Validate each score is within its allowed range
2. Compute `final_score = phase1_score + technical_score + presentation_score`
3. Sort teams by final_score descending
4. Secondary sort by ai_accuracy, then technical, then presentation for tie-breaking
5. Assign ranks (ties share same rank, next rank adjusts by count)

## Validation Rules
- `phase1_score`: 0–60
- `technical_score`: 0–20
- `presentation_score`: 0–20
- Raises `LeaderboardError` on out-of-range values
- Empty input returns empty list

## Output
```json
{
  "rank": 1,
  "team_id": "A",
  "scores": {
    "ai_accuracy": 60.0,
    "technical": 19,
    "presentation": 19.2
  },
  "final_score": 98.2
}
```

## Related APIs
- `POST /api/v1/leaderboard/calculate`

## Related Database Entities
- `leaderboard` — stores final ranked entries per team
- `cumulative_phase_scores` — source for phase scores
