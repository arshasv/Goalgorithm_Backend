"""
TRUE HARD RESET for the GOALGORITHM system.

Truncates ALL application tables with CASCADE,
removes ALL uploaded files,
and reseeds ONLY mandatory reference data.

Usage:
    cd backend && python hard_reset.py

DANGER: This destroys ALL application data irreversibly.
"""
import logging
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.auth_service import hash_password
from app.config import settings
from app.database.base import Base
from app.database.connection import engine
from app.database.session import SessionLocal
from app.models.enums import UserRole
from app.models.leaderboard_visibility import LeaderboardVisibilityModel
from app.models.scoring_config import ScoringConfigModel
from app.models.upload_window import UploadWindowModel
from app.models.user import UserModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("hard_reset")


# ── All application tables in no particular order (CASCADE handles FKs) ──────
ALL_TABLES = [
    "player_predictions",
    "player_actuals",
    "model_executions",
    "model_evaluations",
    "model_uploads",
    "predictions",
    "actual_results",
    "scores",
    "cumulative_phase_scores",
    "leaderboard",
    "technical_evaluations",
    "presentation_evaluations",
    "model_submissions",
    "team_members",
    "password_reset_otps",
    "teams",
    "users",
    "matches",
    "judges",
    "presentation_rounds",
    "scoring_configs",
    "upload_window_config",
    "leaderboard_visibility",
]

# Tables that must NOT be truncated
PRESERVED_TABLES = {"alembic_version"}


def truncate_all(db: Session) -> dict[str, int]:
    """TRUNCATE every application table with CASCADE + RESTART IDENTITY.

    Returns a dict of table_name -> rows_affected (approximate).
    """
    logger.info("─── Truncating all application tables ───")
    before = {}
    for t in ALL_TABLES:
        try:
            before[t] = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        except Exception:
            before[t] = -1  # table might not exist

    table_list = ", ".join(ALL_TABLES)
    db.execute(
        text(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE")
    )
    db.commit()
    logger.info(f"Truncated {len(ALL_TABLES)} tables via TRUNCATE ... CASCADE")

    after = {}
    for t in ALL_TABLES:
        try:
            after[t] = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        except Exception:
            after[t] = -1

    deleted_counts = {}
    for t in ALL_TABLES:
        if before[t] >= 0:
            deleted_counts[t] = before[t] - after[t]
            if deleted_counts[t] > 0:
                logger.info(f"  {t}: {before[t]} rows deleted")

    logger.info("All application tables are now empty.")
    return deleted_counts


def clean_uploaded_files():
    """Remove ALL uploaded model files and temp execution artifacts."""
    logger.info("─── Cleaning uploaded files ───")

    backend_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        ("backend/uploads/models", os.path.join(backend_dir, "uploads", "models")),
        ("/tmp/model_uploads", "/tmp/model_uploads"),
    ]

    for label, path in paths:
        resolved = os.path.abspath(path)
        if os.path.isdir(resolved):
            count = 0
            for fname in os.listdir(resolved):
                fpath = os.path.join(resolved, fname)
                try:
                    if os.path.isfile(fpath) or os.path.islink(fpath):
                        os.remove(fpath)
                        count += 1
                    elif os.path.isdir(fpath):
                        shutil.rmtree(fpath)
                        count += 1
                except Exception as e:
                    logger.warning(f"  Failed to remove {fpath}: {e}")
            logger.info(f"  {label}: removed {count} file(s)")
        else:
            logger.info(f"  {label}: directory does not exist, nothing to clean")


def reseed_mandatory_data(db: Session):
    """Re-seed ONLY the data required for the application to function."""
    logger.info("─── Reseeding mandatory reference data ───")

    # 1. Organizer admin account
    org = UserModel(
        username="admin",
        email="arshas@opentrends.net",
        password_hash=hash_password("admin123"),
        role=UserRole.ORGANIZER,
        is_active=True,
    )
    db.add(org)
    db.flush()
    logger.info(f"  users: created ORGANIZER 'arshas@opentrends.net' / 'admin123'")

    # 2. Default active scoring config
    config = ScoringConfigModel(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="Default 2026",
        is_active=True,
        version=1,
    )
    db.add(config)
    db.flush()
    logger.info(f"  scoring_configs: created default active config 'Default 2026'")

    # 3. Default leaderboard visibility (all visible, analytics off)
    vis = LeaderboardVisibilityModel(
        show_all_teams_leaderboard=True,
        show_rank=True,
        show_team_name=True,
        show_phase_scores=True,
        show_phase_1_score=True,
        show_technical_score=True,
        show_presentation_score=True,
        show_final_score=True,
        show_total_points=True,
        show_score_breakdown=True,
        show_predictions_count=True,
        show_correct_predictions=True,
        analytics_visibility_enabled=False,
        show_model_analytics=True,
        show_prediction_analytics=True,
        show_technical_analytics=True,
        show_presentation_analytics=True,
        show_overall_comparison=True,
        show_judge_analytics=True,
        show_leaderboard_analytics=True,
    )
    db.add(vis)
    db.flush()
    logger.info(f"  leaderboard_visibility: created default visibility row")

    # 4. Default upload window config (disabled)
    upload = UploadWindowModel(
        is_enabled=False,
        start_time=None,
        end_time=None,
    )
    db.add(upload)
    db.flush()
    logger.info(f"  upload_window_config: created default disabled config")

    db.commit()
    logger.info("Mandatory reference data reseeded successfully.")


