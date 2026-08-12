from pathlib import Path
# pyright: ignore[reportMissingImports]
from dotenv import load_dotenv

_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=False)


import os  # noqa: E402 — load_dotenv must run first


class Settings:

    def __init__(self) -> None:
        self.app_name: str = os.environ.get("APP_NAME", "FIFA Scoring System")
        self.environment: str = os.environ.get("APP_ENV", "development")
        self.debug: bool = os.environ.get("DEBUG", "false").lower() == "true"

        self.api_prefix: str = os.environ.get("API_PREFIX", "/api/v1")
        self.api_version: str = os.environ.get("API_VERSION", "v1")
        self.host: str = os.environ.get("HOST", "0.0.0.0")
        self.port: int = int(os.environ.get("PORT", "8000"))

        self.database_url: str = os.environ["DATABASE_URL"]
        self.db_pool_size: int = int(os.environ.get("DB_POOL_SIZE", "5"))
        self.db_max_overflow: int = int(os.environ.get("DB_MAX_OVERFLOW", "10"))
        self.db_pool_pre_ping: bool = (
            os.environ.get("DB_POOL_PRE_PING", "true").lower() == "true"
        )
        self.db_pool_recycle: int = int(os.environ.get("DB_POOL_RECYCLE", "3600"))
        self.db_echo_sql: bool = (
            os.environ.get("DB_ECHO_SQL", "false").lower() == "true"
        )

        self.secret_key: str = os.environ.get("SECRET_KEY", "development_secret_key")
        self.access_token_expire_minutes: int = int(
            os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        )

        self.football_api_key: str = os.environ.get("FOOTBALL_API_KEY", "")
        self.football_api_base_url: str = os.environ.get(
            "FOOTBALL_API_BASE_URL", "https://v3.football.api-sports.io"
        )
        
        allowed_leagues_str = os.environ.get("FOOTBALL_ALLOWED_LEAGUES", "1,15")
        self.football_allowed_leagues: set[str] = {
            lg.strip() for lg in allowed_leagues_str.split(",") if lg.strip()
        }
        self.football_timezone: str = os.environ.get("FOOTBALL_TIMEZONE", "Asia/Kolkata")

        self.agentmail_api_key: str = os.environ.get("AGENTMAIL_API_KEY", "")
        self.agentmail_inbox_id: str = os.environ.get("AGENTMAIL_INBOX_ID", "")


settings = Settings()