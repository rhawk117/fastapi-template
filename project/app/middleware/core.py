from app.core.config import AppConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .exception_handling import register_exception_handlers
from .request_logging import RequestLoggingMiddleware


def register_middleware(app: FastAPI, config: AppConfig) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ALLOW_ORIGINS,
        allow_credentials=config.CORS_ALLOW_CREDENTIALS,
        allow_methods=config.CORS_ALLOW_METHODS,
        allow_headers=config.CORS_ALLOW_HEADERS,
    )

    app.add_middleware(RequestLoggingMiddleware)

    register_exception_handlers(app)
