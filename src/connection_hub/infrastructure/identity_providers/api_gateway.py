# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

from uuid import UUID

from fastapi import Request

from connection_hub.domain import UserId
from connection_hub.application import IdentityProvider


class CommonWebAPIIdentityProvider(IdentityProvider):
    """
    Identity provider for processing requests from
    from any sources except centrifugo.
    """

    __slots__ = ("_request",)

    def __init__(self, request: Request):
        self._request = request

    async def user_id(self) -> UserId:
        user_id = self._request.headers.get("X-UserId")
        if not user_id:
            raise Exception("HTTP request's headers have no 'X-UserId' key.")

        return UserId(UUID(user_id))
