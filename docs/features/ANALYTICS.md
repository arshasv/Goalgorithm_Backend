# GOALGORITHM Analytics Module

> **Status:** Architecture & Implementation Plan  
> **Type:** Read-only insights layer  
> **Dependencies:** scoring engine, leaderboard, predictions, evaluations

---

## 1. Feature Goal

The Analytics module provides Organizers and Team Leaders with data-driven insights across the full competition lifecycle:

| Area | Insight |
|---|---|
| AI Model Performance | How well did each team's model predict match outcomes? |
| Prediction Accuracy | Breakdown across winner, scoreline, probability, and player categories. |
| Team Comparison | Side-by-side model accuracy, scores, and ranking across teams. |
| Presentation Performance | Per-criteria scores, judge variation, round trends. |
| Strengths & Weaknesses | Per-team strongest/weakest criteria across presentation and technical phases. |
| Overall Competition Insights | Phase contribution, leaderboard trends, top performers. |

**Golden rule:** Analytics is **read-only**. It never modifies scores, leaderboard data, or competition state.

---

## 2. Roles

### Organizer

- Full access to all analytics sections, all teams, all models, all scores.
- Can configure visibility settings for Team Leaders.
- Can export data (PDF / CSV).

### Team Leader

- Access controlled by `analytics_visibility_enabled` flag.
- When enabled, can see only the sections the Organizer has permitted.
- When disabled, the Analytics tab/navigation is hidden entirely.
- May see anonymised team labels if `anonymous_mode` is enabled.

---

## 3. Model Analytics

### Data Sources

| Table | Fields Used |
|---|---|
| `model_submissions` | name, version, created_at, metadata, model_type, algorithm |
| `predictions` | match_id, predicted_winner, predicted_scoreline, probabilities, player_predictions |
| `scores` | base_score, winner_points, scoreline_points, probability_points, player_points |
| `actual_results` | actual_winner, actual_scoreline, actual_player_stats |

### Per-Team Metrics

| Metric | Formula / Source |
|---|---|
| Model Name | `model_submissions.name` (latest active) |
| Model Version | `model_submissions.version` |
| Upload Timestamp | `model_submissions.created_at` |
| Accuracy | `model_submissions.metrics.accuracy` (self-reported, informational) |
| Total Predictions | `COUNT(scores)` for team |
| Correct Predictions | `SUM(winner_points > 0)` |
| Incorrect Predictions | Total - Correct |
| Average Prediction Score | `AVG(scores.base_score)` |
| Best Performing Match | Match ID + score where `scores.base_score` is max |
| Weakest Match | Match ID + score where `scores.base_score` is min |

### Accuracy Categories

| Category | Formula |
|---|---|
| Correct Winner % | `COUNT(winner_points > 0) / total_predictions × 100` |
| Exact Scoreline % | `COUNT(scoreline_points == max) / total_predictions × 100` |
| Player Prediction % | `COUNT(player_points > 0) / total_predictions × 100` |
| Probability Accuracy % | Based on configured probability scoring rules |

### Charts

#### 3.1 Team Model Accuracy Comparison

- **Type:** Grouped bar chart
- **X-axis:** Teams
- **Y-axis:** Accuracy %
- **Bars per team:** Correct Winner %, Exact Scoreline %, Player Prediction %, Probability Accuracy %

#### 3.2 Model Score Progression

- **Type:** Line chart
- **X-axis:** Matches (chronological order)
- **Y-axis:** Score (`base_score`)
- **One line per team**
- **Purpose:** Track how each team's model performed match-by-match

#### 3.3 Prediction Breakdown (Donut / Pie)

- **Type:** Donut chart (one per team, or toggled)
- **Segments:** Correct Winner, Exact Scoreline, Player Correct, Probability Correct, All Incorrect

---

## 4. Presentation Analytics

### Data Sources

| Table | Fields Used |
|---|---|
| `presentation_evaluations` | team_id, round_id, judge_id, raw_total, grade, multiplier, judge_scores (JSON) |
| `presentation_rounds` | name, ordering |
| `judges` | name |
| `leaderboard` | `presentation_score` (authoritative final Phase 3 score) |

### Criteria

Configurable via `ScoringConfig.presentation_criteria`. Default example:

| Criterion | Max Score |
|---|---|
| Problem Understanding | 10 |
| Feature Engineering | 15 |
| Team Work | 10 |
| Presentation Quality | 10 |
| Q&A | 5 |

**Total = 50**

### Per-Team Per-Round Calculation

| Value | Formula |
|---|---|
| Raw Score | `AVG(judge_scores[ criterion ])` summed across criteria |
| Grade | Assigned by scoring engine based on `raw_total` |
| Multiplier | 3 (A), 2 (B), 1 (C) |
| Weighted Score | `raw_total × multiplier` |

### Overall Presentation Score (Phase 3)

```
total_weighted       = SUM(weighted_score) over all rounds
num_rounds           = COUNT(completed rounds)
dynamic_denominator  = num_rounds × 150
final_presentation   = (total_weighted / dynamic_denominator) × 20
```

