# Feature 18: Reports & Score Analysis

## Feature Overview

Organizer-only transparency feature providing detailed scoring journey reports. Includes team score breakdown, multiplier impact analysis, rank movement analysis, and phase contribution analysis. Pure analysis layer — never modifies data.

## Purpose & Requirements

- 4 report types: team breakdown, multiplier impact, rank analysis, phase contribution
- Organizer-only access
- Read-only: never modifies scoring/leaderboard data
- Detailed per-phase breakdown with raw/normalized scores
- Multiplier gain calculation
- Before/after rank comparison
- Phase composition visualization data

## Related Specifications

- `features/score-reports-analysis.md` — Report specification
- `api/reports-api.md` — Report API endpoints

## How the Feature Works Internally

### Report Types

#### 1. Team Score Journey (`team-breakdown`)
```python
def get_team_breakdown():
    for team in teams:
        yield {
            "team": team,
            "phase_1_ai": {
                "raw_score": total_earned,
                "normalized": phase1_score,
                "max_marks": 60,
            },
            "phase_2_technical": {
                "raw": technical_total,
                "normalized": technical_score,
                "max_marks": 20,
            },
            "phase_3_presentation": {
                "rounds": [...],
                "combined": combined_weighted,
                "normalized": presentation_score,
                "max_marks": 20,
            },
            "final_score": final_score,
        }
```

#### 2. Multiplier Impact (`multiplier-impact`)
```python
def get_multiplier_impact():
    for team in teams:
        yield {
            "grade": score.grade,
            "multiplier": score.multiplier,
            "raw_score": base_score,
            "weighted_score": earned_points,
            "gain": earned_points - base_score,
        }
```

#### 3. Rank Analysis (`rank-analysis`)
```python
def get_rank_analysis():
    return {
        "pre_processing": sorted_by_raw_base,
        "post_processing": sorted_by_final_score,
        "rank_movements": calculate_movements(pre, post),
    }
```

#### 4. Phase Contribution (`phase-contribution`)
```python
def get_phase_contribution():
    return {
        "composition_weights": {
            "ai": 60,
            "technical": 20,
            "presentation": 20,
        },
        "team_contributions": [
            {"team": t, "ai_pct": t.phase1/100*60, "tech_pct": t.technical/100*20, "pres_pct": t.presentation/100*20}
            for t in teams
        ],
    }
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/services/report_service.py` | 208 | All report generation logic |
| `app/api/report_routes.py` | 26 | Report endpoints |

### Key Functions

- `ReportService.get_team_breakdown()` → list of team score journeys
- `ReportService.get_multiplier_impact()` → multiplier gain analysis
- `ReportService.get_rank_analysis()` → before/after rank comparison
- `ReportService.get_phase_contribution()` → phase composition data

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/reports/team-breakdown` | ORGANIZER | Team score journey |
| GET | `/api/v1/reports/multiplier-impact` | ORGANIZER | Multiplier gain analysis |
| GET | `/api/v1/reports/rank-analysis` | ORGANIZER | Rank movement analysis |
| GET | `/api/v1/reports/phase-contribution` | ORGANIZER | Phase composition |

## External Script Support

| Script | Lines | Purpose |
|--------|-------|---------|
| `scripts/generate_reports.py` | 1044 | Generate MD/HTML/PDF reports |
| `scripts/generate_consolidated_prediction_report.py` | 632 | Cross-team PDF with charts |

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/integration/test_reports.py` | Report endpoint tests (4 tests) |

## Dependencies on Other Features

- **Scoring Engine** — Per-match score data
- **Phase Normalization** — Phase 1 scores
- **Ranking & Multiplier** — Grade and multiplier data
- **Leaderboard** — Final rankings

## Step-by-Step Implementation Sequence

1. Create ReportService with all report generators
2. Create report routes (organizer-only)
3. Implement team breakdown report
4. Implement multiplier impact report
5. Implement rank analysis report
6. Implement phase contribution report
7. Create report generation scripts
8. Write tests
