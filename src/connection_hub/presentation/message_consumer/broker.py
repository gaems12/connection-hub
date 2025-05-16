# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from faststream.nats import NatsBroker
from faststream import ExceptionMiddleware

from connection_hub.domain import DomainError
from connection_hub.application import ApplicationError
from .routes import router
from .middlewares import OperationIdMiddleware, LoggingMiddleware


def create_broker(nats_url: str) -> NatsBroker:
    error_handlers = {
        DomainError: lambda _: ...,
        ApplicationError: lambda _: ...,
    }
    exception_middleware = ExceptionMiddleware(error_handlers)

    middlewares = [
        OperationIdMiddleware,
        LoggingMiddleware,
        exception_middleware,
    ]
    broker = NatsBroker(
        nats_url,
        middlewares=middlewares,
    )

    broker.include_router(router)

    return broker
