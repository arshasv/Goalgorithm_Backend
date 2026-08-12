# Ranking & Multiplier

## Purpose
Rank all teams by their Base Score for each match and assign relative grade multipliers (A/B/C) to compute Earned Points.

## User / Actor
System (automated)

## Input
List of team base scores for a single match: `[{team_id, base_score}, ...]`

## Processing Workflow

### Step 1 — Ranking
- Sort teams by base_score descending
- Assign rank 1–5 (ties share same rank)

### Step 2 — Grade Assignment
| Rank | Grade | Multiplier |
|---|---|---|
| 1st (unique top score) | A | 3× |
| 2nd, 3rd, 4th | B | 2× |
| 5th (unique bottom score) | C | 1× |
| Tie at top (n teams tied for 1st) | All tied teams → B (2×) | |
| Tie at bottom (n teams tied for last) | All tied teams → C (1×) | |
| All tied | All → B (2×) | |

### Step 3 — Earned Points
- `earned_points = base_score × multiplier`

## Validation Rules
- Base scores are pre-validated (0–25 range)
- All 5 teams must be ranked per match

## Output
```json
{
  "team_id": "...",
  "rank": 1,
  "grade": "A",
  "multiplier": 3,
  "base_score": 25,
  "earned_points": 75
}
```

## Related APIs
- `POST /api/v1/calculate-match-score` (ranking is part of scoring pipeline)

## Related Database Entities
- `scores` — stores match_rank, grade, multiplier, earned_points