def verify_reset(db: Session) -> bool:
    """Verify that every application table is empty and mandatory rows exist."""
    logger.info("─── Verification ───")
    all_ok = True

    # All content tables should be empty (exclude reseeded reference tables)
    RESEEDED = {"users", "scoring_configs", "leaderboard_visibility", "upload_window_config"}
    content_tables = [t for t in ALL_TABLES if t not in RESEEDED]
    for t in sorted(content_tables):
        try:
            count = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        except Exception as e:
            logger.error(f"  {t}: ERROR — {e}")
            all_ok = False
            continue
        if count == 0:
            logger.info(f"  ✓ {t}: empty")
        else:
            logger.warning(f"  ✗ {t}: {count} row(s) remain — UNEXPECTED")
            all_ok = False

    # alembic_version must still exist
    try:
        av = db.execute(text("SELECT COUNT(*) FROM alembic_version")).scalar()
        logger.info(f"  ✓ alembic_version: preserved ({av} row(s))")
    except Exception:
        logger.error("  ✗ alembic_version table is missing!")
        all_ok = False

    # Check mandatory seed rows
    checks = [
        ("users (ORGANIZER)",
         "SELECT COUNT(*) FROM users WHERE role = 'ORGANIZER'"),
        ("scoring_configs (active default)",
         "SELECT COUNT(*) FROM scoring_configs WHERE is_active = TRUE"),
        ("leaderboard_visibility",
         "SELECT COUNT(*) FROM leaderboard_visibility"),
        ("upload_window_config",
         "SELECT COUNT(*) FROM upload_window_config"),
    ]
    for label, sql in checks:
        try:
            count = db.execute(text(sql)).scalar()
            if count >= 1:
                logger.info(f"  ✓ {label}: {count} row(s)")
            else:
                logger.warning(f"  ✗ {label}: MISSING")
                all_ok = False
        except Exception as e:
            logger.error(f"  ✗ {label}: ERROR — {e}")
            all_ok = False

    # Verify file storage is clean
    for path in [
        os.path.join(os.path.dirname(__file__), "uploads", "models"),
        "/tmp/model_uploads",
    ]:
        if os.path.isdir(path):
            remaining = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            if remaining:
                logger.warning(f"  ✗ {path}: {len(remaining)} file(s) remain")
                all_ok = False
            else:
                logger.info(f"  ✓ {path}: clean")

    return all_ok


def main():
    logger.info("=" * 60)
    logger.info("  GOALGORITHM — TRUE HARD RESET")
    logger.info("=" * 60)
    logger.info(f"Database: {settings.database_url}")

    # Confirm with user
    print("\n⚠️  DANGER: This will DESTROY ALL application data!", file=sys.stderr)
    print("  - All teams, matches, predictions, scores, evaluations", file=sys.stderr)
    print("  - All uploaded model files and execution history", file=sys.stderr)
    print("  - All leaderboard data and analytics", file=sys.stderr)
    print("  - All users (except the default organizer)", file=sys.stderr)
    print("\nMandatory reference data will be re-created:", file=sys.stderr)
    print("  - Admin account: arshas@opentrends.net / admin123", file=sys.stderr)
    print("  - Default scoring configuration", file=sys.stderr)
    print("  - Default leaderboard visibility settings", file=sys.stderr)
    print("  - Default upload window configuration", file=sys.stderr)
    print("\nThe alembic_version table is PRESERVED.", file=sys.stderr)

    try:
        response = input("\nType 'YES' to proceed: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.", file=sys.stderr)
        sys.exit(1)

    if response != "YES":
        print("Aborted.", file=sys.stderr)
        sys.exit(0)

    db = SessionLocal()
    try:
        # Step 1: Truncate all tables
        deleted = truncate_all(db)

        # Step 2: Remove uploaded files
        clean_uploaded_files()

        # Step 3: Re-seed mandatory data
        reseed_mandatory_data(db)

        # Step 4: Verify
        print()
        ok = verify_reset(db)

        print()
        if ok:
            logger.info("=" * 60)
            logger.info("  HARD RESET COMPLETE — system is in fresh-install state")
            logger.info("=" * 60)
        else:
            logger.warning("=" * 60)
            logger.warning("  HARD RESET completed with WARNINGS — see above")
            logger.warning("=" * 60)
            sys.exit(1)

    except Exception as e:
        db.rollback()
        logger.error(f"Fatal error during reset: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
