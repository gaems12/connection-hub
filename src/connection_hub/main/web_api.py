# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from importlib.metadata import version

from fastapi import FastAPI
from dishka.integrations.fastapi import FastapiProvider, setup_dishka

from connection_hub.infrastructure import ioc_container_factory
from connection_hub.presentation.web_api import (
    setup_routes,
    create_lobby_command_factory,
    join_lobby_command_factory,
)


def create_web_api_app() -> FastAPI:
    app = FastAPI(
        title="Connection Hub",
        version=version("connection_hub"),
        swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    )
    ioc_container = ioc_container_factory(
        [create_lobby_command_factory, join_lobby_command_factory],
        FastapiProvider(),
    )

    setup_routes(app)
    setup_dishka(ioc_container, app)

    return app
