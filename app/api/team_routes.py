import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_team,
    get_current_user,
    get_current_organizer,
)

from app.database.session import get_db

from app.models.enums import UserRole
from app.models.team import TeamModel
from app.models.team_member import TeamMemberModel
from app.models.user import UserModel

from app.schemas.team_schema import (
    TeamMemberCreate,
    TeamCreate,
    TeamUpdate,
    TeamResponse,
)

logger = logging.getLogger(__name__)

VALID_TEAM_IDS = {"A", "B", "C", "D", "E"}

router = APIRouter(
    prefix="/teams",
    tags=["teams"]
)


@router.get("/my-team", response_model=TeamResponse)
def get_my_team(
    team: TeamModel = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    return team



@router.put("/my-team")
def update_my_team(
    body: TeamUpdate,
    current_user: UserModel = Depends(get_current_user),
    team: TeamModel = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    if body.name is not None:

        team.name = body.name


    if body.team_leader_name is not None:
        team.team_leader_name = body.team_leader_name

    if body.is_active is not None and current_user.role == UserRole.ORGANIZER:
        team.is_active = body.is_active


    db.commit()
    db.refresh(team)


    return {
        "message": "Team updated",
        "team_id": str(team.id),
    }



@router.post("/my-team/members", status_code=201)
def add_member(
    body: TeamMemberCreate,
    current_user: UserModel = Depends(get_current_user),
    team: TeamModel = Depends(get_current_team),
    db: Session = Depends(get_db),
):

    member = TeamMemberModel(
        team_id=team.id,
        name=body.name,
        employee_id=body.employee_id,
    )

    db.add(member)
    db.commit()
    db.refresh(member)

    return member



@router.get("", response_model=list[TeamResponse])
def list_teams(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if current_user.role == UserRole.ORGANIZER:
        return db.query(TeamModel).all()


    return (
        db.query(TeamModel)
        .filter(
            TeamModel.user_id == current_user.id
        )
        .all()
    )



@router.post("", status_code=201)
def create_team(
    body: TeamCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ORGANIZER:
        raise HTTPException(status_code=403, detail="Only organizers can create teams.")

    team_code = body.team_code.strip().upper()
    if team_code not in VALID_TEAM_IDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid team_code '{team_code}'. Must be one of: {', '.join(sorted(VALID_TEAM_IDS))}"
        )

    existing = db.query(TeamModel).filter(TeamModel.team_id == team_code).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Team with code '{team_code}' already exists."
        )

    import uuid
    team = TeamModel(
        id=uuid.uuid4(),
        team_id=team_code,
        name=body.team_name.strip(),
        code=team_code,
        team_leader_name=body.team_leader.strip(),
        is_csv_managed=False,
    )

    db.add(team)
    db.commit()
    db.refresh(team)

    return TeamResponse.model_validate(team)



def parse_uploaded_file(file: UploadFile) -> tuple[list[str], list[dict]]:
    import csv
    import io
    filename = file.filename.lower()
    data_rows = []
    headers = []

    if filename.endswith(".csv"):
        try:
            content = file.file.read().decode("utf-8")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid file encoding: {str(e)}")

        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            raise HTTPException(status_code=400, detail="CSV is empty or invalid.")

        headers = [h.strip() for h in reader.fieldnames]
        reader.fieldnames = headers
        for row in reader:
            data_rows.append({k: (v or "").strip() for k, v in row.items()})

    elif filename.endswith(".xlsx"):
        import openpyxl
        try:
            file_bytes = file.file.read()
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
            sheet = wb.active
            rows = list(sheet.iter_rows(values_only=True))
            if not rows:
                raise HTTPException(status_code=400, detail="Excel file is empty.")
            header_row_idx = 0
            while header_row_idx < len(rows) and all(v is None for v in rows[header_row_idx]):
                header_row_idx += 1
            if header_row_idx >= len(rows):
                raise HTTPException(status_code=400, detail="Excel file is empty.")
            headers = [str(h).strip() if h is not None else "" for h in rows[header_row_idx]]
            num_cols = len(headers)
            for r in rows[header_row_idx + 1:]:
                if all(v is None or str(v).strip() == "" for v in r):
                    continue
                row_dict = {}
                for col_idx, h in enumerate(headers):
                    if h:
                        val = r[col_idx] if col_idx < len(r) else None
                        row_dict[h] = str(val).strip() if val is not None else ""
                data_rows.append(row_dict)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=400, detail=f"Failed to parse XLSX file: {str(e)}")

    elif filename.endswith(".xls"):
        import xlrd
        try:
            file_bytes = file.file.read()
            wb = xlrd.open_workbook(file_contents=file_bytes)
            sheet = wb.sheet_by_index(0)
            if sheet.nrows == 0:
                raise HTTPException(status_code=400, detail="Excel file is empty.")
            
            header_row_idx = 0
            while header_row_idx < sheet.nrows:
                row_vals = [sheet.cell_value(header_row_idx, col) for col in range(sheet.ncols)]
                if not all(v == "" or v is None for v in row_vals):
                    break
                header_row_idx += 1
            if header_row_idx >= sheet.nrows:
                raise HTTPException(status_code=400, detail="Excel file is empty.")
            
            headers = [str(sheet.cell_value(header_row_idx, col)).strip() for col in range(sheet.ncols)]
            num_cols = len(headers)
            
            for row_idx in range(header_row_idx + 1, sheet.nrows):
                row_vals = [sheet.cell_value(row_idx, col) for col in range(sheet.ncols)]
                if all(v == "" or v is None for v in row_vals):
                    continue
                row_dict = {}
                for col_idx, h in enumerate(headers):
                    if h:
                        val = row_vals[col_idx] if col_idx < len(row_vals) else None
                        if isinstance(val, float) and val.is_integer():
                            val = int(val)
                        row_dict[h] = str(val).strip() if val is not None else ""
                data_rows.append(row_dict)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=400, detail=f"Failed to parse XLS file: {str(e)}")
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a .csv, .xls, or .xlsx file."
        )

    return headers, data_rows


