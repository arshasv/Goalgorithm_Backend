from sqlalchemy import text
from app.database.connection import SessionLocal

def wipe_data():
    db = SessionLocal()
    try:
        # Disable foreign key checks for the session
        db.execute(text("SET session_replication_role = 'replica';"))
        
        tables_to_wipe = [
            "scores",
            "model_evaluations",
            "predictions",
            "actual_results",
            "matches",
            "model_submissions",
            "team_members",
            "teams",
            "leaderboard",
            "leaderboard_visibility",
            "presentation_evaluations",
            "technical_evaluations",
            "upload_windows",
            "scoring_config"
        ]
        
        for table in tables_to_wipe:
            try:
                db.execute(text(f"TRUNCATE TABLE {table} CASCADE;"))
                print(f"Truncated {table}")
            except Exception as e:
                print(f"Skipped or error on {table}: {e}")
                db.rollback()
                
        # Re-enable foreign key checks
        db.execute(text("SET session_replication_role = 'origin';"))
        db.commit()
        print("Data wipe complete!")
    finally:
        db.close()

if __name__ == "__main__":
    wipe_data()
