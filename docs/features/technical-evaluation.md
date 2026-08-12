# Technical Evaluation

## Purpose
Accept architecture committee scores for Phase 2 (Technical Implementation) and compute the total out of 20 marks.

## User / Actor
Architecture Committee (submission), Organizer (view)

## Input
Technical evaluation per team:
- `team_id`
- `code_quality` (0–5)
- `backend_quality` (0–5)
- `teamwork` (0–5)
- `ai_explanation` (0–5)

## Processing Workflow
1. Committee submits scores for all sub-dimensions
2. System validates each score is within 0–5 range
3. Sum all four sub-dimension scores
4. Return total (no multiplier or normalization applied)

## Validation Rules
- Each sub-dimension score: integer, 0–5 inclusive
- `team_id` must be non-empty
- Negative values or values > 5 are rejected

## Output
```json
{
  "team_id": "...",
  "breakdown": {
    "code_quality": 5,
    "backend_quality": 5,
    "teamwork": 4,
    "ai_explanation": 5
  },
  "technical_score": 19
}
```

## Related APIs
- `POST /api/v1/technical-score`

## Related Database Entities
- `technical_evaluations` — stores Phase 2 scores per team
