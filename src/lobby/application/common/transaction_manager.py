# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = ("TransactionManager",)

from typing import Protocol


class TransactionManager(Protocol):
    async def commit(self) -> None:
        raise NotImplementedError
