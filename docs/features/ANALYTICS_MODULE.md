# Analytics Module — GOALGORITHM

> **Status:** Implemented (Backend refactored into Controller/Service/Repository, frontend updated with granular toggles)
> **Scope:** Read-only insights and visualizations for competition scoring data

---

## 1. Purpose

The Analytics module provides Organizers and Team Leaders with data-driven insights into:

- **AI model performance** — how each team's predictions performed across matches
- **Prediction accuracy** — breakdown of winner, scoreline, probability, and player prediction accuracy
- **Technical evaluation performance** — per-category strengths and weaknesses in Phase 2
- **Presentation strengths and weaknesses** — per-criterion analysis across rounds and judges
- **Final competition score analysis** — phase contribution breakdown and leaderboard visualisation

Analytics is **visualization and insights only**. It must **never modify** scoring calculations, leaderboard data, or any competition state. It reads from existing scoring engine outputs and never recalculates scores differently.

### Source of Truth for Scores

Analytics must **never independently calculate final competition scores**.

Analytics **may** calculate:
- percentages
- comparisons
- strengths
- weaknesses
- chart values (for visualisation)

But official phase scores must come from existing scoring outputs.

| Phase | Source of Truth |
|---|---|
| Phase 1: AI Prediction | Existing prediction scoring engine output |
| Phase 2: Technical | `technical_evaluations.total_score` (stored score) |
| Phase 3: Presentation | `leaderboard.presentation_score` |
| Final Score | `leaderboard.final_score` |

Any derived breakdowns or intermediate calculations within analytics (e.g., per-round weighted scores) are used for visualisation only and must never overwrite the stored leaderboard values.

---

## 2. User Roles

### Organizer View

Full access to all analytics sections. An organizer can see:

- All teams, all models, all scores
- All comparisons and rankings
- Judge scoring analysis
- Strength/weakness analysis per team
- Phase contribution breakdowns

### Team Leader View

Access is controlled by Organizer-configured **visibility settings**. A team leader can only see analytics sections and data that the Organizer has explicitly enabled. By default, all analytics are **hidden** from team leaders.

---

## 3. Analytics Visibility Configuration

### Location

Accessible from the **Organizer Dashboard** > **Analytics Configuration**.

A single database record (or a section within `LeaderboardVisibilityModel`) controls what team leaders can see.

### Master Toggle

| Setting | Type | Default | Description |
|---|---|---|---|
| `enable_analytics` | bool | `false` | Master switch — when off, no analytics are exposed to team leaders |

### Team Leader Visibility Toggles

When master toggle is `true`, these individual toggles control which sections are visible to team leaders:

| Setting | Type | Default | Description |
|---|---|---|---|
| `show_overall_comparison` | bool | `true` | Displays the high-level competition overview cards. |
| `show_model_analytics` | bool | `true` | Displays accuracy comparisons, final model scores, and version improvements. |
| `show_prediction_analytics` | bool | `true` | Displays prediction scores across matches. |
| `show_technical_analytics` | bool | `true` | Displays technical evaluation metrics and comparisons. |
| `show_presentation_analytics` | bool | `true` | Allows teams to view criteria comparison charts and strength/weakness analysis. |
| `show_judge_analytics` | bool | `true` | Displays judge scoring patterns, consistency metrics, and severity metrics to teams. |
| `show_leaderboard_analytics` | bool | `true` | Allows teams to see top performers and competition-wide score distributions. |

- For the **Organizer** all settings are implicitly `true`.
- When the master toggle is `false`, all individual toggles are ignored and analytics are hidden from team leaders.

### Anonymous Mode

When enabled, team leader views display anonymised labels:

```
Team 1
Team 2
...
```

instead of real team names. The Organizer always sees real names.

| Setting | Type | Default | Description |
|---|---|---|---|
| `anonymous_mode` | bool | `false` | Replace real team names with "Team N" for team leaders |

### Storage

