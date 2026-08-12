import re
import logging

from sqlalchemy.exc import IntegrityError

from app.exceptions.base_exception import ApplicationException

logger = logging.getLogger(__name__)

_UNIQUE_PATTERN = re.compile(
    r"UNIQUE constraint failed:\s+(\S+)", re.IGNORECASE
)
_UNIQUE_PATTERN_PG = re.compile(
    r'duplicate key value violates unique constraint\s+"(\S+)"', re.IGNORECASE
)
_FK_PATTERN = re.compile(
    r"FOREIGN KEY constraint failed", re.IGNORECASE
)
_FK_PATTERN_PG = re.compile(
    r'insert or update on table "(\S+)" violates foreign key constraint', re.IGNORECASE
)
_NOTNULL_PATTERN = re.compile(
    r"NOT NULL constraint failed:\s+(\S+)", re.IGNORECASE
)


def _extract_detail(error: IntegrityError) -> str:
    msg = str(error.orig) if error.orig else str(error)
    for pat in (_UNIQUE_PATTERN, _UNIQUE_PATTERN_PG, _FK_PATTERN, _FK_PATTERN_PG, _NOTNULL_PATTERN):
        m = pat.search(msg)
        if m:
            return m.group(0)
    return msg[:120]


def handle_integrity_error(error: IntegrityError) -> ApplicationException:
    msg = str(error.orig) if error.orig else str(error)
    detail = _extract_detail(error)
    logger.warning("IntegrityError: %s", detail)

    if _UNIQUE_PATTERN.search(msg) or _UNIQUE_PATTERN_PG.search(msg):
        return ApplicationException(
            error_code="DUPLICATE_ENTRY",
            message="A record with the same unique identifier already exists",
            status_code=409,
            details={"detail": detail},
        )

    if _FK_PATTERN.search(msg) or _FK_PATTERN_PG.search(msg):
        return ApplicationException(
            error_code="FOREIGN_KEY_VIOLATION",
            message="Referenced resource does not exist",
            status_code=400,
            details={"detail": detail},
        )

    if _NOTNULL_PATTERN.search(msg):
        return ApplicationException(
            error_code="NULL_CONSTRAINT_VIOLATION",
            message="A required field is missing",
            status_code=400,
            details={"detail": detail},
        )

    return ApplicationException(
        error_code="DATABASE_ERROR",
        message="A database error occurred",
        status_code=400,
        details={"detail": detail},
    )
