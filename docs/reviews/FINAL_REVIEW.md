# Final Architecture Review

## 1. Architecture

The system follows a layered architecture with clear separation of concerns:

```
main.py → config.py
   │
   ├── health_routes.py   (root level)
   └── api/               (/api/v1)
        ├── prediction_routes.py
        ├── result_routes.py
        ├── scoring_routes.py
        └── leaderboard_routes.py
              │
              └── services/
                   └── leaderboard_service.py
                         │
                         └── scoring_engine/   (pure logic)
                              ├── base_score/
                              ├── multiplier/
                              ├── normalization/
                              ├── technical_evaluation/
                              └── presentation_evaluation/
```

Routes receive requests, validate with schemas, delegate to services/engine, and return responses. No scoring formulas live in routes. The scoring engine is fully stateless and deterministic — no I/O, no database calls, no HTTP.

Settings are loaded from `.env` via `config.py` and consumed throughout the app.

---

## 2. Validation Layer

Four Pydantic v2 schema modules enforce strict input contracts:

| Schema | Validates |
|---|---|
| `prediction_schema.py` | Predictions, scoreline, probabilities, player predictions |
| `actual_result_schema.py` | Match results, final score, player results |
| `technical_evaluation_schema.py` | Phase 2 committee scores (0–5 per category) |
| `presentation_schema.py` | Phase 3 peer scores (within defined per-field max) |

All schemas include custom field validators for string enums (`predicted_winner`, `actual_winner`, `first_goal_team`), range checks, and non-empty list enforcement. Invalid payloads are rejected at the boundary with 422 responses.

---

## 3. Scoring Engine

Five independent modules, each with a single responsibility:

| Module | Function | Output Range |
|---|---|---|
| `base_score/` | Winner, scoreline, probability, player scoring | 0–25 per match |
| `multiplier/` | Rank teams per match, assign A/B/C grades | ×3 / ×2 / ×1 |
| `normalization/` | Scale cumulative scores to 60-mark phase | 0–60 |
| `technical_evaluation/` | Sum committee scores | 0–20 |
| `presentation_evaluation/` | Rank peer scores, apply multiplier, normalize | 0–20 |
| `leaderboard_service.py` | Aggregate all phases, sort, assign ranks | 0–100 |

All functions are pure — given the same inputs they always produce the same outputs. No external state is consulted.

---

## 4. API Separation

Routes are organized by domain. Each router file is responsible for a single concern:

| File | Endpoints | Responsibility |
|---|---|---|
| `health_routes.py` | `GET /health`, `GET /version` | Operational checks |
| `prediction_routes.py` | `POST /predictions` | Accept team predictions |
| `result_routes.py` | `POST /actual-results` | Accept match results |
| `scoring_routes.py` | `POST /calculate-match-score`, `POST /technical-score`, `POST /presentation-score` | Calculate all score types |
| `leaderboard_routes.py` | `POST /leaderboard/calculate` | Generate ranked leaderboard |

Health routes are registered at root level; all business routes are under `/api/v1`. Every route follows the same pattern: receive → validate with Pydantic schema → call service/engine → return response.

---

## 5. Testing

**127 tests across 10 test files**, all passing:

| Test file | Scope | Tests |
|---|---|---|
| `test_health.py` | Health/version endpoints | 4 |
| `test_api.py` | Full API integration via TestClient | 8 |
| `test_full_competition_flow.py` | End-to-end pipeline | 5 |
| `test_schemas.py` | Schema validation (valid, invalid, edge cases) | 26 |
| `test_base_score.py` | Winner, scoreline, probability, player scoring | 14 |
| `test_multiplier.py` | Ranking engine, grade assignment | 12 |
| `test_normalization.py` | Phase 1 normalizer | 10 |
| `test_presentation_score.py` | Presentation evaluation | 10 |
| `test_technical_score.py` | Technical evaluation | 10 |
| `test_leaderboard.py` | Leaderboard calculation | 17 |

Test fixtures use 6 JSON data files covering valid, invalid, and five-team scenarios.

---

## 6. Docker Readiness

| Artifact | Purpose |
|---|---|
| `Dockerfile` | `python:3.12-slim`, installs deps, runs uvicorn on port 8000 |
| `docker-compose.yml` | Single service, port mapping, `.env` injection, `unless-stopped` restart |
| `.dockerignore` | Excludes `.git`, `venv`, `.pytest_cache` (preserves `__pycache__`) |
| `.env.example` | Template for local configuration |
| `.env` | Active config (gitignored) |

Verified: `docker build` succeeds, `docker compose up -d` starts cleanly, `GET /health` returns `200`, all 127 tests pass inside and outside the container.

---

## Completed Features

- Prediction validation and submission API
- Actual result ingestion API
- Match-level base score calculation (winner, scoreline, probability, player)
- Multi-team ranking with A/B/C grade multipliers
- Phase 1 normalisation (AI accuracy /60)
- Technical evaluation scoring API (Phase 2 /20)
- Presentation evaluation with peer ranking and multiplier (Phase 3 /20)
- Final leaderboard generation with tie-breaking (/100)
- Full REST API surface under `/api/v1`
- Docker image and Compose configuration for deployment
- Centralised environment configuration

---

## Future Improvements

- **Database persistence** — Currently all endpoints are stateless stubs. A database layer would allow storing predictions, results, and scores for querying and audit.
- **Authentication** — No auth middleware exists. Organizer, committee, and participant roles would need JWT or session-based access control.
- **Admin dashboard** — A frontend or admin panel could provide a UI for submitting results, viewing leaderboards, and managing teams.