@router.post("/upload-members")
def upload_members_csv(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ORGANIZER:
        raise HTTPException(status_code=403, detail="Only organizers can upload files.")

    import uuid
    headers, data_rows = parse_uploaded_file(file)
    col_map = {h.lower().replace(" ", "_"): h for h in headers}

    if "employeeid" not in col_map or "name" not in col_map or "group" not in col_map:
        raise HTTPException(
            status_code=400,
            detail="Members file must have columns: EmployeeID, Name, Group"
        )

    db.query(TeamMemberModel).delete()
    db.flush()

    created = 0
    skipped = 0
    for row in data_rows:
        employee_id = (row.get(col_map["employeeid"]) or "").strip()
        name = (row.get(col_map["name"]) or "").strip()
        group = (row.get(col_map["group"]) or "").strip().upper()

        if not name or not group:
            skipped += 1
            continue
        if not employee_id:
            employee_id = None

        team = db.query(TeamModel).filter(TeamModel.team_id == group).first()
        member = TeamMemberModel(
            id=uuid.uuid4(),
            team_id=team.id if team else None,
            group_code=None if team else group,
            name=name,
            employee_id=employee_id,
        )
        db.add(member)
        created += 1

    db.commit()
    return {
        "message": f"Uploaded {created} member(s).",
        "created": created,
        "skipped": skipped,
    }


@router.post("/upload-teams")
def upload_teams_csv(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ORGANIZER:
        raise HTTPException(status_code=403, detail="Only organizers can upload files.")

    import uuid

    try:
        headers, data_rows = parse_uploaded_file(file)
    except Exception as e:
        logger.error("Failed to parse upload file: %s", str(e))
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    col_map = {h.lower().replace(" ", "_"): h for h in headers}

    if "team" not in col_map or "team_leader" not in col_map or "team_name" not in col_map:
        raise HTTPException(
            status_code=400,
            detail="Team Details file must have columns: Timestamp, Team, Team Leader, Team Name"
        )

    if not data_rows:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file contains no data rows."
        )

    db.query(TeamMemberModel).delete()
    db.flush()
    db.query(TeamModel).delete()
    db.flush()

    teams_created = 0

    for row in data_rows:
        team_code = (row.get(col_map["team"]) or "").strip().upper()
        team_leader_name = (row.get(col_map["team_leader"]) or "").strip()
        team_name = (row.get(col_map["team_name"]) or "").strip()

        if not team_code or not team_name:
            continue

        team = TeamModel(
            id=uuid.uuid4(),
            team_id=team_code,
            name=team_name,
            code=team_code,
            team_leader_name=team_leader_name,
            is_csv_managed=True,
        )
        db.add(team)
        db.flush()
        teams_created += 1

    db.commit()

    team_count = db.query(TeamModel).count()
    logger.info("Uploaded %d teams; total teams = %d", teams_created, team_count)

    msg = f"Created {teams_created} team(s)."
    return {
        "message": msg,
        "teams_created": teams_created,
    }



@router.get("/template/members")
def download_members_template(
    _organizer: UserModel = Depends(get_current_organizer),
):
    import io
    import csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["EmployeeID", "Name", "Group"])
    output.seek(0)
    from starlette.responses import StreamingResponse
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=members_template.csv"},
    )


@router.get("/template/teams")
def download_teams_template(
    _organizer: UserModel = Depends(get_current_organizer),
):
    import io
    import csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "Team", "Team Leader", "Team Name"])
    output.seek(0)
    from starlette.responses import StreamingResponse
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=teams_template.csv"},
    )


