"""
Safely delete all prediction submissions and prediction-derived scores/results.
Preserves users, teams, team_members, matches, actual_results, judges,
presentation/technical evaluations, configuration, and all other data.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.database.session import SessionLocal  # noqa: E402


def clear_predictions() -> dict[str, int]:
    db = SessionLocal()
    stats: dict[str, int] = {}
    try:
        # 1. Delete player_predictions first (FK -> predictions.id)
        result = db.execute(text("DELETE FROM player_predictions"))
        stats["player_predictions"] = result.rowcount

        # 2. Delete predictions
        result = db.execute(text("DELETE FROM predictions"))
        stats["predictions"] = result.rowcount

        # 3. Delete prediction-derived scores
        result = db.execute(text("DELETE FROM scores"))
        stats["scores"] = result.rowcount

        # 4. Delete cumulative phase scores (contain phase1 prediction score)
        result = db.execute(text("DELETE FROM cumulative_phase_scores"))
        stats["cumulative_phase_scores"] = result.rowcount

        # 5. Delete leaderboard cache (contains phase1/final scores from predictions)
        result = db.execute(text("DELETE FROM leaderboard"))
        stats["leaderboard"] = result.rowcount

        db.commit()
        return stats
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def count_preserved(db) -> dict[str, int]:
    counts = {}
    tables = [
        "users", "teams", "team_members", "matches",
        "actual_results", "judges", "technical_evaluations",
        "presentation_evaluations", "presentation_scores",
        "scoring_configs", "model_submissions", "leaderboard_visibility",
    ]
    for table in tables:
        result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
        counts[table] = result.scalar()
    return counts


def main():
    print("=" * 60)
    print("  Clear Prediction Data — FIFA Scoring System")
    print("=" * 60)

    confirm = input(
        "\nThis will permanently DELETE ALL:\n"
        "  - predictions\n"
        "  - player_predictions\n"
        "  - scores (prediction-derived)\n"
        "  - cumulative_phase_scores\n"
        "  - leaderboard\n\n"
        "The following will be PRESERVED:\n"
        "  - users, teams, team_members\n"
        "  - matches, actual_results\n"
        "  - judges, presentation/technical evaluations\n"
        "  - configuration, model submissions\n\n"
        "Type 'yes' to continue: "
    )
    if confirm.strip().lower() != "yes":
        print("Aborted.")
        sys.exit(0)

    db = SessionLocal()
    try:
        preserved = count_preserved(db)
    except Exception:
        pass
    finally:
        db.close()

    try:
        stats = clear_predictions()
        print("\nCleanup completed successfully!")
        print("-" * 40)
        print("  Deleted:")
        print(f"    Predictions:           {stats.get('predictions', 0)}")
        print(f"    Player predictions:    {stats.get('player_predictions', 0)}")
        print(f"    Scores:                {stats.get('scores', 0)}")
        print(f"    Cumulative scores:     {stats.get('cumulative_phase_scores', 0)}")
        print(f"    Leaderboard entries:   {stats.get('leaderboard', 0)}")
        print()
        print("  Preserved:")
        print(f"    Users:                 {preserved.get('users', '?')}")
        print(f"    Teams:                 {preserved.get('teams', '?')}")
        print(f"    Team members:          {preserved.get('team_members', '?')}")
        print(f"    Matches:               {preserved.get('matches', '?')}")
        print(f"    Actual results:        {preserved.get('actual_results', '?')}")
        print(f"    Judges:                {preserved.get('judges', '?')}")
        print(f"    Technical evals:       {preserved.get('technical_evaluations', '?')}")
        print(f"    Presentation evals:    {preserved.get('presentation_evaluations', '?')}")
        print(f"    Presentation scores:   {preserved.get('presentation_scores', '?')}")
        print(f"    Scoring configs:       {preserved.get('scoring_configs', '?')}")
        print(f"    Model submissions:     {preserved.get('model_submissions', '?')}")
        print(f"    Leaderboard settings:  {preserved.get('leaderboard_visibility', '?')}")
        print("-" * 40)
    except Exception as e:
        print(f"\nError during cleanup: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
