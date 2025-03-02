# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from connection_hub.infrastructure import OperationId, log_extra_context_var


class ContextVarSetter:
    __slots__ = ("_operation_id",)

    def __init__(self, operation_id: OperationId):
        self._operation_id = operation_id

    def set(self) -> None:
        current_log_extra = log_extra_context_var.get().copy()
        current_log_extra["operation_id"] = self._operation_id
        log_extra_context_var.set(current_log_extra)
