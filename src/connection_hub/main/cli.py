# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

import sys
from importlib.metadata import version
from typing import Annotated

from cyclopts import App, Parameter
from faststream.cli.main import cli as run_faststream
from taskiq.cli.scheduler.run import run_scheduler_loop

from .task_executor import create_task_executor_app


def main() -> None:
    app = create_cli_app()
    app()


def create_cli_app() -> App:
    app = App(
        name="Connection Hub",
        version=version("connection_hub"),
        help_format="rich",
    )
    app.command(run_message_consumer)
    app.command(run_task_executor)

    return app


def run_message_consumer(
    workers: Annotated[
        str,
        Parameter("--workers", show_default=True),
    ] = "1",
) -> None:
    """Run message consumer."""
    sys.argv = [
        "faststream",
        "run",
        "connection_hub.main.message_consumer:create_message_consumer_app",
        "--workers",
        workers,
        "--factory",
    ]
    run_faststream()


async def run_task_executor():
    """Run task executor."""
    task_executor = create_task_executor_app()
    await run_scheduler_loop(task_executor)
