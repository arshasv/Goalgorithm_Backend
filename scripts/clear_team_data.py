"""
Safely delete all TEAM_LEADER users and their associated data.
Preserves ORGANIZER accounts and system configuration.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.database.session import SessionLocal  # noqa: E402
from app.models.enums import UserRole  # noqa: E402


def clear_team_data() -> dict[str, int]:
    db = SessionLocal()
    stats: dict[str, int] = {}
    try:
        team_leader_users = db.execute(
            text("SELECT id, username, email FROM users WHERE role = :role"),
            {"role": UserRole.TEAM_LEADER.value},
        ).fetchall()

        if not team_leader_users:
            print("No TEAM_LEADER users found. Nothing to clean.")
            return stats

        user_ids = [u[0] for u in team_leader_users]

        teams = db.execute(
            text("SELECT id, team_id FROM teams WHERE user_id = ANY(:uids)"),
            {"uids": user_ids},
        ).fetchall()

        team_uuids = [t[0] for t in teams]
        team_uuid_strs = [str(t[0]) for t in teams]

        result = db.execute(
            text("DELETE FROM password_reset_otps WHERE user_id = ANY(:uids)"),
            {"uids": user_ids},
        )
        stats["password_reset_otps"] = result.rowcount

        if team_uuid_strs:
            result = db.execute(
                text("DELETE FROM predictions WHERE team_id = ANY(:tids)"),
                {"tids": team_uuid_strs},
            )
            stats["predictions"] = result.rowcount

            result = db.execute(
                text("DELETE FROM scores WHERE team_id = ANY(:tids)"),
                {"tids": team_uuid_strs},
            )
            stats["scores"] = result.rowcount

            result = db.execute(
                text("DELETE FROM cumulative_phase_scores WHERE team_id = ANY(:tids)"),
                {"tids": team_uuid_strs},
            )
            stats["cumulative_phase_scores"] = result.rowcount

            result = db.execute(
                text("DELETE FROM technical_evaluations WHERE team_id = ANY(:tids)"),
                {"tids": team_uuid_strs},
            )
            stats["technical_evaluations"] = result.rowcount

            result = db.execute(
                text("DELETE FROM presentation_evaluations WHERE team_id = ANY(:tids)"),
                {"tids": team_uuid_strs},
            )
            stats["presentation_evaluations"] = result.rowcount

            result = db.execute(
                text("DELETE FROM leaderboard WHERE team_id = ANY(:tids)"),
                {"tids": team_uuid_strs},
            )
            stats["leaderboard"] = result.rowcount

        if team_uuids:
            result = db.execute(
                text("DELETE FROM model_submissions WHERE team_id = ANY(:tuids)"),
                {"tuids": team_uuids},
            )
            stats["model_submissions"] = result.rowcount

            result = db.execute(
                text("DELETE FROM team_members WHERE team_id = ANY(:tuids)"),
                {"tuids": team_uuids},
            )
            stats["team_members"] = result.rowcount

            result = db.execute(
                text("DELETE FROM teams WHERE id = ANY(:tuids)"),
                {"tuids": team_uuids},
            )
            stats["teams"] = result.rowcount

        # Also delete orphan demo teams (created by seed.py) that have no user_id
        orphan_teams = db.execute(
            text("SELECT id, team_id FROM teams WHERE user_id IS NULL"),
        ).fetchall()

        if orphan_teams:
            orphan_uuid_objs = [t[0] for t in orphan_teams]
            orphan_uuid_strs = [str(t[0]) for t in orphan_teams]

            result = db.execute(
                text("DELETE FROM predictions WHERE team_id = ANY(:tids)"),
                {"tids": orphan_uuid_strs},
            )
            stats.setdefault("predictions", 0)
            stats["predictions"] += result.rowcount

            result = db.execute(
                text("DELETE FROM scores WHERE team_id = ANY(:tids)"),
                {"tids": orphan_uuid_strs},
            )
            stats.setdefault("scores", 0)
            stats["scores"] += result.rowcount

            result = db.execute(
                text("DELETE FROM cumulative_phase_scores WHERE team_id = ANY(:tids)"),
                {"tids": orphan_uuid_strs},
            )
            stats.setdefault("cumulative_phase_scores", 0)
            stats["cumulative_phase_scores"] += result.rowcount

            result = db.execute(
                text("DELETE FROM technical_evaluations WHERE team_id = ANY(:tids)"),
                {"tids": orphan_uuid_strs},
            )
            stats.setdefault("technical_evaluations", 0)
            stats["technical_evaluations"] += result.rowcount

            result = db.execute(
                text("DELETE FROM presentation_evaluations WHERE team_id = ANY(:tids)"),
                {"tids": orphan_uuid_strs},
            )
            stats.setdefault("presentation_evaluations", 0)
            stats["presentation_evaluations"] += result.rowcount

            result = db.execute(
                text("DELETE FROM leaderboard WHERE team_id = ANY(:tids)"),
                {"tids": orphan_uuid_strs},
            )
            stats.setdefault("leaderboard", 0)
            stats["leaderboard"] += result.rowcount

            result = db.execute(
                text("DELETE FROM model_submissions WHERE team_id = ANY(:tuids)"),
                {"tuids": orphan_uuid_objs},
            )
            stats.setdefault("model_submissions", 0)
            stats["model_submissions"] += result.rowcount

            result = db.execute(
                text("DELETE FROM team_members WHERE team_id = ANY(:tuids)"),
                {"tuids": orphan_uuid_objs},
            )
            stats.setdefault("team_members", 0)
            stats["team_members"] += result.rowcount

            result = db.execute(
                text("DELETE FROM teams WHERE id = ANY(:tuids)"),
                {"tuids": orphan_uuid_objs},
            )
            stats.setdefault("teams", 0)
            stats["teams"] += result.rowcount

        result = db.execute(
            text("DELETE FROM users WHERE id = ANY(:uids)"),
            {"uids": user_ids},
        )
        stats["users"] = result.rowcount

        db.commit()
        return stats
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main():
    print("=" * 60)
    print("  Clear Team Data — FIFA Scoring System")
    print("=" * 60)

    confirm = input(
        "\nThis will permanently delete ALL TEAM_LEADER users, teams, "
        "predictions, scores, evaluations, and leaderboard data.\n"
        "Organizer accounts and system configuration will be preserved.\n\n"
        "Type 'yes' to continue: "
    )
    if confirm.strip().lower() != "yes":
        print("Aborted.")
        sys.exit(0)

    try:
        stats = clear_team_data()
        print("\nCleanup completed successfully!")
        print("-" * 40)
        print(f"  Password reset OTPs:  {stats.get('password_reset_otps', 0)}")
        print(f"  Predictions:          {stats.get('predictions', 0)}")
        print(f"  Scores:               {stats.get('scores', 0)}")
        print(f"  Cumulative scores:    {stats.get('cumulative_phase_scores', 0)}")
        print(f"  Technical evals:      {stats.get('technical_evaluations', 0)}")
        print(f"  Presentation evals:   {stats.get('presentation_evaluations', 0)}")
        print(f"  Leaderboard entries:  {stats.get('leaderboard', 0)}")
        print(f"  Model submissions:    {stats.get('model_submissions', 0)}")
        print(f"  Team members:         {stats.get('team_members', 0)}")
        print(f"  Teams:                {stats.get('teams', 0)}")
        print(f"  Users (TEAM_LEADER):  {stats.get('users', 0)}")
        print("-" * 40)
    except Exception as e:
        print(f"\nError during cleanup: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
