


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from asgi_correlation_id import CorrelationIdMiddleware



def register_middleware(app: FastAPI) -> None:

    MIDDLEWARE = [
        CorrelationIdMiddleware,
        CORSMiddleware
    ]