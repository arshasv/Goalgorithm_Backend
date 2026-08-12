import os

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import Settings, settings


class TestDatabaseSettings:
    def test_default_url_contains_postgresql(self):
        assert settings.database_url.startswith("postgresql") or settings.database_url.startswith("sqlite")

    def test_pool_settings_have_defaults(self):
        assert isinstance(settings.db_pool_size, int)
        assert isinstance(settings.db_max_overflow, int)
        assert isinstance(settings.db_pool_pre_ping, bool)
        assert isinstance(settings.db_pool_recycle, int)

    def test_custom_url_via_env(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h:5432/db")
        s = Settings()
        assert s.database_url == "postgresql://u:p@h:5432/db"


class TestEngineCreation:
    def test_engine_imports(self):
        from app.database.connection import engine

        assert engine is not None
        assert engine.url is not None

    def test_engine_has_configured_pool(self):
        from app.database.connection import engine

        assert engine.pool.size() == settings.db_pool_size


class TestSession:
    def test_engine_is_bound_to_session(self):
        from app.database.session import SessionLocal

        assert SessionLocal.kw["bind"] is not None

    def test_get_db_yields_session(self):
        from app.database.session import get_db

        gen = get_db()
        db = next(gen)
        assert isinstance(db, Session)
        try:
            next(gen)
        except StopIteration:
            pass


class TestIntegrationWithSQLite:
    @pytest.fixture
    def sqlite_session(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine("sqlite:///:memory:", echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    def test_basic_query_execution(self, sqlite_session):
        result = sqlite_session.execute(text("SELECT 1 AS value"))
        assert result.scalar_one() == 1

    def test_create_and_query_table(self, sqlite_session):
        sqlite_session.execute(
            text("CREATE TABLE ping (id INTEGER PRIMARY KEY, val TEXT)")
        )
        sqlite_session.commit()

        sqlite_session.execute(text("INSERT INTO ping (val) VALUES ('pong')"))
        sqlite_session.commit()

        result = sqlite_session.execute(text("SELECT val FROM ping"))
        assert result.scalar_one() == "pong"
