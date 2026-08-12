# Team Management

## Purpose
Enables tournament organizers to bulk-upload team lists using Excel or CSV files, establishing a structured list of members for each of the five teams. It also manages authentication badges and coordinates permissions for member edits.

## User / Actor
- **Organizer**: Uploads CSV/Excel lists, manages teams, views all members.
- **Team Leader**: Registers team details, views team information.

## Organizer Excel/CSV Team Upload

### Supported File Types
- **CSV** (Comma Separated Values)
- **XLS** / **XLSX** (Microsoft Excel Spreadsheets)

### Upload Workflow
1. Organizer navigates to the **Teams** section and clicks **Upload Members CSV/Excel**.
2. Selects a file matching the correct format.
3. System parses the spreadsheet rows, validating the columns and contents.
4. If validation succeeds:
   - All previous members of the uploaded teams are cleared.
   - New members are stored.
   - The team is flagged as `is_csv_managed = true`.
5. If validation fails, an informative error is returned and no database write occurs.

### Ingestion Specifications

#### Input Columns
The uploaded file must contain the following headers:
- `SL No`
- `EmployeeID`
- `Name`
- `Seniority`
- `Gender`
- `Football Knowledge`
- `Group`

#### Stored Fields
Only the following fields are parsed and persisted in the database:
- **EmployeeID** (saved as `employee_id` in `team_members` table)
- **Name** (saved as `name` in `team_members` table)
- **Group** (defines the target team code, e.g. `A`, `B`, `C`, `D`, `E`)

#### Ignored Fields
The following fields are completely ignored by the system and are not saved, displayed, or audited:
- `SL No`
- `Seniority`
- `Gender`
- `Football Knowledge`

#### Group-to-Team Mapping
- The **Group** column value directly maps to the team's code.
- Only exactly five teams exist in the system: **A**, **B**, **C**, **D**, **E**.
- Any group code in the file that does not match one of these five teams (case-insensitive) will trigger a validation error.
- All legacy name mapping (e.g. A → Alpha) has been removed. Teams are named strictly A, B, C, D, E.

---

## Team Management Flow

### Ingested Members
Members uploaded via CSV/Excel are stored as references in the `team_members` table, linked to the respective team by `team_id`.

### Member Display Logic
When viewing a team, the members are displayed in a clean table showing only two columns:
1. **Name**
2. **Employee ID**

All other fields are ignored in the view.

### Manual Addition Restriction
- Once a team is imported via CSV/Excel, its `is_csv_managed` attribute is set to `true`.
- For any team marked as `is_csv_managed`, manual addition or modification of team members via the registration page or leader forms is disabled. This prevents unsynced manual changes from corrupting the official uploaded roster.

---

## Role Badge System

To provide clear visibility of privileges, a role badge is displayed in the top-right corner of the application:
- **Team Leader**: Displays a badge reading **"Team Leader"**.
- **Admin/Organizer**: Displays a badge reading **"Organiser"**.
- **No Role**: If the user has no role (or is not logged in), the badge is completely hidden.

### Styling & Contrast
The badge is designed to be clearly visible against the header background in both theme variations:
- **GOALGORITHM Executive (Light Mode)**: High contrast, leveraging a dark border/text or vivid accent color against the white header.
- **GOALGORITHM Night Stadium (Dark Mode)**: Vivid text and subtle background contrast.
- Uses semantic class mappings ensuring text never blends into the background.
