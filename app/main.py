"""FastAPI application entrypoint for the EcoLogistics Carbon Tracker Service."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.routes.emissions import router as emissions_router
from app.domain.exceptions import EmissionsDomainError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Application factory for the Carbon Tracker Service.

    Using a factory (rather than a bare module-level ``FastAPI()``) keeps
    app construction testable and side-effect free at import time.
    """
    app = FastAPI(
        title="EcoLogistics Carbon Tracker Service",
        description=(
            "Microservicio para el cálculo de emisiones de CO2 generadas por "
            "el transporte de mercancías."
        ),
        version="1.0.0",
    )

    app.include_router(emissions_router)

    @app.exception_handler(EmissionsDomainError)
    async def handle_domain_error(request: Request, exc: EmissionsDomainError) -> JSONResponse:
        """Map business-rule violations to 422 without leaking internals."""
        logger.warning(
            "domain_validation_error",
            extra={"path": request.url.path, "detail": str(exc)},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        """Last-resort safety net: never expose stack traces or internals to clients."""
        logger.exception("unexpected_error", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Ha ocurrido un error interno inesperado."},
        )

    return app


app = create_app()
