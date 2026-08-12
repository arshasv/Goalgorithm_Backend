# Model Submission

## Overview
The Model Submission feature allows participating teams to securely upload their prediction machine learning models (code or serialized models) for organizational review, evaluation, and archival.

## Model Performance Concept
Currently, analytics are based mostly on leaderboard results and match prediction scores (competition match performance). This does NOT reflect the actual model performance natively. 

The future Model Performance system introduces actual AI model evaluation workflows.

**Version Control:**
Each team uploads AI models during the competition.
Example for Team A:
- `model_v1`
- `model_v2`
- `model_v3`

All model versions are securely stored. The latest active model is evaluated for final metrics, while old versions remain available for history, comparison, and team improvement tracking.

## Features
- **Supported ML Files**: Accepts standard model and code formats including `.zip`, `.tar.gz`, `.py`, and `.ipynb`. Maximum file size is strictly enforced (50MB).
- **Upload Workflow**: Team Leaders use a dedicated upload interface. Uploads are securely mapped to the authenticated Team ID.
- **Time Window Locking**: Submissions are strictly constrained to an "Upload Window". If closed, new uploads are blocked with `403 Forbidden`. Existing submissions are never altered during rejected attempts.
- **Organizer Controls**: Organizers can dynamically enable/disable the window and set specific start/end timestamps via the UI.

## Model Evaluation Workflow
The organizer evaluates submitted models using the following flow:
1. Team uploads models
2. Organizer selects an evaluation approach
3. Latest active models are tested
4. Performance metrics are generated/stored
5. Analytics dashboard displays insights

### Evaluation Methods
The system supports two methods:
1. **Future Automatic Evaluation**: The backend will automatically load the submitted model, run it against a hidden test dataset, collect predictions, compare against actual results, and calculate metrics.
2. **Manual Evaluation Upload**: The organizer can upload evaluation results manually. This is highly useful because different teams may submit models with wildly different structures. Analytics rely on the stored evaluation results, not directly inspecting model files on the fly.

## APIs
- `GET /api/v1/upload-window` - Get current window status and times.
- `PUT /api/v1/upload-window` - Organizer endpoint to update window constraints.
- `POST /api/v1/teams/my-team/model` - Team Leader endpoint to upload a model (enforces window and tracks versioning).
- `GET /api/v1/teams/my-team/model` - View the active uploaded model details.
- `GET /api/v1/admin/models` - Organizer endpoint to list all team submissions.
- `GET /api/v1/admin/models/{id}/download` - Organizer endpoint to securely download a team's model file.

*(Future endpoints will be added for `/api/v1/models/evaluate` for evaluation integration).*

## Database Schema
- **Table: `upload_window_config`**
  - Tracks `is_enabled`, `start_time`, `end_time`.

- **Table: `model_submissions`**
  - Stores every uploaded model from every team.
  - Fields: `id`, `team_id`, `model_name`, `file_name`, `file_path`, `version`, `uploaded_at`, `is_active`, `status` (`Uploaded`, `Testing`, `Evaluated`, `Failed`), `model_type`, `description`, `notes`.
  - Example tracking: 
    - Model Name: GoalGPT Predictor v3
    - Type: Random Forest + LSTM
    - Description: Uses historical FIFA data, player statistics and xG features.

- **Table: `model_evaluations`** (Future)
  - Stores evaluation results after testing models.
  - Fields: `id`, `model_id`, `team_id`, `overall_accuracy`, `winner_prediction_accuracy`, `scoreline_accuracy`, `probability_accuracy`, `player_prediction_accuracy`, `matches_tested`, `average_score`, `final_ai_score`, `strength_category`, `weakness_category`, `evaluation_notes`, `evaluated_at`.
  - **Relationship:** `teams` -> `model_submissions` -> `model_evaluations` -> `analytics dashboard`

## Frontend
- **Team Leader Page**: `Model Submission`
  - Displays current submission details, window status (Open/Closed), version history, and an upload form when the window is active.
- **Organizer Page**: `Model Management`
  - Displays a configuration panel to set the Upload Window.
  - Lists all teams with their corresponding submission status and secure download buttons.
