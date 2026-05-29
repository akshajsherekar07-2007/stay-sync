"""Global error handler middleware.

Catches StaySyncException subclasses and returns
the standard API error envelope defined in PROJECT_RULES.md.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import StaySyncException


def register_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(StaySyncException)
    async def staysync_exception_handler(
        request: Request,
        exc: StaySyncException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {},
                },
            },
        )
