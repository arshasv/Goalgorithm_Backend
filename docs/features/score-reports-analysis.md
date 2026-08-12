# 📊 Score Reports & Normalization Analysis

## Feature Overview
The Score Reports & Normalization Analysis module is an **ORGANIZER ONLY** feature designed to provide complete transparency into the scoring journey of every team. It explains exactly *why* a team has a particular final score by showing how raw marks transform through multipliers, weighting, and normalization before contributing to the final leaderboard.

Team Leaders do NOT have access to this feature unless visibility is explicitly enabled in settings.

## Purpose
- **Transparency**: Easily explain final scores and resolve disputes.
- **Analysis**: Understand the impact of specific scoring mechanisms like multipliers and normalization formulas.
- **Insights**: Compare raw performance against mathematically weighted performance.

---

## Report Sections

### 1. Team Score Journey
For every team, the system tracks and displays the entire transformation of their score:
`Original Score` → `Multiplier Applied` → `Weighted Score` → `Normalization Formula` → `Final Contribution`

**Example:**
*Team A*
- **Phase 1 Prediction:**
  - Raw AI Score: 45 / 60
  - Normalized: 15 / 20
- **Technical Evaluation:**
  - Raw Technical Score: 42 / 50
  - Normalized: 20 / 20
- **Presentation Evaluation:**
  - Presentation Round 1: Raw Judge Average: 40.88 / 50 | Grade: A | Multiplier: x3 | Weighted: 122.64 / 150
  - Presentation Round 2: Raw Judge Average: 35 / 50 | Grade: B | Multiplier: x2 | Weighted: 70 / 150
  - Combined Presentation: 192.64 / 300
  - Normalized: 12.84 / 20
- **Final Competition:**
  - AI Phase: 15 / 60
  - Technical: 20 / 20
  - Presentation: 12.84 / 20
  - **Final:** 47.84 / 100

### 2. Before vs After Comparison Charts
Graphs visually comparing raw rankings versus final rankings.
- **Example:**
  - *Before Multipliers:* Team A (40.8), Team D (35.1), Team C (34.6)
  - *After Multipliers:* Team A (122.6), Team D (70.2), Team C (69.2)

### 3. Multiplier Impact Report
Highlights how grade-based multipliers alter team standings.
- **Formula:** `Multiplier Gain = Weighted Score - Raw Score`
- **Example:** Team A (Raw 40.88, Multiplier x3, Weighted 122.64) → Boost: +81.76 points

### 4. Phase Contribution Breakdown
Visualizes final score composition using stacked bar charts, radar charts, and percentage contribution graphs.
- **Composition Breakdown:** AI Prediction (60%), Technical Evaluation (20%), Presentation Evaluation (20%)

### 5. Rank Movement Analysis
Compares pre-processing rank vs final post-processing rank.
- **Example:** Team 'Goal Jyolsyan' (Raw Presentation Rank: 2 → Final Overall Rank: 1) → Movement: +1

---

## Access Control
- **Organizer:** Full default access.
- **Team Leader:** No access by default. (Future configuration via settings may allow visibility.)

> **Note:** This module serves purely as an **ANALYSIS layer**. It does not affect scoring calculations, leaderboards, existing APIs, or database values. It strictly READS existing scoring data.
