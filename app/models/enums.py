import enum


class MatchStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    FROZEN = "FROZEN"
    COMPLETED = "COMPLETED"
    RESULT_ENTERED = "RESULT_ENTERED"
    SCORED = "SCORED"
    AWAITING_RESULT = "AWAITING_RESULT"


class PredictionStatus(str, enum.Enum):
    PENDING_VALIDATION = "PENDING_VALIDATION"
    VALIDATED = "VALIDATED"
    INVALID = "INVALID"
    LATE = "LATE"


class Winner(str, enum.Enum):
    HOME = "home"
    AWAY = "away"
    DRAW = "draw"


class FirstGoalTeam(str, enum.Enum):
    HOME = "home"
    AWAY = "away"
    NONE = "none"


class Grade(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"


class UserRole(str, enum.Enum):
    TEAM_LEADER = "TEAM_LEADER"
    ORGANIZER = "ORGANIZER"


class ExternalSyncStatus(str, enum.Enum):
    PENDING = "PENDING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"


class ModelStatus(str, enum.Enum):
    UPLOADED = "Uploaded"
    TESTING = "Testing"
    EVALUATED = "Evaluated"
    FAILED = "Failed"