**Displayed value:** Read `leaderboard.presentation_score` — do not recompute.

### Charts

#### 4.1 Criteria Strength Radar Chart

- **Type:** Radar chart
- **Axes:** One per criterion (dynamically read from config)
- **Each team:** One polygon
- **Purpose:** Compare team profiles across all presentation dimensions

#### 4.2 Criteria Comparison Bar Chart

- **Type:** Grouped bar chart per criterion
- **X-axis:** Teams
- **Y-axis:** Average score for that criterion
- **Example:**

```
Feature Engineering:
  Team A — 13
  Team B —  7
  Team C — 10
  Team D —  9
```

#### 4.3 Highest Performing Teams Per Criterion

| Criterion | 1st | 2nd | 3rd |
|---|---|---|---|
| Problem Understanding | Team A (9.2) | Team C (8.5) | Team D (7.8) |
| Feature Engineering | Team A (13.0) | Team C (10.5) | Team D (9.0) |
| Team Work | Team B (9.0) | Team A (8.5) | Team C (8.0) |
| ... | ... | ... | ... |

#### 4.4 Weakness Analysis

Per team, identify the criterion with the lowest percentage of max.

```
Team B:
  Strongest:  Team Work          9/10  (90%)
  Weakest:    Feature Engineering 7/15  (47%)
```

---

## 5. Team Comparison Analytics

### Data Sources

`leaderboard` table — authoritative final scores per phase.

### Metrics

| Metric | Source |
|---|---|
| Rank | `leaderboard.rank` |
| Phase 1: AI Prediction | `leaderboard.phase1_score` /60 |
| Phase 2: Technical | `leaderboard.technical_score` /20 |
| Phase 3: Presentation | `leaderboard.presentation_score` /20 |
| Final Score | `leaderboard.final_score` /100 |

### Charts

#### 5.1 Final Score Leaderboard

- **Type:** Bar chart
- **X-axis:** Teams (sorted by rank)
- **Y-axis:** Final score /100

#### 5.2 Phase Contribution Stacked Chart

- **Type:** Stacked bar chart
- **Each bar:** One team
- **Segments:** Phase 1 (AI), Phase 2 (Technical), Phase 3 (Presentation)

---

## 6. Data Sources Reference

All analytics data is derived from existing tables. No new data collection is required.

| Existing Table | Used By Analytics For |
|---|---|
| `teams` | Team names, IDs, active status |
| `users` | Role detection (organizer / team_leader) |
| `model_submissions` | Model name, version, timestamps, algorithm, metrics, training data |
| `predictions` | Per-match predicted values for winner, scoreline, probability, players |
| `scores` | Ground-truth comparison: base_score, winner_points, scoreline_points, probability_points, player_points |
| `actual_results` | Actual match outcomes for accuracy computation |
| `presentation_evaluations` | Per-round raw_total, grade, multiplier, judge_scores (JSON) |
| `presentation_rounds` | Round names and ordering |
| `judges` | Judge names for variation analysis |
| `technical_evaluations` | Per-category scores (code_quality, backend_quality, teamwork, ai_explanation) |
| `leaderboard` | Authoritative phase scores, final scores, ranks |

**Do not duplicate stored data.** Analytics calculates derived values (percentages, averages, best/worst) from these tables at query time.

---

## 7. Configuration

### Visibility Settings

Stored in `LeaderboardVisibilityModel` or a new `AnalyticsVisibilityModel`.

| Setting | Type | Default | Description |
|---|---|---|---|
| `analytics_visibility_enabled` | bool | `false` | Master switch for Team Leader access |

When disabled, Team Leaders see no analytics. When enabled, individual section toggles (see `ANALYTICS_MODULE.md §3`) control fine-grained visibility.

Anonymous mode can additionally be enabled to replace real team names with "Team N" labels in Team Leader views.

---

## 8. API Plan

All endpoints are prefixed with `/api/v1/analytics`.

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| `GET` | `/overview` | Summary cards (top team, best accuracy, highest scores) | Organizer / Team Leader (if enabled) |
| `GET` | `/models` | Per-team model metadata + accuracy breakdown | Organizer / Team Leader (if enabled) |
| `GET` | `/predictions` | Per-team prediction stats with category breakdown | Organizer / Team Leader (if enabled) |
| `GET` | `/presentation` | Per-round scores, criteria breakdown, judge analysis, cross-team rankings | Organizer / Team Leader (if enabled) |
| `GET` | `/technical` | Per-category technical scores + strengths/weaknesses | Organizer / Team Leader (if enabled) |
| `GET` | `/visibility` | Current visibility settings | Organizer only |
| `PUT` | `/visibility` | Update visibility settings | Organizer only |
| `GET` | `/export/csv/:type` | CSV export by type (scores, models, predictions, presentation, technical) | Organizer only |
| `GET` | `/export/pdf` | Full PDF report | Organizer only |

Each Team Leader endpoint must:
1. Check `analytics_visibility_enabled`
2. Check the specific section toggle for the requested data
3. Apply `anonymous_mode` if active
4. Return 403 if the Team Leader is not permitted

