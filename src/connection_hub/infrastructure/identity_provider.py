# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = ("NATSIdentityProvider",)

from uuid import UUID

from faststream.broker.message import StreamMessage

from connection_hub.domain import UserId
from connection_hub.application import IdentityProvider


class NATSIdentityProvider(IdentityProvider):
    __slots__ = ("_message",)

    def __init__(self, message: StreamMessage):
        self._message = message

    async def user_id(self) -> UserId:
        decoded_message = await self._message.decode()
        if not decoded_message or not isinstance(decoded_message, dict):
            raise Exception("StreamMessage cannot be converter to dict.")

        user_id = decoded_message.get("user_id")
        return UserId(UUID(user_id))
