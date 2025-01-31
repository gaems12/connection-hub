# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from fastapi import FastAPI

from .routes import router


def setup_routes(app: FastAPI) -> None:
    app.include_router(router)
