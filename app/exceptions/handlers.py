from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "APP_ERROR",
    ) -> None:
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        super().__init__(detail)


class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND",
        )


class ConflictException(AppException):
    """Resource conflict (e.g., duplicate)."""

    def __init__(self, detail: str = "Resource already exists") -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT",
        )


class UnauthorizedException(AppException):
    """Authentication failure."""

    def __init__(self, detail: str = "Not authenticated") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED",
        )


class ForbiddenException(AppException):
    """Authorization failure."""

    def __init__(self, detail: str = "Not authorized") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN",
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.error_code, "detail": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        errors: list[dict[str, Any]] = []
        for error in exc.errors():
            errors.append(
                {
                    "loc": list(error.get("loc", [])),
                    "msg": error.get("msg", ""),
                    "type": error.get("type", ""),
                }
            )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "VALIDATION_ERROR", "detail": errors},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "INTERNAL_ERROR", "detail": "An unexpected error occurred"},
        )
