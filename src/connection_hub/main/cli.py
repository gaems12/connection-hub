# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

import sys
from importlib.metadata import version
from typing import Annotated

from cyclopts import App, Parameter
from gunicorn.app.wsgiapp import run as run_gunicorn


def main() -> None:
    app = create_cli_app()
    app()


def create_cli_app() -> App:
    app = App(
        name="Connection Hub",
        version=version("connection_hub"),
        help_format="rich",
    )
    app.command(run_web_api)

    return app


def run_web_api(
    address: Annotated[
        str,
        Parameter("--address", show_default=True),
    ] = "0.0.0.0:8000",
    workers: Annotated[
        str,
        Parameter("--workers", show_default=True),
    ] = "1",
) -> None:
    """Run web api."""
    sys.argv = [
        "gunicorn",
        "--bind",
        address,
        "--workers",
        workers,
        "--worker-class",
        "uvicorn.workers.UvicornWorker",
        "connection_hub.main.web_api:create_web_api_app()",
    ]
    run_gunicorn()