Reuse and extend the existing `LeaderboardVisibilityModel` (or create a new `AnalyticsVisibilityModel` if separation is preferred). Example minimal schema:

```json
{
  "id": "uuid",
  "enable_analytics": false,
  "show_overall_rankings": false,
  "show_model_analytics": false,
  "show_presentation_analytics": false,
  "show_judge_analytics": false,
  "show_prediction_breakdown": false,
  "show_strength_weakness": false,
  "anonymous_mode": false,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 4. Final Score Analytics

### Data Source

Existing `leaderboard` table (populated by `compute_and_save_leaderboard`). This is the **single source of truth** for all phase and final scores — analytics must read phase values from here, not recompute them.

### Display

| Column | Value | Source of Truth |
|---|---|---|
| Team Name | `team_name` | `leaderboard` |
| Rank | `rank` | `leaderboard` |
| Phase 1: AI Prediction | `phase1_score` /60 | Existing prediction scoring engine output |
| Phase 2: Technical | `technical_score` /20 | `technical_evaluations.total_score` |
| Phase 3: Presentation | `presentation_score` /20 | `leaderboard.presentation_score` |
| Final Score | `final_score` /100 | `leaderboard.final_score` |

### Charts

#### 4.1 Final Score Leaderboard Chart

- **Type:** Bar chart (horizontal or vertical)
- **X-axis:** Teams (sorted by rank)
- **Y-axis:** Final score /100
- **Purpose:** Instant visual of the competitive order

#### 4.2 Phase Contribution Chart

- **Type:** Stacked bar chart
- **Each bar:** One team
- **Segments per bar:**
  - AI Prediction (Phase 1) — contribution in points
  - Technical (Phase 2) — contribution in points
  - Presentation (Phase 3) — contribution in points
- **Purpose:** Understand **why** a team is leading or trailing — e.g., Team A may dominate Phase 1 but lag in Presentation.

---

## 5. Prediction Scoring Analytics (Match Performance)

### Data Sources

- `model_submissions` table — model metadata
- `predictions` table — per-match predictions
- `scores` table — per-match score breakdowns
- `actual_results` table — ground truth

### Model Metadata Management

Teams can upload different AI models throughout the competition. The system stores detailed model metadata alongside each submission.

#### Displayed Model Fields

| Field | Source | Notes |
|---|---|---|
| Team | `teams.name` | |
| Model Name | `model_submissions.name` | |
| Model Type | `model_submissions.model_type` | e.g., Classification, Regression, Ensemble |
| Algorithm Used | `model_submissions.algorithm` | e.g., XGBoost, Random Forest, LSTM |
| Version | `model_submissions.version` | |
| Upload Date | `model_submissions.created_at` | |
| Training Dataset Details | `model_submissions.training_data` | Free text / JSON |
| Feature Engineering Approach | `model_submissions.feature_approach` | Free text / JSON |
| Accuracy | `model_submissions.metrics.accuracy` | Self-reported, informational only |
| Precision | `model_submissions.metrics.precision` | Self-reported, informational only |
| Recall | `model_submissions.metrics.recall` | Self-reported, informational only |
| F1 Score | `model_submissions.metrics.f1_score` | Self-reported, informational only |
| Loss Metrics | `model_submissions.metrics.loss` | Self-reported, informational only |
| Additional Notes | `model_submissions.notes` | Free text |

**Important:** These model metadata fields are **informational only**. They must **never** affect competition scoring. Competition scoring still comes from actual prediction performance against ground truth.

#### Latest Active Model

Model analytics should always use the latest active model (highest version / most recent upload). Historical versions are preserved for improvement trend charts.

### Model Upload / Update Workflow

The Organizer can add or update model metadata through:

- **Manual entry** — form fields in the Organizer Dashboard
- **CSV upload** — bulk import of model metadata
- **Existing model submission metadata extraction** — parse metadata from the `model_submissions.metadata` JSON field if submitted by the team

All methods feed into the same `model_submissions` table. No separate table is needed.

### Per-Team Display

#### Performance Metrics

| Metric | Formula |
|---|---|
| Total Predictions | `COUNT(scores)` for team |
| Average Prediction Score | `AVG(scores.base_score)` |
| Best Match Performance | `MAX(scores.base_score)` + match ID |
| Weakest Match Performance | `MIN(scores.base_score)` + match ID |

#### Accuracy Breakdown

| Metric | Formula | Source |
|---|---|---|
| Winner Prediction Accuracy | `correct_winner_count / total_predictions × 100` | `scores.winner_points > 0` |
| Scoreline Accuracy | `exact_scoreline_count / total_predictions × 100` | `scores.scoreline_points == max_scoreline_points` |
| Probability Accuracy | Based on configured probability scoring rules | `scores.probability_points > 0` |
| Player Performance Accuracy | Based on configured player scoring rules | `scores.player_points > 0` |

### Charts

#### 5.1 Model Comparison Chart

- **Type:** Grouped bar chart
- **X-axis:** Teams
- **Y-axis:** Accuracy percentage
- **Bars per team:** Winner %, Scoreline %, Probability %, Player %
- **Purpose:** Compare prediction accuracy across teams at a glance

#### 5.2 Prediction Category Radar Chart

- **Type:** Radar/spider chart
- **Axes (4 categories):** Winner, Scoreline, Probability, Player
- **Each team:** One line/shape on the radar
- **Purpose:** Identify a team's prediction profile — e.g., strong at winners but weak at scorelines

#### 5.3 Model Improvement Trend

- **Conditional:** Only shown for teams with multiple model submissions
- **Type:** Line chart
- **X-axis:** Model version (chronological)
- **Y-axis:** Average base score
- **One line per team**
- **Purpose:** Visualise whether successive model iterations improve prediction performance

---

## 6. Model Performance Analytics (Actual AI Evaluation)

### Data Source
- `model_evaluations` table — stores offline test results, distinct from live match performance.

### Purpose
To understand the structural and mathematical robustness of the actual AI model files uploaded by teams.

### 6.1 Model Performance Overview
Display top-level summary cards for quick insights:
- **Best Performing Model:** Model version with the highest overall accuracy.
- **Highest Accuracy:** The peak percentage accuracy registered.
- **Best Team Improvement:** The team that improved their accuracy the most from their first model version to their final version.

### 6.2 Team Model Ranking
Compare final, active models across teams using a horizontal bar chart.
**Example:**
- Team A model - 90%
- Team B model - 85%

### 6.3 Model Strength Analysis
Grouped analysis breaking down the core capabilities. 
**Show categories:**
- Winner prediction
- Scoreline prediction
- Probability prediction
- Player performance

### 6.4 Version Improvement
Line chart showing accuracy progression over multiple submissions for a single team.
**Example:**
- `v1` → 60%
- `v2` → 75%
- `v3` → 90%

### 6.5 Strength and Weakness Insights
Text-based insights generated from `strength_category` and `weakness_category` stored in `model_evaluations`.
**Example for Team GoalGPT:**
- **Strong:** Winner prediction
- **Weak:** Scoreline prediction

---

## 7. Presentation Analytics

### Data Sources

- `presentation_evaluations` — per-round, per-team evaluation records
- `presentation_rounds` — round metadata
- `judges` — judge information

### Unlimited Rounds

The system supports an arbitrary number of presentation rounds. Analytics must dynamically adjust to however many rounds exist (never hardcode round count).

### Per-Team Per-Round Display

| Column | Value |
|---|---|
| Round Name | `presentation_rounds.name` |
| Raw Score | `raw_total` / max_marks (typically /50) |
| Grade | `grade` (A/B/C) |
| Multiplier | `multiplier` (3/2/1) |
| Weighted Score | `raw_total × multiplier` |

### Overall Presentation Score

The per-round calculation is:

```
weighted_score       = raw_average × multiplier
total_weighted       = SUM(weighted_score) over all rounds
dynamic_denominator  = number_of_completed_rounds × 150
final_presentation   = (total_weighted / dynamic_denominator) × 20
```

**Important:** The final normalized Phase 3 score displayed in analytics must use the stored `leaderboard.presentation_score` value to avoid mismatch. Analytics may compute intermediate per-round weighted scores for charting, but the authoritative phase outcome always comes from the leaderboard.

### Charts

#### 6.1 Round Comparison Chart

- **Type:** Grouped bar chart
- **X-axis:** Teams
- **Y-axis:** Weighted score
- **Bars per team:** One bar per round, side-by-side
- **Purpose:** Compare performance across rounds and identify which teams improved or declined

#### 6.2 Presentation Score Trend

- **Type:** Line chart
- **X-axis:** Round (chronological)
- **Y-axis:** Weighted score
- **One line per team**
- **Purpose:** Track presentation performance trajectory over the competition

---

## 7. Presentation Strength / Weakness Analysis

### Data Source

`presentation_evaluations.judge_scores` (JSON array of per-judge scores) combined with `presentation_criteria_config` for criterion names and max scores.

### Criteria

Configurable via `ScoringConfig.presentation_criteria`. This must work dynamically with whatever criteria are configured — **never hardcode criterion names**.

Default example:

| Criterion | Max Score |
|---|---|
| Problem Understanding | 10 |
| Feature Engineering | 15 |
| Team Work | 10 |
| Presentation Quality | 10 |
| Q&A | 5 |

### Individual Team Analysis

For every criterion, calculate the **team average** across all judges and all rounds:

```
criterion_score   = AVG(score given by each judge for this criterion)
criterion_pct     = (criterion_score / criterion_max_score) × 100
```

Identify:

| Label | Definition |
|---|---|
| **Strongest Category** | criterion with highest `criterion_pct` |
| **Weakest Category** | criterion with lowest `criterion_pct` |

### Cross-Team Analysis

For every presentation criterion, calculate across all teams:

| Metric | Definition |
|---|---|
| Highest scoring team | team with max `criterion_pct` |
| Lowest scoring team | team with min `criterion_pct` |
| Team ranking | all teams sorted by `criterion_pct` descending |

### Example Output

```
Feature Engineering:
  1. Team A — 13.5/15  (90%)
  2. Team C — 12.0/15  (80%)
  3. Team D — 10.0/15  (67%)
  4. Team E —  9.5/15  (63%)
  5. Team B —  8.0/15  (53%)

