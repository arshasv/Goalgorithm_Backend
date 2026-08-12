# Scoring Engine Layer

Contains pure mathematical calculations only.

**Responsibility:** Compute match base scores, evaluate winner/scoreline/probability/player predictions, apply multipliers, and normalize scores.

**Key principle:** The Scoring Engine decides HOW scoring happens. It contains no I/O, no database calls, no HTTP requests. All functions are pure and deterministic — same inputs always produce the same outputs.

**Contents:**
- **base_score/** — Winner, scoreline, probability, and player evaluators
- **multiplier/** — Grade multiplier application
- **normalization/** — Phase 1 and Phase 3 score normalization
- **player_evaluation/** — Player performance scoring
