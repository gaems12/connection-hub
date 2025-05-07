# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

from uuid import UUID

from faststream.broker.message import StreamMessage

from connection_hub.domain import UserId
from connection_hub.application import IdentityProvider


class MessageBrokerIdentityProvider(IdentityProvider):
    __slots__ = ("_message",)

    def __init__(self, message: StreamMessage):
        self._message = message

    async def user_id(self) -> UserId:
        decoded_message = await self._message.decode()
        if not decoded_message or not isinstance(decoded_message, dict):
            raise Exception(
                "Message received from message broker cannot be "
                "converted to dict.",
            )

        user_id = decoded_message.get("current_user_id")
        if not user_id:
            raise Exception(
                "Message received from message borker has no "
                "'current_user_id'.",
            )

        return UserId(UUID(user_id))  # type: ignore[arg-type]
