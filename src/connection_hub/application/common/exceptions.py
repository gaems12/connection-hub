# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = (
    "ApplicationError",
    "InvalidLobbyNameError",
    "InvalidLobbyRuleSetError",
    "InvalidLobbyPasswordError",
    "UserInLobbyError",
    "UserNotInLobbyError",
    "UserInGameError",
    "UserNotInGameError",
    "LobbyDoesNotExistError",
    "GameDoesNotExistError",
)


class ApplicationError(Exception): ...


class InvalidLobbyNameError(ApplicationError): ...


class InvalidLobbyRuleSetError(ApplicationError): ...


class InvalidLobbyPasswordError(ApplicationError): ...


class UserInLobbyError(ApplicationError): ...


class UserNotInLobbyError(ApplicationError): ...


class UserInGameError(ApplicationError): ...


class UserNotInGameError(ApplicationError): ...


class LobbyDoesNotExistError(ApplicationError): ...


class GameDoesNotExistError(ApplicationError): ...
