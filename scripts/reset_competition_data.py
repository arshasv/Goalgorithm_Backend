#!/usr/bin/env python3
"""
reset_competition_data.py
=========================
Safely clears competition data for fresh deployment while preserving
essential configuration (organizer, teams, judges, matches, scoring config).

Deletes (in FK-safe order):
  - player_predictions       (child of predictions)
  - predictions              (AI match predictions)
  - scores                   (per-match team scores)
  - cumulative_phase_scores
  - presentation_scores      (per-judge marks — child of judges)
  - presentation_evaluations
  - technical_evaluations
  - leaderboard
  - password_reset_otps      (FK → users — MUST go before users)
  - team_members             (FK → teams)
  - users (TEAM_LEADER only) (leader accounts / credentials)
  - teams.user_id nulled     (unlinks ownership; team name/id kept)

Preserves:
  - organizer user account
  - teams (names + identifiers — only ownership cleared)
  - judges
  - matches (and actual_results)
  - scoring_config / upload_window / leaderboard_visibility
  - model_submissions (optional — see flag below)
  - password_reset_otps (cleanup handled separately)

Usage:
    cd /path/to/fifa-scoring-system/backend
    python scripts/reset_competition_data.py [--dry-run] [--also-clear-model-submissions]

Options:
    --dry-run                       Print what would be deleted without committing.
    --also-clear-model-submissions  Also delete model submission records.
"""

import sys
import os
import argparse
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Bootstrap: make sure the app package is importable when running from CLI
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, BACKEND_DIR)

# Load .env so DATABASE_URL is available
from dotenv import load_dotenv
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings

# ---------------------------------------------------------------------------
# Colour helpers for terminal output
# ---------------------------------------------------------------------------
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}✓{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}⚠{RESET}  {msg}")
def err(msg):  print(f"  {RED}✗{RESET} {msg}")
def info(msg): print(f"  {CYAN}→{RESET} {msg}")
def header(msg): print(f"\n{BOLD}{msg}{RESET}")


