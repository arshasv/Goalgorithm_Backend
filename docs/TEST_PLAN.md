# Test Plan

> This document describes the planned testing strategy for the GOALGORITHM Scoring System. Tests are organized by layer and feature area, following the project's separation of concerns.

---

## Testing Philosophy

| Principle | Application |
|---|---|
| **Pure functions first** | Scoring engine calculators are pure functions — test with zero mocking, just input/output assertions. |
| **Layer isolation** | Unit tests never cross layer boundaries. Integration tests use real HTTP requests against the API. |
| **Contract-driven** | Schemas define the contract boundary; tests verify both valid payloads pass and invalid payloads are rejected. |
| **Deterministic fixtures** | All test data is static, version-controlled JSON fixtures. No randomness in test inputs. |

---

## 1. JSON Schema Validation Tests

**Scope:** `app/schemas/` — Pydantic model validation

| Test Case | Expected Outcome |
|---|---|
| Valid prediction payload is accepted | Passes schema validation |
| Missing required field (`predicted_winner`) | ValidationError raised |
| Wrong data type (string instead of float for probability) | ValidationError raised |
| Probability values outside [0.0, 1.0] range | ValidationError raised |
| Probability sum ≠ 1.0 ± 0.01 | ValidationError raised |
| Negative goal values | ValidationError raised |
| Player predictions array < 6 entries | ValidationError raised |
| Goalkeeper missing `clean_sheet_probability` | ValidationError raised |
| Outfield player has non-null `clean_sheet_probability` | ValidationError raised |
| Valid actual result payload is accepted | Passes schema validation |
| Winner field inconsistent with scoreline (e.g., `home_goals > away_goals` but winner = `away`) | ValidationError raised |
| `total_goals` ≠ `home_goals + away_goals` | ValidationError raised |
| Phase 2 score exceeds sub-dimension max (value > 5) | ValidationError raised |
| Phase 3 score exceeds sub-dimension max (QA > 15) | ValidationError raised |
| Empty team_evaluations array | ValidationError raised |

---

## 2. Prediction Submission Tests

**Scope:** `app/services/prediction_service.py` + `app/api/`

| Test Case | Expected Outcome |
|---|---|
| Submit valid prediction before freeze deadline | 201 Created |
| Submit prediction after freeze deadline | 423 Locked, `PREDICTION_WINDOW_CLOSED` |
| Duplicate prediction for same (team, match) | 200 OK (Idempotent), `PREDICTION_ALREADY_EXISTS` or overwrites |
| Submit prediction for non-existent match | 404 Not Found |
| Submit prediction with invalid team token | 401 Unauthorized |
| Submit prediction for match in COMPLETED state | 423 Locked |
| Prediction stored with `raw_payload` preserving original JSON | Field matches exact submission |
| Prediction status set to `PENDING_VALIDATION` on receipt | Status field updated |
| Prediction status transitions to `VALIDATED` or `INVALID` | Status field updated after validation |

---

## 3. Actual Result Processing Tests

**Scope:** `app/services/result_service.py` + `app/api/`

| Test Case | Expected Outcome |
|---|---|
| Enter valid actual result for a COMPLETED match | 201 Created |
| Enter result for non-existent match | 404 Not Found |
| Enter result for match that already has a result | 400 Bad Request |
| Enter result for match in SCHEDULED state | 423 Locked |
| Non-organizer tries to enter result | 403 Forbidden |
| Winner field contradicts scoreline (home_goals > away_goals but winner = "away") | 422 Unprocessable Entity |
| `home_clean_sheet` is false when `actual_away_goals == 0` | 422 Unprocessable Entity |

---

## 4. Base Score Calculation Tests

**Scope:** `app/scoring_engine/` — pure functions

### 4.1 Winner Evaluator

| Test Case | Expected Outcome |
|---|---|
| Predicted winner matches actual winner | 5 points |
| Predicted winner does not match actual winner | 0 points |
| Predicted draw and actual draw | 5 points |
| Predicted draw but one team won | 0 points |

### 4.2 Scoreline Evaluator

| Test Case | Expected Outcome |
|---|---|
| Exact scoreline match | 10 points |
| Correct goal margin (predicted 2-1, actual 1-0) | 5 points |
| Completely incorrect scoreline | 0 points |
| Same scoreline reversed (predicted 2-1, actual 1-2) | 0 points |

### 4.3 Probability Evaluator

| Test Case | Expected Outcome |
|---|---|
| All three probabilities within ±15% of actual | 5 points |
| One probability outside ±15% threshold | 0 points |
| Boundary case: difference exactly 0.15 | 5 points (within threshold) |
| Boundary case: difference exactly 0.151 | 0 points (outside threshold) |

### 4.4 Player Performance Evaluator

| Test Case | Expected Outcome |
|---|---|
| Predicted goals exactly match actual goals | 5 points |
| Predicted off by ±1 goal | 2 points |
| Predicted off by ≥2 goals | 0 points |
| Player predicted but not in actual lineup | 0 points |
| Missing player prediction for an actual scorer | 0 points |

### 4.5 Base Score Aggregation

| Test Case | Expected Outcome |
|---|---|
| Sum of all four evaluators within [0, 25] | Correct total |
| Raw sum exceeds 25 | Capped at 25 |
| All evaluators return 0 | Base score = 0 |

