from pydantic import BaseModel, Field

class AdminCreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=255)
    team_name: str = Field(..., min_length=1, max_length=255)
    team_leader_name: str = Field(..., min_length=1, max_length=255)


class AdminCreateUserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    team_id: str | None = None
    team_name: str | None = None
