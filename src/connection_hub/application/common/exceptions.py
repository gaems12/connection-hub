# Copyright (c) 2024, Egor Romanov.
# All rights reserved.

__all__ = (
    "ApplicationError",
    "UserInLobbyError",
    "UserNotInLobbyError",
    "UserInGameError",
    "UserNotInGameError",
    "LobbyDoesNotExistError",
)


class ApplicationError(Exception): ...


class UserInLobbyError(ApplicationError): ...


class UserNotInLobbyError(ApplicationError): ...


class UserInGameError(ApplicationError): ...


class UserNotInGameError(ApplicationError): ...


class LobbyDoesNotExistError(ApplicationError): ...
