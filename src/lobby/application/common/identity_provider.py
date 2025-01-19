# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = ("IdentityProvider",)

from typing import Protocol

from lobby.domain import UserId


class IdentityProvider(Protocol):
    async def user_id(self) -> UserId:
        raise NotImplementedError