# ---------------------------------------------------------------------------
# Parse CLI flags
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Reset competition data for fresh GOALGORITHM deployment."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without making any DB changes.",
    )
    parser.add_argument(
        "--also-clear-model-submissions",
        action="store_true",
        help="Also delete model submission records (default: kept).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Core reset logic
# ---------------------------------------------------------------------------
def run_reset(db: Session, dry_run: bool, clear_model_submissions: bool):
    counters = {}

    def delete_rows(label: str, table: str, where: str = "1=1", params: dict | None = None):
        """Count matching rows then delete them (unless dry-run)."""
        count_sql = text(f"SELECT COUNT(*) FROM {table} WHERE {where}")
        count = db.execute(count_sql, params or {}).scalar()
        counters[label] = count
        info(f"{label}: {count} row(s) found")
        if count and not dry_run:
            db.execute(text(f"DELETE FROM {table} WHERE {where}"), params or {})

    def zero_columns(label: str, table: str, updates: str, where: str = "1=1", params: dict | None = None):
        """Nullify specific columns instead of deleting rows."""
        count_sql = text(f"SELECT COUNT(*) FROM {table} WHERE {where}")
        count = db.execute(count_sql, params or {}).scalar()
        counters[label] = count
        info(f"{label}: {count} row(s) to update")
        if count and not dry_run:
            db.execute(text(f"UPDATE {table} SET {updates} WHERE {where}"), params or {})

    # ------------------------------------------------------------------
    # 1. SCORES & PREDICTIONS
    # ------------------------------------------------------------------
    header("🗑  Phase 1 – Clearing scores and predictions")

    # Child rows first (FK order)
    delete_rows("player_predictions", "player_predictions")
    delete_rows("predictions", "predictions")
    delete_rows("scores", "scores")
    delete_rows("cumulative_phase_scores", "cumulative_phase_scores")

    # ------------------------------------------------------------------
    # 2. EVALUATIONS
    # ------------------------------------------------------------------
    header("🗑  Phase 2 – Clearing technical & presentation evaluations")

    delete_rows("presentation_scores (judge marks)", "presentation_scores")
    delete_rows("presentation_evaluations", "presentation_evaluations")
    delete_rows("technical_evaluations", "technical_evaluations")

    # ------------------------------------------------------------------
    # 3. LEADERBOARD
    # ------------------------------------------------------------------
    header("🗑  Phase 3 – Clearing leaderboard")

    delete_rows("leaderboard entries", "leaderboard")

    # ------------------------------------------------------------------
    # 4. MODEL SUBMISSIONS (optional)
    # ------------------------------------------------------------------
    if clear_model_submissions:
        header("🗑  Phase 4 – Clearing model submissions (requested)")
        delete_rows("model_submissions", "model_submissions")
    else:
        counters["model_submissions (kept)"] = db.execute(
            text("SELECT COUNT(*) FROM model_submissions")
        ).scalar()
        warn("model_submissions preserved (use --also-clear-model-submissions to remove)")

    # ------------------------------------------------------------------
    # 5. TEAM REGISTRATIONS
    #    Correct FK deletion order:
    #      password_reset_otps → users (must delete OTPs BEFORE users)
    #      team_members (FK to teams)
    #      users (TEAM_LEADER only)
    #      teams.user_id (nulled — keeps team shells intact)
    # ------------------------------------------------------------------
    header("🗑  Phase 5 – Clearing team registrations")

    # OTPs reference users via FK — must go first
    try:
        delete_rows("password_reset_otps (pre-user)", "password_reset_otps")
    except Exception:
        warn("password_reset_otps table not found — skipped")

    delete_rows("team_members", "team_members")

    # Delete only team-leader accounts (preserve organizer)
    delete_rows(
        "team_leader user accounts",
        "users",
        "role = :role",
        {"role": "TEAM_LEADER"},
    )

    # Sever the team → user link so teams appear unregistered
    zero_columns(
        "team ownership links unlinked",
        "teams",
        "user_id = NULL, team_leader_name = ''",
        "user_id IS NOT NULL",
    )

    # (OTPs already deleted in Phase 5 before users)

    return counters


# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------
def print_summary(counters: dict, dry_run: bool, db: Session, clear_model_submissions: bool):
    header("📊 Summary")

    deleted_labels = [k for k in counters if "kept" not in k]
    kept_labels    = [k for k in counters if "kept" in k]

    if dry_run:
        print(f"\n  {YELLOW}[DRY RUN — no changes committed]{RESET}\n")

    print(f"\n  {BOLD}Would delete / deleted:{RESET}")
    for label in deleted_labels:
        count = counters[label]
        print(f"    {RED if count else GREEN}{'–' if count else '–'}{RESET}  {count:>5}  {label}")

    print(f"\n  {BOLD}Preserved:{RESET}")

    preserved = {
        "organizer accounts":       "SELECT COUNT(*) FROM users WHERE role = 'ORGANIZER'",
        "teams":                    "SELECT COUNT(*) FROM teams",
        "judges":                   "SELECT COUNT(*) FROM judges",
        "matches":                  "SELECT COUNT(*) FROM matches",
        "actual_results":           "SELECT COUNT(*) FROM actual_results",
        "scoring_configs":          "SELECT COUNT(*) FROM scoring_configs",
        "upload_window_config":     "SELECT COUNT(*) FROM upload_window_config",
        "leaderboard_visibility":   "SELECT COUNT(*) FROM leaderboard_visibility",
    }
    if not clear_model_submissions:
        preserved["model_submissions"] = "SELECT COUNT(*) FROM model_submissions"

    for label, sql in preserved.items():
        try:
            count = db.execute(text(sql)).scalar()
            print(f"    {GREEN}✓{RESET}  {count:>5}  {label}")
        except Exception:
            print(f"    {YELLOW}?{RESET}       {label} (table not found)")

    print()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def main():
    args = parse_args()

    print(f"\n{BOLD}{'='*60}")
    print("  GOALGORITHM Competition Data Reset Script")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*60}{RESET}")

    if args.dry_run:
        print(f"\n  {YELLOW}[DRY RUN MODE] — Nothing will be deleted.{RESET}")
    else:
        print(f"\n  {RED}[LIVE MODE] — Data will be permanently deleted.{RESET}")
        confirm = input("\n  Type 'YES' to continue: ").strip()
        if confirm != "YES":
            print(f"\n  {YELLOW}Aborted.{RESET}\n")
            sys.exit(0)

    # Connect
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db: Session = SessionLocal()

    try:
        counters = run_reset(db, args.dry_run, args.also_clear_model_submissions)

        if not args.dry_run:
            db.commit()
            ok("Transaction committed.")
        else:
            db.rollback()
            warn("Dry run — transaction rolled back.")

        print_summary(counters, args.dry_run, db, args.also_clear_model_submissions)

        if args.dry_run:
            print(f"  {YELLOW}To apply changes, run without --dry-run.{RESET}\n")
        else:
            print(f"  {GREEN}{BOLD}Reset complete. Teams are ready for fresh registration.{RESET}\n")

    except Exception as exc:
        db.rollback()
        err(f"Error during reset: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