---

## 5. Ranking and Multiplier Tests

**Scope:** `app/scoring_engine/ranking_engine.py`, `app/scoring_engine/multiplier_engine.py`

| Test Case | Expected Outcome |
|---|---|
| 5 teams ranked by base score descending | Ranks 1 through 5 |
| Two teams with identical base score | Tie-breaking rule applied deterministically |
| Rank 1 assigned Grade A (3× multiplier) | Multiplier = 3 |
| Ranks 2, 3, 4 assigned Grade B (2× multiplier) | Multiplier = 2 |
| Rank 5 assigned Grade C (1× multiplier) | Multiplier = 1 |
| Earned points = base_score × multiplier | Correct multiplication |
| Re-ranking after score correction produces same tie-break order | Deterministic |

---

## 6. Normalization Tests

**Scope:** `app/scoring_engine/normalization_engine.py`

### 6.1 Phase 1 Normalization

| Test Case | Expected Outcome |
|---|---|
| Highest total_earned receives exactly 60 marks | phase1_score = 60.00 |
| Other teams scaled proportionally | phase1_score = (team_earned / max_earned) × 60 |
| All teams have same total_earned | All receive 60.00 |
| One team has 0 total_earned | phase1_score = 0.00 |
| Scores rounded to 2 decimal places | e.g., 45.67 not 45.666... |
| Normalization triggered before all 32 matches scored | Rejected, `NORMALIZATION_INCOMPLETE` |

### 6.2 Phase 3 Normalization

| Test Case | Expected Outcome |
|---|---|
| Formula: earned / 150 × 20 | Correct normalized score |
| Max earned (50 × 3 = 150) maps to 20.00 | phase3_score = 20.00 |
| Zero earned maps to 0.00 | phase3_score = 0.00 |

---

## 7. Technical Scoring (Phase 2) Tests

**Scope:** `app/api/` + `app/services/`

| Test Case | Expected Outcome |
|---|---|
| Committee submits valid Phase 2 scores | 201 Created |
| Sub-dimension score exceeds 5 | 422 Unprocessable Entity |
| Non-committee user attempts Phase 2 entry | 403 Forbidden |
| Scores persisted and retrievable | GET returns stored scores |
| Duplicate evaluation for same team | 409 Conflict |

---

## 8. Presentation Scoring (Phase 3) Tests

**Scope:** `app/api/` + `app/services/` + `app/scoring_engine/`

| Test Case | Expected Outcome |
|---|---|
| Reviewer submits valid raw scores | 201 Created |
| Raw score exceeds 50 total (20+15+15) | 422 Unprocessable Entity |
| Ranking applied correctly across 5 teams | Ranks 1–5 |
| Multiplier applied to raw score | earned = raw × multiplier |
| Normalization to 20 marks applied | Correct phase3_score |
| Non-reviewer attempts Phase 3 entry | 403 Forbidden |

---

## 9. Final Leaderboard Tests

**Scope:** `app/services/leaderboard_service.py` + `app/api/`

| Test Case | Expected Outcome |
|---|---|
| All three phases complete → leaderboard generated | 200 OK |
| Phase 1 incomplete (not all 32 matches scored) | Rejected, `LEADERBOARD_PHASE_INCOMPLETE` |
| Phase 2 scores missing | Rejected |
| Phase 3 scores missing | Rejected |
| Grand total = phase1 + phase2 + phase3 | Correct sum |
| Grand total capped at 100.00 | Does not exceed 100 |
| Teams ranked by grand total descending | Rank 1 = highest total |
| Tie in grand total | Tie-breaking rules applied |
| Leaderboard snapshot persisted | Retrievable via GET endpoint |
| Re-generation overwrites previous snapshot | Idempotent |

---

## 10. Edge Cases & Error Handling Tests

| Test Case | Expected Outcome |
|---|---|
| Empty request body | 422 or 400 error |
| Malformed JSON (syntax error) | 400 Bad Request |
| Unknown endpoint | 404 Not Found |
| Expired JWT token | 401 Unauthorized |
| Correct token, insufficient role | 403 Forbidden |
| Database connection failure | 500 Internal Server Error |
| Concurrent scoring triggers for same match | Graceful handling (idempotency) |
| Prediction payload exceeds 512 KB | 413 Payload Too Large (if enforced) |
| ISO 8601 datetime in wrong timezone | Rejected |

---

## Test Data Strategy

All test data lives in `backend/tests/fixtures/` as static JSON files:

| Fixture File | Purpose |
|---|---|
| `valid_prediction.json` | Correctly structured prediction payload |
| `valid_result.json` | Correctly structured actual result payload |
| `invalid_prediction_*.json` | Various malformed prediction payloads |
| `invalid_result_*.json` | Various malformed result payloads |
| `phase2_evaluation.json` | Sample technical evaluation payload |
| `phase3_evaluation.json` | Sample presentation evaluation payload |
| `scoring_scenarios.json` | Pre-computed input/expected-output pairs for scoring engine tests |

---

## Running Tests

```bash
# Run all tests
pytest tests/

# Run unit tests only (scoring engine pure functions)
pytest tests/unit/

# Run integration tests only (API routes)
pytest tests/integration/

# Run with coverage
pytest --cov=app tests/
```
