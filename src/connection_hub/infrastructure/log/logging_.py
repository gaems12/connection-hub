# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

import sys
import logging
from contextvars import ContextVar

from pythonjsonlogger.json import JsonFormatter

from .config import load_logging_config


log_extra_context_var: ContextVar[dict] = ContextVar(
    "log_extra_context_var",
    default={},
)


class _ContextVarLogExtraSetterFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        log_extra = log_extra_context_var.get()

        for key, value in log_extra.values():
            setattr(record, key, value)

        return True


def setup_logging() -> None:
    config = load_logging_config()

    stream_handler = logging.StreamHandler(sys.stdout)

    context_var_log_extra_filter = _ContextVarLogExtraSetterFilter()
    stream_handler.addFilter(context_var_log_extra_filter)

    json_formatter = JsonFormatter(
        fmt="%(timestamp)s %(levelname)s %(message)s",
        timestamp=True,
        json_ensure_ascii=False,
    )
    stream_handler.setFormatter(json_formatter)

    logging.basicConfig(level=config.level, handlers=[stream_handler])
