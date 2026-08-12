import json
import os
import tempfile
import uuid
from collections.abc import Generator
from pathlib import Path

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mktemp(suffix='.db')}")
os.environ.setdefault("SECRET_KEY", "test_secret_key")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event, text  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
import pytest  # noqa: E402

from app.auth.auth_service import create_access_token, hash_password  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.main import app  # noqa: E402
from app.database.session import get_db  # noqa: E402
from datetime import datetime, timezone

from app.models.enums import UserRole, MatchStatus  # noqa: E402
from app.models.match import MatchModel  # noqa: E402
from app.models.scoring_config import ScoringConfigModel  # noqa: E402
from app.models.team import TeamModel  # noqa: E402
from app.models.user import UserModel  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"

_db_file = Path(tempfile.mktemp(suffix=".db"))


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    import sqlite3
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


test_engine = create_engine(f"sqlite:///{_db_file}", echo=False)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

import app.database.session as session_module
session_module.SessionLocal = TestSessionLocal


@pytest.fixture(scope="session", autouse=True)
def _setup_test_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with test_engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"DELETE FROM {table.name}"))
        conn.commit()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def organizer(db_session: Session) -> UserModel:
    user = UserModel(
        username="organizer",
        email="organizer@fifa-scoring.com",
        password_hash=hash_password("password123"),
        role=UserRole.ORGANIZER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def organizer_headers(organizer: UserModel) -> dict[str, str]:
    token = create_access_token(data={"sub": str(organizer.id), "role": organizer.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def team_a(db_session: Session) -> TeamModel:
    team = TeamModel(
        team_id="A",
        name="Team A",
        code="A",
        team_leader_name="Leader A",
    )
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)
    return team


@pytest.fixture
def team_leader(db_session: Session, team_a: TeamModel) -> UserModel:
    user = UserModel(
        username="teamleader",
        email="teama@gmail.com",
        password_hash=hash_password("password123"),
        role=UserRole.TEAM_LEADER,
    )
    db_session.add(user)
    db_session.flush()
    team_a.user_id = user.id
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def team_leader_headers(team_leader: UserModel) -> dict[str, str]:
    token = create_access_token(
        data={"sub": str(team_leader.id), "role": team_leader.role}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_match(db_session: Session) -> MatchModel:
    match = MatchModel(
        match_number=1,
        home_team_name="Brazil",
        away_team_name="Argentina",
        scheduled_at=datetime(2026, 6, 15, 20, 0, 0, tzinfo=timezone.utc),
        freeze_deadline=datetime(2026, 6, 14, 20, 0, 0, tzinfo=timezone.utc),
        status=MatchStatus.SCHEDULED,
    )
    db_session.add(match)
    db_session.commit()
    db_session.refresh(match)
    return match


@pytest.fixture
def default_scoring_config(db_session: Session) -> ScoringConfigModel:
    config = ScoringConfigModel(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="Test Default",
        is_active=True,
        version=1,
    )
    db_session.add(config)
    db_session.commit()
    db_session.refresh(config)
    return config


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())
