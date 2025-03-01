# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = ("OperationId", "default_operation_id_factory")

from typing import NewType
from uuid import UUID

from uuid_extensions import uuid7


OperationId = NewType("OperationId", UUID)


async def default_operation_id_factory() -> OperationId:
    """
    Operation id factory that should be used if
    there is no other factory
    (for example if no operation id was provided with request).
    """
    return OperationId(uuid7())
