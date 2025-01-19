# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from importlib.metadata import version

from fastapi import FastAPI
from dishka.integrations.fastapi import FastapiProvider, setup_dishka

from lobby.infrastructure import ioc_container_factory
from lobby.presentation.web_api import (
    router,
    create_lobby_command_factory,
)


def create_web_api_app() -> FastAPI:
    app = FastAPI(
        title="Lobby",
        version=version("lobby"),
        swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    )
    app.include_router(router)

    ioc_container = ioc_container_factory(
        [create_lobby_command_factory],
        FastapiProvider(),
    )
    setup_dishka(ioc_container, app)

    return app
