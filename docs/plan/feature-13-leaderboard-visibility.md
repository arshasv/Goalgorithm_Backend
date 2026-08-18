# Feature 13: Leaderboard Visibility

## Feature Overview

Singleton configuration table controlling what data team leaders can see on the leaderboard and analytics dashboards. Organizers see everything; team leaders see only enabled sections. Includes a master toggle and 20+ granular boolean flags.

## Purpose & Requirements

- Master toggle to enable/disable all analytics for team leaders
- Granular flags for leaderboard fields (rank, team name, scores, etc.)
- Granular flags for analytics sections (model, prediction, technical, presentation, judge)
- Organizers always bypass visibility checks
- Real-time filtering on API responses

## Related Specifications

- `features/ANALYTICS_MODULE.md` — Analytics visibility system
- `database/schema-design.md` — LeaderboardVisibilityModel

## How the Feature Works Internally

### Visibility Model (`LeaderboardVisibilityModel`)
Singleton row with 20+ boolean fields:

**Leaderboard Flags:**
- `show_all_teams_leaderboard`, `show_rank`, `show_team_name`
- `show_phase_scores`, `show_phase_1_score`, `show_technical_score`, `show_presentation_score`
- `show_final_score`, `show_total_points`, `show_score_breakdown`
- `show_predictions_count`, `show_correct_predictions`

**Analytics Flags:**
- `analytics_visibility_enabled` (master toggle)
- `show_model_analytics`, `show_prediction_analytics`
- `show_technical_analytics`, `show_presentation_analytics`
- `show_overall_comparison`, `show_judge_analytics`, `show_leaderboard_analytics`

### Visibility Check Pattern
```python
def check_visibility(setting_name, visibility_model):
    if not visibility_model.analytics_visibility_enabled:
        raise HTTPException(403, "Analytics not visible")
    if not getattr(visibility_model, setting_name):
        raise HTTPException(403, "Section not visible")
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/models/leaderboard_visibility.py` | 62 | Singleton visibility model |
| `app/schemas/leaderboard_visibility_schema.py` | 55 | Update/Response schemas |
| `app/repositories/leaderboard_repository.py` | 82 | Visibility CRUD queries |
| `app/api/leaderboard_settings_routes.py` | 46 | Admin settings endpoints |
| `app/api/analytics_routes.py` | 122 | Analytics with visibility checks |

### Key Functions

- `LeaderboardRepository.get_visibility()` → Get or create singleton
- `LeaderboardRepository.update_visibility(data)` → Update flags
- `check_analytics_visibility(section, db, current_user)` → Raise 403 if hidden

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/admin/leaderboard/settings` | ORGANIZER | Get all visibility settings |
| PUT | `/api/v1/admin/leaderboard/settings` | ORGANIZER | Update visibility settings |

Analytics endpoints check visibility per-request for TEAM_LEADER role.

## Database/Data Models Involved

### `leaderboard_visibility` Table (Singleton)
All columns are Boolean with defaults (mostly True for organizer control).

## Error Handling

| Scenario | HTTP Code |
|----------|-----------|
| Team leader accessing hidden section | 403 FORBIDDEN |
| Analytics master toggle off | 403 ANALYTICS_DISABLED |

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_leaderboard_visibility.py` | CRUD, filtering, role-based access (8 tests) |

## Dependencies on Other Features

- **Leaderboard** — Visibility applied to leaderboard responses
- **Analytics** — Visibility checked per analytics section
- **Authentication** — Role determines visibility enforcement

## Step-by-Step Implementation Sequence

1. Create LeaderboardVisibilityModel ORM (singleton pattern)
2. Create Pydantic schemas for update/response
3. Create repository methods for get/update
4. Create admin settings routes
5. Add visibility checks to analytics routes
6. Add visibility filtering to leaderboard responses
7. Run Alembic migration
8. Write tests
