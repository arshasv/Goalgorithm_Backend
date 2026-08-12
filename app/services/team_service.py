from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.team_repository import TeamRepository
from app.models.user import UserModel
from app.models.enums import UserRole
from app.models.team import TeamModel
from app.models.team_member import TeamMemberModel
from app.schemas.team_schema import TeamCreate, TeamUpdate, TeamMemberCreate
import uuid

class TeamService:
    def __init__(self, repository: TeamRepository) -> None:
        self.repository = repository

    def update_my_team(self, body: TeamUpdate, current_user: UserModel, team: TeamModel) -> dict:
        if body.name is not None:
            team.name = body.name

        if body.team_leader_name is not None:
            team.team_leader_name = body.team_leader_name

        if body.is_active is not None and current_user.role == UserRole.ORGANIZER:
            team.is_active = body.is_active

        self.repository.save(team)
        return {
            "message": "Team updated",
            "team_id": str(team.id),
        }

    def add_member(self, body: TeamMemberCreate, current_user: UserModel, team: TeamModel) -> TeamMemberModel:
        if current_user.role != UserRole.ORGANIZER:
            raise HTTPException(status_code=403, detail="Only organizers can manage team members.")

        member = TeamMemberModel(
            team_id=team.id,
            name=body.name,
            employee_id=body.employee_id,
        )
        return self.repository.create_member(member)

    def list_teams(self, current_user: UserModel) -> list[TeamModel]:
        if current_user.role == UserRole.ORGANIZER:
            return self.repository.get_all()
        return self.repository.get_by_user_id(current_user.id)

    def create_team(self, body: TeamCreate, current_user: UserModel) -> TeamModel:
        if current_user.role != UserRole.ORGANIZER:
            raise HTTPException(status_code=403, detail="Only organizers can create teams.")

        team_code = body.team_code.strip().upper()
        VALID_TEAM_IDS = {"A", "B", "C", "D", "E"}
        if team_code not in VALID_TEAM_IDS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid team_code '{team_code}'. Must be one of: {', '.join(sorted(VALID_TEAM_IDS))}"
            )

        existing = self.repository.get_by_code(team_code)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Team with code '{team_code}' already exists."
            )

        team = TeamModel(
            id=uuid.uuid4(),
            team_id=team_code,
            name=body.team_name.strip(),
            code=team_code,
            team_leader_name=body.team_leader.strip(),
            is_csv_managed=False,
        )
        return self.repository.create(team)

    def upload_members(self, headers: list[str], data_rows: list[dict], current_user: UserModel) -> dict:
        if current_user.role != UserRole.ORGANIZER:
            raise HTTPException(status_code=403, detail="Only organizers can upload files.")

        col_map = {h.lower().replace(" ", "_"): h for h in headers}

        if "employeeid" not in col_map or "name" not in col_map or "group" not in col_map:
            raise HTTPException(
                status_code=400,
                detail="Members file must have columns: EmployeeID, Name, Group"
            )

        self.repository.delete_all_members()

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

            team = self.repository.get_by_code(group)
            member = TeamMemberModel(
                id=uuid.uuid4(),
                team_id=team.id if team else None,
                group_code=None if team else group,
                name=name,
                employee_id=employee_id,
            )
            self.repository.add_to_session(member)
            created += 1

        self.repository.commit()
        return {
            "message": f"Uploaded {created} member(s).",
            "created": created,
            "skipped": skipped,
        }

    def upload_teams(self, headers: list[str], data_rows: list[dict], current_user: UserModel) -> dict:
        if current_user.role != UserRole.ORGANIZER:
            raise HTTPException(status_code=403, detail="Only organizers can upload files.")

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

        self.repository.delete_all_members()
        self.repository.delete_all_teams()

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
            self.repository.add_to_session(team)
            self.repository.flush()
            teams_created += 1

        self.repository.commit()

        team_count = self.repository.count()
        import logging
        logging.getLogger(__name__).info("Uploaded %d teams; total teams = %d", teams_created, team_count)

        msg = f"Created {teams_created} team(s)."
        return {
            "message": msg,
            "teams_created": teams_created,
        }

    def update_team(self, team_id: str, body: TeamUpdate, current_user: UserModel) -> dict:
        if current_user.role != UserRole.ORGANIZER:
            raise HTTPException(status_code=403, detail="Only organizers can update teams.")

        try:
            team_uuid = uuid.UUID(team_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid team ID format")

        team = self.repository.get_by_id(team_uuid)
        if not team:
            raise HTTPException(
                status_code=404,
                detail="Team not found"
            )

        if body.name is not None:
            team.name = body.name

        VALID_TEAM_IDS = {"A", "B", "C", "D", "E"}
        if body.team_code is not None:
            new_code = body.team_code.strip().upper()
            if new_code not in VALID_TEAM_IDS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid team_code '{new_code}'. Must be one of: {', '.join(sorted(VALID_TEAM_IDS))}"
                )
            existing = self.repository.get_by_code(new_code)
            if existing and existing.id != team_uuid:
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
            current_members = {str(m.id): m for m in team.members}
            incoming_ids = set()
            for m_data in body.members:
                if m_data.id and m_data.id in current_members:
                    mem = current_members[m_data.id]
                    mem.name = m_data.name
                    mem.employee_id = m_data.employee_id
                    incoming_ids.add(m_data.id)
                else:
                    new_mem = TeamMemberModel(
                        team_id=team.id,
                        name=m_data.name,
                        employee_id=m_data.employee_id
                    )
                    self.repository.add_to_session(new_mem)

            for m_id, mem in current_members.items():
                if m_id not in incoming_ids:
                    self.repository.delete_from_session(mem)

        self.repository.save(team)
        return {
            "message": "Team updated",
            "team_id": str(team.id),
        }

    def remove_member(self, member_id: str, current_user: UserModel, team: TeamModel) -> dict:
        if current_user.role != UserRole.ORGANIZER:
            raise HTTPException(status_code=403, detail="Only organizers can manage team members.")

        try:
            member_uuid = uuid.UUID(member_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid member ID format")

        member = self.repository.get_member(team.id, member_uuid)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        self.repository.delete_member(member)
        return {"message": "Member removed"}

    def update_member(self, member_id: str, body: TeamMemberCreate, current_user: UserModel, team: TeamModel) -> TeamMemberModel:
        if current_user.role != UserRole.ORGANIZER:
            raise HTTPException(status_code=403, detail="Only organizers can manage team members.")

        try:
            member_uuid = uuid.UUID(member_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")

        member = self.repository.get_member(team.id, member_uuid)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        member.name = body.name
        member.employee_id = body.employee_id
        return self.repository.save(member)

    def list_team_members_admin(self, team_id: str) -> list[TeamMemberModel]:
        try:
            team_uuid = uuid.UUID(team_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid team ID format")

        team = self.repository.get_by_id(team_uuid)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        return self.repository.get_members_by_team(team.id)

    def add_team_member_admin(self, team_id: str, body: TeamMemberCreate) -> TeamMemberModel:
        try:
            team_uuid = uuid.UUID(team_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid team ID format")

        team = self.repository.get_by_id(team_uuid)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        member = TeamMemberModel(
            team_id=team.id,
            name=body.name,
            employee_id=body.employee_id,
        )
        return self.repository.create_member(member)

    def remove_team_member_admin(self, team_id: str, member_id: str) -> dict:
        try:
            team_uuid = uuid.UUID(team_id)
            member_uuid = uuid.UUID(member_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")

        team = self.repository.get_by_id(team_uuid)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        member = self.repository.get_member(team.id, member_uuid)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        self.repository.delete_member(member)
        return {"message": "Member removed"}

    def update_team_member_admin(self, team_id: str, member_id: str, body: TeamMemberCreate) -> TeamMemberModel:
        try:
            team_uuid = uuid.UUID(team_id)
            member_uuid = uuid.UUID(member_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")

        team = self.repository.get_by_id(team_uuid)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        member = self.repository.get_member(team.id, member_uuid)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        member.name = body.name
        member.employee_id = body.employee_id
        return self.repository.save(member)
