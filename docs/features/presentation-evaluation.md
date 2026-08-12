# Presentation Evaluation

## Purpose
Accept peer review panel scores for Phase 3 (Presentation), apply relative ranking multipliers, and normalize results to a 20-mark scale.

## User / Actor
Peer Review Panel (submission), System (automated ranking + normalization)

## Input
List of presentation evaluations (one per team):
- `team_id`
- `ai_explanation_score` (0–20)
- `qa_score` (0–15)
- `delivery_score` (0–15)

## Processing Workflow
1. **Judge Entry/CSV Upload**: Judges submit scores /50 for each team in a specific presentation round. The system averages these scores.
2. **Ranking & Multiplier**: Teams are ranked per round. The highest-ranked team gets a Grade A (×3 multiplier), middle teams Grade B (×2), lowest team Grade C (×1).
3. **Round Weighted Score**: The raw average is multiplied by the grade multiplier. (Max: 50 × 3 = 150 marks per round).
4. **Multiple Rounds**: There are TWO presentation rounds. The round weighted scores are summed together to form the Total Weighted Score (Max: 300).
5. **Phase 3 Final Score**: The total weighted score is normalized to 20 marks: `(Total / 300) × 20`. This normalized score is fed into the Leaderboard.

## Validation Rules
- Each sub-score within defined per-field max
- Negative values rejected

## Output (per-round)
```json
{
  "team_id": "...",
  "raw_total": 48,
  "rank": 1,
  "grade": "A",
  "multiplier": 3,
  "weighted_score": 144,
  "presentation_score": null
}
```

## Output (leaderboard)
```json
{
  "team_id": "...",
  "presentation_score": 19.2
}
```

## Related APIs
- `POST /api/v1/presentation-score`

## Related Database Entities
- `presentation_evaluations` — stores Phase 3 raw scores and computed results
