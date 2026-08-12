# Admin Scoring Configuration

## Overview
The Admin Scoring Configuration feature allows Organizers to dynamically adjust the rules, thresholds, and point allocations for the Base Scoring Engine and Evaluation phases without modifying code. 

## Features
- **Editable Thresholds**: Organizers can update parameters such as `probability_threshold`, `probability_medium_threshold`, `player_avg_threshold_exact`, and max scores across the technical/presentation evaluations.
- **Probability/Accuracy Rules**: Dynamic assignment of `probability_points_pass`, medium accuracy points, and failing points.
- **Future Matches Only**: Changes strictly apply to future scoring operations. Existing scores and leaderboards are not retroactively recalculated to preserve historical integrity.
- **Dynamic Grade Multipliers**: Update multiplier values for A, B, and C grades.

## APIs
- `GET /api/v1/admin/scoring-config` - List configurations
- `GET /api/v1/admin/scoring-config/active` - Get the current active configuration
- `PUT /api/v1/admin/scoring-config/{id}` - Update a configuration
- `POST /api/v1/admin/scoring-config/{id}/activate` - Activate a configuration
- `POST /api/v1/admin/scoring-config/reset` - Reset to system defaults

## Database Schema
Table: `scoring_configs`
Fields: `id`, `name`, `is_active`, `version`, and columns for every configurable parameter (e.g., `winner_points_correct`, `scoreline_points_exact`, `probability_threshold`). 
The `scores` table also holds an optional `config_id` to trace which configuration produced a specific score.

## Frontend
- **Page**: `Scoring Config` (`scoring-config.js`)
- **Access**: Organizer only
- **UI Elements**: Config form with validation, grouped by logical categories (Base Score, Probability, Player Performance, etc.). Includes warning messages that changes apply only to future matches.
