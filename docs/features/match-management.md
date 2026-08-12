# Match Management

## Purpose
Enables tournament organizers to manage the schedule of matches. This includes manual creation, updating, deletion, and bulk uploading via CSV.

## User / Actor
- **Organizer**: Has full CRUD permissions and bulk upload capabilities.
- **Team Leader**: Read-only access to view the schedule.

## Features

### Match Creation and Editing
Organizers can manually create matches through the application. Each match tracks:
- **Match Number**
- **Home Team & Away Team** (Real-world teams, e.g., Brazil, Argentina)
- **Scheduled Kickoff Time**
- **Freeze Deadline**: The point after which predictions can no longer be submitted (automatically defaults to 1 hour prior to kickoff).
- **Status**: SCHEDULED, FROZEN, COMPLETED, RESULT_ENTERED, SCORED

### CSV Schedule Upload
To quickly populate the tournament schedule, organizers can upload a CSV file containing all match details.
- **Accepted Format**: CSV only.
- **Required Columns**: `match_number`, `home_team`, `away_team`, `kickoff_date`.
- The system parses ISO-8601 or simple date string formats for the `kickoff_date` and automatically assigns the prediction freeze deadline to 1 hour before the kickoff time.

### Status Tracking
Matches automatically progress through status states affecting the system's behavior:
1. **SCHEDULED**: Future match, predictions allowed.
2. **FROZEN**: Freeze deadline passed, predictions blocked.
3. **COMPLETED**: Match ended.
4. **RESULT_ENTERED**: Ground-truth actual results entered by Organizer.
5. **SCORED**: Points calculated for all participating AI teams.
