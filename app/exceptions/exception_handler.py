import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from sqlalchemy.exc import IntegrityError
from starlette.responses import JSONResponse

from app.exceptions.base_exception import ApplicationException
from app.exceptions.database_exceptions import handle_integrity_error
from app.services.leaderboard_service import LeaderboardError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: "FastAPI") -> None:
    @app.exception_handler(ApplicationException)
    async def application_exception_handler(
        _request: Request, exc: ApplicationException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        detail = []
        for err in errors:
            detail.append({
                "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", "Invalid value"),
            })
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": detail,
            },
        )

    @app.exception_handler(IntegrityError)
    async def sqlalchemy_integrity_handler(
        _request: Request, exc: IntegrityError
    ) -> JSONResponse:
        app_exc = handle_integrity_error(exc)
        return JSONResponse(
            status_code=app_exc.status_code,
            content=app_exc.to_dict(),
        )

    @app.exception_handler(LeaderboardError)
    async def leaderboard_error_handler(
        _request: Request, exc: LeaderboardError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error_code": "LEADERBOARD_ERROR",
                "message": str(exc),
                "details": {},
            },
        )

    @app.exception_handler(ResponseValidationError)
    async def response_validation_handler(
        _request: Request, exc: ResponseValidationError
    ) -> JSONResponse:
        logger.exception("Response validation error: %s", exc)
        errors = exc.errors()
        detail = []
        for err in errors:
            detail.append({
                "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", "Invalid value"),
            })
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_code": "RESPONSE_VALIDATION_ERROR",
                "message": "Internal server error: response data could not be serialized",
                "details": detail,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        _request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Unexpected server error occurred",
                "details": {},
            },
        )
