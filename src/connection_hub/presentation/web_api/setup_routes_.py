# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from fastapi import FastAPI

from .public_routes import public_router
from .internal_routes import internal_router


def setup_routes(app: FastAPI) -> None:
    app.include_router(public_router)
    app.include_router(internal_router)
