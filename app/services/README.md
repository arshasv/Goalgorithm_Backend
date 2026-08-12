# Service Layer

Controls workflows and orchestrates domain operations.

**Responsibility:** Implement all business logic, orchestrate scoring workflows, and decide WHEN scoring happens.

**Key principle:** Services decide WHEN scoring happens. The Scoring Engine decides HOW scoring happens. Services are the only layer allowed to contain scoring formulas and business rules.

**Contents:**
- PredictionService
- ResultService
- ScoringService
- RankingService
- NormalizationService
- EvaluationService (Phase 2 and Phase 3)
- LeaderboardService
- TeamService
- MatchService
