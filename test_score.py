from app.database.session import SessionLocal
from app.api.scoring_routes import calculate_all_scores_for_match

db = SessionLocal()
match_id = "52039fc7-25eb-43c4-96ab-a47cd0038219"

try:
    res = calculate_all_scores_for_match(match_id, db, _organizer=None)
    print("Result:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