---

## 9. Frontend Component Plan

### Route

```
/analytics
```

### Layout

Tabbed interface within the existing GOALGORITHM dark theme shell.

### Component Tree

```
AnalyticsPage
├── OverviewCards
│   ├── TopTeamCard
│   ├── BestAccuracyCard
│   ├── HighestPresentationCard
│   └── HighestTechnicalCard
│
├── ModelAnalyticsTab
│   ├── TeamModelAccuracyChart      (bar, §3.1)
│   ├── ModelScoreProgressionChart   (line, §3.2)
│   ├── PredictionBreakdownChart     (donut, §3.3)
│   └── ModelMetadataTable           (per-team details)
│
├── PresentationAnalyticsTab
│   ├── CriteriaRadarChart           (radar, §4.1)
│   ├── CriteriaComparisonChart      (bar, §4.2)
│   ├── HighestPerformingTable       (table, §4.3)
│   ├── WeaknessAnalysisCards        (cards, §4.4)
│   ├── RoundComparisonChart         (bar, per-round)
│   └── JudgeVariationChart          (scatter)
│
├── TechnicalAnalyticsTab
│   ├── TechnicalCriteriaRadar       (radar)
│   └── TeamTechnicalComparison      (bar)
│
├── ComparisonTab
│   ├── FinalScoreLeaderboardChart   (bar, §5.1)
│   └── PhaseContributionChart       (stacked bar, §5.2)
│
└── AnalyticsConfigurationPanel      (Organizer only)
    ├── EnableAnalyticsToggle
    ├── SectionVisibilityToggles
    └── AnonymousModeToggle
```

### Reusable Chart Wrapper

Each chart should use a shared wrapper that handles:
- Loading state (skeleton spinner)
- Empty state (contextual message from §12 of `ANALYTICS_MODULE.md`)
- Error state (retry button)

### Theme Tokens

| Token | Value |
|---|---|
| `--color-bg` | `#0f0f1a` |
| `--color-card-bg` | `#1a1a2e` |
| `--color-primary` | `#e94560` |
| `--color-text` | `#ffffff` |
| `--color-muted` | `#8888aa` |
| `--color-success` | `#2ecc71` |
| `--color-warning` | `#f39c12` |
| `--color-danger` | `#e74c3c` |

---

## 10. Database Changes

| Change | Details |
|---|---|
| **No new tables required** | All source data exists in current schema |
| **Optional:** `analytics_visibility_settings` | Only if not extending `LeaderboardVisibilityModel` |
| **Optional:** Add `model_type`, `algorithm`, `metrics` columns to `model_submissions` | If not already present for metadata fields |

No migrations are strictly required — analytics can be built using only existing tables and computed queries.

---

## 11. Calculation Formulas Reference

### Prediction Accuracy

```
winner_accuracy   = (correct_winners / total_predictions) × 100
scoreline_accuracy = (exact_scorelines / total_predictions) × 100
player_accuracy   = (correct_player_preds / total_predictions) × 100
prob_accuracy     = (correct_prob_preds / total_predictions) × 100
```

### Presentation

```
per_round_weighted  = raw_total × multiplier
total_weighted      = SUM(per_round_weighted) across rounds
denominator         = number_of_completed_rounds × 150
final_pct           = (total_weighted / denominator) × 100
final_presentation  = final_pct × 20 / 100 = (total_weighted / denominator) × 20
```

### Strength / Weakness

```
criterion_pct  = (team_avg_score_for_criterion / criterion_max_score) × 100
strongest      = MAX(criterion_pct)
weakest        = MIN(criterion_pct)
```

### Technical

```
category_pct   = (category_score / 5) × 100
```

---

## 12. Implementation Order

| Phase | Work | Depends On |
|---|---|---|
| 1 | Backend: GET `/analytics/overview`, `/analytics/models`, `/analytics/predictions` | Existing prediction scoring |
| 2 | Backend: GET `/analytics/presentation`, `/analytics/technical` | Existing eval data |
| 3 | Backend: GET/PUT `/analytics/visibility`, visibility guard middleware | Phase 1–2 |
| 4 | Backend: GET `/analytics/export/csv/:type`, GET `/analytics/export/pdf` | Phase 1–3 |
| 5 | Frontend: `AnalyticsPage` shell + tab routing + OverviewCards | Phase 1 |
| 6 | Frontend: Model + Prediction tabs (charts + tables) | Phase 1 |
| 7 | Frontend: Presentation + Technical tabs (charts + tables) | Phase 2 |
| 8 | Frontend: Configuration panel (visibility toggles) | Phase 3 |
| 9 | Frontend: Export buttons + download handling | Phase 4 |
| 10 | Frontend: Empty states, loading states, error handling | Phase 5–9 |

---

## 13. Non-Goals / Out of Scope

- Real-time live updates (analytics refreshes on page load / manual refresh)
- Push notifications or alerts based on analytics thresholds
- Drill-down into individual judge comments (only scores)
- Machine learning model retraining or recommendation
- Modifying any scoring configuration from analytics