@router.put("/{team_id}")
def update_team(
    team_id: str,
    body: TeamUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ORGANIZER:
        raise HTTPException(status_code=403, detail="Only organizers can update teams.")

    import uuid
    try:
        team_uuid = uuid.UUID(team_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid team ID format")

    team = (
        db.query(TeamModel)
        .filter(
            TeamModel.id == team_uuid
        )
        .first()
    )


    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found"
        )


    if body.name is not None:
        team.name = body.name

    if body.team_code is not None:
        new_code = body.team_code.strip().upper()
        if new_code not in VALID_TEAM_IDS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid team_code '{new_code}'. Must be one of: {', '.join(sorted(VALID_TEAM_IDS))}"
            )
        existing = db.query(TeamModel).filter(TeamModel.team_id == new_code, TeamModel.id != team_uuid).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Team with code '{new_code}' already exists."
            )
        team.team_id = new_code
        team.code = new_code

    if body.team_leader_name is not None:
        team.team_leader_name = body.team_leader_name


    if body.is_active is not None:
        team.is_active = body.is_active

    if body.members is not None:
        
        # Current members
        current_members = {str(m.id): m for m in team.members}
        
        # Process incoming members
        incoming_ids = set()
        for m_data in body.members:
            if m_data.id and m_data.id in current_members:
                # Update existing
                mem = current_members[m_data.id]
                mem.name = m_data.name
                mem.employee_id = m_data.employee_id
                incoming_ids.add(m_data.id)
            else:
                # Add new
                new_mem = TeamMemberModel(
                    team_id=team.id,
                    name=m_data.name,
                    employee_id=m_data.employee_id
                )
                db.add(new_mem)
                
        # Remove deleted
        for m_id, mem in current_members.items():
            if m_id not in incoming_ids:
                db.delete(mem)

    db.commit()
    db.refresh(team)
    return {
        "message": "Team updated",
        "team_id": str(team.id),
    }


@router.delete("/my-team/members/{member_id}")
def remove_member(
    member_id: str,
    current_user: UserModel = Depends(get_current_user),
    team: TeamModel = Depends(get_current_team),
    db: Session = Depends(get_db),
):

    import uuid
    try:
        member_uuid = uuid.UUID(member_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid member ID format")

    member = (
        db.query(TeamMemberModel)
        .filter(
            TeamMemberModel.team_id == team.id,
            TeamMemberModel.id == member_uuid
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    db.delete(member)
    db.commit()

    return {"message": "Member removed"}

@router.put("/my-team/members/{member_id}")
def update_member(
    member_id: str,
    body: TeamMemberCreate,
    current_user: UserModel = Depends(get_current_user),
    team: TeamModel = Depends(get_current_team),
    db: Session = Depends(get_db),
):

    import uuid
    try:
        member_uuid = uuid.UUID(member_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    member = (
        db.query(TeamMemberModel)
        .filter(
            TeamMemberModel.team_id == team.id,
            TeamMemberModel.id == member_uuid
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
        
    member.name = body.name
    member.employee_id = body.employee_id
    db.commit()
    db.refresh(member)
    return member


@router.get("/{team_id}/members")
def list_team_members_admin(
    team_id: str,
    _organizer: UserModel = Depends(get_current_organizer),
    db: Session = Depends(get_db),
):
    import uuid
    try:
        team_uuid = uuid.UUID(team_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid team ID format")
    team = db.query(TeamModel).filter(TeamModel.id == team_uuid).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    members = db.query(TeamMemberModel).filter(TeamMemberModel.team_id == team.id).all()
    return members


@router.post("/{team_id}/members", status_code=201)
def add_team_member_admin(
    team_id: str,
    body: TeamMemberCreate,
    _organizer: UserModel = Depends(get_current_organizer),
    db: Session = Depends(get_db),
):
    import uuid
    try:
        team_uuid = uuid.UUID(team_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid team ID format")
    team = db.query(TeamModel).filter(TeamModel.id == team_uuid).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    member = TeamMemberModel(
        team_id=team.id,
        name=body.name,
        employee_id=body.employee_id,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.delete("/{team_id}/members/{member_id}")
def remove_team_member_admin(
    team_id: str,
    member_id: str,
    _organizer: UserModel = Depends(get_current_organizer),
    db: Session = Depends(get_db),
):
    import uuid
    try:
        team_uuid = uuid.UUID(team_id)
        member_uuid = uuid.UUID(member_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    team = db.query(TeamModel).filter(TeamModel.id == team_uuid).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    member = db.query(TeamMemberModel).filter(
        TeamMemberModel.team_id == team.id,
        TeamMemberModel.id == member_uuid
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return {"message": "Member removed"}


@router.put("/{team_id}/members/{member_id}")
def update_team_member_admin(
    team_id: str,
    member_id: str,
    body: TeamMemberCreate,
    _organizer: UserModel = Depends(get_current_organizer),
    db: Session = Depends(get_db),
):
    import uuid
    try:
        team_uuid = uuid.UUID(team_id)
        member_uuid = uuid.UUID(member_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    team = db.query(TeamModel).filter(TeamModel.id == team_uuid).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    member = db.query(TeamMemberModel).filter(
        TeamMemberModel.team_id == team.id,
        TeamMemberModel.id == member_uuid
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    member.name = body.name
    member.employee_id = body.employee_id
    db.commit()
    db.refresh(member)
    return member