Best Performing:      Team A
Needs Improvement:    Team B
```

### Individual Team Example

```
Team A:
  Strength:  Feature Engineering   13/15  (86%)
  Weakness:  Q&A                    3/5   (60%)
```

### Charts

#### 7.1 Criteria Radar Chart

- **Type:** Radar/spider chart
- **Axes:** One per criterion (dynamic — read from config)
- **Each team:** One line
- **Purpose:** Visualise each team's presentation profile across categories

#### 7.2 Criteria Ranking Chart

- **Type:** Bar chart (one per criterion)
- **Y-axis:** Teams ranked by criterion score
- **Purpose:** See which teams excel at which specific criteria

---

## 8. Presentation Comparison Charts

### Chart 1: Criteria Radar Chart

(Described in §7.1 — shared visual for strength/weakness analysis)

### Chart 2: Criteria Ranking Chart

(Described in §7.2 — highlights per-criterion ordering)

### Chart 3: Judge Scoring Behavior & Variation (Judge Analytics)

- **Type:** Scatter or box plot
- **X-axis:** Judges
- **Y-axis:** Normalized percentage score given
- **One point per team–judge pair**
- **Purpose:** Analyze judge scoring behaviour. Surface scoring differences — e.g., identifying strict vs generous judges, or conducting consistency analysis (e.g. Judge A consistently scores 20% higher than Judge B, indicating a calibration need).

### Important: Criteria Percentage Normalization
When comparing presentation criteria, analytics must **always use percentage normalization**.
Different criteria often have different maximum weights.

**Example:**
- Do not compare raw marks directly: e.g., Q&A (4/5 marks) vs Feature Engineering (12/15 marks).
- Instead, compare the percentage achieved: Q&A (80%) vs Feature Engineering (80%).

---

## 9. Technical Evaluation Analytics

### Data Source

`technical_evaluations` table — per-category scores and total.

### Per-Team Display

| Category | Score | Max |
|---|---|---|
| Code Quality & Model Innovation | `code_quality` | 5 |
| Backend APIs Robustness | `backend_quality` | 5 |
| Teamwork & Cross-Role Collaboration | `teamwork` | 5 |
| AI Explanation Engine | `ai_explanation` | 5 |
| **Total** | `total_score` | 20 |

### Strength / Weakness

Identical logic to presentation criteria (§7):

- **Strongest:** category with highest percentage of max
- **Weakest:** category with lowest percentage of max

### Charts

#### 9.1 Technical Criteria Radar

- **Type:** Radar chart
- **Axes:** Code Quality & Model Innovation, Backend APIs Robustness, Teamwork & Cross-Role Collaboration, AI Explanation Engine
- **One line per team**
- **Purpose:** Compare technical skill profiles across teams

#### 9.2 Team Technical Comparison

- **Type:** Grouped bar chart
- **X-axis:** Teams
- **Y-axis:** Score /5
- **Bars per team:** One per category
- **Purpose:** Side-by-side comparison of each category

---

## 10. Required Backend APIs

> Do not implement yet. These are the planned endpoints and expected response shapes.

### `GET /api/v1/analytics/overview`

High-level summary cards.

```json
{
  "top_team": {
    "team_name": "A-Paul",
    "final_score": 85.5,
    "rank": 1
  },
  "best_model_accuracy": {
    "team_name": "Data Dragons",
    "winner_accuracy_pct": 92.3
  },
  "highest_presentation_score": {
    "team_name": "AI Wizards",
    "final_presentation": 18.2
  },
  "highest_technical_score": {
    "team_name": "Byte Crunchers",
    "technical_score": 19.0
  }
}
```

### `GET /api/v1/analytics/models`

```json
{
  "models": [
    {
      "team_id": "...",
      "team_name": "A-Paul",
      "model_name": "Gradient-Boost-v3",
      "model_type": "Ensemble",
      "algorithm": "XGBoost",
      "version": "3.1",
      "uploaded_at": "2026-06-15T10:00:00Z",
      "training_data": "Premier League 2023-2025",
      "feature_approach": "Rolling averages + ELO",
      "metrics": {
        "accuracy": 87.0,
        "precision": 84.5,
        "recall": 82.0,
        "f1_score": 83.2,
        "loss": 0.21
      },
      "notes": "Best performing on underdog upsets",
      "total_predictions": 10,
      "avg_base_score": 18.5,
      "best_match_id": "match-003",
      "best_base_score": 25.0,
      "weakest_match_id": "match-007",
      "weakest_base_score": 8.0,
      "winner_accuracy_pct": 80.0,
      "scoreline_accuracy_pct": 40.0,
      "probability_accuracy_pct": 70.0,
      "player_accuracy_pct": 60.0,
      "model_history": [
        { "version": "1.0", "avg_base_score": 12.3 },
        { "version": "2.0", "avg_base_score": 15.8 },
        { "version": "3.1", "avg_base_score": 18.5 }
      ]
    }
  ]
}
```

### `GET /api/v1/analytics/predictions`

```json
{
  "teams": [
    {
      "team_id": "...",
      "team_name": "A-Paul",
      "total_predictions": 10,
      "correct_winners": 8,
      "exact_scorelines": 4,
      "avg_probability_score": 3.2,
      "avg_player_score": 4.1,
      "breakdown": {
        "winner": 80.0,
        "scoreline": 40.0,
        "probability": 64.0,
        "player": 82.0
      }
    }
  ]
}
```

### `GET /api/v1/analytics/presentation`

```json
{
  "rounds": ["Round 1", "Round 2"],
  "teams": [
    {
      "team_id": "...",
      "team_name": "AI Wizards",
      "rounds": [
        {
          "round_id": "...",
          "round_name": "Round 1",
          "raw_total": 41.0,
          "grade": "A",
          "multiplier": 3,
          "weighted_score": 123.0
        },
        {
          "round_id": "...",
          "round_name": "Round 2",
          "raw_total": 38.0,
          "grade": "B",
          "multiplier": 2,
          "weighted_score": 76.0
        }
      ],
      "total_weighted": 199.0,
      "dynamic_denominator": 300,
      "final_presentation": 13.27,
      "strengths": [
        { "criterion": "Feature Engineering", "score": 13, "max": 15, "pct": 86.7 }
      ],
      "weaknesses": [
        { "criterion": "Q&A", "score": 3, "max": 5, "pct": 60.0 }
      ],
      "criteria_scores": [
        { "criterion": "Problem Understanding", "avg_score": 8.5, "max": 10, "pct": 85.0 },
        { "criterion": "Feature Engineering", "avg_score": 13.0, "max": 15, "pct": 86.7 },
        { "criterion": "Team Work", "avg_score": 7.0, "max": 10, "pct": 70.0 },
        { "criterion": "Presentation Quality", "avg_score": 8.0, "max": 10, "pct": 80.0 },
        { "criterion": "Q&A", "avg_score": 3.0, "max": 5, "pct": 60.0 }
      ]
    }
  ],
  "judge_analysis": [
    {
      "judge_id": "...",
      "judge_name": "Dr. Smith",
      "avg_score_given": 35.2,
      "score_stddev": 4.1
    }
  ]
}
```

### `GET /api/v1/analytics/technical`

```json
{
  "teams": [
    {
      "team_id": "...",
      "team_name": "Byte Crunchers",
      "categories": {
        "code_quality": { "score": 5, "max": 5, "pct": 100.0 },
        "backend_quality": { "score": 4, "max": 5, "pct": 80.0 },
        "teamwork": { "score": 5, "max": 5, "pct": 100.0 },
        "ai_explanation": { "score": 5, "max": 5, "pct": 100.0 }
      },
      "total_score": 19,
      "total_max": 20,
      "strongest": { "category": "Code Quality & Model Innovation", "pct": 100.0 },
      "weakest": { "category": "Backend APIs Robustness", "pct": 80.0 }
    }
  ]
}
```

### `GET /api/v1/analytics/visibility`

```json
{
  "enable_analytics": false,
  "show_overall_rankings": false,
  "show_own_model_analytics": false,
  "show_all_team_model_comparison": false,
  "show_prediction_breakdown": false,
  "show_presentation_analysis": false,
  "show_strength_weakness": false,
  "show_judge_analytics": false,
  "anonymous_mode": false
}
```

### `PUT /api/v1/analytics/visibility`

Organizer-only endpoint to update visibility settings.

**Request body:** Same shape as GET response.

**Response:** Updated visibility settings.

---

## 11. Database Plan

### Reuse Existing Tables

| Table | Used For |
|---|---|
| `teams` | Team names, IDs |
| `users` | Role detection (organizer vs team_leader) |
| `model_submissions` | Model metadata, version history, model_type, algorithm, metrics, training data |
| `predictions` | Per-match prediction data |
| `scores` | Per-match base_score, winner_points, scoreline_points, etc. |
| `actual_results` | Ground truth for accuracy comparison |
| `presentation_evaluations` | Per-round scores, judge_scores, grade, multiplier |
| `presentation_rounds` | Round names and ordering |
| `judges` | Judge names and IDs |
| `technical_evaluations` | Per-category technical scores |
| `leaderboard` | Final phase scores and ranking |

### New Table (if needed)

#### `analytics_visibility_settings`

Only required if the team prefers a separate model from extending `LeaderboardVisibilityModel`. See §3 for schema.

---

## 12. Frontend Design Plan

### Section: Overview Dashboard

A top-level summary with 4 metric cards:

| Card | Value |
|---|---|
| Top Team | Team with rank 1 + final score |
| Best Model Accuracy | Team with highest winner prediction % |
| Highest Presentation Score | Team with highest `final_presentation` |
| Highest Technical Score | Team with highest `total_score` |

### Tabbed Navigation

| Tab | Content |
|---|---|
| Model Analytics | §5 charts + per-team model table + model metadata display |
| Prediction Analytics | §5 accuracy breakdown + radar chart |
| Presentation Analytics | §6–8 rounds, criteria, judge analysis, cross-team ranking |
| Technical Analytics | §9 per-category breakdown + radar |

### Empty Data Handling

Analytics must gracefully handle missing data and never crash charts due to empty arrays, null values, or missing scores.

| Scenario | Display Message |
|---|---|
| No models uploaded | "No model analytics available yet." |
| No presentation scores | "Presentation analytics will appear after evaluation." |
| No prediction results | "Prediction analytics available after matches are scored." |
| No technical evaluations | "Technical analytics will appear after Phase 2 evaluation." |

Each section should render a clean empty state card rather than a blank page or broken chart.

### Theme

Use existing GOALGORITHM **dark theme**:
- Background: `--color-bg` (#0f0f1a / dark)
- Cards: `--color-card-bg`
- Primary accent: `--color-primary`
- Charts: Use a library consistent with the existing stack (e.g., Recharts or Chart.js)

### Responsiveness

Analytics pages must be usable on tablet and desktop. Charts should resize with the viewport.

---

## 13. Analytics Export

Export is **Organizer-only** functionality. Team leaders cannot export analytics data.

### PDF Report

A downloadable PDF containing:

- Final leaderboard (ranked team list with phase breakdowns)
- Key charts (phase contribution, model comparison, criteria radar)
- Strengths / weaknesses summary per team
- Model performance overview (accuracy table)

### CSV Export

Granular CSV exports per data domain:

| Export | Content |
|---|---|
| Final Scores CSV | All columns from the leaderboard view |
| Model Analytics CSV | Model metadata + accuracy metrics per team |
| Prediction Analytics CSV | Per-match prediction scores and accuracy flags |
| Presentation Analytics CSV | Per-round scores, grades, multipliers, criteria breakdown |
| Technical Evaluation CSV | Per-category scores per team |

Each CSV export includes a header row and one row per logical entity (team, match, or round).

---

## 14. Important Rules

| Rule | Rationale |
|---|---|
| **Read-only** | Analytics must never write to scoring, evaluation, or prediction tables |
| **Never modify competition scores** | Scores are the source of truth; analytics only reads them |
| **Never recalculate leaderboard differently** | Must use the `presentation_score` column from `leaderboard` as-is |
| **Use existing scoring engine outputs** | Do not duplicate scoring logic in analytics code |
| **All criteria must remain configurable** | Presentation criteria come from `ScoringConfig.presentation_criteria` |
| **Do not hardcode number of teams** | Always read dynamically from `teams` table |
| **Do not hardcode judges** | Always read dynamically from `judges` table |
| **Do not hardcode presentation rounds** | Always read dynamically from `presentation_rounds` table |
| **Respect organizer visibility settings** | Team leaders must only see what the organizer permits |
| **No implementation in this spec** | This document is purely a spec; implementation starts after review |

### Implementation Safety Rules

During implementation:

**DO NOT:**
- duplicate scoring formulas in analytics code
- create an alternative leaderboard calculation
- hardcode team names or IDs
- hardcode judge names or IDs
- hardcode presentation round names
- hardcode criteria names (read from config)
- modify any scoring or evaluation table in any analytics endpoint

**Analytics pipeline must follow:**

```
READ → PROCESS → VISUALIZE
```

**Never:**

```
READ → MODIFY → SAVE SCORES
```
