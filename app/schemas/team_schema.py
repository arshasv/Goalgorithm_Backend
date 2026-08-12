import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator



class TeamMemberCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255
    )
    employee_id: str | None = None

class TeamMemberUpdate(BaseModel):
    id: str | None = None
    name: str = Field(
        ...,
        min_length=1,
        max_length=255
    )
    employee_id: str | None = None



class TeamMemberResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID
    team_id: uuid.UUID

    name: str
    employee_id: str | None = None

    created_at: datetime



class TeamCreate(BaseModel):
    team_code: str = Field(
        ...,
        min_length=1,
        max_length=1,
    )
    team_name: str = Field(
        ...,
        min_length=1,
        max_length=255
    )
    team_leader: str = Field(
        ...,
        max_length=255
    )


class TeamUpdate(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255
    )

    team_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=1,
    )

    team_leader_name: str | None = None
    is_active: bool | None = None
    members: list[TeamMemberUpdate] | None = None



class TeamResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID

    team_id: str

    name: str

    # returning for old frontend compatibility
    code: str = ""

    team_code: str = ""

    team_name: str = ""

    team_leader: str = ""

    team_leader_name: str | None = None

    registered_at: datetime

    is_active: bool

    is_csv_managed: bool = False

    members: list[TeamMemberResponse] = []

    @model_validator(mode="after")
    def populate_aliases(self) -> "TeamResponse":
        self.team_leader_name = self.team_leader_name or ""
        self.team_code = self.team_code or self.team_id or ""
        self.team_name = self.team_name or self.name or ""
        self.team_leader = self.team_leader or self.team_leader_name or ""
        self.code = self.code or self.team_id or ""
        return self