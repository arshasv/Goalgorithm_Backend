from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):

    model_config = ConfigDict(
        extra="ignore"
    )

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
    )

    email: str = Field(
        ...,
        min_length=5,
        max_length=255,
    )

    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
    )

    # team name replaces team code
    team_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    team_leader_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )



class LoginRequest(BaseModel):

    email: str = Field(
        ...,
        min_length=5,
        max_length=255,
    )

    password: str = Field(
        ...,
        min_length=1,
    )



class UserInfo(BaseModel):

    id: str

    username: str

    email: str

    role: str

    team_id: str | None = None

    team_name: str | None = None



class LoginResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

    user: UserInfo



class RegisterResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

    user: UserInfo



class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    email: str = Field(..., min_length=5, max_length=255)


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    email: str = Field(..., min_length=5, max_length=255)
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6, max_length=128)


class ResetPasswordResponse(BaseModel):
    message: str


class UserResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )


    id: str

    username: str

    email: str

    role: str

    team_id: str | None = None

    team_name: str | None = None

    created_at: str