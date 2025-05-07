# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

import sys
import logging
from contextvars import ContextVar

from pythonjsonlogger.json import JsonFormatter

from connection_hub.infrastructure.operation_id import OperationId
from .config import load_logging_config


_log_extra: ContextVar[dict] = ContextVar("log_extra")


def set_operation_id(operation_id: OperationId) -> None:
    """
    Sets the operation ID in the exta context var.
    """
    current_log_extra = _log_extra.get({})
    current_log_extra["operation_id"] = operation_id
    _log_extra.set(current_log_extra)


def get_operation_id() -> OperationId:
    """
    Returns the operation ID from the exta context var.
    """
    current_log_extra = _log_extra.get({})
    return current_log_extra["operation_id"]


class _ContextVarLogExtraSetterFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        log_extra = _log_extra.get()

        for key, value in log_extra.items():
            setattr(record, key, value)

        return True


def setup_logging() -> None:
    config = load_logging_config()

    stream_handler = logging.StreamHandler(sys.stdout)

    context_var_log_extra_filter = _ContextVarLogExtraSetterFilter()
    stream_handler.addFilter(context_var_log_extra_filter)

    json_formatter = JsonFormatter(
        fmt=(
            "%(name)s %(levelname)s %(message)s %(module)s %(filename)s "
            "%(funcName)s %(timestamp)s"
        ),
        timestamp=True,
        json_ensure_ascii=False,
    )
    stream_handler.setFormatter(json_formatter)

    logging.basicConfig(level=config.level, handlers=[stream_handler])
