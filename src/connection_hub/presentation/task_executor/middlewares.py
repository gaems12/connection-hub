# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

import logging
from uuid import UUID

from taskiq import TaskiqMiddleware, TaskiqMessage

from connection_hub.infrastructure import (
    OperationId,
    set_operation_id,
    default_operation_id_factory,
)


_logger = logging.getLogger(__name__)


class OperationIdMiddleware(TaskiqMiddleware):
    def pre_execute(self, message: TaskiqMessage) -> TaskiqMessage:
        operation_id = self._extract_operation_id(message)
        set_operation_id(operation_id)

        return message

    def _extract_operation_id(self, message: TaskiqMessage) -> OperationId:
        if not message.args:
            default_operation_id = default_operation_id_factory()

            _logger.warning(
                {
                    "message": (
                        "Takiq message has no operation id. "
                        "Default operation id will be used instead."
                    ),
                    "operation_id": default_operation_id,
                },
            )
            return default_operation_id

        raw_operation_id = message.args[0]
        try:
            return OperationId(UUID(raw_operation_id))
        except:
            default_operation_id = default_operation_id_factory()

            _logger.warning(
                {
                    "message": (
                        "Operation id from takiq message cannot be "
                        "converted to UUID."
                        "Default operation id will be used instead."
                    ),
                    "operation_id": default_operation_id,
                },
                exc_info=True,
            )
            return default_operation_id


class LoggingMiddleware(TaskiqMiddleware):
    def pre_execute(self, message: TaskiqMessage) -> TaskiqMessage:
        _logger.debug(
            {
                "message": "Got taskiq message.",
                "received_message": message.model_dump(mode="json"),
            },
        )
        return message
