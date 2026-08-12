import re


def normalize_team_name(name: str) -> str:
    normalized = name.lower().strip()
    normalized = re.sub(r'[\s_\-]+', '', normalized)
    return normalized


def is_team_name_duplicate(db_session, name: str, exclude_id=None) -> bool:
    from app.models.team import TeamModel
    norm = normalize_team_name(name)
    query = db_session.query(TeamModel).filter(TeamModel.name_normalized == norm)
    if exclude_id is not None:
        from sqlalchemy import Uuid as SA_Uuid
        query = query.filter(TeamModel.id != exclude_id)
    return query.first() is not None
