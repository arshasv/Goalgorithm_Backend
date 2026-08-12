# Tests

pytest test suite for the FIFA Challenge Scoring System.

## Structure

```
tests/
├── conftest.py              ← Shared fixtures (test DB session, async test client)
├── fixtures/                ← Test data files (sample prediction JSON, etc.)
├── unit/                    ← Pure function tests (no DB, no HTTP)
│   ├── test_winner_evaluator.py
│   ├── test_scoreline_evaluator.py
│   ├── test_probability_evaluator.py
│   ├── test_player_evaluator.py
│   ├── test_base_score_calculator.py
│   ├── test_ranking_engine.py
│   ├── test_multiplier_engine.py
│   └── test_normalization_engine.py
└── integration/             ← API route tests (httpx + pytest-asyncio)
    ├── test_teams.py
    ├── test_matches.py
    ├── test_predictions.py
    ├── test_results.py
    ├── test_scoring.py
    ├── test_evaluations.py
    └── test_leaderboard.py
```

## Running Tests

```bash
pytest tests/
```
