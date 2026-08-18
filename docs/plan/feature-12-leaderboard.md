# Feature 12: Leaderboard

## Feature Overview

Aggregates Phase 1 (0-60), Phase 2 Technical (0-20), and Phase 3 Presentation (0-20) scores into a final leaderboard. Teams ranked by grand total (max 100). Supports visibility filtering, leaderboard freezing (snapshot), and public endpoints.

## Purpose & Requirements

- Combine phase1 + technical + presentation into final_score (capped at 100)
- Rank teams by final_score descending
- Tie-breaking: ai_accuracy → technical → presentation
- Visibility filtering based on LeaderboardVisibilityModel
- Leaderboard freezing for historical snapshots
- Public endpoint for unauthenticated access

## Related Specifications

- `features/leaderboard.md` — Leaderboard specification
- `api/leaderboard-api.md` — Leaderboard API endpoints
- `architecture/leaderboard-architecture.md` — Leaderboard data flow

## How the Feature Works Internally

### Leaderboard Calculation
```python
def calculate_leaderboard(team_scores):
    for team in team_scores:
        team.final_score = min(
            team.phase1_score + team.technical_score + team.presentation_score,
            100.0
        )

    # Sort by final_score descending
    # Tie-break: phase1 > technical > presentation
    ranked = sorted(team_scores, key=lambda t: (t.final_score, t.phase1_score, t.technical_score, t.presentation_score), reverse=True)

    # Assign ranks with tie handling
    for i, team in enumerate(ranked):
        team.rank = i + 1

    return ranked
```

### Visibility Filtering
```python
def filter_leaderboard(leaderboard, visibility_settings, user_role):
    if user_role == "ORGANIZER":
        return leaderboard  # Full access

    # Apply visibility flags
    filtered = []
    for entry in leaderboard:
        filtered_entry = {}
        if visibility_settings.show_rank:
            filtered_entry["rank"] = entry.rank
        if visibility_settings.show_team_name:
            filtered_entry["team_name"] = entry.team_name
        # ... more flags
        filtered.append(filtered_entry)
    return filtered
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/services/leaderboard_service.py` | 84 | Leaderboard calculation + visibility |
| `app/repositories/leaderboard_repository.py` | 82 | Leaderboard CRUD + visibility queries |
| `app/api/leaderboard_routes.py` | 119 | Leaderboard endpoints |
| `app/api/leaderboard_settings_routes.py` | 46 | Visibility settings endpoints |
| `app/models/leaderboard.py` | 33 | LeaderboardModel ORM |
| `app/models/leaderboard_visibility.py` | 62 | LeaderboardVisibilityModel ORM |

### Key Functions

- `LeaderboardService.calculate_leaderboard()` → Ranked leaderboard
- `LeaderboardService.get_leaderboard(visible)` → Filtered leaderboard
- `LeaderboardService.freeze_leaderboard()` → Snapshot
- `LeaderboardRepository.save_leaderboard(entries)` → Persist
- `LeaderboardRepository.get_frozen()` → Historical snapshot

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/leaderboard` | Any | Get leaderboard (filtered for teams) |
| POST | `/api/v1/leaderboard/recalculate` | ORGANIZER | Recalculate leaderboard |
| GET | `/api/v1/leaderboard/frozen` | Any | Get frozen leaderboard |
| GET | `/api/v1/admin/leaderboard/settings` | ORGANIZER | Get visibility settings |
| PUT | `/api/v1/admin/leaderboard/settings` | ORGANIZER | Update visibility settings |

## Database/Data Models Involved

### `leaderboards` Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| team_id | UUID | FK → teams.id, unique |
| rank | Integer | indexed |
| phase1_score | Float | CHECK 0-60 |
| technical_score | Float | CHECK 0-20 |
| presentation_score | Float | CHECK 0-20 |
| final_score | Float | CHECK 0-100 |
| is_frozen | Boolean | default False |
| frozen_at | DateTime | nullable |

### `leaderboard_visibility` Table (Singleton)
20+ boolean flags controlling what team leaders can see (see Feature 14).

## Error Handling

| Scenario | HTTP Code |
|----------|-----------|
| Score out of range | 400 LEADERBOARD_ERROR |
| No scores to rank | 200 empty list |

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_leaderboard.py` | Total, ranking, tie-breaking, max cap (17 tests) |

## Dependencies on Other Features

- **Phase Normalization** — Phase 1 scores
- **Technical Evaluation** — Phase 2 scores
- **Presentation Evaluation** — Phase 3 scores
- **Leaderboard Visibility** — Filtering settings

## Step-by-Step Implementation Sequence

1. Create LeaderboardModel ORM
2. Create leaderboard_service.py with calculation logic
3. Create leaderboard_repository.py with CRUD
4. Create leaderboard_routes.py with endpoints
5. Implement tie-breaking logic
6. Implement visibility filtering
7. Implement leaderboard freezing
8. Create leaderboard settings routes
9. Run Alembic migration
10. Write comprehensive tests
