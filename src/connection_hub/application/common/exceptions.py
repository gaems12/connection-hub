# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = (
    "ApplicationError",
    "UserInLobbyError",
    "UserInGameError",
)


class ApplicationError(Exception): ...


class UserInLobbyError(ApplicationError): ...


class UserInGameError(ApplicationError): ...
