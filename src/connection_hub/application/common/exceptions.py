# Copyright (c) 2024, Egor Romanov.
# All rights reserved.
# Licensed under the Personal Use License (see LICENSE).

__all__ = (
    "ApplicationError",
    "InvalidLobbyNameError",
    "InvalidLobbyRuleSetError",
    "InvalidLobbyPasswordError",
    "CurrentUserInLobbyError",
    "CurrentUserNotInLobbyError",
    "UserNotInLobbyError",
    "CurrentUserInGameError",
    "CurrentUserNotInGameError",
    "UserNotInGameError",
    "LobbyDoesNotExistError",
    "GameDoesNotExistError",
)


class ApplicationError(Exception): ...


class InvalidLobbyNameError(ApplicationError): ...


class InvalidLobbyRuleSetError(ApplicationError): ...


class InvalidLobbyPasswordError(ApplicationError): ...


class CurrentUserInLobbyError(ApplicationError): ...


class CurrentUserNotInLobbyError(ApplicationError): ...


class UserNotInLobbyError(ApplicationError): ...


class CurrentUserInGameError(ApplicationError): ...


class CurrentUserNotInGameError(ApplicationError): ...


class UserNotInGameError(ApplicationError): ...


class LobbyDoesNotExistError(ApplicationError): ...


class GameDoesNotExistError(ApplicationError): ...
